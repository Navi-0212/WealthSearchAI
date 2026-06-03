import os
import sys
import pickle
import logging
import chromadb

# Add parent path to import sibling files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.indexer import EmbeddingGenerator

logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self):
        self.chroma_path = "./db/chroma_store"
        self.bm25_path = "data/bm25_store.pkl"
        self.embedding_generator = EmbeddingGenerator()
        self.reranker_model = None
        
        # Try to initialize local sentence-transformers CrossEncoder
        try:
            from sentence_transformers import CrossEncoder
            logger.info("Initializing CrossEncoder 'cross-encoder/ms-marco-MiniLM-L-6-v2' for re-ranking...")
            self.reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("CrossEncoder re-ranker successfully loaded.")
        except Exception as e:
            logger.warning(f"Could not load CrossEncoder: {e}. Fallback to standard tf-idf matching for secondary scoring.")

    def get_metadata_funds(self, query: str) -> list[str]:
        """
        Analyzes the user query to detect all explicit and implicit references to mutual funds
        and returns a list of matching standardized fund names.
        """
        q = query.lower()
        matched = set()
        
        # Mapping key identifiers to standardized fund names
        mapping = {
            "bandhan small cap": "Bandhan Small Cap Fund Direct Growth",
            "bandhan midcap": "Bandhan Midcap Fund Direct Growth",
            "bandhan multi cap": "Bandhan Multi Cap Fund Direct Growth",
            "edelweiss": "Edelweiss Mid Cap Direct Plan Growth",
            "zerodha": "Zerodha Multi Asset Passive FoF Direct Growth",
            "parag parikh": "Parag Parikh Flexi Cap Fund Direct Growth",
            "ppfas": "Parag Parikh Flexi Cap Fund Direct Growth",
            "nippon small cap": "Nippon India Small Cap Fund Direct Growth",
            "nippon multi asset": "Nippon India Multi Asset Allocation Fund Direct Growth"
        }
        
        for keyword, standardized_name in mapping.items():
            if keyword in q:
                matched.add(standardized_name)
                
        # Structural fallback checks
        if "bandhan" in q:
            if "small" in q:
                matched.add("Bandhan Small Cap Fund Direct Growth")
            if "mid" in q:
                matched.add("Bandhan Midcap Fund Direct Growth")
            if "multi" in q:
                matched.add("Bandhan Multi Cap Fund Direct Growth")
        if "nippon" in q:
            if "small" in q:
                matched.add("Nippon India Small Cap Fund Direct Growth")
            if "multi" in q or "asset" in q:
                matched.add("Nippon India Multi Asset Allocation Fund Direct Growth")
        if "zerodha" in q:
            matched.add("Zerodha Multi Asset Passive FoF Direct Growth")
        if "edelweiss" in q:
            matched.add("Edelweiss Mid Cap Direct Plan Growth")
        if "parikh" in q or "ppfas" in q:
            matched.add("Parag Parikh Flexi Cap Fund Direct Growth")
            
        return list(matched)

    def get_metadata_filter(self, query: str) -> dict:
        """
        Generates a ChromaDB compatible query filter. Supports single matches and multi-fund comparison matches.
        """
        funds = self.get_metadata_funds(query)
        if not funds:
            return {}
        if len(funds) == 1:
            return {"fund_name": funds[0]}
        else:
            return {"fund_name": {"$in": funds}}

    def dense_search(self, query: str, top_n=15) -> list:
        """
        Executes dense semantic search query using ChromaDB vectors with metadata filtering.
        """
        try:
            chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            
            # Embed the user query
            query_embedding = self.embedding_generator.get_embeddings([query])[0]
            
            # Select correct collection matching query embedding dimensionality
            dimension = len(query_embedding)
            collection_name = f"mutual_fund_rag_collection_{dimension}"
            collection = chroma_client.get_collection(collection_name)
            
            # Retrieve metadata filter helper clause if any
            where_clause = self.get_metadata_filter(query)
            logger.info(f"Dense search applying metadata filter scoping: {where_clause}")
            
            # Query collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_n,
                where=where_clause if where_clause else None
            )
            
            hits = []
            if results and results["documents"] and len(results["documents"][0]) > 0:
                for idx in range(len(results["documents"][0])):
                    hits.append({
                        "id": results["ids"][0][idx],
                        "text": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "distance": results["distances"][0][idx]
                    })
            return hits
        except Exception as e:
            logger.error(f"Dense vector database query failed: {e}")
            return []

    def sparse_search(self, query: str, top_n=15) -> list:
        """
        Executes sparse keyword search query using localized BM25 indices with metadata filtering.
        """
        if not os.path.exists(self.bm25_path):
            logger.warning(f"BM25 storage store not found at {self.bm25_path}. Skipping sparse keyword run.")
            return []
            
        try:
            with open(self.bm25_path, 'rb') as f:
                bm25_data = pickle.load(f)
                
            bm25 = bm25_data["bm25_instance"]
            texts = bm25_data["texts"]
            metadatas = bm25_data["metadatas"]
            ids = bm25_data["ids"]
            
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Retrieve metadata filter helper target funds list if any
            matched_funds = self.get_metadata_funds(query)
            logger.info(f"Sparse search applying metadata filter scoping: {matched_funds}")
            
            # Compute BM25 scores
            scores = bm25.get_scores(tokenized_query)
            
            # Pair scores with original indices
            scored_docs = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
            
            hits = []
            for rank, (idx, score) in enumerate(scored_docs):
                # Filter by scoped fund names if specified
                if matched_funds and metadatas[idx].get("fund_name") not in matched_funds:
                    continue
                    
                if score > 0: # Only return actual keyword hits
                    hits.append({
                        "id": ids[idx],
                        "text": texts[idx],
                        "metadata": metadatas[idx],
                        "score": score
                    })
                    if len(hits) >= top_n:
                        break
            return hits
        except Exception as e:
            logger.error(f"Sparse BM25 index query failed: {e}")
            return []

    def reciprocal_rank_fusion(self, dense_hits: list, sparse_hits: list, k=60) -> list:
        """
        Calculates Reciprocal Rank Fusion (RRF) scores to merge and fuse dense and sparse ranks.
        """
        fused_scores = {}
        lookup_table = {}
        
        # Process Dense hits
        for rank, hit in enumerate(dense_hits):
            doc_id = hit["id"]
            lookup_table[doc_id] = hit
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
            
        # Process Sparse hits
        for rank, hit in enumerate(sparse_hits):
            doc_id = hit["id"]
            lookup_table[doc_id] = hit
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
            
        # Sort documents by fused RRF score descending
        sorted_fused = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        
        fused_hits = []
        for doc_id, score in sorted_fused:
            fused_hits.append({
                "doc": lookup_table[doc_id],
                "rrf_score": score
            })
            
        return fused_hits

    def rerank_candidates(self, query: str, fused_candidates: list, top_k=5) -> list:
        """
        Cross-Encoder re-ranking step to discard noise and order chunks by absolute relevance.
        """
        if not fused_candidates:
            return []
            
        chunks = [c["doc"] for c in fused_candidates]
        texts = [chunk["text"] for chunk in chunks]
        
        if self.reranker_model:
            try:
                logger.info(f"Re-ranking {len(texts)} candidate chunks using CrossEncoder model...")
                # Format pairs of (Query, Text)
                pairs = [[query, text] for text in texts]
                scores = self.reranker_model.predict(pairs)
                
                # Pair scores and sort
                scored_chunks = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
                return [chunk for chunk, score in scored_chunks[:top_k]]
            except Exception as e:
                logger.error(f"CrossEncoder prediction failed: {e}. Falling back to RRF rankings.")
                
        # Statistical secondary fallback if CrossEncoder is missing or fails: TF-IDF vector cosine matching
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            vectorizer = TfidfVectorizer().fit_transform([query] + texts)
            vectors = vectorizer.toarray()
            query_vector = vectors[0].reshape(1, -1)
            doc_vectors = vectors[1:]
            
            similarities = cosine_similarity(query_vector, doc_vectors)[0]
            scored_chunks = sorted(zip(chunks, similarities), key=lambda x: x[1], reverse=True)
            return [chunk for chunk, score in scored_chunks[:top_k]]
        except Exception:
            # Fallback to simple first top_k candidates directly if sklearn not loaded
            return chunks[:top_k]

    def retrieve_context(self, query: str, top_k=5) -> list:
        """
        Complete retrieval pipeline combining dense semantic search, BM25, RRF, and Re-ranking.
        """
        logger.info(f"Executing retrieval pipeline for query: '{query}'")
        
        # 1. Perform dual searches
        dense_hits = self.dense_search(query, top_n=15)
        sparse_hits = self.sparse_search(query, top_n=15)
        
        # 2. Fuse ranks
        fused_candidates = self.reciprocal_rank_fusion(dense_hits, sparse_hits)
        logger.info(f"Hybrid search yielded {len(fused_candidates)} unique fused candidate chunks.")
        
        # 3. Apply Re-ranking and return Top-K compliance context
        final_context = self.rerank_candidates(query, fused_candidates, top_k=top_k)
        logger.info(f"Retrieval loop successfully selected Top-{len(final_context)} grounded chunks.")
        return final_context

if __name__ == "__main__":
    # Test runner for verification
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    retriever = HybridRetriever()
    results = retriever.retrieve_context("Saurabh Sharma exit load Bandhan Small Cap")
    for idx, r in enumerate(results):
        print(f"\n--- Chunk {idx} (Section: {r['metadata']['section_header']}) ---")
        print(r['text'])
