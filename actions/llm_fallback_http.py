# actions/llm_fallback_http.py
"""
Simple HTTP client for LLM Service
NO ChromaDB, NO SarvamAI - just HTTP requests!
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class BillMartRAGFallback:
    def __init__(self, llm_service_url="http://localhost:8001"):
        """Initialize with HTTP-based LLM service"""
        self.llm_service_url = llm_service_url
        print(f"🔗 Connecting to LLM Service at {llm_service_url}")
        self._test_llm_service()

    def _test_llm_service(self):
        """Test connection to LLM service"""
        try:
            response = requests.get(f"{self.llm_service_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ LLM Service connected: {data.get('knowledge_base', 'unknown')} KB status")
            else:
                print("⚠️ LLM Service responded but may have issues")
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to LLM Service: {e}")
            print("⚠️ Make sure llm_service.py is running!")

    def generate_fallback_response(self, query: str) -> str:
        """
        Generate response by calling LLM service
        The LLM service handles RAG + SarvamAI internally
        """
        try:
            response = requests.post(
                f"{self.llm_service_url}/generate",
                json={
                    "query": query,
                    "max_tokens": 150,
                    "temperature": 0.3,
                    "use_rag": True  # Let LLM service handle RAG
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    answer = result.get('answer')
                    sources = result.get('sources_used', 0)
                    print(f"✅ Generated response using {sources} sources")
                    return answer
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"❌ LLM Service error: {error}")
                    return self._fallback_message()
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return self._fallback_message()
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return self._fallback_message()

    def _fallback_message(self) -> str:
        """Fallback message when service is unavailable"""
        return """I'm experiencing technical difficulties connecting to our knowledge base. 

Please contact BillMart directly:
📧 care@billmart.com
📞 +91 93269 46663
🌐 www.billmart.com

Our team will be happy to assist you!"""


# Test the system
if __name__ == "__main__":
    print("🚀 Testing HTTP-based LLM Fallback")
    print("=" * 80)
    
    fallback = BillMartRAGFallback()
    
    test_queries = [
        "What are the interest rates for Term Loan?",
        "Tell me about GigCash eligibility",
        "How does RBI regulate supply chain finance?"
    ]
    
    for query in test_queries:
        print(f"\n🎯 Query: {query}")
        print("-" * 40)
        response = fallback.generate_fallback_response(query)
        print(f"📝 Response:\n{response}")
        print("=" * 80)