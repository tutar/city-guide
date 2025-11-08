#!/usr/bin/env python3
"""
Test data service directly without any other dependencies
"""

import logging

from src.services.data_service import DataService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_simple_data():
    """Test data service directly without any other dependencies"""

    print("\n=== Testing Data Service Directly (Simple) ===")

    try:
        with DataService() as data_service:
            # Test 1: Get active service categories
            service_categories = data_service.get_active_service_categories()
            print(f"✓ Retrieved {len(service_categories)} service categories")

            for service in service_categories:
                print(f"  - {service.name}: {service.id}")

            print("\n🎉 Simple data service test passed!")
            return True

    except Exception as e:
        logger.error(f"Simple data service test failed: {e}")
        return False


if __name__ == "__main__":
    """Run simple data service test"""

    print("Starting Simple Data Service Test")
    print("=" * 50)

    test_passed = test_simple_data()

    print("\n" + "=" * 50)
    print(f"Simple Data Service Test: {'PASSED' if test_passed else 'FAILED'}")
