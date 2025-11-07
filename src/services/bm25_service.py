"""
BM25 keyword search service for City Guide Smart Assistant
"""

import logging
import math
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter

# Configure logging
logger = logging.getLogger(__name__)


class BM25Service:
    """BM25 keyword search implementation for sparse retrieval"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.term_freqs = []
        self.doc_freqs = defaultdict(int)
        self.vocab = set()

    def index_documents(self, documents: List[Dict[str, Any]]):
        """Index documents for BM25 search"""
        try:
            self.documents = documents
            self.doc_lengths = []
            self.term_freqs = []
            self.doc_freqs.clear()
            self.vocab.clear()

            # Process each document
            for doc in documents:
                # Tokenize document content
                content = f"{doc.get('document_title', '')} {doc.get('document_content', '')}"
                tokens = self._tokenize_chinese(content)

                # Calculate document length
                doc_length = len(tokens)
                self.doc_lengths.append(doc_length)

                # Calculate term frequencies
                term_freq = Counter(tokens)
                self.term_freqs.append(term_freq)

                # Update document frequencies
                for term in term_freq.keys():
                    self.doc_freqs[term] += 1
                    self.vocab.add(term)

            # Calculate average document length
            if self.doc_lengths:
                self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)

            logger.info(f"Indexed {len(documents)} documents with {len(self.vocab)} unique terms")

        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents using BM25"""
        try:
            if not self.documents:
                return []

            # Tokenize query
            query_terms = self._tokenize_chinese(query)
            query_term_freq = Counter(query_terms)

            # Calculate scores for each document
            scores = []
            for i, doc in enumerate(self.documents):
                score = self._calculate_bm25_score(
                    query_term_freq, i, len(self.documents)
                )
                scores.append((score, doc))

            # Sort by score and return top results
            scores.sort(key=lambda x: x[0], reverse=True)
            results = [doc for score, doc in scores[:limit]]

            # Add BM25 scores to results
            for i, (score, doc) in enumerate(scores[:limit]):
                results[i]['bm25_score'] = score

            logger.debug(f"BM25 search found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    def _calculate_bm25_score(
        self,
        query_term_freq: Counter,
        doc_index: int,
        total_docs: int
    ) -> float:
        """Calculate BM25 score for a document"""
        score = 0.0
        doc_length = self.doc_lengths[doc_index]
        term_freq = self.term_freqs[doc_index]

        for term, query_freq in query_term_freq.items():
            if term not in term_freq:
                continue

            # Term frequency in document
            tf = term_freq[term]

            # Document frequency
            df = self.doc_freqs.get(term, 0)

            # Inverse document frequency
            idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)

            # BM25 term score
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            term_score = idf * (numerator / denominator)

            # Multiply by query term frequency
            score += term_score * query_freq

        return score

    def _tokenize_chinese(self, text: str) -> List[str]:
        """Basic Chinese text tokenization"""
        # This is a simple character-based tokenization
        # In production, you would use jieba or other Chinese tokenizers

        # Remove punctuation and convert to lowercase
        import string
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = text.lower()

        # Character-based tokenization for Chinese
        tokens = []
        for char in text:
            if char.strip() and not char.isspace():
                tokens.append(char)

        return tokens

    def get_index_stats(self) -> Dict[str, Any]:
        """Get BM25 index statistics"""
        return {
            "num_documents": len(self.documents),
            "vocabulary_size": len(self.vocab),
            "avg_document_length": self.avg_doc_length,
            "total_terms": sum(self.doc_lengths),
            "parameters": {
                "k1": self.k1,
                "b": self.b
            }
        }

    def add_document(self, document: Dict[str, Any]):
        """Add a single document to the index"""
        try:
            self.documents.append(document)

            # Tokenize document content
            content = f"{document.get('document_title', '')} {document.get('document_content', '')}"
            tokens = self._tokenize_chinese(content)

            # Update document length
            doc_length = len(tokens)
            self.doc_lengths.append(doc_length)

            # Update term frequencies
            term_freq = Counter(tokens)
            self.term_freqs.append(term_freq)

            # Update document frequencies
            for term in term_freq.keys():
                self.doc_freqs[term] += 1
                self.vocab.add(term)

            # Recalculate average document length
            self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)

            logger.debug(f"Added document to BM25 index: {document.get('document_title', 'Unknown')}")

        except Exception as e:
            logger.error(f"Failed to add document to BM25 index: {e}")
            raise

    def remove_document(self, document_id: str):
        """Remove a document from the index"""
        try:
            # Find document index
            doc_index = None
            for i, doc in enumerate(self.documents):
                if doc.get('id') == document_id:
                    doc_index = i
                    break

            if doc_index is None:
                logger.warning(f"Document not found in BM25 index: {document_id}")
                return

            # Remove document
            removed_doc = self.documents.pop(doc_index)
            removed_length = self.doc_lengths.pop(doc_index)
            removed_term_freq = self.term_freqs.pop(doc_index)

            # Update document frequencies
            for term in removed_term_freq.keys():
                self.doc_freqs[term] -= 1
                if self.doc_freqs[term] == 0:
                    del self.doc_freqs[term]
                    self.vocab.discard(term)

            # Recalculate average document length
            if self.doc_lengths:
                self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
            else:
                self.avg_doc_length = 0

            logger.debug(f"Removed document from BM25 index: {removed_doc.get('document_title', 'Unknown')}")

        except Exception as e:
            logger.error(f"Failed to remove document from BM25 index: {e}")
            raise