import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database import engine, Base
# Import all models so they are registered in Base.metadata
from src.models import spatial, task, transactions

def drop_tables():
    print("Dropping all tables using SQLAlchemy metadata...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped successfully.")

if __name__ == "__main__":
    drop_tables()
