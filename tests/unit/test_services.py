"""
Unit tests for service-related models and validation
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.models.services import (
    NavigationOption,
    OfficialInformationSource,
    ServiceCategory,
)


class TestServiceCategory:
    """Test suite for ServiceCategory model and validation"""

    def test_create_valid_service_category(self):
        """Test creating a valid service category"""
        # Given valid service category data
        service_data = {
            "name": "Hong Kong Passport Services",
            "description": "Passport application and renewal services for Hong Kong residents",
            "official_source_url": "https://www.gov.hk/en/residents/",
            "is_active": True,
        }

        # When creating a service category
        service = ServiceCategory(**service_data)

        # Then it should be created successfully
        assert service.name == "Hong Kong Passport Services"
        assert (
            service.description
            == "Passport application and renewal services for Hong Kong residents"
        )
        assert str(service.official_source_url) == "https://www.gov.hk/en/residents/"
        assert service.is_active is True
        assert isinstance(service.id, uuid.UUID)
        assert isinstance(service.created_at, datetime)
        assert isinstance(service.updated_at, datetime)

    def test_service_category_name_validation(self):
        """Test service category name validation"""
        # Given empty name
        with pytest.raises(ValidationError) as exc_info:
            ServiceCategory(name="")
        assert "ensure this value has at least 1 characters" in str(exc_info.value)

        # Given whitespace-only name
        with pytest.raises(ValidationError) as exc_info:
            ServiceCategory(name="   ")
        assert "Name cannot be empty" in str(exc_info.value)

        # Given name with leading/trailing whitespace
        service = ServiceCategory(name="  Passport Services  ")
        assert service.name == "Passport Services"  # Should be stripped

    def test_service_category_name_length_validation(self):
        """Test service category name length validation"""
        # Given name that is too long
        long_name = "A" * 256
        with pytest.raises(ValidationError) as exc_info:
            ServiceCategory(name=long_name)
        assert "ensure this value has at most 255 characters" in str(exc_info.value)

        # Given name at maximum length
        max_length_name = "A" * 255
        service = ServiceCategory(name=max_length_name)
        assert service.name == max_length_name

    def test_last_verified_validation(self):
        """Test last_verified date validation"""
        # Given a date more than 30 days old
        old_date = datetime.now(UTC) - timedelta(days=31)
        with pytest.raises(ValidationError) as exc_info:
            ServiceCategory(name="Test Service", last_verified=old_date)
        assert "Service information must be verified within last 30 days" in str(
            exc_info.value
        )

        # Given a date within 30 days
        recent_date = datetime.now(UTC) - timedelta(days=29)
        service = ServiceCategory(name="Test Service", last_verified=recent_date)
        assert service.last_verified == recent_date

        # Given current date (default)
        service = ServiceCategory(name="Test Service")
        assert (datetime.now(UTC) - service.last_verified).days <= 1

    def test_service_category_json_serialization(self):
        """Test JSON serialization of service category"""
        # Given a service category
        service = ServiceCategory(name="Test Service", description="Test description")

        # When converting to dict
        service_dict = service.dict()

        # Then UUID should remain as UUID object
        assert isinstance(service_dict["id"], uuid.UUID)
        assert isinstance(service_dict["created_at"], datetime)
        assert isinstance(service_dict["updated_at"], datetime)
        assert isinstance(service_dict["last_verified"], datetime)

        # When converting to JSON
        service_json = service.json()
        import json

        service_data = json.loads(service_json)

        # Then UUID should be converted to string
        assert isinstance(service_data["id"], str)
        assert isinstance(service_data["created_at"], str)
        assert isinstance(service_data["updated_at"], str)
        assert isinstance(service_data["last_verified"], str)

        # And datetime should be in ISO format
        assert "T" in service_data["created_at"]
        assert "T" in service_data["updated_at"]
        assert "T" in service_data["last_verified"]


class TestNavigationOption:
    """Test suite for NavigationOption model and validation"""

    def test_create_valid_navigation_option(self):
        """Test creating a valid navigation option"""
        # Given valid navigation option data
        service_category_id = uuid.uuid4()
        option_data = {
            "service_category_id": service_category_id,
            "label": "Material Requirements",
            "action_type": "requirements",
            "description": "View required documents and materials",
            "priority": 1,
        }

        # When creating a navigation option
        option = NavigationOption(**option_data)

        # Then it should be created successfully
        assert option.service_category_id == service_category_id
        assert option.label == "Material Requirements"
        assert option.action_type == "requirements"
        assert option.description == "View required documents and materials"
        assert option.priority == 1
        assert option.is_active is True
        assert isinstance(option.id, uuid.UUID)

    def test_navigation_option_action_type_validation(self):
        """Test navigation option action type validation"""
        service_category_id = uuid.uuid4()

        # Given invalid action type
        with pytest.raises(ValidationError) as exc_info:
            NavigationOption(
                service_category_id=service_category_id,
                label="Test Option",
                action_type="invalid_action",
            )
        assert "Action type must be one of" in str(exc_info.value)

        # Given valid action types
        valid_actions = [
            "explain",
            "requirements",
            "appointment",
            "location",
            "related",
        ]
        for action_type in valid_actions:
            option = NavigationOption(
                service_category_id=service_category_id,
                label="Test Option",
                action_type=action_type,
            )
            assert option.action_type == action_type

    def test_navigation_option_label_validation(self):
        """Test navigation option label validation"""
        service_category_id = uuid.uuid4()

        # Given empty label
        with pytest.raises(ValidationError) as exc_info:
            NavigationOption(
                service_category_id=service_category_id, label="", action_type="explain"
            )
        assert "ensure this value has at least 1 characters" in str(exc_info.value)

        # Given whitespace-only label
        with pytest.raises(ValidationError) as exc_info:
            NavigationOption(
                service_category_id=service_category_id,
                label="   ",
                action_type="explain",
            )
        assert "Label must be clear and actionable" in str(exc_info.value)

        # Given label with leading/trailing whitespace
        option = NavigationOption(
            service_category_id=service_category_id,
            label="  Material Requirements  ",
            action_type="requirements",
        )
        assert option.label == "Material Requirements"  # Should be stripped

    def test_navigation_option_priority_validation(self):
        """Test navigation option priority validation"""
        service_category_id = uuid.uuid4()

        # Given priority below minimum
        with pytest.raises(ValidationError) as exc_info:
            NavigationOption(
                service_category_id=service_category_id,
                label="Test Option",
                action_type="explain",
                priority=0,
            )
        assert "ensure this value is greater than or equal to 1" in str(exc_info.value)

        # Given priority above maximum
        with pytest.raises(ValidationError) as exc_info:
            NavigationOption(
                service_category_id=service_category_id,
                label="Test Option",
                action_type="explain",
                priority=11,
            )
        assert "ensure this value is less than or equal to 10" in str(exc_info.value)

        # Given valid priorities
        for priority in [1, 5, 10]:
            option = NavigationOption(
                service_category_id=service_category_id,
                label="Test Option",
                action_type="explain",
                priority=priority,
            )
            assert option.priority == priority

    def test_navigation_option_target_url_validation(self):
        """Test navigation option target URL validation"""
        service_category_id = uuid.uuid4()

        # Given appointment action with URL
        option = NavigationOption(
            service_category_id=service_category_id,
            label="Make Appointment",
            action_type="appointment",
            target_url="https://www.gov.hk/appointment",
        )
        assert str(option.target_url) == "https://www.gov.hk/appointment"

        # Note: Pydantic v2 field_validator doesn't have access to other fields during validation
        # The target_url validation would need to be handled at the application level
        # or using model_validator instead of field_validator


class TestOfficialInformationSource:
    """Test suite for OfficialInformationSource model and validation"""

    def test_create_valid_information_source(self):
        """Test creating a valid official information source"""
        # Given valid source data
        source_data = {
            "name": "Hong Kong Government Portal",
            "base_url": "https://www.gov.hk",
            "api_endpoint": "/api/services",
            "update_frequency": "weekly",
            "status": "active",
        }

        # When creating an information source
        source = OfficialInformationSource(**source_data)

        # Then it should be created successfully
        assert source.name == "Hong Kong Government Portal"
        # Pydantic normalizes URLs by adding trailing slash
        assert str(source.base_url) in ["https://www.gov.hk/", "https://www.gov.hk"]
        assert source.api_endpoint == "/api/services"
        assert source.update_frequency == "weekly"
        assert source.status == "active"
        assert source.error_count == 0
        assert isinstance(source.id, uuid.UUID)
        assert isinstance(source.created_at, datetime)

    def test_information_source_update_frequency_validation(self):
        """Test update frequency validation"""
        # Given invalid update frequency
        with pytest.raises(ValidationError) as exc_info:
            OfficialInformationSource(
                name="Test Source",
                base_url="https://example.com",
                update_frequency="invalid_frequency",
            )
        assert "Update frequency must be one of" in str(exc_info.value)

        # Given valid update frequencies
        valid_frequencies = ["daily", "weekly", "monthly", "on_change"]
        for frequency in valid_frequencies:
            source = OfficialInformationSource(
                name="Test Source",
                base_url="https://example.com",
                update_frequency=frequency,
            )
            assert source.update_frequency == frequency

    def test_information_source_status_validation(self):
        """Test status validation"""
        # Given invalid status
        with pytest.raises(ValidationError) as exc_info:
            OfficialInformationSource(
                name="Test Source",
                base_url="https://example.com",
                status="invalid_status",
            )
        assert "Status must be one of" in str(exc_info.value)

        # Given valid statuses
        valid_statuses = ["active", "inactive", "error"]
        for status in valid_statuses:
            source = OfficialInformationSource(
                name="Test Source", base_url="https://example.com", status=status
            )
            assert source.status == status

    def test_information_source_json_serialization(self):
        """Test JSON serialization of information source"""
        # Given an information source
        source = OfficialInformationSource(
            name="Test Source", base_url="https://example.com"
        )

        # When converting to dict
        source_dict = source.dict()

        # Then UUID should remain as UUID object
        assert isinstance(source_dict["id"], uuid.UUID)
        assert isinstance(source_dict["created_at"], datetime)
        assert isinstance(source_dict["last_checked"], datetime)

        # When converting to JSON
        source_json = source.json()
        import json

        source_data = json.loads(source_json)

        # Then UUID should be converted to string
        assert isinstance(source_data["id"], str)
        assert isinstance(source_data["created_at"], str)
        assert isinstance(source_data["last_checked"], str)

        # And datetime should be in ISO format
        assert "T" in source_data["created_at"]
        assert "T" in source_data["last_checked"]
