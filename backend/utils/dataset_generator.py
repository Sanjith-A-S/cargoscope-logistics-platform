import pandas as pd
import numpy as np
from faker import Faker
import random
import os
from datetime import timedelta

fake = Faker()

NUM_RECORDS = 1000

def generate_dataset(output_path: str):
    customers = [fake.company() for _ in range(50)]
    carriers = ['Maersk', 'MSC', 'CMA CGM', 'COSCO', 'Hapag-Lloyd', 'Evergreen', 'ONE']
    products = ['Electronics', 'Machinery', 'Textiles', 'Chemicals', 'Auto Parts', 'Medicines', 'Foodstuff']
    
    cities = [fake.city() for _ in range(20)]
    
    data = []
    
    for i in range(NUM_RECORDS):
        origin = random.choice(cities)
        destination = random.choice([c for c in cities if c != origin])
        distance = round(random.uniform(500, 10000), 2)
        
        # Cost is roughly proportional to distance + some noise
        base_cost = distance * 0.5
        noise = random.uniform(0.8, 1.2)
        
        # Inject some anomalies (5% chance)
        if random.random() < 0.05:
            noise = random.uniform(3.0, 5.0)
            
        cost = round(base_cost * noise, 2)
        invoice_amount = round(cost * random.uniform(1.1, 1.5), 2) # 10-50% markup
        
        order_date = fake.date_time_between(start_date="-1y", end_date="now")
        transit_days_expected = int(distance / 500) + random.randint(2, 5)
        expected_delivery = order_date + timedelta(days=transit_days_expected)
        
        # 20% chance of delay
        is_delayed = random.random() < 0.20
        if is_delayed:
            delay_days = random.randint(1, 14)
            actual_delivery = expected_delivery + timedelta(days=delay_days)
        else:
            early_days = random.randint(0, 2)
            actual_delivery = expected_delivery - timedelta(days=early_days)
            
        # Maybe 5% are still in transit (actual delivery null)
        if random.random() < 0.05 and expected_delivery > fake.date_time_between(start_date="-1w", end_date="now"):
            actual_delivery = pd.NaT
            status = 'In Transit'
        else:
            status = 'Delivered'
            
        # Introduce some data quality issues to test cleaning (5% chance of missing carrier)
        carrier = random.choice(carriers) if random.random() > 0.05 else np.nan
        
        # Introduce duplicate/inconsistent customer names (e.g., 'Apple' vs 'Apple Inc.')
        customer = random.choice(customers)
        if random.random() < 0.1:
            customer = customer + (" Inc" if "Inc" not in customer else "")

        data.append({
            'shipment_id': f"SHP-{fake.unique.random_number(digits=8)}",
            'customer': customer,
            'origin': origin,
            'destination': destination,
            'carrier': carrier,
            'distance': distance,
            'cost': cost,
            'order_date': order_date.strftime("%Y-%m-%d %H:%M:%S"),
            'expected_delivery': expected_delivery.strftime("%Y-%m-%d %H:%M:%S"),
            'actual_delivery': actual_delivery.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(actual_delivery) else np.nan,
            'product': random.choice(products),
            'invoice_amount': invoice_amount,
            'status': status
        })
        
    df = pd.DataFrame(data)
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {NUM_RECORDS} records and saved to {output_path}")

if __name__ == "__main__":
    # Path relative to this script
    current_dir = os.path.dirname(__file__)
    output_path = os.path.abspath(os.path.join(current_dir, "../../datasets/sample_trade_data.csv"))
    generate_dataset(output_path)
