#!/usr/bin/env python3
"""
Database setup script for City Guide Smart Assistant
"""

import asyncio
import logging

from sqlalchemy import create_engine, text

from src.utils.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_database():
    """Create the database if it doesn't exist"""

    # First connect to postgres database to create our target database
    admin_url = (
        f"postgresql://{settings.database.user}:{settings.database.password}"
        f"@{settings.database.host}:{settings.database.port}/postgres"
    )

    try:
        engine = create_engine(admin_url)
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": settings.database.db},
            )

            if not result.fetchone():
                # Create database
                conn.execute(text(f"CREATE DATABASE {settings.database.db}"))
                logger.info(f"Created database: {settings.database.db}")
            else:
                logger.info(f"Database already exists: {settings.database.db}")

    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        raise


async def create_tables():
    """Create database tables"""

    import uuid
    from datetime import datetime

    from sqlalchemy import (
        JSON,
        Boolean,
        Column,
        DateTime,
        ForeignKey,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    class ServiceCategory(Base):
        __tablename__ = "service_categories"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        name = Column(String(255), unique=True, nullable=False)
        description = Column(Text)
        official_source_url = Column(String(500))
        last_verified = Column(DateTime, default=datetime.utcnow)
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class ConversationContext(Base):
        __tablename__ = "conversation_contexts"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_session_id = Column(String(255), nullable=False)
        current_service_category_id = Column(
            UUID(as_uuid=True), ForeignKey("service_categories.id")
        )
        conversation_history = Column(JSON)
        navigation_options = Column(JSON)
        user_preferences = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)
        last_activity = Column(DateTime, default=datetime.utcnow)
        is_active = Column(Boolean, default=True)

    class OfficialInformationSource(Base):
        __tablename__ = "official_information_sources"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        name = Column(String(255), nullable=False)
        base_url = Column(String(500), nullable=False)
        api_endpoint = Column(String(500))
        update_frequency = Column(String(50))  # daily, weekly, monthly, on_change
        last_checked = Column(DateTime, default=datetime.utcnow)
        status = Column(String(50), default="active")  # active, inactive, error
        error_count = Column(Integer, default=0)
        created_at = Column(DateTime, default=datetime.utcnow)

    try:
        engine = create_engine(settings.database.database_url)
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def main():
    """Main setup function"""
    logger.info("Starting database setup...")

    try:
        await create_database()
        await create_tables()
        logger.info("Database setup completed successfully")

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
