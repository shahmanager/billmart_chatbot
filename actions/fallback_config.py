import os
# ===== CHANGE THIS LINE TO SWITCH =====
ACTIVE_FALLBACK = 'llm_only'  # ← Just change this!
# Options:
#   'llm_only'     - Pure LLM (fast, simple)
#   'static_rag'   - Knowledge base + LLM
#   'dynamic_rag'  - KB + simulated updates
#   'dynamic_llm'  - Context-aware LLM
#   'none'         - Disable fallback

# Rasa confidence threshold (when to trigger fallback)
CONFIDENCE_THRESHOLD = 0.6

# Master on/off switch
FALLBACK_ENABLED = True
