from dotenv import load_dotenv
load_dotenv()
import os
from sarvamai import SarvamAI

def llm_only_fallback(user_query, system_message=None, temperature=0.3, max_tokens=300):
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise EnvironmentError("SARVAM_API_KEY not set in your environment.")
    client = SarvamAI(api_subscription_key=api_key)
    if system_message is None:
        system_message = (
            "You are BillMart FinTech's expert assistant. You will provide clear and facutally correct answers to user querries"
            "Be concise, factual, and comply with RBI guidelines.Give reply as per billmart's polices and guidlines as per their website and other banking or nbfc related RBI rules and regulations "
            "If you don't know, say so—do not guess.Do not provide any investment advice.Do not provide vague or generic responses"
            "If the question is not related to BillMart's products or services, politely inform the user that you can only assist with queries related to BillMart."
            "do not show you internal thinking steps"
        )
    response = client.chat.completions(
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_query}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
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
    for question in test_queries:
        print(f"\nQ: {question}")
        print("A:", llm_only_fallback(question))
        print("-----")
