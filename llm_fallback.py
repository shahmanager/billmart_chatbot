import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
import time
from dotenv import load_dotenv
from sarvamai import SarvamAI
from functools import wraps
# Load API keys
load_dotenv()

def retry_on_rate_limit(max_retries=5, initial_wait=15):
    """Decorator to handle rate limit errors with exponential backoff"""
    def decorator_retry(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            wait_time = initial_wait
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    if 'rate limit' in error_str or '429' in error_str:
                        print(f"⚠️ Rate limit hit! Retrying in {wait_time}s... (attempt {attempt+1}/{max_retries})")
                        time.sleep(wait_time)
                        wait_time *= 4  # Exponential backoff
                    else:
                        raise e
            raise Exception(f"Max retries ({max_retries}) exceeded due to rate limiting")
        return wrapper
    return decorator_retry

class BillMartRAGFallback:
    def __init__(self):
        load_dotenv()
        print(f"🔑 Sarvam Key loaded: {bool(os.getenv('SARVAM_API_KEY'))}")
        
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.Client()
        self.setup_knowledge_base()
        self.setup_apis()

    def setup_knowledge_base(self):
        """Load and index knowledge bases"""
        knowledge_files = ['data/billmart_complete_knowledge.json', 'data/knowledge_base.json']
        self.docs = []
        
        for file in knowledge_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    file_docs = json.load(f)
                
                prefix = file.split('/')[-1].split('.')
                
                if isinstance(file_docs, dict):
                    normalized_docs = []
                    for key, value in file_docs.items():
                        if isinstance(value, list):
                            for idx, item in enumerate(value):
                                doc_id = f"{key}_{idx}"
                                doc_content = json.dumps(item, ensure_ascii=False)
                                normalized_docs.append({"id": doc_id, "content": doc_content})
                        else:
                            doc_content = json.dumps(value, ensure_ascii=False)
                            normalized_docs.append({"id": key, "content": doc_content})
                    file_docs = normalized_docs
                
                for doc in file_docs:
                    doc['id'] = f"{prefix}_{doc['id']}"
                
                self.docs.extend(file_docs)
                print(f"✅ Loaded {file} with {len(file_docs)} docs")
                
            except Exception as e:
                print(f"ERROR loading {file}: {e}")

        try:
            self.collection = self.client.get_collection("billmart_kb")
            print("✅ Using existing ChromaDB collection")
        except:
            self.collection = self.client.create_collection("billmart_kb")
            print("✅ Created new ChromaDB collection")

        if self.docs:
            texts = [doc['content'] for doc in self.docs]
            embeddings = self.embedder.encode(texts)
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=[{"id": doc['id']} for doc in self.docs],
                ids=[doc['id'] for doc in self.docs]
            )
            print("✅ Knowledge base indexed successfully")

    def setup_apis(self):
        """Setup Sarvam AI configuration"""
        # Get your Sarvam AI API subscription key here: https://dashboard.sarvam.ai/admin
        self.api_key = os.getenv('SARVAM_API_KEY')

    def retrieve_context(self, query, n_results=3):
        """✅ FIXED: Retrieve relevant documents using RAG"""
        query_embedding = self.embedder.encode([query])
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        
        # ✅ FIX: Handle nested lists in documents
        flattened_docs = []
        for doc in results['documents']:
            if isinstance(doc, list):
                flattened_docs.extend(doc)
            else:
                flattened_docs.append(doc)
        
        context = "\n\n".join(flattened_docs)
        return context

    @retry_on_rate_limit(max_retries=5, initial_wait=15)
    
    def generate_with_sarvam_chat(self, prompt):
        
        try:
            from sarvamai import SarvamAI
            
            if not self.api_key:
                print("❌ SARVAM_API_KEY not found in environment variables")
                return None
            
            # Initialize client
            client = SarvamAI(api_subscription_key=self.api_key)
            
            # ✅ CORRECT: Using only supported parameters from official docs
            response = client.chat.completions(
                messages=[
                    {"role": "system", "content": "You are BillMart FinTech's expert assistant. Provide helpful responses about financial products and RBI regulations. Keep responses under 150 words unless abosultely required for a more complex query."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,           # ✅ Use max_tokens (not max_completion_tokens)
                temperature=0.3,          # ✅ Supported
                
            )
            
            # Extract response
            if response and hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            
            return None
            
        except ImportError:
            print("❌ Sarvam AI SDK not installed. Install with: pip install sarvamai")
            return None
        except Exception as e:
            print(f"❌ Sarvam AI Error: {e}")
            return None

    
    def generate_enhanced_rag_response(self, query, context):
        """Enhanced RAG response generator - Always works as fallback"""
        query_lower = query.lower()
        
        if 'rbi' in query_lower and 'scf' in query_lower:
            intro = "🏛️ RBI Regulations for Supply Chain Finance:"
        elif 'empcash' in query_lower or 'gigcash' in query_lower:
            intro = "💰 Employee & Gig Worker Financing:"
        elif 'eligibility' in query_lower:
            intro = "✅ Eligibility Requirements:"
        elif 'loan' in query_lower:
            intro = "🏦 Loan Information:"
        else:
            intro = "📋 BillMart Financial Services:"
        
        # Extract key sentences from context
        context_sentences = [s.strip() for s in context.split('.') if s.strip() and len(s.strip()) > 20]
        
        response_parts = [
            intro,
            ""
        ]
        
        # Add top 3 most relevant points
        for i, info in enumerate(context_sentences[:3], 1):
            response_parts.append(f"{i}. {info.strip()}.")
        
        response_parts.extend([
            "",
            "💬 Need personalized assistance?",
            "📧 care@billmart.com",
            "📞 +91 93269 46663",
            "🌐 www.billmart.com"
        ])
        
        return "\n".join(response_parts)

    def create_domain_limited_prompt(self, query, context):
        """Create direct, no-thinking prompt for Sarvam AI"""
        prompt = f"""You are BillMart FinTech's expert assistant.
    Answer directly and concisely using the following context.
    Do NOT include internal thoughts, explanations, or step-by-step reasoning.
    Keep your answer under 150 words as much as possible -and focus on BillMart products and RBI regulations.

    CONTEXT:
    {context[:800]}

    QUERY: {query}
    Provide a helpful, professional response focusing on BillMart products and services and their compliance and regulations"""
        return prompt

    def test_sarvam_chat(self, query):
        """Test Sarvam AI Chat Completion specifically"""
        print(f"🔍 Testing query: {query}")
        print("=" * 60)
        
        context = self.retrieve_context(query)
        prompt = self.create_domain_limited_prompt(query, context)
        
        results = []
        
        # Test Sarvam AI Chat Completion
        print(f"\n🤖 Testing Sarvam AI Chat Completion")
        print(f"📋 Model: sarvam m")
        start_time = time.time()
        sarvam_response = self.generate_with_sarvam_chat(prompt)
        end_time = time.time()
        
        sarvam_result = {
            'model': 'Sarvam AI Chat',
            'type': 'Chat Completion',
            'response': sarvam_response,
            'time': round(end_time - start_time, 2),
            'success': sarvam_response is not None
        }
        results.append(sarvam_result)
        
        print(f"⏱️ Time: {sarvam_result['time']}s")
        print(f"✅ Success: {sarvam_result['success']}")
        if sarvam_response:
            print(f"📝 Response: {sarvam_response}")
        print("-" * 40)
        
        # Enhanced RAG Fallback (Always works)
        print(f"\n🤖 Testing Enhanced RAG Fallback")
        start_time = time.time()
        rag_response = self.generate_enhanced_rag_response(query, context)
        end_time = time.time()
        
        rag_result = {
            'model': 'Enhanced RAG',
            'type': 'Context-based Response',
            'response': rag_response,
            'time': round(end_time - start_time, 2),
            'success': True  # Always works
        }
        results.append(rag_result)
        
        print(f"⏱️ Time: {rag_result['time']}s")
        print(f"✅ Success: {rag_result['success']}")
        print(f"📝 Response: {rag_response[:200]}...")
        print("-" * 40)
        
        return results

    def generate_fallback_response(self, query):
        """Production method - Always returns intelligent response"""
        context = self.retrieve_context(query)
        
        if not context:
            return "I can only provide information about BillMart's financial products. Please ask about our services like SCF, EmpCash, GigCash, ICF, or Term Loans."
        
        # Try Sarvam AI Chat first
        prompt = self.create_domain_limited_prompt(query, context)
        chat_response = self.generate_with_sarvam_chat(prompt)
        
        if chat_response:
            return chat_response
        
        # Fall back to enhanced RAG (always works)
        return self.generate_enhanced_rag_response(query, context)

# Test the system
if __name__ == "__main__":
    print("🚀 BillMart RAG + Sarvam AI Chat System")
    print("Get your Sarvam AI API subscription key here: https://dashboard.sarvam.ai/admin")
    print("=" * 80)
    
    fallback = BillMartRAGFallback()
    
    # Test queries specifically for our domain
    test_queries = [
        "How do RBI rules affect SCF for startups?",
        "What is the difference between EmpCash and GigCash?",
        "What are the eligibility criteria for Term Loan?",
        "Tell me about BillMart's compliance with RBI guidelines",
        "what do you think of crpyto currency?",
        "can you give me investement advice?",
        "explain ICF and SCF",
        "what are the requirements for SCF",
        "how to apply for gigcash",
        "what is the complinace for SCF",
        
        
    ]
    test_queries = [
    "What are the interest rates and eligibility criteria for BillMart's Term Loan product?",
    "How do recent RBI guidelines on digital lending affect small businesses using fintech services?",
    "I'm a freelancer with irregular income. Which BillMart product is best for me - EmpCash or GigCash?",
    "What are the KYC requirements for NBFCs under current RBI regulations?",
    "Can you explain the difference between Invoice Contract Financing and Supply Chain Finance? Which is better for a manufacturing company?",
    "What's the best cryptocurrency to invest in for long-term gains?",
    "My company wants to integrate UPI payments. What are the technical and regulatory requirements?",
    "A startup client has foreign investors. What compliance requirements should they know about when using our SCF product?",
    "What documents are needed to apply for GigCash and how long does approval take?",
    "How does the new RBI evergreening rule impact existing supply chain finance customers?",
    "whats the compliance and KYC required for SCF "
    "is KYC madatory for SCF "
    ]

    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"🎯 TESTING: {query}")
        print(f"{'='*80}")
        
        # Test the specific chat functionality
        results = fallback.test_sarvam_chat(query)
        
        # Show final production response
        print(f"\n🏆 PRODUCTION RESPONSE:")
        print("-" * 40)
        final_response = fallback.generate_fallback_response(query)
        print(final_response)
        print(f"\n{'='*80}")
        
        # Small pause between tests
        time.sleep(1)
