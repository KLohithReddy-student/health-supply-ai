import logging
from datetime import date, timedelta
from typing import Optional
from sqlalchemy import func, desc
from database.connection import get_db
from database.models import Alert, Medicine, SalesRecord

logger = logging.getLogger(__name__)


class AlertService:
    @staticmethod
    def scan_and_generate_alerts() -> int:
        """
        Scans all medicines in inventory and generates alerts for:
        1. Low Stock (current_stock <= reorder_level)
        2. Expiry Risk (expiry_date within 90 days)
        3. Demand Surge (recent sales spiking > 40% over baseline)
        """
        today = date.today()
        new_alerts_count = 0

        with get_db() as session:
            medicines = session.query(Medicine).all()

            for med in medicines:
                # 1. Low Stock Check
                if med.current_stock <= med.reorder_level:
                    existing = session.query(Alert).filter(
                        Alert.medicine_id == med.medicine_id,
                        Alert.alert_type == "Low Stock",
                        Alert.alert_status == "Active"
                    ).first()

                    if not existing:
                        priority = "Critical" if med.current_stock <= (med.reorder_level * 0.3) else "High"
                        alert = Alert(
                            medicine_id=med.medicine_id,
                            alert_type="Low Stock",
                            alert_status="Active",
                            alert_date=today,
                            message=f"Stock alert: '{med.medicine_name}' has only {med.current_stock} units remaining (Reorder Threshold: {med.reorder_level}).",
                            priority=priority
                        )
                        session.add(alert)
                        new_alerts_count += 1

                # 2. Expiry Risk Check
                days_left = (med.expiry_date - today).days
                if days_left <= 90:
                    existing = session.query(Alert).filter(
                        Alert.medicine_id == med.medicine_id,
                        Alert.alert_type == "Expiry Risk",
                        Alert.alert_status == "Active"
                    ).first()

                    if not existing:
                        priority = "Critical" if days_left <= 30 else ("High" if days_left <= 60 else "Medium")
                        status_str = f"EXPIRED {abs(days_left)} days ago" if days_left < 0 else f"expires in {days_left} days"
                        alert = Alert(
                            medicine_id=med.medicine_id,
                            alert_type="Expiry Risk",
                            alert_status="Active",
                            alert_date=today,
                            message=f"Expiry warning: Batch of '{med.medicine_name}' {status_str} ({med.expiry_date}).",
                            priority=priority
                        )
                        session.add(alert)
                        new_alerts_count += 1

                # 3. Demand Surge Check (compare 7-day average to 30-day average)
                recent_7 = (
                    session.query(func.avg(SalesRecord.quantity_sold))
                    .filter(
                        SalesRecord.medicine_id == med.medicine_id,
                        SalesRecord.sale_date >= today - timedelta(days=7)
                    )
                    .scalar() or 0.0
                )
                prev_30 = (
                    session.query(func.avg(SalesRecord.quantity_sold))
                    .filter(
                        SalesRecord.medicine_id == med.medicine_id,
                        SalesRecord.sale_date >= today - timedelta(days=30)
                    )
                    .scalar() or 0.0
                )

                if prev_30 > 0 and recent_7 >= (prev_30 * 1.45):
                    existing = session.query(Alert).filter(
                        Alert.medicine_id == med.medicine_id,
                        Alert.alert_type == "Demand Surge",
                        Alert.alert_status == "Active"
                    ).first()

                    if not existing:
                        surge_pct = int(((recent_7 - prev_30) / prev_30) * 100)
                        alert = Alert(
                            medicine_id=med.medicine_id,
                            alert_type="Demand Surge",
                            alert_status="Active",
                            alert_date=today,
                            message=f"Demand Surge: Sales for '{med.medicine_name}' surged by {surge_pct}% over the last 7 days.",
                            priority="High"
                        )
                        session.add(alert)
                        new_alerts_count += 1

        return new_alerts_count

    @staticmethod
    def get_all_alerts(status_filter: Optional[str] = "Active", priority_filter: Optional[str] = None):
        with get_db() as session:
            query = (
                session.query(
                    Alert.alert_id,
                    Alert.medicine_id,
                    Medicine.medicine_name,
                    Medicine.category,
                    Medicine.current_stock,
                    Alert.alert_type,
                    Alert.alert_status,
                    Alert.alert_date,
                    Alert.message,
                    Alert.priority
                )
                .join(Medicine, Alert.medicine_id == Medicine.medicine_id)
            )

            if status_filter and status_filter != "All":
                query = query.filter(Alert.alert_status == status_filter)
            if priority_filter and priority_filter != "All":
                query = query.filter(Alert.priority == priority_filter)

            alerts = query.order_by(
                desc(Alert.alert_date),
                desc(Alert.alert_id)
            ).all()

            return [
                {
                    "alert_id": a.alert_id,
                    "medicine_id": a.medicine_id,
                    "medicine_name": a.medicine_name,
                    "category": a.category,
                    "current_stock": a.current_stock,
                    "alert_type": a.alert_type,
                    "alert_status": a.alert_status,
                    "alert_date": a.alert_date,
                    "message": a.message,
                    "priority": a.priority
                }
                for a in alerts
            ]

    @staticmethod
    def update_alert_status(alert_id: int, new_status: str) -> bool:
        with get_db() as session:
            alert = session.query(Alert).filter(Alert.alert_id == alert_id).first()
            if alert:
                alert.alert_status = new_status
                return True
            return False
