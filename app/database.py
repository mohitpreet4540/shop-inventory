import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Fetch the Database URL from the environment — no hardcoded credential fallback.
#    Your own Setup docs already require a .env with DATABASE_URL, so this should not
#    change anything in your normal workflow. It just stops the app from silently
#    connecting with a baked-in password if the env var is ever missing (e.g. a
#    misconfigured deploy).
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Create a .env file (see README Setup section) "
        "or export DATABASE_URL before starting the app."
    )

# 2. Create the engine that manages connections to PostgreSQL
engine = create_engine(DATABASE_URL)

# 3. Create a Session Local class—each instance will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a Base class that our data models will inherit from
Base = declarative_base()

# One single unified session helper — all routers should import this, not redefine it.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
