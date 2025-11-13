#!/usr/bin/env python3
"""
Generate document embeddings for City Guide Smart Assistant
"""

import logging
import uuid
import os
import re
from datetime import UTC, datetime
from pathlib import Path

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
                "total_chunks": 1,
                "language": "en",
                "section_type": "requirements",
                "source_priority": 1,
                "last_verified": 1700000000,
                "is_active": True,
                "service_category": "港澳通行证",
                "chunk_characteristics": {
                    "word_count": 120,
                    "sentence_count": 8,
                    "has_tables": False,
                },
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
                "total_chunks": 1,
                "language": "en",
                "section_type": "procedures",
                "source_priority": 1,
                "last_verified": 1700000000,
                "is_active": True,
                "service_category": "港澳通行证",
                "chunk_characteristics": {
                    "word_count": 90,
                    "sentence_count": 6,
                    "has_tables": False,
                },
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
                "total_chunks": 1,
                "language": "en",
                "section_type": "locations",
                "source_priority": 1,
                "last_verified": 1700000000,
                "is_active": True,
                "service_category": "港澳通行证",
                "chunk_characteristics": {
                    "word_count": 110,
                    "sentence_count": 7,
                    "has_tables": False,
                },
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
                "total_chunks": 1,
                "language": "en",
                "section_type": "faqs",
                "source_priority": 1,
                "last_verified": 1700000000,
                "is_active": True,
                "service_category": "港澳通行证",
                "chunk_characteristics": {
                    "word_count": 150,
                    "sentence_count": 10,
                    "has_tables": False,
                },
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
                "total_chunks": 1,
                "language": "en",
                "section_type": "requirements",
                "source_priority": 1,
                "last_verified": 1700000000,
                "is_active": True,
                "service_category": "港澳通行证",
                "chunk_characteristics": {
                    "word_count": 80,
                    "sentence_count": 8,
                    "has_tables": False,
                },
            },
        },
    ]

    # Add service category ID to each document
    for doc in documents:
        doc["service_category_id"] = service_category_id

    return documents


def classify_document_type(content: str, title: str) -> str:
    """
    Classify document type based on content and title
    """
    content_lower = content.lower()
    title_lower = title.lower()

    # Check for 办理对象 patterns
    object_patterns = [
        r"办理对象",
        r"申请对象",
        r"适用对象",
        r"服务对象",
        r"哪些人可以",
        r"谁可以办理",
        r"适用人群",
        r"对象",
    ]
    for pattern in object_patterns:
        if re.search(pattern, content_lower) or re.search(pattern, title_lower):
            return "办理对象"

    # Check for 办理材料 patterns
    material_patterns = [
        r"办理材料",
        r"所需材料",
        r"材料要求",
        r"申请材料",
        r"需要准备",
        r"准备材料",
        r"材料清单",
        r"材料",
    ]
    for pattern in material_patterns:
        if re.search(pattern, content_lower) or re.search(pattern, title_lower):
            return "办理材料"

    # Check for 办理流程 patterns
    process_patterns = [
        r"办理流程",
        r"办理步骤",
        r"申请流程",
        r"申请步骤",
        r"操作流程",
        r"操作步骤",
        r"流程",
        r"步骤",
        r"第一步",
        r"第二步",
        r"第三步",
        r"第四步",
        r"如何办理",
        r"怎么办理",
    ]
    for pattern in process_patterns:
        if re.search(pattern, content_lower) or re.search(pattern, title_lower):
            return "办理流程"

    # Check for 办理地点 patterns
    location_patterns = [
        r"办理地点",
        r"服务地点",
        r"办公地点",
        r"地址",
        r"地点",
        r"位置",
        r"在哪里办理",
        r"办理窗口",
    ]
    for pattern in location_patterns:
        if re.search(pattern, content_lower) or re.search(pattern, title_lower):
            return "办理地点"

    # Check for 办理时间 patterns
    time_patterns = [
        r"办理时间",
        r"办理时限",
        r"处理时间",
        r"审批时间",
        r"多久办好",
        r"需要多长时间",
        r"工作日",
        r"自然日",
        r"时限",
        r"时间",
    ]
    for pattern in time_patterns:
        if re.search(pattern, content_lower) or re.search(pattern, title_lower):
            return "办理时间"

    # Check for 费用标准 patterns
    fee_patterns = [r"费用", r"收费标准", r"办理费用", r"申请费用", r"多少钱", r"收费", r"价格", r"费用标准"]
    for pattern in fee_patterns:
        if re.search(pattern, content_lower) or re.search(pattern, title_lower):
            return "费用标准"

    # Check for 常见问题 patterns
    faq_patterns = [
        r"常见问题",
        r"faq",
        r"q&a",
        r"问答",
        r"办理须知",
        r"^q:",
        r"^a:",
        r"^问:",
        r"^答:",
        r"^问题",
        r"注意事项",
        r"注意",
    ]
    for pattern in faq_patterns:
        if re.search(pattern, content_lower) or re.search(pattern, title_lower):
            return "常见问题"

    # Check for 其他事项 patterns
    other_patterns = [r"其他事项", r"其他说明", r"补充说明", r"其他", r"特别说明", r"说明事项"]
    for pattern in other_patterns:
        if re.search(pattern, content_lower) or re.search(pattern, title_lower):
            return "其他事项"

    # Default to 办理对象 if no clear match
    return "办理对象"


