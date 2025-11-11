"""
Database service layer for City Guide Smart Assistant
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.models.conversation_model import (
    ConversationContext as ConversationContextModel,
)
from src.models.conversation_model import Message
from src.models.services import NavigationOption as NavigationOptionModel
from src.models.services import ServiceCategory as ServiceCategoryModel
from src.utils.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(settings.database.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# SQLAlchemy models
class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    official_source_url = Column(String(500))
    last_verified = Column(DateTime, default=lambda: datetime.now(UTC))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


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
    # Service relationship tracking fields
    service_relationships = Column(JSON, default=list)
    related_services_suggested = Column(JSON, default=list)
    service_transitions = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    last_activity = Column(DateTime, default=lambda: datetime.now(UTC))
    is_active = Column(Boolean, default=True)


class NavigationOption(Base):
    __tablename__ = "navigation_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_category_id = Column(
        UUID(as_uuid=True), ForeignKey("service_categories.id"), nullable=False
    )
    label = Column(String(255), nullable=False)
    action_type = Column(String(50), nullable=False)
    target_url = Column(String(500))
    description = Column(Text)
    priority = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)


class DataService:
    """Service layer for database operations"""

    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    # ServiceCategory operations

    def create_service_category(
        self, service_category: ServiceCategoryModel
    ) -> ServiceCategoryModel:
        """Create a new service category"""
        try:
            db_category = ServiceCategory(
                name=service_category.name,
                description=service_category.description,
                official_source_url=str(service_category.official_source_url)
                if service_category.official_source_url
                else None,
                last_verified=service_category.last_verified,
                is_active=service_category.is_active,
            )
            self.db.add(db_category)
            self.db.commit()
            self.db.refresh(db_category)

            # Convert back to Pydantic model
            return ServiceCategoryModel(
                id=db_category.id,
                name=db_category.name,
                description=db_category.description,
                official_source_url=db_category.official_source_url,
                last_verified=db_category.last_verified,
                is_active=db_category.is_active,
                created_at=db_category.created_at,
                updated_at=db_category.updated_at,
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create service category: {e}")
            raise

    def get_service_category(
        self, category_id: uuid.UUID
    ) -> ServiceCategoryModel | None:
        """Get service category by ID"""
        try:
            db_category = (
                self.db.query(ServiceCategory)
                .filter(ServiceCategory.id == category_id)
                .first()
            )
            if db_category:
                return ServiceCategoryModel(
                    id=db_category.id,
                    name=db_category.name,
                    description=db_category.description,
                    official_source_url=db_category.official_source_url,
                    last_verified=db_category.last_verified,
                    is_active=db_category.is_active,
                    created_at=db_category.created_at,
                    updated_at=db_category.updated_at,
                )
            return None

        except Exception as e:
            logger.error(f"Failed to get service category: {e}")
            raise

    def get_active_service_categories(self) -> list[ServiceCategoryModel]:
        """Get all active service categories"""
        try:
            db_categories = (
                self.db.query(ServiceCategory)
                .filter(ServiceCategory.is_active == True)
                .all()
            )

            # Debug: Check datetime types
            for category in db_categories:
                logger.debug(
                    f"Category {category.name}: last_verified type: {type(category.last_verified)}, tzinfo: {category.last_verified.tzinfo if category.last_verified else None}"
                )

            return [
                ServiceCategoryModel(
                    id=category.id,
                    name=category.name,
                    description=category.description,
                    official_source_url=category.official_source_url,
                    last_verified=category.last_verified,
                    is_active=category.is_active,
                    created_at=category.created_at,
                    updated_at=category.updated_at,
                )
                for category in db_categories
            ]

        except Exception as e:
            logger.error(f"Failed to get active service categories: {e}")
            raise

    # ConversationContext operations

    def create_conversation_context(
        self, conversation_context: ConversationContextModel
    ) -> ConversationContextModel:
        """Create a new conversation context"""
        try:
            db_context = ConversationContext(
                user_session_id=conversation_context.user_session_id,
                current_service_category_id=conversation_context.current_service_category_id,
                conversation_history=[
                    {
                        "id": str(msg.id),
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": {
                            key: str(value)
                            if hasattr(value, "__str__")
                            and not isinstance(
                                value, str | int | float | bool | type(None)
                            )
                            else value
                            for key, value in msg.metadata.items()
                        },
                    }
                    for msg in conversation_context.conversation_history
                ],
                navigation_options=[
                    {
                        **option,
                        "target_url": str(option.get("target_url"))
                        if option.get("target_url")
                        else None,
                    }
                    for option in conversation_context.navigation_options
                ],
                user_preferences=conversation_context.user_preferences,
                # Service relationship tracking fields
                service_relationships=conversation_context.service_relationships,
                related_services_suggested=conversation_context.related_services_suggested,
                service_transitions=conversation_context.service_transitions,
                is_active=conversation_context.is_active,
            )
            self.db.add(db_context)
            self.db.commit()
            self.db.refresh(db_context)

            # Convert back to Pydantic model
            return ConversationContextModel(
                id=db_context.id,
                user_session_id=db_context.user_session_id,
                current_service_category_id=db_context.current_service_category_id,
                conversation_history=[
                    Message(**msg) for msg in db_context.conversation_history
                ],
                navigation_options=db_context.navigation_options,
                user_preferences=db_context.user_preferences,
                # Service relationship tracking fields
                service_relationships=db_context.service_relationships,
                related_services_suggested=db_context.related_services_suggested,
                service_transitions=db_context.service_transitions,
                created_at=db_context.created_at,
                last_activity=db_context.last_activity,
                is_active=db_context.is_active,
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create conversation context: {e}")
            raise

    def get_conversation_context(
        self, session_id: str
    ) -> ConversationContextModel | None:
        """Get conversation context by session ID"""
        try:
            db_context = (
                self.db.query(ConversationContext)
                .filter(
                    ConversationContext.user_session_id == session_id,
                    # 在 filter() 中：
                    # - ConversationContext.is_active is True 立即求值
                    # - 如果 is_active 是 Boolean 列，这个表达式总是 False
                    # - 所以最终条件变成了 WHERE false
                    ConversationContext.is_active == True,
                )
                .first()
            )

            if db_context:
                return ConversationContextModel(
                    id=db_context.id,
                    user_session_id=db_context.user_session_id,
                    current_service_category_id=db_context.current_service_category_id,
                    conversation_history=[
                        Message(**msg) for msg in db_context.conversation_history
                    ],
                    navigation_options=db_context.navigation_options,
                    user_preferences=db_context.user_preferences,
                    # Service relationship tracking fields
                    service_relationships=db_context.service_relationships,
                    related_services_suggested=db_context.related_services_suggested,
                    service_transitions=db_context.service_transitions,
                    created_at=db_context.created_at,
                    last_activity=db_context.last_activity,
                    is_active=db_context.is_active,
                )
            return None

        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            raise

    def update_conversation_context(
        self, session_id: str, conversation_context: ConversationContextModel
    ) -> ConversationContextModel:
        """Update existing conversation context"""
        try:
            db_context = (
                self.db.query(ConversationContext)
                .filter(
                    ConversationContext.user_session_id == session_id,
                    ConversationContext.is_active == True,
                )
                .first()
            )

            if not db_context:
                raise ValueError(
                    f"Conversation context not found for session: {session_id}"
                )

            # Update fields
            db_context.current_service_category_id = (
                conversation_context.current_service_category_id
            )
            db_context.conversation_history = [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": {
                        key: str(value)
                        if hasattr(value, "__str__")
                        and not isinstance(value, str | int | float | bool | type(None))
                        else value
                        for key, value in msg.metadata.items()
                    },
                }
                for msg in conversation_context.conversation_history
            ]
            db_context.navigation_options = [
                {
                    **option,
                    "target_url": str(option.get("target_url"))
                    if option.get("target_url")
                    else None,
                }
                for option in conversation_context.navigation_options
            ]
            db_context.user_preferences = {
                key: str(value)
                if hasattr(value, "__str__")
                and not isinstance(value, str | int | float | bool | type(None))
                else value
                for key, value in conversation_context.user_preferences.items()
            }
            # Update service relationship tracking fields
            db_context.service_relationships = (
                conversation_context.service_relationships
            )
            db_context.related_services_suggested = (
                conversation_context.related_services_suggested
            )
            db_context.service_transitions = conversation_context.service_transitions
            db_context.last_activity = conversation_context.last_activity
            db_context.is_active = conversation_context.is_active

            self.db.commit()
            self.db.refresh(db_context)

            # Convert back to Pydantic model
            return ConversationContextModel(
                id=db_context.id,
                user_session_id=db_context.user_session_id,
                current_service_category_id=db_context.current_service_category_id,
                conversation_history=[
                    Message(**msg) for msg in db_context.conversation_history
                ],
                navigation_options=db_context.navigation_options,
                user_preferences=db_context.user_preferences,
                # Service relationship tracking fields
                service_relationships=db_context.service_relationships,
                related_services_suggested=db_context.related_services_suggested,
                service_transitions=db_context.service_transitions,
                created_at=db_context.created_at,
                last_activity=db_context.last_activity,
                is_active=db_context.is_active,
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update conversation context: {e}")
            raise

    # NavigationOption operations

    def create_navigation_option(
        self, navigation_option: NavigationOptionModel
    ) -> NavigationOptionModel:
        """Create a new navigation option"""
        try:
            db_option = NavigationOption(
                service_category_id=navigation_option.service_category_id,
                label=navigation_option.label,
                action_type=navigation_option.action_type,
                target_url=str(navigation_option.target_url)
                if navigation_option.target_url
                else None,
                description=navigation_option.description,
                priority=navigation_option.priority,
                is_active=navigation_option.is_active,
            )
            self.db.add(db_option)
            self.db.commit()
            self.db.refresh(db_option)

            # Convert back to Pydantic model
            return NavigationOptionModel(
                id=db_option.id,
                service_category_id=db_option.service_category_id,
                label=db_option.label,
                action_type=db_option.action_type,
                target_url=db_option.target_url,
                description=db_option.description,
                priority=db_option.priority,
                is_active=db_option.is_active,
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create navigation option: {e}")
            raise

    def get_navigation_options_by_category(
        self, category_id: uuid.UUID
    ) -> list[NavigationOptionModel]:
        """Get navigation options for a service category"""
        try:
            db_options = (
                self.db.query(NavigationOption)
                .filter(
                    NavigationOption.service_category_id == category_id,
                    NavigationOption.is_active == True,
                )
                .order_by(NavigationOption.priority)
                .all()
            )

            return [
                NavigationOptionModel(
                    id=option.id,
                    service_category_id=option.service_category_id,
                    label=option.label,
                    action_type=option.action_type,
                    target_url=option.target_url,
                    description=option.description,
                    priority=option.priority,
                    is_active=option.is_active,
                )
                for option in db_options
            ]

        except Exception as e:
            logger.error(f"Failed to get navigation options: {e}")
            raise

    def get_navigation_options_by_priority(
        self, category_id: uuid.UUID, priority_threshold: int = 5
    ) -> list[NavigationOptionModel]:
        """Get high-priority navigation options for a service category"""
        try:
            db_options = (
                self.db.query(NavigationOption)
                .filter(
                    NavigationOption.service_category_id == category_id,
                    NavigationOption.is_active == True,
                    NavigationOption.priority <= priority_threshold,
                )
                .order_by(NavigationOption.priority)
                .all()
            )

            return [
                NavigationOptionModel(
                    id=option.id,
                    service_category_id=option.service_category_id,
                    label=option.label,
                    action_type=option.action_type,
                    target_url=option.target_url,
                    description=option.description,
                    priority=option.priority,
                    is_active=option.is_active,
                )
                for option in db_options
            ]

        except Exception as e:
            logger.error(f"Failed to get high-priority navigation options: {e}")
            raise

    def update_navigation_option(
        self, navigation_option: NavigationOptionModel
    ) -> NavigationOptionModel:
        """Update an existing navigation option"""
        try:
            db_option = (
                self.db.query(NavigationOption)
                .filter(NavigationOption.id == navigation_option.id)
                .first()
            )

            if not db_option:
                raise ValueError(f"Navigation option not found: {navigation_option.id}")

            # Update fields
            db_option.label = navigation_option.label
            db_option.action_type = navigation_option.action_type
            db_option.target_url = (
                str(navigation_option.target_url)
                if navigation_option.target_url
                else None
            )
            db_option.description = navigation_option.description
            db_option.priority = navigation_option.priority
            db_option.is_active = navigation_option.is_active

            self.db.commit()
            self.db.refresh(db_option)

            # Convert back to Pydantic model
            return NavigationOptionModel(
                id=db_option.id,
                service_category_id=db_option.service_category_id,
                label=db_option.label,
                action_type=db_option.action_type,
                target_url=db_option.target_url,
                description=db_option.description,
                priority=db_option.priority,
                is_active=db_option.is_active,
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update navigation option: {e}")
            raise

    def get_all_active_navigation_options(self) -> list[NavigationOptionModel]:
        """Get all active navigation options across all service categories"""
        try:
            db_options = (
                self.db.query(NavigationOption)
                .filter(NavigationOption.is_active == True)
                .order_by(NavigationOption.priority)
                .all()
            )

            return [
                NavigationOptionModel(
                    id=option.id,
                    service_category_id=option.service_category_id,
                    label=option.label,
                    action_type=option.action_type,
                    target_url=option.target_url,
                    description=option.description,
                    priority=option.priority,
                    is_active=option.is_active,
                )
                for option in db_options
            ]

        except Exception as e:
            logger.error(f"Failed to get all active navigation options: {e}")
            raise

    def get_prioritized_navigation_options(
        self, user_session_id: str
    ) -> list[NavigationOptionModel]:
        """Get navigation options prioritized based on conversation history"""
        try:
            # Get conversation context to understand current focus
            conversation_context = self.get_conversation_context(user_session_id)

            if not conversation_context:
                # Return default options if no conversation context
                return self.get_all_active_navigation_options()

            # Analyze conversation history for prioritization
            current_category_id = conversation_context.current_service_category_id
            recent_messages = conversation_context.get_recent_messages(limit=5)

            # Extract keywords from recent conversation
            conversation_keywords = self._extract_conversation_keywords(recent_messages)

            # Get all active navigation options
            all_options = self.get_all_active_navigation_options()

            # Prioritize options based on conversation context
            prioritized_options = []
            for option in all_options:
                priority_score = self._calculate_priority_score(
                    option, current_category_id, conversation_keywords
                )
                prioritized_options.append((priority_score, option))

            # Sort by priority score (higher score = higher priority)
            prioritized_options.sort(key=lambda x: x[0], reverse=True)

            # Return top options
            return [option for score, option in prioritized_options[:10]]

        except Exception as e:
            logger.error(f"Failed to get prioritized navigation options: {e}")
            # Fallback to all active options
            return self.get_all_active_navigation_options()

    def get_all_service_categories(self) -> list[ServiceCategoryModel]:
        """Get all service categories for main menu navigation"""
        try:
            db_categories = (
                self.db.query(ServiceCategory)
                .filter(ServiceCategory.is_active == True)
                .order_by(ServiceCategory.name)
                .all()
            )

            return [
                ServiceCategoryModel(
                    id=category.id,
                    name=category.name,
                    description=category.description,
                    official_source_url=category.official_source_url,
                    is_active=category.is_active,
                    created_at=category.created_at,
                    updated_at=category.updated_at,
                    last_verified=category.last_verified,
                )
                for category in db_categories
            ]

        except Exception as e:
            logger.error(f"Failed to get all service categories: {e}")
            raise

    def _extract_conversation_keywords(self, messages: list) -> set[str]:
        """Extract keywords from conversation messages for prioritization"""
        keywords = set()

        # Common keywords related to government services
        service_keywords = {
            "requirement",
            "document",
            "material",
            "appointment",
            "schedule",
            "location",
            "address",
            "cost",
            "fee",
            "price",
            "status",
            "track",
            "application",
            "apply",
            "submit",
            "register",
            "renew",
            "extension",
            "passport",
            "visa",
            "permit",
            "license",
            "registration",
            "business",
        }

        for message in messages:
            content = message.content.lower()
            for keyword in service_keywords:
                if keyword in content:
                    keywords.add(keyword)

        return keywords

    def _calculate_priority_score(
        self,
        option: NavigationOptionModel,
        current_category_id: uuid.UUID | None,
        conversation_keywords: set[str],
    ) -> int:
        """Calculate priority score for navigation option based on context"""
        score = 0

        # Base score from option priority (inverted: lower priority number = higher score)
        score += (11 - option.priority) * 10

        # Boost for current service category
        if current_category_id and option.service_category_id == current_category_id:
            score += 50

        # Boost for keyword matches
        option_label_lower = option.label.lower()
        for keyword in conversation_keywords:
            if keyword in option_label_lower:
                score += 20

        # Boost for common action types
        if option.action_type in ["requirements", "appointment", "location"]:
            score += 15

        return score
