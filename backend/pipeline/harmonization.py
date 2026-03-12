import pandas as pd
from sqlalchemy.orm import Session
from database.models import Customer, Route, Order, Shipment, Invoice

def harmonize_and_store(df: pd.DataFrame, db: Session):
    """
    Takes cleaned dataframe and populates the relational SQLite database.
    """
    # Convert pandas NaT and NaN to Python None for SQLite compatibility
    df = df.where(pd.notnull(df), None)
    
    # Create caches to avoid unnecessary DB queries
    customer_cache = {}
    route_cache = {}
    
    for _, row in df.iterrows():
        # Skip if shipment already exists to prevent IntegrityError
        if db.query(Shipment).filter(Shipment.shipment_id == row['shipment_id']).first():
            continue
            
        # 1. Customer
        cust_name = row['customer']
        if cust_name not in customer_cache:
            customer = db.query(Customer).filter(Customer.name == cust_name).first()
            if not customer:
                customer = Customer(name=cust_name)
                db.add(customer)
                db.flush()
            customer_cache[cust_name] = customer.id
            
        cust_id = customer_cache[cust_name]

        # 2. Route
        origin = row['origin']
        destination = row['destination']
        route_key = f"{origin}-{destination}"
        
        if route_key not in route_cache:
            route = db.query(Route).filter(Route.origin == origin, Route.destination == destination).first()
            if not route:
                route = Route(origin=origin, destination=destination, distance=row.get('distance', 0))
                db.add(route)
                db.flush()
            route_cache[route_key] = route.id
            
        route_id = route_cache[route_key]
        
        # 3. Order
        # Assume one row = one order for simplicity
        order = Order(
            customer_id=cust_id,
            order_date=row['order_date'],
            product=row.get('product', 'Unknown')
        )
        db.add(order)
        db.flush()
        
        # 4. Shipment
        exp_del = row['expected_delivery']
        act_del = row.get('actual_delivery')
        
        shipment = Shipment(
            shipment_id=row['shipment_id'],
            order_id=order.id,
            route_id=route_id,
            carrier=row['carrier'],
            expected_delivery=None if pd.isna(exp_del) else exp_del,
            actual_delivery=None if pd.isna(act_del) else act_del,
            status=row.get('status', 'Unknown'),
            is_delayed=row.get('is_delayed', False)
        )
        db.add(shipment)
        
        # 5. Invoice
        invoice = Invoice(
            order_id=order.id,
            amount=row.get('invoice_amount', 0),
            cost=row.get('cost', 0)
        )
        db.add(invoice)
        
    db.commit()
