# actions/enhanced_actions.py
from typing import Dict, Text, Any, List, Optional
import logging
import time
import os
import sys

# Add parent directory to path for imports (Windows compatibility)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction

from .minimal_state import ConversationStateManager, MinimalConversationState

# Initialize logger
logger = logging.getLogger(__name__)

class ActionProcessWithMinimalState(Action):
    """Production-ready action with context awareness and error handling."""
    
    def name(self) -> Text:
        return "action_process_with_minimal_state"
    
    def __init__(self):
        self.state_manager = ConversationStateManager()
    
    # actions/enhanced_actions.py
    def run(self, dispatcher: CollectingDispatcher, 
       tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Nuclear option: Force fresh state for problematic intents."""
        
        try:
            # Extract conversation data
            latest_message = tracker.latest_message
            intent_name = latest_message.get("intent", {}).get("name", "")
            entities = latest_message.get("entities", [])
            user_message = latest_message.get("text", "")
            
            print(f"🔥 NUCLEAR DEBUG: Intent={intent_name}, Message='{user_message}'")
            
            # NUCLEAR OPTION: Reset state for loan requests (ignore old state completely)
            if intent_name == "ask_loan_need":
                print("🔥 NUCLEAR RESET: Forcing fresh state for loan request")
                
                # Don't load ANY old state, start completely fresh
                self.state_manager.current_state = MinimalConversationState()
                
                # Direct response bypass all logic
                dispatcher.utter_message(text="""I'd love to help you find the perfect funding solution! 💡

                    To guide you to the right product, please tell me:

                    👤 **Individual** - Personal funding needs (salary advance, gig work funding)
                    🏢 **Business** - Company funding needs (working capital, growth funding)  
                    🏦 **Lender/NBFC** - Investment opportunities

                    Which category describes you best? 🎯""")
                                
                        # Return completely fresh state
                fresh_state = {
                    "user_type": "unknown",
                    "product_focus": None,
                    "conversation_phase": "initial",
                    "last_intent": intent_name
                }
                
                print(f"🔥 NUCLEAR RESULT: Fresh state = {fresh_state}")
                return [SlotSet("conversation_state", fresh_state)]
            
            # For other intents, proceed normally but with debugging
            existing_state_data = tracker.get_slot("conversation_state") or {}
            print(f"🔥 NORMAL FLOW: Loaded state = {existing_state_data}")
            
            if existing_state_data:
                self.state_manager.current_state = MinimalConversationState.from_dict(existing_state_data)
            
            # Update state
            updated_state = self.state_manager.update_from_intent(
                intent_name, entities, user_message
            )
            
            print(f"🔥 NORMAL RESULT: Updated state = {updated_state.to_dict()}")
            
            # Generate response
            response_text = self._generate_contextual_response(
                intent_name, updated_state, user_message
            )
            
            dispatcher.utter_message(text=response_text)
            
            return [SlotSet("conversation_state", updated_state.to_dict())]
            
        except Exception as e:
            print(f"🔥 ERROR: {str(e)}")
            dispatcher.utter_message(text="I'm having technical difficulties. Please try again!")
            return []


        
    def _generate_contextual_response(self, intent_name: str, 
                                    state: MinimalConversationState,
                                    user_message: str) -> str:
        """Generate context-aware responses."""
        
        try:
            # Context-aware response routing
            if intent_name == "ask_process":
                return self._get_process_response(state)
            elif intent_name == "ask_eligibility":
                return self._get_eligibility_response(state)
            elif intent_name in ["ask_gigcash_info", "ask_empcash_info", "ask_supply_chain_finance"]:
                return self._get_product_info_response(intent_name, state)
            elif intent_name.startswith("declare_"):
                return self._get_declaration_response(state)
            elif intent_name == "ask_loan_need":
                return self._get_loan_need_response(state)
            else:
                return self._get_smart_fallback_response(state, user_message)
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm here to help! What would you like to know about our financial services?"
    
    def _get_process_response(self, state: MinimalConversationState) -> str:
        """Get process information based on product focus."""
        
        if state.product_focus == "gigcash":
            return """🎯 **GigCash Application Process:**

1. **Connect Platform** - Link your gig work account (Uber, Zomato, etc.)
2. **Verify Earnings** - We verify your last 3-6 months earnings
3. **Check Eligibility** - See your advance limit (up to 50% monthly earnings)
4. **Apply** - Request the amount you need
5. **Get Funded** - Money in your account within 2 hours
6. **Auto-Repay** - Deducted from your next platform earnings

Ready to get started? 🚀"""

        elif state.product_focus == "empcash":
            return """💰 **EmpCash Application Process:**

1. **Employee Verification** - Confirm your employer is a BillMart partner
2. **Salary Verification** - Link your salary account for verification
3. **Calculate Limit** - See your advance amount (up to 50% earned salary)
4. **Apply** - Request advance through our secure platform
5. **Instant Approval** - Get approved in minutes
6. **Receive Funds** - Money credited within 2 hours
7. **Auto-Deduction** - Repaid from your next salary automatically

Want to check if your employer is a partner? 📞"""

        elif state.product_focus == "scf":
            return """🔗 **Supply Chain Finance Process:**

1. **Anchor Evaluation** - The buyer company is evaluated and approved
2. **Vendor/Dealer Onboarding** - Suppliers are evaluated and approved  
3. **Limit Setup** - Credit limit is sanctioned for the anchor
4. **Transaction Initiation** - Either party uploads an invoice
5. **Verification & Approval** - GST and compliance checks
6. **Disbursement** - Funds disbursed directly to the supplier
7. **Repayment** - Buyer repays as per agreed terms

Which specific SCF service interests you? 💼"""

        elif state.product_focus == "icf":
            return """🏥 **Insurance Claim Finance Process:**

1. **Hospital Verification** - Confirm NABH/NABL certification
2. **Claim Documentation** - Submit pending insurance claims
3. **Verification** - We verify claim validity and amounts
4. **Quick Approval** - Fast approval based on claim strength
5. **Disbursement** - Funds transferred within 24-48 hours
6. **Claim Settlement** - Repayment when insurance pays

Ready to improve your hospital's cash flow? 🏥"""
        
        else:
            return """I'd be happy to explain our process! Which product interests you?

• **GigCash** 🎯 - For gig workers and freelancers
• **EmpCash** 💰 - For salaried employees  
• **Supply Chain Finance** 🔗 - For businesses
• **Insurance Claim Finance** 🏥 - For hospitals
• **Term Loans** 💼 - For business expansion
• **iMark** 📊 - AI credit rating

Just let me know which one! 😊"""
    
    def _get_eligibility_response(self, state: MinimalConversationState) -> str:
        """Get eligibility information based on product focus."""
        
        if state.product_focus == "gigcash":
            return """🎯 **GigCash Eligibility Requirements:**

✅ **Basic Requirements:**
• Active on gig platforms (Uber, Ola, Zomato, Swiggy, Dunzo, etc.)
• Minimum 3 months consistent earnings history
• Valid KYC documents (Aadhar, PAN)
• Active bank account linked to platforms

✅ **Earnings Criteria:**
• Consistent monthly earnings of ₹15,000+
• Regular activity on platforms (not dormant accounts)
• Good platform ratings (4+ stars typically)
• Verifiable payment history

📊 **Advance Details:**
• Up to 50% of average monthly earnings
• Maximum ₹50,000 per advance
• Can combine multiple platform earnings

Ready to check your specific eligibility? 🚀"""
        
        elif state.product_focus == "empcash":
            return """💰 **EmpCash Eligibility Requirements:**

✅ **Employment Requirements:**
• Salaried employee at BillMart partner company
• Minimum 3 months employment with current employer
• Regular salary credits to bank account
• No pending disciplinary issues

✅ **Financial Criteria:**
• Monthly salary of ₹15,000+
• Consistent salary payments
• Valid bank account with salary credits
• Good repayment history (if applicable)

📊 **Advance Details:**
• Up to 50% of earned salary
• Maximum ₹1,00,000 per advance
• Multiple advances allowed per month

Want to check if your employer is a partner? 📞 +91 93269 46663"""

        elif state.product_focus == "scf":
            return """🔗 **Supply Chain Finance Eligibility:**

✅ **Business Requirements:**
• GST-registered business entity
• Minimum 1 year of operations
• Valid trade licenses and registrations
• Established buyer-supplier relationships

✅ **Financial Criteria:**
• Annual turnover of ₹1 crore+
• Regular business transactions
• Good credit history
• Valid financial statements

📊 **Financing Details:**
• Up to 80-95% of invoice value
• Invoice amount minimum ₹50,000
• Quick processing and disbursement

Ready to check your business eligibility? 💼"""

        elif state.product_focus == "icf":
            return """🏥 **Insurance Claim Finance Eligibility:**

✅ **Hospital Requirements:**
• NABH/NABL certified hospital
• Valid insurance empanelment
• Minimum 2 years operational
• Good claim settlement history

✅ **Claim Criteria:**
• Pending insurance claims ≥30 days
• Valid claim documentation
• TPA/Insurance company acknowledgment
• Claim amount minimum ₹1 lakh

📊 **Financing Details:**
• Up to 80% of claim value
• Quick disbursement within 24-48 hours
• Flexible repayment options

Want to improve your hospital's cash flow? 🏥"""
        
        else:
            return f"Let me check eligibility requirements for you! Which product are you interested in? I can provide specific requirements for {state.product_focus or 'any of our services'}."
    
    def _get_product_info_response(self, intent_name: str, state: MinimalConversationState) -> str:
        """Get detailed product information."""
        
        if "gigcash" in intent_name or state.product_focus == "gigcash":
            return """🎯 **GigCash - Fast, Flexible Funding for Gig Workers**

**What is GigCash?**
Quick financial support for freelancers and gig workers facing irregular income flows. Perfect for covering urgent expenses or bridging payment gaps.

**Key Benefits:**
• 💰 Up to 50% of monthly earnings
• ⚡ Funds credited within 2 hours
• 📱 100% digital application process
• 🔄 Auto-repay from platform earnings
• ✅ No traditional credit score required

**Supported Platforms:**
🚗 Uber, Ola | 🍕 Zomato, Swiggy | 📦 Dunzo, Amazon | 💻 Freelance platforms

Want to know about **eligibility**, **process**, or **fees**? 🤔"""
        
        elif "empcash" in intent_name or state.product_focus == "empcash":
            return """💰 **EmpCash - Your Salary, When You Need It Most**

**What is EmpCash?**
Salary advance solution for employees to access their earnings before payday. Perfect for emergency expenses without long-term debt.

**Key Benefits:**
• 💵 Up to 50% of earned salary
• ⚡ Instant approval in minutes
• 🏦 Funds credited within 2 hours
• 🔄 Auto-deducted from next paycheck
• 📈 No impact on credit score

**Perfect For:**
🚑 Medical emergencies | 💡 Bill payments | 👨‍👩‍👧‍👦 Family needs | 📚 Education expenses

Want to know about **eligibility**, **process**, or check if your **employer partners** with us? 💼"""

        elif "supply_chain_finance" in intent_name or state.product_focus == "scf":
            return """🔗 **Supply Chain Finance - Complete Business Funding Suite**

**What is SCF?**
Comprehensive financing solutions for your entire supply chain. From vendor payments to dealer funding, we've got your business covered.

**Our SCF Services:**
• 📋 **Sales Bill Discounting** - Get cash against sales invoices
• 🛒 **Purchase Bill Discounting** - Pay suppliers early
• 🏭 **Vendor Finance** - Support your suppliers
• 🏪 **Dealer Finance** - Fund your dealers
• ⚡ **Early Payment Finance** - Optimize payment cycles

**Key Benefits:**
• 💰 Up to 95% of invoice value
• ⚡ Quick processing (24-48 hours)
• 📊 Flexible repayment terms
• 🔒 Secure and compliant

Which SCF service interests you most? 💼"""
        
        else:
            return "I'd be happy to provide detailed information! Which product would you like to know about?"
    
    def _get_declaration_response(self, state: MinimalConversationState) -> str:
        """Handle user type declarations."""
        
        if state.user_type.value == "individual":
            return """Perfect! 👤 **Individual Financial Solutions**

I can help you with:
💰 **EmpCash** - Salary advance for salaried employees (up to 50% salary)
🎯 **GigCash** - Funding for gig workers & freelancers (up to 50% earnings)

Both offer:
• ⚡ Quick approval (minutes)
• 💸 Fast funding (2 hours)
• 🔄 Automatic repayment
• 📱 100% digital process

Which solution fits your situation better? 🤔"""

        elif state.user_type.value == "business":
            return """Excellent! 🏢 **Business Financial Solutions**

We offer comprehensive funding for your business:

🔗 **Supply Chain Finance** - Invoice financing, bill discounting
🏥 **Insurance Claim Finance** - Quick cash for hospitals  
🏠 **Lease Rental Discounting** - Property-backed financing
📊 **iMark** - AI-powered credit rating for MSMEs
💼 **Term Loans** - Long-term business expansion funding
⚡ **Short-term Loans** - Quick working capital solutions

Which type of funding does your business need? 💼"""

        elif state.user_type.value == "lender":
            return """Welcome! 🏦 **Lender Partnership Opportunities**

**BillMart Lender Advantages:**
• 📊 Deal flow from 23,000+ screened invoices
• 🤖 API integration for automated bidding
• 📈 Granular risk data for informed decisions
• 🔒 ISO-27001 & SOC-2 compliant infrastructure
• 💰 Consistent deal flow across multiple sectors

**Next Steps:**
📄 View our **deal-flow presentation**
☎️ Speak with our **capital markets team**
🤝 Discuss **partnership terms**

Which would you prefer? 💼"""
        
        else:
            return "Thanks for that information! How can I assist you today? 😊"
    
    def _get_loan_need_response(self, state: MinimalConversationState) -> str:
        """Handle general loan inquiries - ALWAYS ask for clarification."""
        
        return """I'd love to help you find the perfect funding solution! 💡

To guide you to the right product, please tell me:

👤 **Individual** - Personal funding needs (salary advance, gig work funding)
🏢 **Business** - Company funding needs (working capital, growth funding)  
🏦 **Lender/NBFC** - Investment opportunities

Which category describes you best? 🎯"""
    
    def _get_smart_fallback_response(self, state: MinimalConversationState, user_message: str) -> str:
        """Context-aware fallback that prioritizes PRODUCT context over USER TYPE."""
        
        user_lower = user_message.lower()
        
        # PRIORITY 1: Product-focused queries (regardless of user type)
        if state.product_focus and state.product_focus != "lender_services":
            
            # Product eligibility questions
            if any(word in user_lower for word in ["eligibility", "eligible", "qualify", "requirement"]):
                return self._get_eligibility_response(state)
            
            # Product process questions  
            if any(word in user_lower for word in ["process", "steps", "how", "procedure"]):
                return self._get_process_response(state)
            
            # Product information questions
            if any(word in user_lower for word in ["what is", "what's", "tell me about", "info", "details"]):
                return self._get_product_info_response(f"ask_{state.product_focus}_info", state)
        
        # PRIORITY 2: Affirmation handling with context
        if any(word in user_lower for word in ["yes", "yeah", "ok", "sure", "proceed"]):
            return self._handle_affirmation_with_context(state)
        
        # PRIORITY 3: Lender-specific queries (only for actual lender services)
        if state.user_type.value == "lender" and (state.product_focus == "lender_services" or not state.product_focus):
            if any(word in user_lower for word in ["deal", "flow", "partnership", "invest"]):
                return """📊 **BillMart Deal Flow Information:**

    We provide:
    • **Verified deal pipeline** from 23k+ invoices
    • **Real-time bidding** opportunities  
    • **Risk assessment** data
    • **API integration** for automation

    📞 **Next Steps:** Contact our capital markets team at partnerships@billmart.com

    What specific aspect would you like to know more about?"""
        
        # PRIORITY 4: Generic contextual help
        return f"""I'm here to help! Based on our conversation, I can provide more details about:

    • **{state.product_focus or 'Our Products'}** - Features and benefits
    • **Eligibility** - Requirements and criteria
    • **Process** - Application steps
    • **Fees** - Transparent pricing

    📞 **Direct Contact:** +91 93269 46663 | care@billmart.com

    What would you like to know? 😊"""

    def _handle_affirmation_with_context(self, state: MinimalConversationState) -> str:
        """Handle 'yes' responses based on conversation context."""
        
        if state.product_focus == "gigcash":
            return self._get_eligibility_response(state)
        elif state.product_focus == "empcash":
            return self._get_eligibility_response(state)
        elif state.user_type.value == "lender":
            return """Perfect! Let me connect you with our team:

    📞 **Capital Markets:** partnerships@billmart.com
    📱 **Direct Line:** +91 93269 46663
    📄 **Deal Flow Deck:** Available upon request

    Would you prefer a call or email introduction?"""
        else:
            return "Great! How can I help you proceed? Please let me know what specific information you need."