def extract_title_from_content(content: str) -> str:
    """
    Extract title from markdown content
    """
    # Look for markdown headers
    header_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if header_match:
        return header_match.group(1).strip()

    # Look for the first line that might be a title
    first_line = content.split("\n")[0].strip()
    if first_line and len(first_line) < 100:  # Reasonable title length
        return first_line

    return "Untitled Document"


def split_document_by_sections(content: str, title: str) -> list:
    """
    Split a document into sections based on markdown headers
    """
    sections = []

    # Split by markdown headers (##, ###)
    header_pattern = r"(^#{2,3}\s+.+$)"
    parts = re.split(header_pattern, content, flags=re.MULTILINE)

    current_section_title = title
    current_section_content = ""

    for i, part in enumerate(parts):
        if i == 0 and not part.strip():
            continue

        if re.match(r"^#{2,3}\s+", part):
            # This is a header, save previous section if any
            if current_section_content.strip():
                sections.append(
                    {
                        "title": current_section_title,
                        "content": current_section_content.strip(),
                    }
                )

            # Start new section
            current_section_title = re.sub(r"^#{2,3}\s+", "", part).strip()
            current_section_content = ""
        else:
            current_section_content += part

    # Add the last section
    if current_section_content.strip():
        sections.append(
            {"title": current_section_title, "content": current_section_content.strip()}
        )

    # If no sections were created, use the whole document as one section
    if not sections:
        sections.append({"title": title, "content": content.strip()})

    return sections


