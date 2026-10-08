import sys
from datetime import date, timedelta
from database.connection import get_db, init_db

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from database.models import (
    Medicine, SalesRecord, RestockingRecommendation, Alert, PharmacyUser
)


def test_database_crud():
    init_db()

    with get_db() as session:
        # 1. Test Medicine creation
        test_med = Medicine(
            medicine_name="Test-Ibuprofen-Express-400mg",
            category="Analgesic / Test",
            current_stock=25,
            reorder_level=50,
            unit_price=15.0,
            expiry_date=date.today() + timedelta(days=200),
            supplier="Test Supplier Ltd.",
            lead_time=2
        )
        session.add(test_med)
        session.flush()
        med_id = test_med.medicine_id
        assert med_id is not None, "Medicine ID should be generated"

        # 2. Test Sales Record creation
        sale = SalesRecord(
            medicine_id=med_id,
            sale_date=date.today(),
            quantity_sold=10
        )
        session.add(sale)
        session.flush()
        assert sale.sales_id is not None, "Sale ID should be generated"

        # 3. Test Restocking Recommendation
        rec = RestockingRecommendation(
            medicine_id=med_id,
            recommended_quantity=75,
            status="Pending",
            recommendation_date=date.today(),
            priority="High",
            reason="Test restock trigger"
        )
        session.add(rec)
        session.flush()
        assert rec.status == "Pending"

        # 4. Test Alert
        alert = Alert(
            medicine_id=med_id,
            alert_type="Low Stock",
            alert_status="Active",
            alert_date=date.today(),
            message="Test low stock alert",
            priority="High"
        )
        session.add(alert)
        session.flush()
        assert alert.alert_id is not None

        # Clean up test records
        session.delete(alert)
        session.delete(rec)
        session.delete(sale)
        session.delete(test_med)

    print("✓ test_database_crud PASSED")


if __name__ == "__main__":
    test_database_crud()
