#!/usr/bin/env python3
"""
Load initial service data for City Guide Smart Assistant
"""

import logging
import uuid
from datetime import UTC, datetime

from src.services.data_service import DataService, ServiceCategory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_hong_kong_macau_passport_service():
    """Create Hong Kong/Macau passport service category with official sources"""

    # Hong Kong/Macau Passport Service Category
    passport_service = ServiceCategory(
        id=uuid.uuid4(),
        name="Hong Kong/Macau Passport Services",
        description="Passport application and renewal services for Hong Kong and Macau residents in Shenzhen",
        official_source_url="https://www.immd.gov.hk/eng/services/index.html",
        is_active=True,
        last_verified=datetime.now(tz=UTC),
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )

    return passport_service


def create_additional_services():
    """Create additional common government services"""

    services = []

    # Resident Permit Services
    resident_permit = ServiceCategory(
        id=uuid.uuid4(),
        name="Resident Permit Services",
        description="Resident permit application and renewal services for foreigners in Shenzhen",
        official_source_url="https://www.sz.gov.cn/en/immigration/",
        is_active=True,
        last_verified=datetime.now(tz=UTC),
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )

    # Business Registration
    business_registration = ServiceCategory(
        id=uuid.uuid4(),
        name="Business Registration",
        description="Business registration and licensing services in Shenzhen",
        official_source_url="https://www.sz.gov.cn/en/business/",
        is_active=True,
        last_verified=datetime.now(tz=UTC),
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )

    # Tax Services
    tax_services = ServiceCategory(
        id=uuid.uuid4(),
        name="Tax Services",
        description="Tax registration, filing, and consultation services",
        official_source_url="https://www.sz.gov.cn/en/tax/",
        is_active=True,
        last_verified=datetime.now(tz=UTC),
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )

    services.extend([resident_permit, business_registration, tax_services])
    return services


def load_initial_data():
    """Load all initial service data into the database"""

    try:
        with DataService() as data_service:
            logger.info("Starting initial data loading...")

            # Create Hong Kong/Macau passport service
            passport_service = create_hong_kong_macau_passport_service()

            # Add passport service to database
            data_service.db.add(passport_service)
            data_service.db.flush()  # Get the ID for navigation options

            # Create additional services
            additional_services = create_additional_services()
            for service in additional_services:
                data_service.db.add(service)

            # Commit all changes
            data_service.db.commit()

            logger.info(
                f"Successfully loaded {len(additional_services) + 1} service categories"
            )

            return {
                "passport_service_id": str(passport_service.id),
                "total_services": len(additional_services) + 1,
            }

    except Exception as e:
        logger.error(f"Failed to load initial data: {e}")
        raise


if __name__ == "__main__":
    """Run data loading when script is executed directly"""
    try:
        result = load_initial_data()
        logger.info(f"Data loading completed successfully: {result}")
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        exit(1)
