from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_analysis_schema():
    inspector = inspect(engine)
    if "analysis" not in inspector.get_table_names():
        Base.metadata.create_all(bind=engine)
        return

    existing_columns = {column["name"] for column in inspector.get_columns("analysis")}
    required_columns = {
        "created_at": "DATETIME NULL DEFAULT CURRENT_TIMESTAMP",
        "error_message": "VARCHAR(500) NULL",
        "completed_at": "DATETIME NULL",
    }

    with engine.begin() as connection:
        for column_name, column_sql in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE analysis ADD COLUMN {column_name} {column_sql}"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
