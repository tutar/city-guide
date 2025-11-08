#!/usr/bin/env python3
"""
Generate document embeddings for City Guide Smart Assistant
"""

import logging
import uuid
from datetime import UTC, datetime

from src.models.document_embeddings import DocumentEmbedding
from src.services.ai_service import AIService
from src.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_passport_documents(service_category_id: uuid.UUID):
    """Create sample passport document content for embedding generation"""

    documents = [
        {
            "title": "Hong Kong Passport Application Requirements",
            "content": """Requirements for Hong Kong passport application:

1. Completed application form (ID 853)
2. Two recent color photographs (45mm x 35mm)
3. Hong Kong Identity Card
4. Proof of Hong Kong permanent residence
5. Previous passport (if applicable)
6. Supporting documents for name change (if applicable)

Processing time: 10-14 working days
Application fee: HKD 370 for 32-page passport

Official source: Hong Kong Immigration Department""",
            "document_type": "requirements",
            "metadata": {
                "source": "immd.gov.hk",
                "language": "en",
                "last_updated": "2024-01-15",
            },
        },
        {
            "title": "Macau Passport Application Process",
            "content": """Macau passport application procedure:

Step 1: Complete application form
Step 2: Submit required documents
Step 3: Pay application fee
Step 4: Collect passport

Required documents:
- Macau Resident Identity Card
- Two passport photos
- Birth certificate
- Previous passport (if any)

Processing time: 15 working days
Fee: MOP 300

Official source: Macau Identification Services Bureau""",
            "document_type": "procedures",
            "metadata": {
                "source": "dsedt.gov.mo",
                "language": "en",
                "last_updated": "2024-01-10",
            },
        },
        {
            "title": "Passport Service Locations in Shenzhen",
            "content": """Hong Kong and Macau passport service locations in Shenzhen:

1. Hong Kong Immigration Department Shenzhen Office
   Address: 28/F, Shenzhen Bay Port, Nanshan District
   Hours: Monday-Friday 9:00-17:00
   Services: Passport application, collection

2. Macau Government Services Center
   Address: 15/F, Futian Free Trade Zone Building, Futian District
   Hours: Monday-Friday 8:30-17:30
   Services: Passport services, document authentication

Note: Appointments required for all services.""",
            "document_type": "locations",
            "metadata": {
                "source": "gov.hk",
                "language": "en",
                "last_updated": "2024-01-20",
            },
        },
        {
            "title": "Passport Application FAQ",
            "content": """Frequently Asked Questions about passport applications:

Q: How long does it take to get a new passport?
A: 10-14 working days for Hong Kong, 15 working days for Macau.

Q: Can I apply for passport renewal online?
A: Yes, through the official government portals.

Q: What documents do I need for a child's passport?
A: Birth certificate, parent's ID, and consent forms.

Q: Can I expedite my passport application?
A: Expedited service available for urgent cases with additional fee.

Q: Where can I collect my new passport?
A: At the application office or designated collection points.""",
            "document_type": "faqs",
            "metadata": {
                "source": "official_guidelines",
                "language": "en",
                "last_updated": "2024-01-18",
            },
        },
        {
            "title": "Passport Photo Requirements",
            "content": """Passport photo specifications:

- Size: 45mm x 35mm
- Color: Recent color photograph
- Background: Plain white or light-colored
- Expression: Neutral, both eyes open
- Headwear: Only for religious purposes
- Glasses: Thin frames, no tinted lenses
- Quality: High resolution, no shadows

Photo must be taken within the last 6 months.
Digital photos must be in JPEG format.""",
            "document_type": "requirements",
            "metadata": {
                "source": "immd.gov.hk",
                "language": "en",
                "last_updated": "2024-01-12",
            },
        },
    ]

    # Add service category ID to each document
    for doc in documents:
        doc["service_category_id"] = service_category_id

    return documents


def generate_document_embeddings(
    documents: list, ai_service: AIService, embedding_service: EmbeddingService
):
    """Generate embeddings for documents and store in vector database"""

    embeddings_created = 0
    failed_embeddings = 0

    for doc in documents:
        try:
            # Generate embedding for document content
            embedding_vector = ai_service.generate_embedding(doc["content"])

            # Create document embedding object
            document_embedding = DocumentEmbedding(
                service_category_id=doc["service_category_id"],
                document_type=doc["document_type"],
                title=doc["title"],
                content=doc["content"],
                embedding=embedding_vector,
                metadata=doc.get("metadata", {}),
                is_active=True,
            )

            # Store in vector database
            embedding_service.store_document_embedding(document_embedding)
            embeddings_created += 1

            logger.info(f"Generated embedding for: {doc['title']}")

        except Exception as e:
            logger.error(f"Failed to generate embedding for {doc['title']}: {e}")
            failed_embeddings += 1

    return embeddings_created, failed_embeddings


def generate_sample_embeddings():
    """Generate sample passport document embeddings"""

    try:
        logger.info("Starting sample embedding generation...")

        # Initialize services
        ai_service = AIService()
        embedding_service = EmbeddingService()

        # Create a sample service category ID for testing
        # In production, this would come from the actual database
        sample_service_id = uuid.uuid4()

        # Create sample documents
        documents = create_sample_passport_documents(sample_service_id)

        # Generate embeddings
        start_time = datetime.now(UTC)
        embeddings_created, failed_embeddings = generate_document_embeddings(
            documents, ai_service, embedding_service
        )
        processing_time = (datetime.now(UTC) - start_time).total_seconds()

        # Log results
        logger.info("Embedding generation completed:")
        logger.info(f"- Documents processed: {len(documents)}")
        logger.info(f"- Embeddings created: {embeddings_created}")
        logger.info(f"- Failed embeddings: {failed_embeddings}")
        logger.info(f"- Processing time: {processing_time:.2f} seconds")

        # Get collection stats
        stats = embedding_service.get_collection_stats()
        logger.info(f"Vector database stats: {stats}")

        return {
            "total_documents": len(documents),
            "embeddings_created": embeddings_created,
            "failed_embeddings": failed_embeddings,
            "processing_time": processing_time,
            "collection_stats": stats,
        }

    except Exception as e:
        logger.error(f"Failed to generate sample embeddings: {e}")
        raise


if __name__ == "__main__":
    """Run embedding generation when script is executed directly"""
    try:
        result = generate_sample_embeddings()
        logger.info(f"Sample embedding generation completed successfully: {result}")
    except Exception as e:
        logger.error(f"Sample embedding generation failed: {e}")
        exit(1)
