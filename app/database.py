import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Fetch the Database URL from the Docker environment variables with a safe admin fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://shop_admin:super_secure_password123@db:5432/shop_db")

# 2. Create the engine that manages connections to PostgreSQL
engine = create_engine(DATABASE_URL)

# 3. Create a Session Local class—each instance will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a Base class that our data models will inherit from
Base = declarative_base()

# One single unified session helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()