#!/usr/bin/env python3
"""
Data ingestion script for City Guide Smart Assistant
Populates the database with Hong Kong/Macau passport service data
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from pydantic import HttpUrl

from src.models.embeddings import DocumentEmbedding
from src.models.services import NavigationOption, ServiceCategory
from src.services.data_service import DataService
from src.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_passport_service_category():
    """Create Hong Kong/Macau passport service category with official sources"""

    logger.info("Creating Hong Kong/Macau passport service category...")

    with DataService() as data_service:
        # Check if passport service already exists
        existing_categories = data_service.get_active_service_categories()
        passport_exists = any(
            "passport" in category.name.lower() for category in existing_categories
        )

        if passport_exists:
            logger.info("Passport service category already exists, skipping creation")
            return None

        # Create Hong Kong/Macau passport service category
        passport_service = ServiceCategory(
            name="Hong Kong and Macau Passport Services",
            description="Passport application, renewal, and related services for Hong Kong and Macau residents",
            official_source_url=HttpUrl(
                "https://www.gov.hk/en/residents/immigration/traveldoc/"
            ),
            last_verified=datetime.now(UTC),
            is_active=True,
        )

        created_service = data_service.create_service_category(passport_service)
        logger.info(f"Created passport service category: {created_service.name}")

        return created_service


async def create_passport_navigation_options(service_category_id):
    """Create navigation options for passport service"""

    logger.info("Creating passport service navigation options...")

    with DataService() as data_service:
        # Navigation options for passport service
        navigation_options = [
            NavigationOption(
                service_category_id=service_category_id,
                label="Passport Requirements",
                action_type="requirements",
                description="View required documents and eligibility criteria for passport applications",
                priority=1,
                is_active=True,
            ),
            NavigationOption(
                service_category_id=service_category_id,
                label="Make Appointment",
                action_type="appointment",
                target_url=HttpUrl(
                    "https://www.gov.hk/en/residents/immigration/traveldoc/hksarpassport/applyhkpassport.htm"
                ),
                description="Schedule an appointment for passport application or renewal",
                priority=2,
                is_active=True,
            ),
            NavigationOption(
                service_category_id=service_category_id,
                label="Required Materials",
                action_type="requirements",
                description="Checklist of documents and materials needed for passport application",
                priority=3,
                is_active=True,
            ),
            NavigationOption(
                service_category_id=service_category_id,
                label="Service Locations",
                action_type="location",
                target_url=HttpUrl(
                    "https://www.immd.gov.hk/eng/contactus/office_hour.html"
                ),
                description="Find nearby Immigration Department offices for passport services",
                priority=4,
                is_active=True,
            ),
            NavigationOption(
                service_category_id=service_category_id,
                label="Passport Renewal",
                action_type="explain",
                description="Step-by-step guide for passport renewal process",
                priority=5,
                is_active=True,
            ),
            NavigationOption(
                service_category_id=service_category_id,
                label="Lost Passport",
                action_type="explain",
                description="Procedures for reporting and replacing lost or stolen passports",
                priority=6,
                is_active=True,
            ),
            NavigationOption(
                service_category_id=service_category_id,
                label="Fees and Payment",
                action_type="explain",
                description="Current passport application fees and payment methods",
                priority=7,
                is_active=True,
            ),
            NavigationOption(
                service_category_id=service_category_id,
                label="Processing Time",
                action_type="explain",
                description="Estimated processing times for passport applications",
                priority=8,
                is_active=True,
            ),
            NavigationOption(
                service_category_id=service_category_id,
                label="Related Services",
                action_type="related",
                description="Other immigration and travel document services",
                priority=9,
                is_active=True,
            ),
        ]

        created_options = []
        for option in navigation_options:
            created_option = data_service.create_navigation_option(option)
            created_options.append(created_option)
            logger.info(f"Created navigation option: {created_option.label}")

        return created_options


async def create_sample_passport_documents():
    """Create sample passport document embeddings for search"""

    logger.info("Creating sample passport document embeddings...")

    with EmbeddingService() as embedding_service:
        # Sample passport-related documents for semantic search
        passport_documents = [
            {
                "source_id": uuid.uuid4(),
                "document_url": "https://www.gov.hk/en/residents/immigration/traveldoc/hksarpassport/applyhkpassport.htm",
                "document_title": "Hong Kong SAR Passport Application Requirements",
                "document_content": "Hong Kong Special Administrative Region Passport Application Requirements",
                "metadata": {
                    "document_type": "requirements",
                    "service_category": "passport",
                    "source": "official",
                    "language": "en",
                },
            },
            {
                "source_id": uuid.uuid4(),
                "document_url": "https://www.gov.hk/en/residents/immigration/traveldoc/hksarpassport/applyhkpassport.htm",
                "document_title": "Hong Kong Passport Eligibility and Documents",
                "document_content": "To apply for a Hong Kong SAR passport, you must be a Chinese citizen and a permanent resident of Hong Kong. Required documents include: completed application form, recent photograph, proof of identity, and proof of Hong Kong permanent residence.",
                "metadata": {
                    "document_type": "requirements",
                    "service_category": "passport",
                    "source": "official",
                    "language": "en",
                },
            },
            {
                "source_id": uuid.uuid4(),
                "document_url": "https://www.immd.gov.hk/eng/fees/passport.html",
                "document_title": "Hong Kong Passport Application Fees",
                "document_content": "Passport application fees for Hong Kong SAR passport: Standard application HKD 370, 32-page passport HKD 460. Payment can be made at Immigration Department offices or through designated banks.",
                "metadata": {
                    "document_type": "fees",
                    "service_category": "passport",
                    "source": "official",
                    "language": "en",
                },
            },
            {
                "source_id": uuid.uuid4(),
                "document_url": "https://www.immd.gov.hk/eng/services/travel_document/processing_time.html",
                "document_title": "Hong Kong Passport Processing Times",
                "document_content": "Standard processing time for Hong Kong passport applications is 10 working days. Urgent service (additional fee) can reduce processing to 5 working days. Applications can be submitted in person or by post.",
                "metadata": {
                    "document_type": "processing_time",
                    "service_category": "passport",
                    "source": "official",
                    "language": "en",
                },
            },
            {
                "source_id": uuid.uuid4(),
                "document_url": "https://www.gov.mo/en/services/passport/",
                "document_title": "Macau SAR Passport Requirements",
                "document_content": "Macau Special Administrative Region Passport application requires Macau permanent resident status. Application can be made at the Identification Services Bureau of Macau with required documents including ID card and proof of residence.",
                "metadata": {
                    "document_type": "requirements",
                    "service_category": "passport",
                    "source": "official",
                    "language": "en",
                },
            },
            {
                "source_id": uuid.uuid4(),
                "document_url": "https://www.gov.hk/en/residents/immigration/traveldoc/hksarpassport/renewhkpassport.htm",
                "document_title": "Hong Kong Passport Renewal Guide",
                "document_content": "Passport renewal in Hong Kong can be done if your current passport has less than 12 months validity or has expired. You need to complete application form ID 843 and provide your current passport.",
                "metadata": {
                    "document_type": "renewal",
                    "service_category": "passport",
                    "source": "official",
                    "language": "en",
                },
            },
            {
                "source_id": uuid.uuid4(),
                "document_url": "https://www.gov.hk/en/residents/immigration/traveldoc/hksarpassport/lostpassport.htm",
                "document_title": "Lost or Stolen Hong Kong Passport Procedures",
                "document_content": "For lost or stolen Hong Kong passport, you must report to the police immediately and obtain a police report. Then visit Immigration Department with the report and other identification documents to apply for replacement.",
                "metadata": {
                    "document_type": "lost_passport",
                    "service_category": "passport",
                    "source": "official",
                    "language": "en",
                },
            },
            {
                "source_id": uuid.uuid4(),
                "document_url": "https://www.immd.gov.hk/eng/contactus/office_hour.html",
                "document_title": "Hong Kong Immigration Department Offices",
                "document_content": "Hong Kong Immigration Department offices for passport services are located in Wan Chai, Kowloon, and Tsuen Wan. Office hours are Monday to Friday 9:00 AM to 4:30 PM, Saturday 9:00 AM to 12:30 PM.",
                "metadata": {
                    "document_type": "locations",
                    "service_category": "passport",
                    "source": "official",
                    "language": "en",
                },
            },
            {
                "source_id": uuid.uuid4(),
                "document_url": "https://www.gov.hk/en/residents/immigration/traveldoc/hksarpassport/photo.htm",
                "document_title": "Passport Photograph Requirements",
                "document_content": "Passport photograph requirements: recent color photo, 40mm x 50mm size, plain white background, full face without head covering (except for religious reasons), no sunglasses or hats that obscure facial features.",
                "metadata": {
                    "document_type": "requirements",
                    "service_category": "passport",
                    "source": "official",
                    "language": "en",
                },
            },
            {
                "source_id": uuid.uuid4(),
                "document_url": "https://www.gov.hk/en/residents/immigration/traveldoc/hksarpassport/childpassport.htm",
                "document_title": "Children's Passport Applications",
                "document_content": "Children's passport applications require additional documents including birth certificate, parent's consent, and both parents' identification documents. Children under 11 must apply in person with parents.",
                "metadata": {
                    "document_type": "requirements",
                    "service_category": "passport",
                    "source": "official",
                    "language": "en",
                },
            },
        ]

        # Add documents to vector database
        for doc in passport_documents:
            # Create a DocumentEmbedding object
            document_embedding = DocumentEmbedding(
                source_id=doc["source_id"],
                document_url=doc["document_url"],
                document_title=doc["document_title"],
                document_content=doc["document_content"],
                metadata=doc["metadata"],
                # Note: In a real implementation, we would generate embeddings here
                # For now, we'll use placeholder embeddings
                embedding_vector=[0.0] * 1024,  # Placeholder for Qwen3-Embedding-0.6B
            )

            embedding_id = embedding_service.store_document_embedding(
                document_embedding
            )
            logger.info(
                f"Added passport document to vector database: {doc['document_title']}"
            )

        logger.info(
            f"Successfully added {len(passport_documents)} passport documents to vector database"
        )
        return len(passport_documents)


async def main():
    """Main data ingestion function"""

    logger.info("Starting data ingestion for Hong Kong/Macau passport services...")

    try:
        # Step 1: Create passport service category
        passport_service = await create_passport_service_category()

        if not passport_service:
            logger.info("Passport service already exists, skipping data ingestion")
            return

        # Step 2: Create navigation options
        navigation_options = await create_passport_navigation_options(
            passport_service.id
        )

        # Step 3: Create sample document embeddings
        document_count = await create_sample_passport_documents()

        logger.info("Data ingestion completed successfully!")
        logger.info(f"- Created service category: {passport_service.name}")
        logger.info(f"- Created navigation options: {len(navigation_options)}")
        logger.info(f"- Added document embeddings: {document_count}")

    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
