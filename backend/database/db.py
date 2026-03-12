import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Use absolute path pointing to datasets directory in the parent folder
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../datasets/trade_intelligence.db"))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# For PostgreSQL in the future, just swap the URL:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
