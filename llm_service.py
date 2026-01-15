# llm_service.py
"""
Standalone FastAPI service for SarvamAI + ChromaDB RAG
Completely isolated from Rasa environment

Usage:
    python llm_service.py
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import chromadb
from sarvamai import SarvamAI
from sentence_transformers import SentenceTransformer
import uvicorn

load_dotenv()

app = FastAPI(title="BillMart LLM Service with RAG")

# Initialize clients
sarvam_client = SarvamAI(api_subscription_key=os.getenv('SARVAM_API_KEY'))
embedder = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.Client()

# Global knowledge base
knowledge_base = None


def setup_knowledge_base():
    """Load and index knowledge base with ChromaDB"""
    global knowledge_base
    
    print("📚 Setting up knowledge base...")
    
    try:
        collection = chroma_client.get_collection("billmart_kb")
        print("✅ Using existing ChromaDB collection")
    except:
        collection = chroma_client.create_collection("billmart_kb")
        print("✅ Created new ChromaDB collection")
        
        # Load knowledge files
        knowledge_files = [
            'data/billmart_complete_knowledge.json',
            'data/knowledge_base.json'
        ]
        
        all_docs = []
        doc_ids = []
        
        for file in knowledge_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    file_docs = json.load(f)
                
                file_prefix = file.split('/')[-1].split('.')[0]
                
                if isinstance(file_docs, dict):
                    for key, value in file_docs.items():
                        if isinstance(value, list):
                            for idx, item in enumerate(value):
                                doc_id = f"{file_prefix}_{key}_{idx}"
                                doc_content = json.dumps(item, ensure_ascii=False)
                                all_docs.append(doc_content)
                                doc_ids.append(doc_id)
                        else:
                            doc_id = f"{file_prefix}_{key}"
                            doc_content = json.dumps(value, ensure_ascii=False)
                            all_docs.append(doc_content)
                            doc_ids.append(doc_id)
                elif isinstance(file_docs, list):
                    for idx, doc in enumerate(file_docs):
                        doc_id = f"{file_prefix}_{idx}"
                        doc_content = json.dumps(doc, ensure_ascii=False)
                        all_docs.append(doc_content)
                        doc_ids.append(doc_id)
                
                print(f"✅ Loaded {file}")
                
            except FileNotFoundError:
                print(f"⚠️ {file} not found, skipping...")
            except Exception as e:
                print(f"❌ Error loading {file}: {e}")
        
        # Index documents
        if all_docs:
            print(f"🔄 Indexing {len(all_docs)} documents...")
            embeddings = embedder.encode(all_docs, show_progress_bar=True)
            
            collection.add(
                ids=doc_ids,
                documents=all_docs,
                embeddings=embeddings.tolist()
            )
            print(f"✅ Indexed {len(all_docs)} documents")
    
    knowledge_base = collection
    print("✅ Knowledge base ready!")


def retrieve_context(query: str, n_results: int = 3) -> str:
    """Retrieve relevant context using ChromaDB"""
    if knowledge_base is None:
        return ""
    
    try:
        query_embedding = embedder.encode([query])
        results = knowledge_base.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        
        # Extract documents
        if results['documents']:
            docs = []
            for doc in results['documents'][0]:
                docs.append(doc)
            return "\n\n".join(docs)
        
        return ""
        
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return ""


class QueryRequest(BaseModel):
    query: str
    context: str = ""
    max_tokens: int = 150
    temperature: float = 0.3
    use_rag: bool = True  # New parameter


class QueryResponse(BaseModel):
    answer: str
    success: bool
    error: str = None
    sources_used: int = 0


@app.post("/generate", response_model=QueryResponse)
async def generate_response(request: QueryRequest):
    """Generate LLM response with optional RAG"""
    try:
        # Get context from RAG if requested
        context = request.context
        sources_used = 0
        
        if request.use_rag and not context:
            print(f"🔍 Retrieving context for: {request.query}")
            context = retrieve_context(request.query, n_results=3)
            if context:
                sources_used = 3
                print(f"✅ Retrieved {sources_used} relevant documents")
        
        # Build prompt
        if context:
            prompt = f"""You are BillMart FinTech's expert assistant.
Answer directly and concisely using the following context.
Keep your answer under 150 words and focus on BillMart products and RBI regulations.

CONTEXT:
{context[:800]}

QUERY: {request.query}

Provide a helpful, professional response:"""
        else:
            prompt = request.query
        
        # Call SarvamAI
        response = sarvam_client.chat.completions(
            messages=[
                {"role": "system", "content": "You are BillMart FinTech's expert assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        answer = response.choices[0].message.content.strip()
        
        return QueryResponse(
            answer=answer,
            success=True,
            sources_used=sources_used
        )
        
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return QueryResponse(
            answer="",
            success=False,
            error=str(e)
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    kb_status = "ready" if knowledge_base is not None else "not initialized"
    return {
        "status": "healthy",
        "service": "BillMart LLM Service with RAG",
        "knowledge_base": kb_status
    }


@app.on_event("startup")
async def startup_event():
    """Initialize knowledge base on startup"""
    setup_knowledge_base()


if __name__ == "__main__":
    print("🚀 Starting BillMart LLM Service with RAG")
    print("📚 Service includes ChromaDB + SarvamAI")
    print("🌐 Running on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)