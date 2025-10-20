import sqlite3
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

db_path = "microsoft_docs.db"
index_path = "microsoft_learn_index.faiss"

print("Loading embedding model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def rebuild_index():
    print("Rebuilding FAISS index...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT content FROM documents")
    
    all_docs = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"Encoding {len(all_docs)} documents...")
    
    # Re-encode all documents
    embeddings = []
    batch_size = 1000
    
    for i in range(0, len(all_docs), batch_size):
        batch = all_docs[i:i+batch_size]
        batch_embeddings = embedder.encode(batch)
        
        # Normalize each embedding
        for embedding in batch_embeddings:
            normalized = embedding / np.linalg.norm(embedding)
            embeddings.append(normalized)
        
        print(f"Processed {min(i+batch_size, len(all_docs))}/{len(all_docs)}")
    
    embeddings_array = np.array(embeddings).astype('float32')
    
    new_index = faiss.IndexFlatIP(embeddings_array.shape[1])
    new_index.add(embeddings_array)
    
    faiss.write_index(new_index, index_path)
    print("Index rebuilt and saved!")

if __name__ == "__main__":
    rebuild_index()
