import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Replace with your actual local database credentials for PostgreSQL or MySQL
# Example Postgres: postgresql://username:password@localhost:5432/hcp_crm
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/hcp_crm")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our models to inherit from
Base = declarative_base()

# Dependency to get the DB session for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        
        yield db
    finally:
        db.close()
        