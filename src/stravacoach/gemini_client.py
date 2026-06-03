import google.generativeai as genai
from pydantic import BaseModel
from pydantic.v1 import BaseModel

DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_SYSTEM_INSTRUCTION = "You are a helpful and knowledgeable Strava coach. You provide training"
ATHLETE_INTELLIGENCE_SYSTEM_INSTRUCTION = ""

model_mappings = {
    # Gemini 3.5 Flash provides sustained frontier-level intelligence optimized for real-world tasks at a higher speed and lower cost. 
    # Designed for the agentic era, it excels at sub-agent deployment, multi-step workflows, and long-horizon tasks at scale. 
    # This model is particularly effective for rapid agentic loops involving complex coding cycles and iterations.
    "flash": "gemini-3.5-flash",
    # Built to refine the performance and reliability of the Gemini 3 Pro series, Gemini 3.1 Pro Preview provides better thinking, 
    # improved token efficiency, and a more grounded, factually consistent experience. 
    # It's optimized for software engineering behavior and usability, 
    # as well as agentic workflows requiring precise tool usage and reliable multi-step execution across real-world domains.
    "pro": "gemini-3.1-pro-preview",
    # Gemini 3.1 Flash-Lite is a low-latency, cost-effective multimodal model optimized for high-frequency, lightweight tasks. 
    # The model supports text, image, video, audio, and PDF inputs, and is designed for high-volume agentic workflows, 
    # simple data extraction, and applications where latency and API cost are the primary constraints.
    "flash-lite": "gemini-3.1-flash-lite",
}

DEFAULT_MODEL = model_mappings["flash"]
ATHLETE_INTELLIGENCE_CFG = {
    "model": DEFAULT_MODEL,
    "system_instruction": ATHLETE_INTELLIGENCE_SYSTEM_INSTRUCTION,
    "tools": []
}

class GeminiManager():

    def __init__(self): # Default constructor
        super().__init__(DEFAULT_MODEL, [], DEFAULT_SYSTEM_INSTRUCTION)


    def __init__(self, athlete_intelligence: bool = False):
        """ Athlete Intelligence constructor. Initializes the GeminiManager with the tools and system instruction attempting to duplicate the behavior of Strava's built-in Athlete Intelligence feature. """
        super().__init__(
            model=ATHLETE_INTELLIGENCE_CFG["model"],
            tools=ATHLETE_INTELLIGENCE_CFG["tools"],
            system_instruction=ATHLETE_INTELLIGENCE_CFG["system_instruction"]
        )
    
    def __init__(self, model=DEFAULT_MODEL, tools=[], system_instruction: str = None):
        self.model = genai.GenerativeModel(
            model=model,
            tools=tools,
            system_instruction=system_instruction
        )