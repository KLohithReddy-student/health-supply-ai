from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class PharmacyUser(Base):
    __tablename__ = "pharmacy_users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="Pharmacist", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PharmacyUser(user_id={self.user_id}, username='{self.username}', role='{self.role}')>"


class Medicine(Base):
    __tablename__ = "medicines"

    medicine_id = Column(Integer, primary_key=True, autoincrement=True)
    medicine_name = Column(String(150), unique=True, nullable=False)
    category = Column(String(100), nullable=False)
    current_stock = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, nullable=False, default=20)
    unit_price = Column(Float, nullable=False, default=10.0)
    expiry_date = Column(Date, nullable=False)
    supplier = Column(String(150), default="Global Pharma Distributors Ltd.")
    lead_time = Column(Integer, default=3)  # Supplier delivery lead time in days
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("current_stock >= 0", name="chk_stock_non_negative"),
        CheckConstraint("reorder_level >= 0", name="chk_reorder_non_negative"),
        CheckConstraint("unit_price >= 0", name="chk_price_non_negative"),
        CheckConstraint("lead_time >= 0", name="chk_lead_time_non_negative"),
    )

    # Relationships
    sales_records = relationship("SalesRecord", back_populates="medicine", cascade="all, delete-orphan")
    demand_predictions = relationship("DemandPrediction", back_populates="medicine", cascade="all, delete-orphan")
    restocking_recommendations = relationship("RestockingRecommendation", back_populates="medicine", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="medicine", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Medicine(id={self.medicine_id}, name='{self.medicine_name}', stock={self.current_stock})>"


class SalesRecord(Base):
    __tablename__ = "sales_records"

    sales_id = Column(Integer, primary_key=True, autoincrement=True)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    sale_date = Column(Date, nullable=False, index=True)
    quantity_sold = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity_sold >= 0", name="chk_quantity_sold_non_negative"),
    )

    medicine = relationship("Medicine", back_populates="sales_records")

    def __repr__(self):
        return f"<SalesRecord(id={self.sales_id}, med_id={self.medicine_id}, date={self.sale_date}, qty={self.quantity_sold})>"


class DemandPrediction(Base):
    __tablename__ = "demand_predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    predicted_demand = Column(Float, nullable=False)
    prediction_date = Column(Date, nullable=False, default=date.today)
    forecast_period = Column(Integer, default=7, nullable=False)  # in days (e.g. 7, 14, 30)
    model_used = Column(String(100), default="Random Forest Regressor", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    medicine = relationship("Medicine", back_populates="demand_predictions")

    def __repr__(self):
        return f"<DemandPrediction(id={self.prediction_id}, med_id={self.medicine_id}, demand={self.predicted_demand})>"


class RestockingRecommendation(Base):
    __tablename__ = "restocking_recommendations"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    recommended_quantity = Column(Integer, nullable=False)
    status = Column(String(50), default="Pending", nullable=False)  # 'Pending', 'Approved', 'Rejected'
    recommendation_date = Column(Date, nullable=False, default=date.today)
    priority = Column(String(50), default="Medium", nullable=False)  # 'Critical', 'High', 'Medium', 'Low'
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_quantity = Column(Integer, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    medicine = relationship("Medicine", back_populates="restocking_recommendations")

    def __repr__(self):
        return f"<RestockingRecommendation(id={self.recommendation_id}, med_id={self.medicine_id}, qty={self.recommended_quantity}, status='{self.status}')>"


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(100), nullable=False)  # 'Low Stock', 'Expiry Risk', 'Demand Surge', 'Forecast Stock Risk'
    alert_status = Column(String(50), default="Active", nullable=False)  # 'Active', 'Resolved', 'Dismissed'
    alert_date = Column(Date, nullable=False, default=date.today)
    message = Column(Text, nullable=False)
    priority = Column(String(50), default="Medium", nullable=False)  # 'Critical', 'High', 'Medium', 'Low'
    created_at = Column(DateTime, default=datetime.utcnow)

    medicine = relationship("Medicine", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.alert_id}, med_id={self.medicine_id}, type='{self.alert_type}', priority='{self.priority}')>"
