import logging
import math
from datetime import date, datetime
from typing import Optional
from sqlalchemy import desc
from database.connection import get_db
from database.models import RestockingRecommendation, Medicine, SalesRecord
from ml.predictor import predictor

logger = logging.getLogger(__name__)


class RestockService:
    @staticmethod
    def calculate_restock_requirements(medicine_id: int, forecast_days: int = 7) -> dict:
        """
        Calculates explainable restocking requirements using ML demand prediction,
        lead time, current stock, and safety stock formulas.
        """
        # 1. Fetch medicine details and forecast
        forecast_res = predictor.predict_demand(medicine_id=medicine_id, forecast_days=forecast_days)

        with get_db() as session:
            med = session.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
            if not med:
                raise ValueError("Medicine not found")

            current_stock = med.current_stock
            reorder_level = med.reorder_level
            lead_time = max(1, med.lead_time)
            unit_price = med.unit_price
            med_name = med.medicine_name
            category = med.category
            supplier = med.supplier

            # Calculate sales standard deviation for statistical safety stock
            sales_history = (
                session.query(SalesRecord.quantity_sold)
                .filter(SalesRecord.medicine_id == medicine_id)
                .order_by(SalesRecord.sale_date.desc())
                .limit(30)
                .all()
            )

        predicted_demand = forecast_res["total_predicted_demand"]
        avg_daily_demand = forecast_res["average_daily_demand"]

        # 2. Safety Stock Formula:
        # Standard inventory formula: SS = Z * sigma * sqrt(lead_time)
        # Using 95% service level factor Z = 1.65
        if sales_history and len(sales_history) >= 7:
            quantities = [s[0] for s in sales_history]
            std_dev = float(math.sqrt(sum((x - avg_daily_demand) ** 2 for x in quantities) / len(quantities)))
            safety_stock = int(round(1.65 * std_dev * math.sqrt(lead_time)))
        else:
            safety_stock = int(round(avg_daily_demand * lead_time * 0.5))

        safety_stock = max(5, safety_stock)

        # 3. Explainable Restock Quantity Formula:
        # Recommended Restock = max(0, Predicted Demand + Safety Stock - Current Stock)
        raw_restock = predicted_demand + safety_stock - current_stock
        recommended_quantity = max(0, int(round(raw_restock)))

        # 4. Priority Assessment
        days_of_supply = round(current_stock / avg_daily_demand, 1) if avg_daily_demand > 0 else 999.0

        if current_stock == 0:
            priority = "Critical"
            reason = f"STOCKOUT: Currently zero units available. Urgent reorder required."
        elif days_of_supply <= lead_time:
            priority = "Critical"
            reason = f"Imminent Stockout Risk: Only {current_stock} units left (~{days_of_supply} days supply), while supplier lead time is {lead_time} days."
        elif current_stock <= reorder_level:
            priority = "High"
            reason = f"Low Stock: Current inventory ({current_stock} units) is below reorder threshold ({reorder_level} units)."
        elif recommended_quantity > 0:
            priority = "Medium"
            reason = f"Preventive Restock: Projected {forecast_days}-day demand ({predicted_demand}) exceeds stock after safety buffer ({safety_stock})."
        else:
            priority = "Low"
            reason = f"Adequate Stock: Current inventory ({current_stock} units) is sufficient for projected demand ({predicted_demand} units)."

        estimated_cost = round(recommended_quantity * unit_price, 2)

        return {
            "medicine_id": medicine_id,
            "medicine_name": med_name,
            "category": category,
            "current_stock": current_stock,
            "reorder_level": reorder_level,
            "lead_time_days": lead_time,
            "predicted_demand": predicted_demand,
            "avg_daily_demand": avg_daily_demand,
            "safety_stock": safety_stock,
            "recommended_quantity": recommended_quantity,
            "days_of_supply": days_of_supply,
            "unit_price": unit_price,
            "estimated_cost": estimated_cost,
            "supplier": supplier,
            "priority": priority,
            "reason": reason,
            "formula_breakdown": f"max(0, {predicted_demand} [Predicted Demand] + {safety_stock} [Safety Stock] - {current_stock} [Current Stock]) = {recommended_quantity} units"
        }

    @staticmethod
    def get_all_recommendations(status_filter: Optional[str] = None):
        with get_db() as session:
            query = (
                session.query(
                    RestockingRecommendation.recommendation_id,
                    RestockingRecommendation.medicine_id,
                    Medicine.medicine_name,
                    Medicine.category,
                    Medicine.current_stock,
                    Medicine.reorder_level,
                    Medicine.unit_price,
                    Medicine.supplier,
                    Medicine.lead_time,
                    RestockingRecommendation.recommended_quantity,
                    RestockingRecommendation.approved_quantity,
                    RestockingRecommendation.status,
                    RestockingRecommendation.priority,
                    RestockingRecommendation.reason,
                    RestockingRecommendation.recommendation_date,
                    RestockingRecommendation.processed_at
                )
                .join(Medicine, RestockingRecommendation.medicine_id == Medicine.medicine_id)
            )

            if status_filter and status_filter != "All":
                query = query.filter(RestockingRecommendation.status == status_filter)

            results = query.order_by(
                desc(RestockingRecommendation.recommendation_date),
                desc(RestockingRecommendation.recommendation_id)
            ).all()

            return [
                {
                    "recommendation_id": r.recommendation_id,
                    "medicine_id": r.medicine_id,
                    "medicine_name": r.medicine_name,
                    "category": r.category,
                    "current_stock": r.current_stock,
                    "reorder_level": r.reorder_level,
                    "unit_price": r.unit_price,
                    "supplier": r.supplier,
                    "lead_time": r.lead_time,
                    "recommended_quantity": r.recommended_quantity,
                    "approved_quantity": r.approved_quantity,
                    "status": r.status,
                    "priority": r.priority,
                    "reason": r.reason,
                    "recommendation_date": r.recommendation_date,
                    "processed_at": r.processed_at,
                    "estimated_cost": round((r.approved_quantity or r.recommended_quantity) * r.unit_price, 2)
                }
                for r in results
            ]

    @staticmethod
    def approve_recommendation(recommendation_id: int, approved_qty: Optional[int] = None, fulfill_immediately: bool = False) -> bool:
        with get_db() as session:
            rec = session.query(RestockingRecommendation).filter(RestockingRecommendation.recommendation_id == recommendation_id).first()
            if not rec:
                return False

            qty = approved_qty if (approved_qty is not None and approved_qty > 0) else rec.recommended_quantity
            rec.status = "Approved"
            rec.approved_quantity = qty
            rec.processed_at = datetime.now()

            # If user selects immediate fulfillment (simulate order arrival)
            if fulfill_immediately:
                med = session.query(Medicine).filter(Medicine.medicine_id == rec.medicine_id).first()
                if med:
                    med.current_stock += qty

            return True

    @staticmethod
    def reject_recommendation(recommendation_id: int, rejection_reason: Optional[str] = None) -> bool:
        with get_db() as session:
            rec = session.query(RestockingRecommendation).filter(RestockingRecommendation.recommendation_id == recommendation_id).first()
            if not rec:
                return False

            rec.status = "Rejected"
            rec.processed_at = datetime.now()
            if rejection_reason:
                rec.reason = f"{rec.reason} | Rejected: {rejection_reason}"
            return True

    @staticmethod
    def fulfill_order(recommendation_id: int) -> bool:
        """Simulates warehouse delivery receipt: marks order fulfilled and increments medicine stock."""
        with get_db() as session:
            rec = session.query(RestockingRecommendation).filter(RestockingRecommendation.recommendation_id == recommendation_id).first()
            if not rec or rec.status != "Approved":
                return False

            qty = rec.approved_quantity or rec.recommended_quantity
            med = session.query(Medicine).filter(Medicine.medicine_id == rec.medicine_id).first()
            if med:
                med.current_stock += qty
                rec.status = "Fulfilled"
                return True
            return False
