
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# Locate the project root.
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env.
load_dotenv(PROJECT_DIR / ".env")


# Build the PostgreSQL connection URL.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)


# Create a database engine.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def test_connection():
    """Check whether Python can connect to PostgreSQL."""

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database();")
        )

        database_name = result.scalar()

        print("Successfully connected to PostgreSQL!")
        print(f"Database: {database_name}")


if __name__ == "__main__":
    test_connection()
