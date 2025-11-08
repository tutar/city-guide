#!/usr/bin/env python3
"""
Fix the navigation option that's missing target_url
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


def fix_navigation_option():
    """Fix the navigation option missing target_url"""

    print("\n=== Fixing Navigation Option ===")

    try:
        with DataService() as data_service:
            # Get all navigation options
            service_categories = data_service.get_active_service_categories()

            for service in service_categories:
                nav_options = data_service.get_navigation_options_by_category(
                    service.id
                )

                for option in nav_options:
                    if (
                        option.label == "Service Locations"
                        and option.action_type == "location"
                        and not option.target_url
                    ):
                        print(
                            f"Found problematic option: {option.label} - {option.action_type}"
                        )

                        # Update the option with target_url
                        option.target_url = "https://www.gov.hk/en/service-locations/"

                        # Update in database
                        updated_option = data_service.update_navigation_option(option)
                        print(
                            f"✓ Fixed option: {updated_option.label} - URL: {updated_option.target_url}"
                        )

            print("\n🎉 Navigation option fixed!")
            return True

    except Exception as e:
        logger.error(f"Failed to fix navigation option: {e}")
        return False


if __name__ == "__main__":
    """Run navigation option fix"""

    print("Starting Navigation Option Fix")
    print("=" * 40)

    fix_passed = fix_navigation_option()

    print("\n" + "=" * 40)
    print(f"Navigation Option Fix: {'PASSED' if fix_passed else 'FAILED'}")
