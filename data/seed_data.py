import logging
from datetime import date, timedelta
from database.connection import get_db, init_db, reset_db
from database.models import (
    PharmacyUser, Medicine, SalesRecord, Alert, RestockingRecommendation
)
from data.synthetic_generator import generate_synthetic_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_database(force_reset: bool = False):
    """
    Seeds the database with initial users, medicine catalog, 1-year sales, and initial alerts.
    """
    if force_reset:
        logger.info("Resetting existing database schema...")
        reset_db()
    else:
        init_db()

    with get_db() as session:
        # Check if already seeded
        existing_meds_count = session.query(Medicine).count()
        if existing_meds_count > 0 and not force_reset:
            logger.info(f"Database already contains {existing_meds_count} medicines. Skipping re-seed.")
            return

        logger.info("Generating synthetic 1-year pharmacy dataset...")
        medicines_df, sales_df = generate_synthetic_data(num_days=365)

        # 1. Seed Pharmacy Users
        default_users = [
            PharmacyUser(
                username="pharmacist_admin",
                password_hash="pbkdf2_sha256$healthsupplyai$demo_hash",
                role="Senior Pharmacist & Store Admin"
            ),
            PharmacyUser(
                username="staff_pharmacist",
                password_hash="pbkdf2_sha256$healthsupplyai$staff_hash",
                role="Staff Pharmacist"
            )
        ]
        session.add_all(default_users)
        session.flush()

        # 2. Seed Medicines
        medicine_objects = {}
        for _, row in medicines_df.iterrows():
            med = Medicine(
                medicine_id=int(row["medicine_id"]),
                medicine_name=str(row["medicine_name"]),
                category=str(row["category"]),
                current_stock=int(row["current_stock"]),
                reorder_level=int(row["reorder_level"]),
                unit_price=float(row["unit_price"]),
                expiry_date=row["expiry_date"],
                supplier=str(row["supplier"]),
                lead_time=int(row["lead_time"])
            )
            session.add(med)
            medicine_objects[med.medicine_id] = med

        session.flush()
        logger.info(f"Inserted {len(medicines_df)} medicines into catalog.")

        # 3. Seed Historical Sales in batches
        sales_records = []
        for _, row in sales_df.iterrows():
            sale = SalesRecord(
                medicine_id=int(row["medicine_id"]),
                sale_date=row["sale_date"],
                quantity_sold=int(row["quantity_sold"])
            )
            sales_records.append(sale)

        # Batch insert for performance
        batch_size = 1000
        for i in range(0, len(sales_records), batch_size):
            session.bulk_save_objects(sales_records[i:i + batch_size])
        session.flush()
        logger.info(f"Inserted {len(sales_records)} historical sales records.")

        # 4. Generate Initial Real-Time Alerts
        today = date.today()
        initial_alerts = []

        for med in medicine_objects.values():
            # Low stock alert check
            if med.current_stock <= med.reorder_level:
                priority = "Critical" if med.current_stock <= (med.reorder_level * 0.4) else "High"
                initial_alerts.append(
                    Alert(
                        medicine_id=med.medicine_id,
                        alert_type="Low Stock",
                        alert_status="Active",
                        alert_date=today,
                        message=f"Stock for '{med.medicine_name}' ({med.current_stock} units) is below reorder threshold ({med.reorder_level} units).",
                        priority=priority
                    )
                )

            # Expiry risk check (< 90 days)
            days_to_expiry = (med.expiry_date - today).days
            if days_to_expiry <= 90:
                priority = "Critical" if days_to_expiry <= 30 else "High"
                initial_alerts.append(
                    Alert(
                        medicine_id=med.medicine_id,
                        alert_type="Expiry Risk",
                        alert_status="Active",
                        alert_date=today,
                        message=f"Batch for '{med.medicine_name}' will expire in {days_to_expiry} days ({med.expiry_date}). Plan clearance or replace batch.",
                        priority=priority
                    )
                )

        session.add_all(initial_alerts)
        session.flush()
        logger.info(f"Generated {len(initial_alerts)} initial alerts.")

        # 5. Generate Initial Pending Restocking Recommendations for Low-Stock Medicines
        initial_recommendations = []
        for med in medicine_objects.values():
            if med.current_stock <= med.reorder_level:
                # Basic initial recommendation (will be superseded/refined by the Agentic workflow)
                rec_qty = (med.reorder_level * 2) - med.current_stock
                priority = "Critical" if med.current_stock < (med.reorder_level * 0.3) else "High"
                initial_recommendations.append(
                    RestockingRecommendation(
                        medicine_id=med.medicine_id,
                        recommended_quantity=int(rec_qty),
                        status="Pending",
                        recommendation_date=today,
                        priority=priority,
                        reason=f"Current stock ({med.current_stock}) is below reorder level ({med.reorder_level}). Restock needed before stockout."
                    )
                )

        session.add_all(initial_recommendations)
        logger.info(f"Created {len(initial_recommendations)} initial restocking recommendations.")

    logger.info("Database seeding finished successfully!")


if __name__ == "__main__":
    seed_database(force_reset=True)
