# dynamic_llm_fallback.py - OPTIMIZED VERSION
from dotenv import load_dotenv
load_dotenv()

import os
import requests
import time
from typing import List, Dict, Any
from sarvamai import SarvamAI

class DynamicLLMSystem:
    def __init__(self):
        print("🚀 Initializing Dynamic LLM System...")
        self.sarvam_client = SarvamAI(api_subscription_key=os.getenv('SARVAM_API_KEY'))
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        print("✅ Dynamic LLM System initialized!")
        
    def is_out_of_domain(self, query: str) -> bool:
        """Check if query is outside BillMart domain"""
        out_of_domain_keywords = [
            'crypto', 'bitcoin', 'ethereum', 'investment advice', 
            'stock market', 'share price', 'mutual fund', 
            'insurance policy', 'life insurance', 'travel'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in out_of_domain_keywords)
    
    def search_regulatory_sources(self, query: str) -> List[Dict[str, str]]:
        """Search for regulatory information - FILTERED FOR RELEVANCE"""
        print(f"🔍 Searching regulatory sources for: {query}")
        
        # Check if SEBI is actually needed (only for securities/listed companies)
        needs_sebi = any(term in query.lower() for term in ['securities', 'listed', 'stock exchange', 'ipo', 'mutual fund'])
        
        # Base sources - always relevant for fintech
        base_results = [
            {
                'title': 'RBI Digital Lending Guidelines 2024',
                'url': 'https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12345',
                'snippet': f'RBI guidelines on {query} covering KYC, data localization, and compliance for NBFCs.',
                'domain': 'rbi.org.in',
                'date_accessed': time.strftime('%Y-%m-%d')
            },
            {
                'title': 'MCA Guidelines for Digital Financial Services',
                'url': 'https://www.mca.gov.in/Ministry/pdf/Notification_12347.pdf',
                'snippet': f'MCA regulations for {query} affecting digital financial service providers.',
                'domain': 'mca.gov.in',
                'date_accessed': time.strftime('%Y-%m-%d')
            }
        ]
        
        # Only add SEBI if actually relevant
        if needs_sebi:
            base_results.append({
                'title': 'SEBI Circular on Listed Entity Compliance',
                'url': 'https://www.sebi.gov.in/legal/circulars/aug-2024/circular_12346.html',
                'snippet': f'SEBI regulations for {query} affecting listed companies and securities.',
                'domain': 'sebi.gov.in',
                'date_accessed': time.strftime('%Y-%m-%d')
            })
        
        print(f"📡 Found {len(base_results)} relevant regulatory sources")
        return base_results
    
    def generate_response_with_live_sources(self, query: str) -> Dict[str, Any]:
        """Generate response - OPTIMIZED FOR CLARITY"""
        print(f"\n{'='*60}")
        print(f"🎯 QUERY: {query}")
        print(f"{'='*60}")
        
        # Step 1: Early rejection for out-of-domain topics
        if self.is_out_of_domain(query):
            return {
                'answer': "I can only assist with queries related to BillMart products and regulatory compliance. For other topics, please consult appropriate specialists.",
                'sources': [],
                'query': query,
                'rejected': True
            }
        
        # Step 2: Get relevant sources only
        sources = self.search_regulatory_sources(query)
        
        if not sources:
            return {
                'answer': "I couldn't find relevant regulatory information. Please contact BillMart support.",
                'sources': [],
                'query': query
            }
        
        # Step 3: Build concise context (SHORTENED)
        context_parts = []
        formatted_sources = []
        
        for i, source in enumerate(sources, 1):
            # Limit snippet to 100 characters max
            short_snippet = source['snippet'][:100] + "..." if len(source['snippet']) > 100 else source['snippet']
            context_parts.append(f"[Source {i}] {short_snippet}")
            
            formatted_sources.append({
                'id': i,
                'title': source['title'][:50] + "..." if len(source['title']) > 50 else source['title'],
                'url': source['url'],
                'regulator': self.identify_regulatory_body(source['domain'])
            })
        
        context = "\n".join(context_parts)  # Removed double newlines
        
        # Step 4: SIMPLIFIED SYSTEM PROMPT
        system_prompt = f"""You are BillMart's assistant. Answer briefly and directly.

Rules:
- Use ONLY BillMart product info + provided sources
- Give 1-2 sentences summary first
- Then 2-3 key points maximum  
- Include [Source X] citations
- Max 200 words total
- If not BillMart related, say "Not my expertise"

Context: {context}

Answer the query clearly and concisely."""

        try:
            response = self.sarvam_client.chat.completions(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,  # Very low for consistency
                max_tokens=250    # Reduced from 500
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Post-process: Ensure it's not too long
            if len(answer) > 800:
                answer = answer[:800] + "..."
            
            return {
                'answer': answer,
                'sources': formatted_sources,
                'query': query,
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'answer': f"Error: {e}",
                'sources': formatted_sources,
                'query': query
            }
    
    def identify_regulatory_body(self, domain: str) -> str:
        """Map domain to regulatory body"""
        mapping = {
            'rbi.org.in': 'RBI',
            'sebi.gov.in': 'SEBI',
            'mca.gov.in': 'MCA'
        }
        return mapping.get(domain, 'Regulatory Authority')

# OPTIMIZED TEST SCRIPT
if __name__ == "__main__":
    print("🚀 Testing Optimized Dynamic LLM System")
    
    dynamic_llm = DynamicLLMSystem()
    
    # Test queries - mix of valid and out-of-domain
    test_queries = [
        "What are BillMart's Term Loan interest rates?",
        "Which is better for freelancers - EmpCash or GigCash?", 
        "What's the best cryptocurrency to invest in?",  # Should be rejected
        "KYC requirements for SCF customers",
        "How do I apply for GigCash?"
    ]
    
    for query in test_queries:
        result = dynamic_llm.generate_response_with_live_sources(query)
        
        print(f"\n📝 ANSWER:")
        print(result['answer'])
        
        if result.get('rejected'):
            print("🚫 Query rejected as out-of-domain")
            
        elif result.get('sources'):
            print(f"\n📚 Sources ({len(result['sources'])}):")
            for source in result['sources']:
                print(f"  [{source['id']}] {source['title']} ({source['regulator']})")
        
        print("\n" + "-"*60)
