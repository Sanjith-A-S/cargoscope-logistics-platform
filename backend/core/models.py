"""
core/models.py — canonical ORM model definitions for the entire platform.

All modules import from here. database/models.py is a thin re-export shim.

Schema changes from baseline:
  NEW tables:   Organization, User, Dataset
  MODIFIED:     Shipment (+ dataset_id, weight, weight_unit, order_quantity, shipped_quantity)
                Route, Order, Invoice, Customer, AnomalyReview (+ dataset_id FK)
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import relationship
from core.db import Base
from datetime import datetime


# ─── NEW: Multi-tenancy tables ─────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="organization")
    datasets = relationship("Dataset", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow)
    source_row_count = Column(Integer, default=0)

    organization = relationship("Organization", back_populates="datasets")
    shipments = relationship("Shipment", back_populates="dataset")


# ─── Pipeline logs (unchanged) ────────────────────────────────────────────────

class PipelineLog(Base):
    __tablename__ = "pipeline_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String, index=True)
    description = Column(String)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True, index=True)


# ─── Core data tables (modified: + dataset_id FK) ─────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True, index=True)

    orders = relationship("Order", back_populates="customer")


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    distance = Column(Float)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True, index=True)

    shipments = relationship("Shipment", back_populates="route")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    order_date = Column(DateTime)
    product = Column(String)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True, index=True)

    customer = relationship("Customer", back_populates="orders")
    shipment = relationship("Shipment", back_populates="order", uselist=False)
    invoice = relationship("Invoice", back_populates="order", uselist=False)


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id = Column(String, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    route_id = Column(Integer, ForeignKey("routes.id"))
    carrier = Column(String, index=True)
    expected_delivery = Column(DateTime)
    actual_delivery = Column(DateTime, nullable=True)
    status = Column(String)
    is_delayed = Column(Boolean, default=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), primary_key=True, nullable=True, index=True)

    # Weight & quantity fields (from spec §1.2)
    weight = Column(Float, nullable=True)
    weight_unit = Column(String, nullable=True)      # "kg" | "lb" — raw from source
    weight_kg = Column(Float, nullable=True)          # normalised to kg at ingestion
    order_quantity = Column(Float, nullable=True)
    shipped_quantity = Column(Float, nullable=True)

    order = relationship("Order", back_populates="shipment")
    route = relationship("Route", back_populates="shipments")
    dataset = relationship("Dataset", back_populates="shipments")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    amount = Column(Float)
    cost = Column(Float)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True, index=True)

    # Optional cost breakdown fields (populated when source has accessorial columns)
    base_cost = Column(Float, nullable=True)
    accessorial_cost = Column(Float, nullable=True)
    contracted_rate = Column(Float, nullable=True)

    order = relationship("Order", back_populates="invoice")


class AnomalyReview(Base):
    __tablename__ = "anomaly_reviews"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, index=True, unique=True)
    # status: open | investigated | dismissed
    status = Column(String, default="open", nullable=False)
    notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True, index=True)
    detection_method = Column(String, nullable=True)  # "contract_deviation" | "statistical_isolation_forest"
