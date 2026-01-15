from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

class ActionRouteAfterForm(Action):
    def name(self) -> Text:
        return "action_route_after_form"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        prod = tracker.get_slot("product_name")
        user = tracker.get_slot("user_type")

        # route to your existing utterances
        mapping = {
            "supply chain finance": "utter_supply_chain_finance",
            "vendor finance": "utter_vendor_finance",
            "dealer finance": "utter_dealer_finance",
            "sales bill discounting": "utter_sales_bill_discounting",
            "purchase bill discounting": "utter_purchase_bill_discounting",
            "early payment finance": "utter_early_payment_finance",
            "empcash": "utter_empcash_info",
            "gigcash": "utter_gigcash_info",
            "insurance claim finance": "utter_insurance_claim_finance",
        }

        if user == "lender":
            dispatcher.utter_message(response="utter_lender_info")
        elif prod in mapping:
            dispatcher.utter_message(response=mapping[prod])
        else:
            dispatcher.utter_message(text="Great! Ask me about process, eligibility or documents.")

        return [SlotSet("conversation_stage", "product_inquiry")]
