#!/usr/bin/env python3
"""
Fix the navigation option directly in database
"""

import logging
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.data_service import DataService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_navigation_direct():
    """Fix the navigation option directly in database"""

    print("\n=== Fixing Navigation Option (Direct) ===")

    try:
        with DataService() as data_service:
            # Get all navigation options directly from database
            from src.services.data_service import NavigationOption

            db_options = (
                data_service.db.query(NavigationOption)
                .filter(
                    NavigationOption.label == "Service Locations",
                    NavigationOption.action_type == "location",
                )
                .all()
            )

            for db_option in db_options:
                print(
                    f"Found problematic option: {db_option.label} - {db_option.action_type}"
                )

                # Update the option with target_url
                db_option.target_url = "https://www.gov.hk/en/service-locations/"

                data_service.db.commit()
                print(
                    f"✓ Fixed option: {db_option.label} - URL: {db_option.target_url}"
                )

            print("\n🎉 Navigation option fixed!")
            return True

    except Exception as e:
        logger.error(f"Failed to fix navigation option: {e}")
        return False


if __name__ == "__main__":
    """Run navigation option fix"""

    print("Starting Navigation Option Fix (Direct)")
    print("=" * 50)

    fix_passed = fix_navigation_direct()

    print("\n" + "=" * 50)
    print(f"Navigation Option Fix: {'PASSED' if fix_passed else 'FAILED'}")
