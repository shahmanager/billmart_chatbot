from typing import Any, Text, Dict, List, Optional
from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.shared.nlu.training_data.message import Message
import difflib

@DefaultV1Recipe.register(
    DefaultV1Recipe.ComponentType.MESSAGE_FEATURIZER, is_trainable=False
)
class TypoCorrectorComponent(GraphComponent):
    """Custom component to correct typos before NLU processing."""
    
    def __init__(self, config: Dict[Text, Any] = None):
        self.known_terms = [
            "gigcash", "empcash", "scf", "icf", "imark",
            "eligibility", "process", "fees", "individual", 
            "business", "lender", "freelancer"
        ]
    
    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: Any,
        resource: Any,
        execution_context: ExecutionContext,
    ) -> "TypoCorrectorComponent":
        return cls(config)
    
    def process_training_data(self, training_data: TrainingData) -> TrainingData:
        """Process training data - required method."""
        # Apply typo correction to training examples too
        for example in training_data.training_examples:
            original_text = example.get("text")
            corrected_text = self._correct_typos(original_text)
            example.set("text", corrected_text)
        
        return training_data
    
    def process(self, messages: List[Message]) -> List[Message]:
        """Process messages during prediction."""
        for message in messages:
            original_text = message.get("text")
            corrected_text = self._correct_typos(original_text)
            message.set("text", corrected_text)
        
        return messages
    
    def _correct_typos(self, text: str) -> str:
        """Correct typos using fuzzy matching."""
        if not text:
            return text
            
        words = text.lower().split()
        corrected_words = []
        
        for word in words:
            if len(word) <= 2:
                corrected_words.append(word)
                continue
            
            # Find best match
            matches = difflib.get_close_matches(
                word, self.known_terms, n=1, cutoff=0.7
            )
            
            if matches:
                corrected_words.append(matches[0])
            else:
                corrected_words.append(word)
        
        return " ".join(corrected_words)
