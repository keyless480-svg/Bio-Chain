import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.database import engine
from sqlalchemy import text

def check():
    with engine.begin() as conn:
        res = conn.execute(text("SELECT count(*) FROM farmers")).scalar()
        print(f"Farmers count: {res}")

if __name__ == "__main__":
    check()
