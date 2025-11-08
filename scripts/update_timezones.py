#!/usr/bin/env python3
"""
Update existing service categories with timezone-aware datetimes
"""

import logging
import os
import sys
from datetime import UTC, datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.data_service import DataService, ServiceCategory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_service_category_timezones():
    """Update service categories with timezone-aware datetimes"""

    try:
        with DataService() as data_service:
            logger.info("Updating service categories with timezone-aware datetimes...")

            # Get all active service categories
            service_categories = data_service.get_active_service_categories()

            updated_count = 0
            for category in service_categories:
                # Check if the datetime is naive (no timezone)
                if category.last_verified and category.last_verified.tzinfo is None:
                    # Update with timezone-aware datetime
                    db_category = (
                        data_service.db.query(ServiceCategory)
                        .filter(ServiceCategory.id == category.id)
                        .first()
                    )

                    if db_category:
                        db_category.last_verified = datetime.now(tz=UTC)
                        updated_count += 1
                        logger.info(f"Updated timezone for: {category.name}")

            # Commit changes
            data_service.db.commit()

            logger.info(f"Successfully updated {updated_count} service categories")
            return updated_count

    except Exception as e:
        logger.error(f"Failed to update service category timezones: {e}")
        raise


if __name__ == "__main__":
    """Run timezone update script"""

    try:
        result = update_service_category_timezones()
        logger.info(
            f"Timezone update completed successfully: {result} categories updated"
        )
    except Exception as e:
        logger.error(f"Timezone update failed: {e}")
        exit(1)
