import os
import sqlite3
import faiss
import numpy as np
import torch
from dotenv import load_dotenv
from huggingface_hub import login
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from category_mappings import get_categories_for_query, CATEGORY_GROUPS

# Load .env and login
load_dotenv()
hf_token = os.getenv("HF_Login")
if not hf_token:
    raise ValueError("HF_Login not found in .env file")
login(hf_token)

print("Loading FAISS index and database...")
# Load FAISS index and connect to database
index = faiss.read_index("microsoft_learn_index.faiss")
db_path = "microsoft_docs.db"

# Test database connection
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT COUNT(*) FROM documents")
doc_count = cursor.fetchone()[0]
conn.close()

print(f"Connected to database with {doc_count} documents")

print("Loading embedding model...")
# Load embedding model (same as used for generating embeddings)
embedder = SentenceTransformer("./models/all-MiniLM-L6-v2")

print("Loading tokenizer and model...")
# Configure quantization to improve performance
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

# Load model
model_name = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=hf_token)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map="auto",
    torch_dtype=torch.float16,
    use_auth_token=hf_token
)

print("Model loaded successfully!")


def retrieve_documents(query, top_k=5):
    """Retrieve relevant documents using FAISS similarity search."""

    target_categories = get_categories_for_query(query)

    if target_categories:
        print(f"Targeting categories: {target_categories[:3]}...")
        docs = search_by_category(query, target_categories, top_k)
        
        
        if docs and len(docs) > 0 and docs[0].get('similarity_score', 0) > 0.4:
            return docs
        else:
            print("Category search yielded poor results, falling back...")

    print("Using general search")
    return search_general(query, top_k)

def search_by_category(query, categories, top_k):
    """Search within specific categories."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    if not categories:
        return []

    category_placeholders = ','.join(['?' for _ in categories])
    cursor = conn.execute(f"""
        SELECT rowid-1 as faiss_idx, * FROM documents 
        WHERE category IN ({category_placeholders})
    """, categories)

    category_docs = cursor.fetchall()
    conn.close()

    if not category_docs:
        print(f"No documents found in categories: {categories}")
        return []

    print(f"Found {len(category_docs)} documents in target categories")

    query_embedding = embedder.encode([query])
    query_embedding = query_embedding / np.linalg.norm(query_embedding)

    doc_similarities = []
    for doc in category_docs:
        try:
            faiss_idx = doc['faiss_idx']
            doc_embedding = index.reconstruct(faiss_idx)
            doc_embedding = doc_embedding / np.linalg.norm(doc_embedding)
            
            similarity = float(np.dot(query_embedding[0], doc_embedding))
            
            doc_similarities.append({
                'similarity_score': similarity,
                'title': doc['title'],
                'category': doc['category'],
                'content': doc['content']
            })
        except Exception as e:
            print(f"Error processing document {doc['title']}: {e}")
            continue
    
    # Sort by similarity and return top results
    doc_similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
    return doc_similarities[:top_k]

def search_general(query, top_k):
    """Original general search method."""

    query_embedding = embedder.encode([query])
    query_embedding = query_embedding / np.linalg.norm(query_embedding)
    
    similarities, indices = index.search(query_embedding.astype('float32'), top_k)

    retrieved_docs = []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    for (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
        if idx == -1:
            continue
            
        cursor = conn.execute("SELECT * FROM documents WHERE rowid = ?", (idx + 1,))
        doc = cursor.fetchone()
        
        if doc:
            retrieved_docs.append({
                'similarity_score': float(similarity),
                'title': doc['title'],
                'category': doc['category'], 
                'content': doc['content']
            })
    
    conn.close()
    return retrieved_docs

def generate_answer(query):
    """Generate answer using retrieved documents from database."""
    print(f"Processing query: {query}")
    
    # Retrieve relevant documents
    retrieved_docs = retrieve_documents(query, top_k=5)
    
    if not retrieved_docs:
        return "No relevant documents found in the Microsoft Learn knowledge base."
    
    print(f"Retrieved {len(retrieved_docs)} document chunks")
    
    # Build context from database documents
    context_parts = []
    for doc in retrieved_docs:
        title = doc.get('title', 'Untitled Document')
        content = doc.get('content', '')
        category = doc.get('category', '')
        
        # Show category for better context
        header = f"[{category}] {title}" if category else title
        
        # Limit content length
        if len(content) > 800:
            content = content[:800] + "..."
        
        context_parts.append(f"{header}\n{content}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    prompt = f"""[INST] You are a Microsoft technology expert specializing in Power Platform, Azure, and Microsoft 365.

    INSTRUCTIONS:
    • Use provided Microsoft Learn documentation as primary source
    • Supplement with Microsoft expertise when documentation is limited
    • Provide clear, well-formatted responses with proper spacing
    • Include step-by-step instructions with numbered lists
    • Add code examples and configuration details
    • Mention alternative approaches when relevant

    FORMATTING REQUIREMENTS:
    • Use proper spacing between all words and sentences
    • Separate sections with line breaks
    • Format code blocks with triple backticks
    • Use bullet points (•) or numbered lists (1.)
    • Bold important terms with **text**

    PROVIDED DOCUMENTATION:
    {context}

    USER QUESTION:
    {query}

    Please provide a comprehensive, well-formatted answer with proper spacing and structure: [/INST]"""

    try:
        # Generate response
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=3072)
        input_ids = inputs.input_ids.to(model.device)
        attention_mask = inputs.attention_mask.to(model.device)
        input_length = input_ids.shape[1]
        
        print("Generating response...")
        
        with torch.no_grad():
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=800,
                temperature=0.5,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.15,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                no_repeat_ngram_size=3,
                early_stopping=True
            )
        
        # Extract generated text
        generated_tokens = outputs[0][input_length:]
        answer = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        
        return answer if answer else "I couldn't generate a proper response."
        
    except Exception as e:
        print(f"Error: {e}")
        return f"An error occurred: {str(e)}"


if __name__ == "__main__":
    while True:
        query = input("\nQuestion (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
            
        # Generate answer
        answer = generate_answer(query)
        print(f"\nAnswer: {answer}")
