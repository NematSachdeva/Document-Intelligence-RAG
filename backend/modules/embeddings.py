"""
Embeddings Module
Generates embeddings and manages Chroma Cloud vector storage.
"""

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import os


class EmbeddingManager:
    """Manages embeddings generation and Chroma Cloud operations."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding manager with Chroma Cloud.
        
        Args:
            model_name: Sentence transformer model to use
        """
        # Get Chroma Cloud credentials from environment
        self.host = os.getenv("CHROMA_HOST", "api.trychroma.com")
        self.api_key = os.getenv("CHROMA_API_KEY")
        self.tenant = os.getenv("CHROMA_TENANT")
        self.database = os.getenv("CHROMA_DATABASE", "DocumentIntelligence")
        
        # Initialize sentence transformer model
        self.model = SentenceTransformer(model_name)
        
        # Collection name
        self.collection_name = "DocumentIntelligence"
        
        # Client will be initialized lazily
        self.client = None
    
    def _get_client(self):
        """Lazily initialize Chroma Cloud client."""
        if self.client is None:
            if not self.api_key or not self.tenant:
                raise ValueError("CHROMA_API_KEY or CHROMA_TENANT not set in environment")
            
            try:
                # Connect to Chroma Cloud using CloudClient
                self.client = chromadb.CloudClient(
                    api_key=self.api_key,
                    tenant=self.tenant,
                    database=self.database
                )
                print(f"✓ Connected to Chroma Cloud (database: {self.database})")
            except Exception as e:
                print(f"⚠️  Chroma Cloud connection failed: {e}")
                print(f"   Falling back to local ChromaDB...")
                # Fallback to local ChromaDB
                try:
                    self.client = chromadb.PersistentClient(path="./chroma_db")
                    print(f"✓ Using local ChromaDB at ./chroma_db")
                except Exception as e2:
                    print(f"✗ Local ChromaDB also failed: {e2}")
                    raise
        
        return self.client
    
    def get_or_create_collection(self, collection_name: str):
        """Get or create a Chroma Cloud collection."""
        client = self._get_client()
        try:
            return client.get_collection(name=collection_name)
        except Exception:
            return client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
        
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
    
    def store_embeddings(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> None:
        """
        Generate and store embeddings in Chroma Cloud.
        
        Args:
            collection_name: Name of the collection
            texts: List of text chunks
            metadatas: List of metadata dicts
            ids: List of unique IDs for chunks
        """
        collection = self.get_or_create_collection(collection_name)
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Store in Chroma Cloud
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        print(f"✓ Stored {len(ids)} embeddings in Chroma Cloud collection: {collection_name}")
    
    def retrieve_similar_chunks(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5
    ) -> Tuple[List[str], List[Dict], List[float]]:
        """
        Retrieve top-k similar chunks for a query from Chroma Cloud.
        
        Args:
            collection_name: Name of the collection
            query: Query text
            top_k: Number of results to retrieve
        
        Returns:
            Tuple of (texts, metadatas, distances)
        """
        collection = self.get_or_create_collection(collection_name)
        
        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]
        
        # Query Chroma Cloud
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Extract results
        texts = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []
        
        return texts, metadatas, distances
    
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection from Chroma Cloud."""
        try:
            self.client.delete_collection(name=collection_name)
            print(f"✓ Deleted collection from Chroma Cloud: {collection_name}")
        except Exception as e:
            print(f"Error deleting collection: {e}")
