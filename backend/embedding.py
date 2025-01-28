import os
import google.generativeai as genai
import pinecone
from pinecone import ServerlessSpec
import asyncio
import logging
from collections import deque
import hashlib
from typing import List, Dict
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
BATCH_SIZE = 50
CACHE_SIZE = 1000

class DimensionMismatchError(Exception):
    pass

class EmbeddingManager:
    def __init__(self):
        self.GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        self.PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
        
        if not self.GOOGLE_API_KEY or not self.PINECONE_API_KEY:
            raise ValueError("Missing required API keys in environment variables")
        
        # Initialize models and clients
        genai.configure(api_key=self.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.embedding_model = 'models/text-embedding-004'
        
        self.pc = pinecone.Pinecone(api_key=self.PINECONE_API_KEY)
        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'file-embeddings')
        self.index = None
        
        # Initialize cache
        self.embedding_cache = {}
        self.cache_queue = deque(maxlen=CACHE_SIZE)

    def get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def cache_embedding(self, text: str, embedding: List[float]):
        key = self.get_cache_key(text)
        if key not in self.embedding_cache:
            if len(self.cache_queue) >= CACHE_SIZE:
                old_key = self.cache_queue.popleft()
                self.embedding_cache.pop(old_key, None)
            self.cache_queue.append(key)
        self.embedding_cache[key] = embedding

    def get_cached_embedding(self, text: str) -> List[float]:
        return self.embedding_cache.get(self.get_cache_key(text))

    async def initialize_index(self, dimension: int):
        try:
            if self.index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
            else:
                index_info = self.pc.describe_index(self.index_name)
                existing_dimension = index_info.dimension
                
                if existing_dimension != dimension:
                    logger.info(f"Recreating index with new dimension: {dimension}")
                    self.pc.delete_index(self.index_name)
                    while self.index_name in self.pc.list_indexes().names():
                        await asyncio.sleep(1)
                    
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=dimension,
                        metric='cosine',
                        spec=ServerlessSpec(
                            cloud='aws',
                            region='us-east-1'
                        )
                    )
            
            while True:
                info = self.pc.describe_index(self.index_name)
                if hasattr(info, 'status') and info.status.get('ready'):
                    break
                await asyncio.sleep(1)
                
            self.index = self.pc.Index(self.index_name)
            return dimension
            
        except Exception as e:
            logger.error(f"Error initializing index: {str(e)}")
            raise

    async def get_embedding_dimension(self, text: str) -> int:
        try:
            embedding = await asyncio.to_thread(
                lambda: genai.embed_content(
                    model=self.embedding_model,
                    content=text,
                    task_type="retrieval_document"
                )['embedding']
            )
            return len(embedding)
        except Exception as e:
            logger.error(f"Error getting embedding dimension: {str(e)}")
            raise

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        results = []
        texts_to_process = []
        indices_to_process = []

        for i, text in enumerate(texts):
            cached_embedding = self.get_cached_embedding(text)
            if cached_embedding is not None:
                results.append((i, cached_embedding))
            else:
                texts_to_process.append(text)
                indices_to_process.append(i)

        if texts_to_process:
            embeddings = await asyncio.gather(
                *[asyncio.to_thread(
                    lambda t: genai.embed_content(
                        model=self.embedding_model,
                        content=t,
                        task_type="retrieval_document"
                    )['embedding'],
                    text
                ) for text in texts_to_process]
            )

            for text, embedding in zip(texts_to_process, embeddings):
                self.cache_embedding(text, embedding)

            results.extend(zip(indices_to_process, embeddings))

        results.sort(key=lambda x: x[0])
        return [emb for _, emb in results]

    def rerank_results(self, search_results: dict, question: str) -> List[dict]:
        matches = search_results['matches']
        
        for match in matches:
            text = match['metadata']['text']
            question_words = set(question.lower().split())
            text_words = set(text.lower().split())
            word_overlap = len(question_words.intersection(text_words))
            
            match['combined_score'] = (
                match['score'] * 0.6 +
                word_overlap * 0.4
            )
        
        matches.sort(key=lambda x: x['combined_score'], reverse=True)
        return matches[:3]

