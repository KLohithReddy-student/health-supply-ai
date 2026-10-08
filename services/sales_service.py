import logging
from datetime import date, timedelta
from typing import Optional
import pandas as pd
from sqlalchemy import func, desc
from database.connection import get_db
from database.models import SalesRecord, Medicine

logger = logging.getLogger(__name__)


class SalesService:
    @staticmethod
    def log_sale(medicine_id: int, quantity_sold: int, sale_date: Optional[date] = None) -> dict:
        """
        Logs a sale transaction and automatically deducts the quantity from current inventory stock.
        """
        if quantity_sold <= 0:
            raise ValueError("Quantity sold must be a positive integer.")

        if sale_date is None:
            sale_date = date.today()

        with get_db() as session:
            med = session.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
            if not med:
                raise ValueError(f"Medicine with ID {medicine_id} does not exist.")

            if med.current_stock < quantity_sold:
                raise ValueError(f"Insufficient stock for {med.medicine_name}. Available: {med.current_stock}, Requested: {quantity_sold}")

            # Deduct stock
            med.current_stock -= quantity_sold

            # Add sales record
            sale = SalesRecord(
                medicine_id=medicine_id,
                sale_date=sale_date,
                quantity_sold=quantity_sold
            )
            session.add(sale)
            session.flush()

            result = {
                "sales_id": sale.sales_id,
                "medicine_id": med.medicine_id,
                "medicine_name": med.medicine_name,
                "quantity_sold": quantity_sold,
                "remaining_stock": med.current_stock,
                "sale_date": sale_date.strftime("%Y-%m-%d")
            }

        return result

    @staticmethod
    def get_sales_history(medicine_id: Optional[int] = None, start_date: Optional[date] = None, end_date: Optional[date] = None, limit: int = 500):
        with get_db() as session:
            query = (
                session.query(
                    SalesRecord.sales_id,
                    SalesRecord.medicine_id,
                    Medicine.medicine_name,
                    Medicine.category,
                    SalesRecord.sale_date,
                    SalesRecord.quantity_sold,
                    (SalesRecord.quantity_sold * Medicine.unit_price).label("total_revenue")
                )
                .join(Medicine, SalesRecord.medicine_id == Medicine.medicine_id)
            )

            if medicine_id:
                query = query.filter(SalesRecord.medicine_id == medicine_id)
            if start_date:
                query = query.filter(SalesRecord.sale_date >= start_date)
            if end_date:
                query = query.filter(SalesRecord.sale_date <= end_date)

            records = query.order_by(desc(SalesRecord.sale_date), SalesRecord.sales_id.desc()).limit(limit).all()

            return [
                {
                    "sales_id": r.sales_id,
                    "medicine_id": r.medicine_id,
                    "medicine_name": r.medicine_name,
                    "category": r.category,
                    "sale_date": r.sale_date,
                    "quantity_sold": r.quantity_sold,
                    "total_revenue": round(float(r.total_revenue or 0), 2)
                }
                for r in records
            ]

    @staticmethod
    def get_top_selling_medicines(days: int = 30, limit: int = 6):
        with get_db() as session:
            start_date = date.today() - timedelta(days=days)
            query = (
                session.query(
                    Medicine.medicine_name,
                    func.sum(SalesRecord.quantity_sold).label("total_sold"),
                    func.sum(SalesRecord.quantity_sold * Medicine.unit_price).label("revenue")
                )
                .join(Medicine, SalesRecord.medicine_id == Medicine.medicine_id)
                .filter(SalesRecord.sale_date >= start_date)
                .group_by(Medicine.medicine_name)
                .order_by(desc("total_sold"))
                .limit(limit)
                .all()
            )

            return [
                {
                    "medicine_name": r.medicine_name,
                    "total_sold": int(r.total_sold or 0),
                    "revenue": round(float(r.revenue or 0), 2)
                }
                for r in query
            ]

    @staticmethod
    def get_daily_sales_timeline(medicine_id: Optional[int] = None, days: int = 60):
        with get_db() as session:
            start_date = date.today() - timedelta(days=days)
            query = session.query(
                SalesRecord.sale_date,
                func.sum(SalesRecord.quantity_sold).label("daily_total")
            ).filter(SalesRecord.sale_date >= start_date)

            if medicine_id:
                query = query.filter(SalesRecord.medicine_id == medicine_id)

            query = query.group_by(SalesRecord.sale_date).order_by(SalesRecord.sale_date).all()

            return [
                {
                    "date": r.sale_date.strftime("%Y-%m-%d"),
                    "quantity": int(r.daily_total or 0)
                }
                for r in query
            ]

    @staticmethod
    def bulk_import_sales(df: pd.DataFrame) -> int:
        """
        Validates and imports a pandas DataFrame of sales into the database.
        Expected columns: medicine_id (or medicine_name), sale_date, quantity_sold
        """
        count = 0
        with get_db() as session:
            med_map = {m.medicine_name.lower(): m.medicine_id for m in session.query(Medicine).all()}
            id_set = set(med_map.values())

            for _, row in df.iterrows():
                med_id = None
                if "medicine_id" in row and int(row["medicine_id"]) in id_set:
                    med_id = int(row["medicine_id"])
                elif "medicine_name" in row and str(row["medicine_name"]).lower() in med_map:
                    med_id = med_map[str(row["medicine_name"]).lower()]

                if not med_id:
                    continue

                sale_dt = pd.to_datetime(row["sale_date"]).date()
                qty = int(row["quantity_sold"])

                session.add(SalesRecord(
                    medicine_id=med_id,
                    sale_date=sale_dt,
                    quantity_sold=qty
                ))
                count += 1

        return count
