#!/usr/bin/env python3
"""
Test data service directly without AI dependencies
"""

import logging

from src.services.data_service import DataService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_data_service():
    """Test data service directly"""

    print("\n=== Testing Data Service Directly ===")

    try:
        with DataService() as data_service:
            # Test 1: Get active service categories
            service_categories = data_service.get_active_service_categories()
            print(f"✓ Retrieved {len(service_categories)} service categories")

            for service in service_categories:
                print(f"  - {service.name}: {service.id}")

            print("\n🎉 Data service tests passed!")
            return True

    except Exception as e:
        logger.error(f"Data service test failed: {e}")
        return False


if __name__ == "__main__":
    """Run data service test"""

    print("Starting Data Service Test")
    print("=" * 40)

    test_passed = test_data_service()

    print("\n" + "=" * 40)
    print(f"Data Service Test: {'PASSED' if test_passed else 'FAILED'}")
