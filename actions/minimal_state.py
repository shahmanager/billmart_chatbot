# actions/minimal_state.py
from typing import Dict, Text, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum 
import json 
from rasa_sdk import Tracker, Action  # Fixed: Action not action
from rasa_sdk.executor import CollectingDispatcher 
from rasa_sdk.events import SlotSet, FollowupAction

class UserType(Enum):
    """Enumeration for user categories."""
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    LENDER = "lender"
    UNKNOWN = "unknown"

class ConversationPhase(Enum):
    """Tracks where user is in their journey."""
    INITIAL = "initial"
    EXPLORING = "exploring"
    FOCUSED = "focused"
    PROCESS = "process"
    APPLYING = "applying"

@dataclass
class MinimalConversationState:
    """Minimal state representation for conversation context."""
    user_type: UserType = UserType.UNKNOWN
    product_focus: Optional[str] = None  # Fixed: Removed duplicate
    conversation_phase: ConversationPhase = ConversationPhase.INITIAL  # Fixed: Proper field name
    last_intent: Optional[str] = None
    
    def to_dict(self) -> Dict[Text, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_type": self.user_type.value,
            "product_focus": self.product_focus,
            "conversation_phase": self.conversation_phase.value,  # Fixed: Proper field name
            "last_intent": self.last_intent
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MinimalConversationState':  # Fixed: Added return type
        """Create instance from dictionary."""
        return cls(
            user_type=UserType(data.get("user_type", "unknown")),
            product_focus=data.get("product_focus"),  # Fixed: Typo corrected
            conversation_phase=ConversationPhase(data.get("conversation_phase", "initial")),
            last_intent=data.get("last_intent")
        )

class ConversationStateManager:
    """Manages conversation state transitions and context extraction."""
    
    # Complete product keywords mapping
    PRODUCT_KEYWORDS = {
        "gigcash": [
            # Direct product names
            "gigcash", "gig cash", "gig-cash", "gig", "gog",
            # User types
            "freelancer", "contractor", "independent contractor",
            # Platforms
            "zomato", "uber", "swiggy", "ola", "dunzo", "rapido",
            # Work types
            "delivery", "driver", "gig worker", "gig work"
        ],
        
        "empcash": [
            # Direct product names  
            "empcash", "emp cash", "emp-cash",
            # Employment terms
            "salary", "employee", "salaried", "payroll", "advance", 
            "salary advance", "salary loan", "employee advance",
            # Job types
            "full time", "permanent", "company employee"
        ],
        
        "scf": [
            # Direct product names
            "scf", "supply chain finance", "supply chain financing",
            # Business types
            "business", "SME", "MSME", "company", "corporate",
            # Financial instruments
            "invoice", "bill", "vendor", "dealer", "supplier",
            "bill discounting", "invoice financing", "working capital"
        ],
        
        "icf": [
            # Direct product names
            "icf", "insurance claim finance", "insurance claim financing",
            # Healthcare sector
            "hospital", "medical", "healthcare", "clinic", "nursing home",
            # Insurance terms
            "insurance", "claim", "TPA", "cashless", "reimbursement"
        ],
        
        "imark": [
            # Direct product names
            "imark", "i-mark", "i mark",
            # Credit services
            "credit rating", "credit score", "credit grading", "rating",
            "creditworthiness", "credit assessment", "financial rating",
            # Business evaluation
            "business rating", "company rating", "MSME rating"
        ],
        
        "short_term_loan": [
            # Direct product names  
            "short term loan", "short-term loan", "BEST loan", "best loan",
            # Loan characteristics
            "quick loan", "immediate loan", "urgent loan", "fast loan",
            "small loan", "emergency loan", "instant loan",
            # Time-sensitive needs
            "urgent money", "quick cash", "immediate funding"
        ],
        
        "term_loan": [
            # Direct product names
            "term loan", "long term loan", "long-term loan",
            # Business purposes
            "business loan", "expansion loan", "equipment loan", 
            "machinery loan", "growth loan", "capital loan",
            # Loan characteristics
            "fixed term", "installment loan", "EMI loan"
        ],
        
        "lrd": [
            # Direct product names
            "lrd", "lease rental discounting", "lease rental financing",
            # Property terms
            "lease", "rental", "rent", "property", "real estate",
            "commercial property", "office lease", "shop lease",
            # Financial terms
            "lease finance", "rental finance", "property finance"
        ],
        
        "lender_services": [
            # Institution types
            "lender", "NBFC", "bank", "financial institution",
            "finance company", "lending partner",
            # Investment terms
            "invest", "investment", "funding partner", "capital",
            "finance partner", "loan provider", "funding opportunity",
            # Business development
            "partnership", "deal flow", "investment opportunity",
            "lending opportunity", "portfolio"
        ]
    }
    
    # User type detection keywords
    USER_TYPE_KEYWORDS = {
        "individual": [
            "individual", "person", "personal", "me", "myself",
            "employee", "worker", "freelancer", "gig worker"
        ],
        "business": [
            "business", "company", "firm", "organization", "enterprise",
            "SME", "MSME", "startup", "corporate", "merchant", "family business"
        ],
        "lender": [
            "lender", "NBFC", "bank", "investor", "financier",
            "financial institution", "funding partner", "capital provider" , "want to invest"
        ]
    }
    
    INTENT_PHASE_MAP = {
        "ask_process": ConversationPhase.PROCESS,
        "ask_eligibility": ConversationPhase.FOCUSED,
        "ask_apply": ConversationPhase.APPLYING,
        "ask_info": ConversationPhase.EXPLORING,
    }
    
    def __init__(self):
        """Initialize with default state."""
        self.current_state = MinimalConversationState()
    
    def update_from_intent(self, intent_name: str, entities: List[Dict], user_message: str) -> MinimalConversationState:
        """Update state based on intent and entities."""
        
        # Handle explicit declarations
        if intent_name.startswith("declare_"):
            user_type_str = intent_name.replace("declare_", "")
            try:
                self.current_state.user_type = UserType(user_type_str)
            except ValueError:
                self.current_state.user_type = UserType.UNKNOWN
        
        # ✅ FIX: Reset user_type for loan requests (they need clarification)
        elif intent_name == "ask_loan_need":
            self.current_state.user_type = UserType.UNKNOWN  # Force clarification
        
        # Product detection (this part is fine)
        detected_product = self._detect_product_from_message(user_message)
        if detected_product:
            self.current_state.product_focus = detected_product
        
        # Update conversation phase
        if intent_name in self.INTENT_PHASE_MAP:
            self.current_state.conversation_phase = self.INTENT_PHASE_MAP[intent_name]
        
        # Track last intent
        self.current_state.last_intent = intent_name
        
        return self.current_state


    
    def _detect_product_from_message(self, message: str) -> Optional[str]:
        """Detect product interest from user message using keyword matching."""
        message_lower = message.lower()
        
        # Score each product based on keyword matches
        product_scores = {}
        for product, keywords in self.PRODUCT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                product_scores[product] = score
        
        # Return product with highest score, if any
        if product_scores:
            return max(product_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _detect_user_type_from_message(self, message: str) -> Optional[str]:
        """Detect user type from message content."""
        message_lower = message.lower()
        
        # Score each user type based on keyword matches
        type_scores = {}
        for user_type, keywords in self.USER_TYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in message_lower)
            if score > 0:
                type_scores[user_type] = score
        
        # Return user type with highest score, if any
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def get_context_for_response(self) -> Dict[str, str]:
        """Generate context information for response selection."""
        context = {
            "user_type": self.current_state.user_type.value,
            "product": self.current_state.product_focus or "general",
            "phase": self.current_state.conversation_phase.value
        }
        
        return context
    
    def should_ask_for_clarification(self) -> bool:
        """Determine if we need more information from user."""
        return (
            self.current_state.user_type == UserType.UNKNOWN or 
            self.current_state.product_focus is None
        )
    
    def get_clarification_question(self) -> str:
        """Generate appropriate clarification question."""
        if self.current_state.user_type == UserType.UNKNOWN:
            return "To help you better, are you an **individual**, **business**, or **lender**?"
        
        if self.current_state.product_focus is None:
            if self.current_state.user_type == UserType.INDIVIDUAL:
                return "Which product interests you? **EmpCash** (salary advance) or **GigCash** (gig worker funding)?"
            elif self.current_state.user_type == UserType.BUSINESS:
                return "Which service do you need? **Supply Chain Finance**, **Term Loan**, **iMark** credit rating, or something else?"
            elif self.current_state.user_type == UserType.LENDER:
                return "Are you interested in our **lender partnership** opportunities or **deal flow** information?"
        
        return "How can I help you today?"

# Example Action using the Minimal State
class ActionProcessWithMinimalState(Action):
    """Enhanced action that uses minimal state for context-aware responses."""
    
    def name(self) -> Text:
        return "action_process_with_minimal_state"
    
    def __init__(self):
        self.state_manager = ConversationStateManager()
    
    def run(self, dispatcher: CollectingDispatcher, 
           tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Main action execution logic."""
        
        # Extract current conversation data
        latest_message = tracker.latest_message
        intent_name = latest_message.get("intent", {}).get("name", "")
        entities = latest_message.get("entities", [])
        user_message = latest_message.get("text", "")
        
        # Load existing state from tracker (if any)
        existing_state_data = tracker.get_slot("conversation_state") or {}
        if existing_state_data:
            self.state_manager.current_state = MinimalConversationState.from_dict(existing_state_data)
        
        # Update state based on current input
        updated_state = self.state_manager.update_from_intent(
            intent_name, entities, user_message
        )
        
        # Generate response based on state
        if self.state_manager.should_ask_for_clarification():
            response_text = self.state_manager.get_clarification_question()
        else:
            response_text = self._generate_contextual_response(updated_state, intent_name)
        
        # Send response to user
        dispatcher.utter_message(text=response_text)
        
        # Return events to update Rasa's state
        return [
            SlotSet("conversation_state", updated_state.to_dict())
        ]
    
    def _generate_contextual_response(self, state: MinimalConversationState, intent_name: str) -> str:
        """Generate context-aware response based on current state."""
        
        context = f"User: {state.user_type.value}, Product: {state.product_focus}, Phase: {state.conversation_phase.value}"
        
        # Basic contextual responses - expand as needed
        if state.product_focus == "gigcash" and intent_name == "ask_process":
            return """
            🎯 **GigCash Application Process:**
            
            1. **Connect Platform** - Link your gig work account
            2. **Verify Earnings** - We verify your last 3-6 months earnings  
            3. **Check Eligibility** - See your advance limit
            4. **Apply** - Request the amount you need
            5. **Get Funded** - Money in your account within 2 hours
            
            Ready to get started?
            """
        
        elif state.product_focus == "empcash" and intent_name == "ask_process":
            return """
            💰 **EmpCash Application Process:**
            
            1. **Employee Verification** - Confirm your employer partnership
            2. **Salary Verification** - Link your salary account
            3. **Calculate Limit** - See your advance amount
            4. **Apply** - Request advance through our platform
            5. **Receive Funds** - Money credited within 2 hours
            
            """
        
        elif state.user_type == UserType.LENDER:
            return """
            💼 **Welcome to BillMart's Lender Services!**
            
            We offer:
            • **Deal flow** from 23k+ screened invoices
            • **API integration** for automated bidding
            • **Granular risk data** for informed decisions
            • **ISO-27001 compliant** infrastructure
            
            Would you like our **deal-flow deck** or to speak with our capital markets team?
            """
        
        else:
            return f"I understand you're interested in {state.product_focus or 'our services'}. How can I help you specifically?"
