import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from app.models.company import CompanyProfile
from sqlalchemy import text

try:
    with engine.connect() as conn:
        print("Connected to DB successfully!")
        
        # Check existing tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result]
        print("Tables in public schema:", tables)

    db = SessionLocal()
    # Try querying company profiles
    try:
        profiles = db.query(CompanyProfile).all()
        print("Queried CompanyProfile successfully, count:", len(profiles))
    except Exception as e:
        print("Error querying CompanyProfile:", str(e))
    finally:
        db.close()

except Exception as e:
    print("Database connection error:", str(e))
