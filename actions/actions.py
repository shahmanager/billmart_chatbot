from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

class ActionRouteAfterForm(Action):
    def name(self) -> Text:
        return "action_route_after_form"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_type = tracker.get_slot("user_type")
        product_name = tracker.get_slot("product_name")
        
        if user_type == "lender":
            dispatcher.utter_message(response="utter_lender_info")
        elif user_type == "business":
            dispatcher.utter_message(text="Great! Here are our business solutions:\n\n🔗 **Supply Chain Finance** - Invoice financing\n🏥 **Insurance Claim Finance** - For hospitals\n🏠 **Lease Rental Discounting** - Property financing\n📊 **iMARK** - AI credit rating\n\nWhich interests you most?")
        elif user_type == "individual":
            dispatcher.utter_message(text="Perfect! Here are our individual solutions:\n\n💰 **EmpCash** - Salary advance (up to 50%)\n🎯 **GigCash** - For gig workers/freelancers\n\nWhich would you like to know about?")
        elif product_name:
            if product_name == "gigcash":
                dispatcher.utter_message(response="utter_gigcash_info")
            elif product_name == "empcash":
                dispatcher.utter_message(response="utter_empcash_info")
            elif product_name == "supply chain finance":
                dispatcher.utter_message(response="utter_supply_chain_finance_info")
        else:
            dispatcher.utter_message(response="utter_services_offered")
            
        return []

class ActionProvideProcessInfo(Action):
    def name(self) -> Text:
        return "action_provide_process_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        product_name = tracker.get_slot("product_name")
        
        if product_name == "gigcash":
            dispatcher.utter_message(response="utter_gigcash_process")
        elif product_name == "empcash":
            dispatcher.utter_message(response="utter_empcash_process")
        elif product_name == "insurance claim finance":
            dispatcher.utter_message(response="utter_insurance_claim_finance_process")
        elif product_name == "supply chain finance":
            dispatcher.utter_message(response="utter_supply_chain_finance_process")
        else:
            dispatcher.utter_message(text="Which product's process would you like to know about? We offer EmpCash, GigCash, SCF, ICF, and more.")
            
        return []

class ActionProvideEligibilityInfo(Action):
    def name(self) -> Text:
        return "action_provide_eligibility_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        product_name = tracker.get_slot("product_name")
        
        if product_name == "gigcash":
            dispatcher.utter_message(response="utter_gigcash_eligibility")
        elif product_name == "empcash":
            dispatcher.utter_message(response="utter_empcash_eligibility")
        elif product_name == "insurance claim finance":
            dispatcher.utter_message(text="ICF eligibility: NABH/NABL hospitals with pending insurance claims, valid TPAs/insurers, claim docs required.")
        else:
            dispatcher.utter_message(text="Which product's eligibility would you like to check? EmpCash, GigCash, SCF, or ICF?")
            
        return []

class ActionSmartDemo(Action):
    def name(self) -> Text:
        return "action_smart_demo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_type = tracker.get_slot("user_type")
        product_name = tracker.get_slot("product_name")
        
        if user_type == "lender":
            dispatcher.utter_message(text="I'll connect you with our capital markets team for a detailed demo.\n\n📞 Call: +91 93269 46663\n✉️ Email: care@billmart.com\n\nThey'll walk you through our lender dashboard and deal flow.")
        elif product_name:
            dispatcher.utter_message(text=f"I'll arrange a demo for {product_name}.\n\n📞 Call: +91 93269 46663\n✉️ Email: care@billmart.com\n\nOur team will show you the complete process and answer all your questions.")
        else:
            dispatcher.utter_message(text="I'd be happy to arrange a demo! First, let me know:\n\nAre you a **lender**, **business**, or **individual**?\n\nThis helps me connect you with the right specialist.")
            
        return []
