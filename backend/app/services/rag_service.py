"""RAG Service for document retrieval and processing"""

import io
import uuid
from typing import List, Dict, Any, Optional, BinaryIO
from datetime import datetime
import PyMuPDF  # fitz
from docx import Document as DocxDocument
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import tiktoken

from app.core.config import settings


class RAGService:
    """Service for Retrieval-Augmented Generation"""

    def __init__(self):
        """Initialize RAG service"""
        self.qdrant_client = None
        self.embedding_model = None
        self.tokenizer = None
        self.initialized = False

    async def initialize(self):
        """Initialize Qdrant client and embedding model"""
        if self.initialized:
            return

        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )

        # Initialize embedding model
        # Using BGE for self-hosted or OpenAI for cloud
        if settings.openai_api_key:
            # Will use OpenAI embeddings API
            self.embedding_type = "openai"
        else:
            # Use local embedding model
            self.embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
            self.embedding_type = "local"

        # Initialize tokenizer for chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        self.initialized = True

    async def create_collection(self, organization_id: str):
        """Create a Qdrant collection for an organization"""
        if not self.initialized:
            await self.initialize()

        collection_name = f"org_{organization_id}"

        # Check if collection exists
        collections = self.qdrant_client.get_collections().collections
        if collection_name not in [c.name for c in collections]:
            # Create collection with appropriate vector size
            vector_size = 1536 if self.embedding_type == "openai" else 384

            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    async def process_document(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        document_id: str,
        organization_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a document: extract text, chunk, embed, and store in vector DB

        Args:
            file: File object
            filename: Original filename
            content_type: MIME type
            document_id: Document UUID
            organization_id: Organization UUID
            metadata: Additional metadata

        Returns:
            Processing results with chunk count and IDs
        """
        if not self.initialized:
            await self.initialize()

        # Extract text based on file type
        text = await self._extract_text(file, content_type)

        # Chunk the text
        chunks = self._chunk_text(text, chunk_size=512, overlap=50)

        # Generate embeddings and store
        chunk_ids = await self._embed_and_store(
            chunks=chunks,
            document_id=document_id,
            organization_id=organization_id,
            filename=filename,
            metadata=metadata or {}
        )

        return {
            "text_length": len(text),
            "chunk_count": len(chunks),
            "chunk_ids": chunk_ids
        }

    async def _extract_text(self, file: BinaryIO, content_type: str) -> str:
        """Extract text from various file types"""
        file_content = file.read()

        if content_type == "application/pdf":
            # Extract text from PDF
            doc = PyMuPDF.open(stream=file_content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            return text

        elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            # Extract text from Word document
            doc = DocxDocument(io.BytesIO(file_content))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text

        elif content_type.startswith("text/"):
            # Plain text file
            return file_content.decode("utf-8", errors="ignore")

        else:
            raise ValueError(f"Unsupported file type: {content_type}")

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller segments with overlap

        Args:
            text: Input text
            chunk_size: Target size in tokens
            overlap: Overlap between chunks in tokens

        Returns:
            List of chunk dicts with text and position
        """
        # Tokenize
        tokens = self.tokenizer.encode(text)

        chunks = []
        start = 0

        while start < len(tokens):
            # Get chunk
            end = start + chunk_size
            chunk_tokens = tokens[start:end]

            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)

            chunks.append({
                "text": chunk_text,
                "start": start,
                "end": min(end, len(tokens)),
                "tokens": len(chunk_tokens)
            })

            # Move to next chunk with overlap
            start = end - overlap

        return chunks

    async def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.embedding_type == "openai":
            import openai
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text
            )
            return response.data[0].embedding
        else:
            # Use local model
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()

    async def _embed_and_store(
        self,
        chunks: List[Dict[str, Any]],
        document_id: str,
        organization_id: str,
        filename: str,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Embed chunks and store in Qdrant"""
        collection_name = f"org_{organization_id}"

        # Ensure collection exists
        await self.create_collection(organization_id)

        chunk_ids = []
        points = []

        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)

            # Generate embedding
            embedding = await self._get_embedding(chunk["text"])

            # Create point
            point = PointStruct(
                id=chunk_id,
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk["text"],
                    "filename": filename,
                    "tokens": chunk["tokens"],
                    "metadata": metadata,
                    "created_at": datetime.utcnow().isoformat()
                }
            )

            points.append(point)

        # Batch upload to Qdrant
        self.qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )

        return chunk_ids

    async def search(
        self,
        query: str,
        organization_id: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks

        Args:
            query: Search query
            organization_id: Organization UUID
            limit: Number of results to return
            filters: Additional filters (e.g., document_id, metadata)

        Returns:
            List of search results with text and metadata
        """
        if not self.initialized:
            await self.initialize()

        collection_name = f"org_{organization_id}"

        # Generate query embedding
        query_embedding = await self._get_embedding(query)

        # Build filters
        qdrant_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                qdrant_filter = Filter(must=conditions)

        # Search
        search_results = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=qdrant_filter,
            limit=limit
        )

        # Format results
        results = []
        for result in search_results:
            results.append({
                "id": result.id,
                "score": result.score,
                "text": result.payload["text"],
                "document_id": result.payload["document_id"],
                "filename": result.payload["filename"],
                "chunk_index": result.payload["chunk_index"],
                "metadata": result.payload.get("metadata", {})
            })

        return results

    async def delete_document(self, document_id: str, organization_id: str):
        """Delete all chunks for a document"""
        if not self.initialized:
            await self.initialize()

        collection_name = f"org_{organization_id}"

        # Delete points with matching document_id
        self.qdrant_client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
