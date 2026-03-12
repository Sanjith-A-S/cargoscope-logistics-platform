from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.db import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    orders = relationship("Order", back_populates="customer")

class Route(Base):
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    distance = Column(Float)
    
    shipments = relationship("Shipment", back_populates="route")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    order_date = Column(DateTime)
    product = Column(String)
    
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
    
    order = relationship("Order", back_populates="shipment")
    route = relationship("Route", back_populates="shipments")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    amount = Column(Float)
    cost = Column(Float)
    
    order = relationship("Order", back_populates="invoice")
