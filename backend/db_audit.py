"""Temporary DB audit script — checks schema, tables, columns, data integrity."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from core.db import engine, DB_PATH
from sqlalchemy import text, inspect

print(f"DB path: {DB_PATH}")
print(f"DB exists: {os.path.exists(DB_PATH)}")
print(f"DB size: {os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 'N/A'} bytes")
print()

# 1. Connection check
with engine.connect() as conn:
    r = conn.execute(text("SELECT 1")).scalar()
    print(f"Connection check (SELECT 1): {r}")
    print()

    # 2. Table list
    rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
    tables = [r[0] for r in rows]
    print(f"Tables ({len(tables)}): {tables}")
    print()

    # 3. Column details for each table
    inspector = inspect(engine)
    for table in tables:
        cols = inspector.get_columns(table)
        col_names = [c['name'] for c in cols]
        print(f"  {table}: {col_names}")
    print()

    # 4. Row counts
    print("Row counts:")
    for table in tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM [{table}]")).scalar()
        print(f"  {table}: {count}")
    print()

    # 5. Check for existing users/orgs/datasets
    print("Users:")
    users = conn.execute(text("SELECT id, email, org_id FROM users")).fetchall()
    for u in users:
        print(f"  id={u[0]}, email={u[1]}, org_id={u[2]}")
    
    print("Organizations:")
    orgs = conn.execute(text("SELECT id, name FROM organizations")).fetchall()
    for o in orgs:
        print(f"  id={o[0]}, name={o[1]}")

    print("Datasets:")
    datasets = conn.execute(text("SELECT id, org_id, name, source_row_count FROM datasets")).fetchall()
    for d in datasets:
        print(f"  id={d[0]}, org_id={d[1]}, name={d[2]}, rows={d[3]}")

    # 6. Cross-reference: do shipments exist and are they linked correctly?
    if datasets:
        for d in datasets:
            ds_id = d[0]
            ship_count = conn.execute(text(f"SELECT COUNT(*) FROM shipments WHERE dataset_id = {ds_id}")).scalar()
            print(f"  Dataset {ds_id} shipment count: {ship_count}")

# 7. Check admin env vars
print()
print("Admin env vars:")
print(f"  ADMIN_USERNAME: {os.getenv('ADMIN_USERNAME', '(not set)')}")
admin_hash = os.getenv('ADMIN_PASSWORD_HASH', '(not set)')
print(f"  ADMIN_PASSWORD_HASH: {admin_hash[:20]}... ({len(admin_hash)} chars)" if len(admin_hash) > 20 else f"  ADMIN_PASSWORD_HASH: {admin_hash}")

# 8. Verify admin password hash
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
if admin_hash and admin_hash != '(not set)':
    try:
        result = pwd_context.verify("admin123", admin_hash)
        print(f"  admin123 vs ADMIN_PASSWORD_HASH: {'MATCH' if result else 'NO MATCH'}")
    except Exception as e:
        print(f"  Hash verification error: {e}")

# 9. Check CSV headers
print()
print("CSV file headers:")
import csv
csv_dir = os.path.join(os.path.dirname(__file__), "..", "datasets")
for fname in sorted(os.listdir(csv_dir)):
    if fname.endswith('.csv'):
        fpath = os.path.join(csv_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            # Count rows
            row_count = sum(1 for _ in reader)
        print(f"  {fname}: {row_count} rows, columns: {headers}")
