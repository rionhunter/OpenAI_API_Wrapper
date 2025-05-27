from .openai_wrapper import generate_content
from .model_manager import get_available_models


# Unified OpenAI API CLI Toolkit

__version__ = "1.0.0"

__all__ = [
    "main",
    "Gpt_Api_Module",
    "Dalle_Api_Module",
    "Whisper_Api_Module",
    "model_manager",
    "openai_wrapper",
    "utils",
    "demo_runner"
]