def create_faq_from_progress_query(content: str, title: str) -> list:
    """
    Create FAQ documents from progress query content
    """
    faq_documents = []

    # Check if this is a progress query document
    progress_keywords = ["办理进度", "进度查询", "查询进度", "查看进度"]
    is_progress_query = any(
        keyword in title or keyword in content for keyword in progress_keywords
    )

    if not is_progress_query:
        return []

    # Create FAQ question
    faq_question = "如何查看港澳通行证办理进度？"

    # Extract the main answer from content
    lines = content.split("\n")
    answer_lines = []

    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("办理入口"):
            # Clean up the line
            line = re.sub(r"^\d+、", "", line)  # Remove numbered lists
            line = re.sub(r"^\s*[-•]\s*", "", line)  # Remove bullet points
            if line:
                answer_lines.append(line)

    if answer_lines:
        # Clean and structure the answer
        clean_answer_lines = []

        for line in answer_lines:
            # Skip empty lines and redundant information
            if line and not any(keyword in line for keyword in ["办理入口", "点击这里查询"]):
                clean_answer_lines.append(line)

        faq_answer = "\n".join(clean_answer_lines)

        # Add entry point information if available
        entry_match = re.search(r"办理入口：\[([^\]]+)\]\(([^)]+)\)", content)
        if entry_match:
            entry_text = entry_match.group(1)
            entry_url = entry_match.group(2)
            faq_answer += f"\n\n办理入口：{entry_text} ({entry_url})"

        # Add processing time information if available in the document
        time_match = re.search(r"(广东省[内外]户籍.*?\d+[个]?[工作日自然日]+)", content)
        if time_match:
            faq_answer += f"\n\n{time_match.group(1)}"

        # Add fee information if available
        fee_match = re.search(r"(港澳通行证.*?\d+元)", content)
        if fee_match:
            faq_answer += f"\n\n{fee_match.group(1)}"

        faq_document = {
            "title": faq_question,
            "content": faq_answer,
            "document_type": "常见问题",
            "metadata": {
                "total_chunks": 1,
                "language": "zh",
                "section_type": "faqs",
                "source_priority": 1,
                "last_verified": int(datetime.now(UTC).timestamp()),
                "is_active": True,
                "service_category": "港澳通行证",
                "chunk_characteristics": {
                    "word_count": len(faq_answer.split()),
                    "sentence_count": len(faq_answer.split("。")),
                    "has_tables": False,
                },
            },
        }

        faq_documents.append(faq_document)

    return faq_documents


def load_documents_from_external_dir(service_category_id: uuid.UUID) -> list:
    """
    Load and process documents from docs-external directory
    """
    docs_external_dir = Path("docs-external")
    documents = []

    if not docs_external_dir.exists():
        logger.warning(f"docs-external directory not found: {docs_external_dir}")
        return documents

    # Supported file extensions
    supported_extensions = [".md", ".txt"]

    for file_path in docs_external_dir.glob("*"):
        if file_path.suffix.lower() in supported_extensions:
            try:
                # Read file content
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()

                if not content:
                    logger.warning(f"Empty file: {file_path}")
                    continue

                # Extract title
                title = extract_title_from_content(content)

                # Try to create FAQ from progress query content
                faq_documents = create_faq_from_progress_query(content, title)

                if faq_documents:
                    # Add FAQ documents
                    for faq_doc in faq_documents:
                        faq_doc["service_category_id"] = service_category_id
                        documents.append(faq_doc)
                        logger.info(
                            f"Created FAQ from {file_path.name}: {faq_doc['title']}"
                        )

                # Also process as regular sections
                sections = split_document_by_sections(content, title)

                for i, section in enumerate(sections):
                    section_title = section["title"]
                    section_content = section["content"]

                    # Classify document type
                    document_type = classify_document_type(
                        section_content, section_title
                    )

                    # Create document entry
                    document = {
                        "title": section_title,
                        "content": section_content,
                        "document_type": document_type,
                        "metadata": {
                            "total_chunks": len(sections),
                            "language": "zh",
                            "section_type": document_type,
                            "source_priority": 1,
                            "last_verified": int(datetime.now(UTC).timestamp()),
                            "is_active": True,
                            "service_category": "港澳通行证",
                            "chunk_characteristics": {
                                "word_count": len(section_content.split()),
                                "sentence_count": len(section_content.split("。")),
                                "has_tables": "表格" in section_content,
                            },
                        },
                        "service_category_id": service_category_id,
                    }

                    documents.append(document)

                    logger.info(
                        f"Processed section {i+1}/{len(sections)} from {file_path.name}: "
                        f"{section_title} ({document_type})"
                    )

                logger.info(
                    f"Successfully processed {file_path.name}: {len(sections)} sections"
                )

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")

    logger.info(
        f"Loaded {len(documents)} document sections from docs-external directory"
    )
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

        # Create sample documents from external directory
        documents = load_documents_from_external_dir(sample_service_id)

        # If no external documents found, fall back to sample documents
        if not documents:
            logger.info("No external documents found, using sample documents")
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
