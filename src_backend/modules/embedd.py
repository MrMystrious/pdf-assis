import chromadb,json,time
from src.modules.knowedge_graph import KG
from src.modules.extractor import getPage
from langchain_ollama import OllamaEmbeddings
import requests
from chromadb.api.types import EmbeddingFunction, Embeddings 

class LangChainChromaWrapper(EmbeddingFunction):
   
    def __init__(self, lc_embedding_model):
        self.lc_embedding_model = lc_embedding_model

    def __call__(self, texts: list[str]) -> Embeddings:
        return self.lc_embedding_model.embed_documents(texts)

class VecDB:
    def __init__(self, db_name='myChromaDB', model_name='nomic-embed-text', max_retries=5, retry_delay=5):
        self.client = chromadb.PersistentClient(path=f"./{db_name}")
        self.model_name = model_name

        OLLAMA_URL = "http://127.0.0.1:11434"

        for attempt in range(max_retries):
            try:
                lc_ollama_embd = OllamaEmbeddings(
                    model=self.model_name,
                    base_url=OLLAMA_URL 
                )

                self.embd = LangChainChromaWrapper(lc_ollama_embd)
                
                _ = lc_ollama_embd.embed_query("test") 
                
                print("Connected to Ollama server using custom LangChain wrapper!")
                break
            except Exception as e:
                if "ConnectionError" in str(e) or "Max retries exceeded" in str(e):
                    error_message = f"Failed to establish connection to Ollama at {OLLAMA_URL}."
                else:
                    error_message = str(e)
                    
                print(f"Ollama connection/initialization failed (attempt {attempt+1}/{max_retries}): {error_message}")
                    
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise ConnectionError("Failed to connect to Ollama after multiple attempts.") from e

        self.collection = self.client.get_or_create_collection(
            name="pdf_chunks",
            embedding_function=self.embd
        )
    
    def save_to_chroma(self,data):
        if not data:
            return
        
        txts = [txt.get('text','') for txt in data]
        metadata = []
        for txt in data:
            meta = {}
            for i, e in enumerate(txt.get('entity', [])):
                meta[f"entity_{i}"] = e
            for i, r in enumerate(txt.get('relation', [])):
                meta[f"relation_{i}"] = "|".join(r) 
            if not meta:
                meta['source'] = 'pdf_chunk' 
            metadata.append(meta)

        ids = [f"chunk_{i}" for i in range(len(txts))]
       # print(len(txts),len(metadata))
        self.collection.add(
            ids = ids,
            documents = txts,
            metadatas = metadata
        )
        print(f"Saved {len(txts)} chunks to ChromaDB.")
    
    def query_with_kg_filter(self, query_text, query_entities=None, query_relation=None, k=10):
        if query_entities is None:
            query_entities = []
        if query_relation is None:
            query_relation = []

        filters = []
        if query_entities:
            entity_or = [{"entity_{}".format(i): {"$eq": e}} for i, e in enumerate(query_entities)]
            filters.append(entity_or[0] if len(entity_or) == 1 else {"$or": entity_or})

        if query_relation:
            relation_or = [{"relation_{}".format(i): {"$eq": "|".join(r)}} for i, r in enumerate(query_relation)]
            filters.append(relation_or[0] if len(relation_or) == 1 else {"$or": relation_or})

        where_filter = None if not filters else (filters[0] if len(filters) == 1 else {"$and": filters})

        # --- Run query safely ---
        try:
            start = time.time()
            query_result = self.collection.query(
                query_texts=[query_text],
                n_results=k,
                where=where_filter
            )
            print(f"[QUERY SUCCESS] {len(query_result['documents'][0]) if 'documents' in query_result else 0} results in {time.time() - start:.2f}s")
            return query_result

        except chromadb.errors.InternalError as e:
            print(f"[ChromaDB InternalError] → {e}")
            print("[DEBUG] Possible causes: missing IDs, corrupted collection, or metadata mismatch.")
            print("[ACTION] Retrying query without filters...")

            # Try a fallback query without filters
            try:
                query_result = self.collection.query(
                    query_texts=[query_text],
                    n_results=k
                )
                print("[RECOVERY] Fallback query succeeded.")
                return query_result
            except Exception as e2:
                print(f"[FATAL] Fallback query also failed: {e2}")
                return {"error": str(e2)}

        except Exception as e:
            print(f"[Unexpected Error in query_with_kg_filter] {e}")
            return {"error": str(e)}
