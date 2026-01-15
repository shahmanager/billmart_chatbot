# dynamic_rag_fallback.py
from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests
import chromadb
import time
from typing import List, Dict, Any
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sarvamai import SarvamAI

@dataclass
class DocumentSource:
    content: str
    title: str
    url: str
    doc_type: str  # 'pdf', 'web', 'internal'
    page_number: int = None
    date_accessed: str = None

class DynamicRAGSystem:
    def __init__(self):
        print("🚀 Initializing Dynamic RAG System...")
        
        # Initialize components
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.Client()
        self.sarvam_client = SarvamAI(api_subscription_key=os.getenv('SARVAM_API_KEY'))
        
        # Setup knowledge base
        self.setup_knowledge_base()
        print("✅ Dynamic RAG System initialized!")
        
    def setup_knowledge_base(self):
        """Setup ChromaDB collection with existing knowledge"""
        try:
            self.collection = self.chroma_client.get_collection("dynamic_billmart_kb")
            print("✅ Using existing ChromaDB collection")
        except:
            self.collection = self.chroma_client.create_collection("dynamic_billmart_kb")
            print("✅ Created new ChromaDB collection")
            
        # Load existing knowledge
        self.load_static_documents()
    
    def load_static_documents(self):
        """Load existing BillMart knowledge base"""
        knowledge_files = [
            'data/billmart_complete_knowledge.json', 
            'data/knowledge_base.json'
        ]
        
        total_docs = 0
        for file in knowledge_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                    
                if isinstance(docs, dict):
                    for doc_id, content in docs.items():
                        self.add_document_to_db(
                            content=json.dumps(content, ensure_ascii=False),
                            title=f"BillMart: {doc_id}",
                            url="internal://billmart",
                            doc_type="internal",
                            doc_id=f"internal_{doc_id}"
                        )
                        total_docs += 1
                        
                print(f"✅ Loaded {file}: {total_docs} documents")
                        
            except FileNotFoundError:
                print(f"⚠️ {file} not found, skipping...")
            except Exception as e:
                print(f"❌ Error loading {file}: {e}")
        
        print(f"📚 Total documents in knowledge base: {total_docs}")
    
    def add_document_to_db(self, content: str, title: str, url: str, doc_type: str, doc_id: str):
        """Add a document to ChromaDB with embeddings"""
        try:
            # Generate embedding
            embedding = self.embedder.encode([content])
            
            # Add to collection
            self.collection.add(
                ids=[doc_id],
                documents=[content],
                embeddings=embedding.tolist(),
                metadatas=[{
                    'title': title,
                    'url': url,
                    'doc_type': doc_type,
                    'date_added': time.strftime('%Y-%m-%d')
                }]
            )
        except Exception as e:
            print(f"❌ Error adding document {doc_id}: {e}")
    
    def search_regulatory_updates(self, query: str) -> List[DocumentSource]:
        """Search for recent regulatory updates online"""
        print(f"🔍 Searching for regulatory updates: {query}")
        
        sources = []
        
        # Search RBI website (simulated - you'll need Google Search API)
        rbi_sources = self.search_rbi_updates(query)
        sources.extend(rbi_sources)
        
        return sources[:3]  # Limit to top 3 online sources
    
    def search_rbi_updates(self, query: str) -> List[DocumentSource]:
        """Search RBI website for updates (requires Google Search API)"""
        # For now, return simulated regulatory updates
        # Replace this with actual Google Custom Search API call
        
        simulated_updates = [
            DocumentSource(
                content=f"Recent RBI circular on {query} - Digital lending guidelines updated with enhanced KYC requirements and data localization norms.",
                title=f"RBI Circular - Digital Lending Guidelines 2024",
                url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12345",
                doc_type="web",
                date_accessed=time.strftime('%Y-%m-%d')
            ),
            DocumentSource(
                content=f"Master Direction on {query} - Updated compliance requirements for NBFCs with specific focus on supply chain financing.",
                title=f"RBI Master Direction - NBFC Regulations",
                url="https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12346",
                doc_type="web", 
                date_accessed=time.strftime('%Y-%m-%d')
            )
        ]
        
        print(f"📡 Found {len(simulated_updates)} regulatory updates")
        return simulated_updates
    
    def hybrid_retrieval(self, query: str, k: int = 5) -> List[DocumentSource]:
        """Combine static knowledge with dynamic regulatory updates"""
        print(f"🔄 Performing hybrid retrieval for: {query}")
        
        # Step 1: Search static knowledge base
        static_sources = self.search_static_knowledge(query, k//2)
        
        # Step 2: Get dynamic regulatory updates
        dynamic_sources = self.search_regulatory_updates(query)
        
        # Step 3: Combine and return
        all_sources = static_sources + dynamic_sources
        
        print(f"📋 Retrieved {len(static_sources)} static + {len(dynamic_sources)} dynamic sources")
        return all_sources[:k]
    
    def search_static_knowledge(self, query: str, k: int) -> List[DocumentSource]:
        """Search existing ChromaDB knowledge base"""
        try:
            query_embedding = self.embedder.encode([query])
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=k
            )
            
            sources = []
            if results['documents']:
                for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    source = DocumentSource(
                        content=doc,
                        title=metadata.get('title', f'Internal Doc {i+1}'),
                        url=metadata.get('url', 'internal://billmart'),
                        doc_type=metadata.get('doc_type', 'internal')
                    )
                    sources.append(source)
            
            return sources
            
        except Exception as e:
            print(f"❌ Error searching static knowledge: {e}")
            return []
    
    def generate_response_with_citations(self, query: str) -> Dict[str, Any]:
        """Generate response with properly formatted citations"""
        print(f"\n{'='*80}")
        print(f"🎯 DYNAMIC RAG QUERY: {query}")
        print(f"{'='*80}")
        
        # Step 1: Hybrid retrieval
        sources = self.hybrid_retrieval(query, k=5)
        
        if not sources:
            return {
                'answer': "I couldn't find relevant information for this query. Please contact BillMart support.",
                'sources': [],
                'query': query
            }
        
        # Step 2: Build context with citation markers
        context_parts = []
        citation_list = []
        
        for i, source in enumerate(sources, 1):
            # Truncate content for context
            content_preview = source.content[:300] + "..." if len(source.content) > 300 else source.content
            context_parts.append(f"[Source {i}] {content_preview}")
            
            citation_list.append({
                'id': i,
                'title': source.title,
                'url': source.url,
                'type': source.doc_type,
                'date_accessed': source.date_accessed or 'N/A'
            })
        
        context = "\n\n".join(context_parts)
        
        # Step 3: Generate response with Sarvam AI
        system_prompt = """You are BillMart FinTech's regulatory compliance assistant with access to both internal knowledge and latest regulatory updates.

INSTRUCTIONS:
1. Answer using ONLY the provided sources
2. Include inline citations [Source X] for every factual claim
3. Prioritize recent regulatory updates over older information
4. Structure your response professionally
5. If sources conflict, mention the discrepancy
6. Keep response under 300 words

CONTEXT WITH SOURCES:
{context}

Provide a comprehensive answer with proper citations."""

        try:
            response = self.sarvam_client.chat.completions(
                messages=[
                    {"role": "system", "content": system_prompt.format(context=context)},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                'answer': answer,
                'sources': citation_list,
                'query': query,
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source_types': {
                    'internal': len([s for s in sources if s.doc_type == 'internal']),
                    'web': len([s for s in sources if s.doc_type == 'web']),
                    'pdf': len([s for s in sources if s.doc_type == 'pdf'])
                }
            }
            
        except Exception as e:
            return {
                'answer': f"Error generating response: {e}",
                'sources': citation_list,
                'query': query,
                'error': str(e)
            }

# Test the system
if __name__ == "__main__":
    print("🚀 Starting Dynamic RAG System Test")
    
    # Initialize system
    dynamic_rag = DynamicRAGSystem()
    
    # Test queries
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
        result = dynamic_rag.generate_response_with_citations(query)
        
        print(f"\n📝 RESPONSE:")
        print(result['answer'])
        
        print(f"\n📚 SOURCES ({len(result['sources'])}):")
        for source in result['sources']:
            print(f"  [{source['id']}] {source['title']}")
            print(f"      🔗 {source['url']}")
            print(f"      📅 {source['date_accessed']}")
            print()
        
        if 'source_types' in result:
            types = result['source_types']
            print(f"📊 Source Distribution: Internal({types['internal']}) Web({types['web']}) PDF({types['pdf']})")
        
        print(f"⏰ Generated: {result.get('generated_at', 'N/A')}")
        print("\n" + "="*80)
