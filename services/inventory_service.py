import logging
from datetime import date, timedelta
from typing import Optional
from sqlalchemy import or_, func
from database.connection import get_db
from database.models import Medicine, SalesRecord

logger = logging.getLogger(__name__)


class InventoryService:
    @staticmethod
    def get_all_medicines(category: Optional[str] = None, low_stock_only: bool = False, search: Optional[str] = None):
        """Fetches medicines list with optional filtering."""
        with get_db() as session:
            query = session.query(Medicine)
            if category and category != "All":
                query = query.filter(Medicine.category == category)
            if low_stock_only:
                query = query.filter(Medicine.current_stock <= Medicine.reorder_level)
            if search:
                term = f"%{search.strip()}%"
                query = query.filter(or_(Medicine.medicine_name.ilike(term), Medicine.category.ilike(term)))

            medicines = query.order_by(Medicine.medicine_name).all()
            # Return list of dicts to prevent DetachedInstance issues
            return [
                {
                    "medicine_id": m.medicine_id,
                    "medicine_name": m.medicine_name,
                    "category": m.category,
                    "current_stock": m.current_stock,
                    "reorder_level": m.reorder_level,
                    "unit_price": m.unit_price,
                    "expiry_date": m.expiry_date,
                    "supplier": m.supplier,
                    "lead_time": m.lead_time,
                    "is_low_stock": m.current_stock <= m.reorder_level,
                    "stock_status": "Out of Stock" if m.current_stock == 0 else ("Low Stock" if m.current_stock <= m.reorder_level else "Adequate"),
                    "days_to_expiry": (m.expiry_date - date.today()).days
                }
                for m in medicines
            ]

    @staticmethod
    def get_medicine_by_id(medicine_id: int) -> Optional[dict]:
        with get_db() as session:
            m = session.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
            if not m:
                return None
            return {
                "medicine_id": m.medicine_id,
                "medicine_name": m.medicine_name,
                "category": m.category,
                "current_stock": m.current_stock,
                "reorder_level": m.reorder_level,
                "unit_price": m.unit_price,
                "expiry_date": m.expiry_date,
                "supplier": m.supplier,
                "lead_time": m.lead_time,
                "days_to_expiry": (m.expiry_date - date.today()).days
            }

    @staticmethod
    def add_medicine(name: str, category: str, current_stock: int, reorder_level: int, unit_price: float, expiry_date: date, supplier: str, lead_time: int) -> int:
        with get_db() as session:
            med = Medicine(
                medicine_name=name.strip(),
                category=category.strip(),
                current_stock=int(current_stock),
                reorder_level=int(reorder_level),
                unit_price=float(unit_price),
                expiry_date=expiry_date,
                supplier=supplier.strip() if supplier else "Primary Pharma Distributor",
                lead_time=int(lead_time)
            )
            session.add(med)
            session.flush()
            med_id = med.medicine_id
        return med_id

    @staticmethod
    def update_medicine(medicine_id: int, **kwargs) -> bool:
        with get_db() as session:
            med = session.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
            if not med:
                return False
            for key, val in kwargs.items():
                if hasattr(med, key):
                    setattr(med, key, val)
            return True

    @staticmethod
    def update_stock(medicine_id: int, quantity_change: int) -> int:
        """Adds quantity_change to current_stock (positive for restock, negative for sale/reduction)."""
        with get_db() as session:
            med = session.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
            if not med:
                raise ValueError("Medicine not found")
            new_stock = max(0, med.current_stock + quantity_change)
            med.current_stock = new_stock
            return new_stock

    @staticmethod
    def get_inventory_kpis() -> dict:
        """Returns high-level inventory metrics for the dashboard."""
        with get_db() as session:
            medicines = session.query(Medicine).all()
            today = date.today()

            total_skus = len(medicines)
            total_units = sum(m.current_stock for m in medicines)
            total_valuation = sum(m.current_stock * m.unit_price for m in medicines)
            low_stock_count = sum(1 for m in medicines if m.current_stock <= m.reorder_level)
            expiring_90_days = sum(1 for m in medicines if 0 <= (m.expiry_date - today).days <= 90)
            critical_stock_count = sum(1 for m in medicines if m.current_stock <= (m.reorder_level * 0.3))

            categories = list(set(m.category for m in medicines))

            return {
                "total_skus": total_skus,
                "total_units": total_units,
                "total_valuation": round(total_valuation, 2),
                "low_stock_count": low_stock_count,
                "expiring_soon_count": expiring_90_days,
                "critical_stock_count": critical_stock_count,
                "categories": sorted(categories)
            }
