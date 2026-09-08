"""
Migrate shipments table in SQLite to have composite primary key (shipment_id, dataset_id).
"""
import sqlite3
import os
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent.parent / "datasets" / "trade_intelligence.db"
print(f"Connecting to {db_path}...")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

cur.execute("PRAGMA foreign_keys=OFF;")
cur.execute("BEGIN TRANSACTION;")

cur.execute("""
CREATE TABLE shipments_new (
    shipment_id VARCHAR NOT NULL, 
    order_id INTEGER, 
    route_id INTEGER, 
    carrier VARCHAR, 
    expected_delivery DATETIME, 
    actual_delivery DATETIME, 
    status VARCHAR, 
    is_delayed BOOLEAN, 
    dataset_id INTEGER, 
    weight FLOAT, 
    weight_unit VARCHAR, 
    weight_kg FLOAT, 
    order_quantity FLOAT, 
    shipped_quantity FLOAT, 
    PRIMARY KEY (shipment_id, dataset_id), 
    FOREIGN KEY(order_id) REFERENCES orders (id), 
    FOREIGN KEY(route_id) REFERENCES routes (id), 
    FOREIGN KEY(dataset_id) REFERENCES datasets (id)
);
""")

cur.execute("""
INSERT INTO shipments_new (shipment_id, order_id, route_id, carrier, expected_delivery, actual_delivery, status, is_delayed, dataset_id, weight, weight_unit, weight_kg, order_quantity, shipped_quantity)
SELECT shipment_id, order_id, route_id, carrier, expected_delivery, actual_delivery, status, is_delayed, dataset_id, weight, weight_unit, weight_kg, order_quantity, shipped_quantity
FROM shipments;
""")

cur.execute("DROP TABLE shipments;")
cur.execute("ALTER TABLE shipments_new RENAME TO shipments;")
cur.execute("CREATE INDEX IF NOT EXISTS ix_shipments_shipment_id ON shipments (shipment_id);")
cur.execute("CREATE INDEX IF NOT EXISTS ix_shipments_carrier ON shipments (carrier);")
cur.execute("CREATE INDEX IF NOT EXISTS ix_shipments_dataset_id ON shipments (dataset_id);")

conn.commit()
cur.execute("PRAGMA foreign_keys=ON;")

cur.execute("SELECT sql FROM sqlite_master WHERE name='shipments'")
print("Migration successful! New schema:")
print(cur.fetchone()[0])
cur.execute("SELECT count(*) FROM shipments")
print(f"Total shipments preserved: {cur.fetchone()[0]}")
conn.close()
