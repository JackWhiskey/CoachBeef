import json

from openai import AsyncOpenAI

from pydantic import BaseModel
from config import Config
from tools import get_activity_from_db, get_activity_list_over_time, get_activity_list_over_time, get_summary_stats_over_time, search_past_advice

DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_SYSTEM_INSTRUCTION = (
    "You are a highly knowledgeable and helpful running coach. You provide training advice and feedback to the user. "
    "CRITICAL RULES FOR RESPONDING:\n"
    "1. FOCUS ON EFFORT, NOT METRICS: When you retrieve activity data using your tools, translate the raw numbers into qualitative feedback (e.g., 'a solid long effort', 'a quick sprint', 'a grueling climb').\n"
    "2. NO RAW DATA UNLESS ASKED: Absolutely do not quote specific numbers (pace, distance, calories, heart rate, or Activity IDs) unless the user explicitly asks for them in their prompt. If they ask for a 'summary', give them a vibes-based, qualitative summary.\n"
    "3. USE NAMES, NOT IDs: If referencing an activity, use its human-readable name, never its numeric ID.\n"
)

ATHLETE_INTELLIGENCE_SYSTEM_INSTRUCTION = """You are a highly knowledgeable and helpful running coach. You provide training advice and feedback to the user."""
ATHLETE_INTELLIGENCE_PROMPT = """Please do the following things in order in exactly 2 sentences: Complement the user's recent activity, give feedback on the level of effort without printing numbers or quoting the description, and compare it to recent activities."""

model_mappings = {
    # GPT-5.4 mini brings the strengths of GPT-5.4 to a faster, more efficient model designed for high-volume workloads.
    "mini": "gpt-5.4-mini",
    # GPT-5.5 is our newest frontier model for the most complex professional work.
    "latest": "gpt-5.5",
    # GPT-5.5 pro is available for Responses API requests, including through the Batch API, 
    # to enable support for multi-turn model interactions before responding to API requests and other advanced API features in the future. 
    # Since GPT-5.5 pro is designed to tackle tough problems, some requests may take several minutes to finish.
    "pro": "gpt-5.5-pro",
}

DEFAULT_MODEL = model_mappings["mini"]
ATHLETE_INTELLIGENCE_CFG = {
    "model": DEFAULT_MODEL,
    "system_instruction": ATHLETE_INTELLIGENCE_SYSTEM_INSTRUCTION,
    "schemas": [
        {
            "type": "function",
            "function": {
                "name": "get_activity_from_db",
                "description": "Fetches statistics (distance, speed, time) for a specific Strava activity from the local database. Always use this when the user asks you to analyze a specific activity ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "activity_id": {
                            "type": "integer",
                            "description": "The numerical ID of the activity to look up."
                        }
                    },
                    "required": ["activity_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_activity_from_db",
                "description": "Fetches statistics (distance, speed, time) for a specific Strava activity from the local database. Always use this when the user asks you to analyze a specific activity ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "activity_id": {
                            "type": "integer",
                            "description": "The numerical ID of the activity to look up."
                        }
                    },
                    "required": ["activity_id"]
                }
            }
        }
    ]
}

coach_tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_activity_list_over_time",
            "description": "Retrieves a list of activities within a specified time range, optionally filtered by activity type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "before_date": {
                        "type": "string",
                        "description": "The date before which to fetch activities."
                    },
                    "after_date": {
                        "type": "string",
                        "description": "The date after which to fetch activities."
                    },
                    "type": {
                        "type": "string",
                        "description": "The type of activity to filter by. Only one kind of activity can be aggregated at a time (e.g. Run, Ride, Swim)."
                    }
                },
                "required": ["before_date", "after_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_summary_stats_over_time",
            "description": "Retrieves summary statistics (max, min, average)for activities within a specified time range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "before_date": {
                        "type": "string",
                        "description": "The date before which to fetch activities."
                    },
                    "after_date": {
                        "type": "string",
                        "description": "The date after which to fetch activities."
                    },
                    "type": {
                        "type": "string",
                        "description": "The type of activity to filter by. Only one kind of activity can be aggregated at a time (e.g. Run, Ride, Swim)."
                    }
                },
                "required": ["before_date", "after_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_activity_from_db",
            "description": "Fetches statistics (distance, speed, time) for a specific Strava activity from the local database. Always use this when the user asks you to analyze a specific activity ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "activity_id": {
                        "type": "integer",
                        "description": "The numerical ID of the activity to look up."
                    }
                },
                "required": ["activity_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_past_advice",
            "description": "Retrieves past conversation history between you (the coach) and the user. Use this if the user asks what you previously discussed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "The number of previous messages to retrieve. Default is 5, max is 20."
                    }
                }
            }
        }
    }
]

coach_tool_functions = {
    "get_activity_from_db": get_activity_from_db,
    "search_past_advice": search_past_advice,
    "get_summary_stats_over_time": get_summary_stats_over_time,
    "get_activity_list_over_time": get_activity_list_over_time
}

class OpenAIManager():

    def __init__(
            self, 
            model=DEFAULT_MODEL, 
            system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION,
            context: dict = None,
            athlete_intelligence: bool = False
        ):

        self.athlete_intelligence = athlete_intelligence
        self.context = context

        # If they pass the flag, override with the Athlete Intelligence config
        if athlete_intelligence:
            self.model = ATHLETE_INTELLIGENCE_CFG["model"]
            self.tools = ATHLETE_INTELLIGENCE_CFG["schemas"]
            self.system_instruction = ATHLETE_INTELLIGENCE_CFG["system_instruction"]
            self.tool_functions = coach_tool_functions
        else:
            self.model = model
            self.system_instruction = system_instruction
            self.tools = coach_tools_schema
            self.tool_functions = coach_tool_functions


        self.client = AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY
        )

        print(f"Initialized OpenAIManager with model {self.model}, tools {self.tools}, and system instruction: {self.system_instruction}")

    async def send_message_athlete_intelligence(self, user_text: str, context: str = "") -> str:
        pass


    async def send_message(self, user_text: str, context: str = "", chat_history: list = None) -> str:
        if chat_history is None:
            chat_history = []
        
        activity_id = context.get("this_activity_id") if context else None
        # ==========================================
        # MODE 1: ATHLETE INTELLIGENCE (Special Case)
        # ==========================================
        if self.athlete_intelligence:
            # Ignore the user's text entirely and use our hardcoded prompt!
            prompt = ATHLETE_INTELLIGENCE_PROMPT
            
            # Explicitly tell the model which activity to use its tools on
            if activity_id:
                prompt += f"\n\nPlease use your tools to fetch and analyze Activity ID: {activity_id}."
            
            # Limit the context to ONLY the system instruction and this specific prompt
            messages = [
                {"role": "system", "content": ATHLETE_INTELLIGENCE_SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ]

        # ==========================================
        # MODE 2: STANDARD CHAT (Coach Beef)
        # ==========================================
        else:
            # 1. Start with the System Instruction
            messages = [{"role": "system", "content": self.system_instruction}]
            
            # 2. Append the recent conversation history so it remembers the context!
            for msg in chat_history:
                # We only want to inject standard user/assistant messages to keep it clean
                if msg["role"] in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 3. Add context to the CURRENT user text if needed
            if activity_id:
                user_text = f"[System Context: The user is currently looking at Activity ID {activity_id}]\n\n{user_text}"
            
            # 4. Finally, append the current user message at the very end
            messages.append({"role": "user", "content": user_text})

        # ==========================================
        # THE OPENAI EXECUTION LOOP
        # ==========================================
        # 1. Initial Call
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools if self.tools else None,
        )
        
        message = response.choices[0].message
        messages.append(message) # Append the model's response to the history

        # 2. Check if the model wants to use a Tool
        if message.tool_calls:
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                print(f"Model requested tool: {func_name} with args {args}")
                
                # Execute the matched Python function
                if func_name in self.tool_functions:
                    try:
                        result = self.tool_functions[func_name](**args)
                    except Exception as e:
                        print(f"❌ CRITICAL: Tool function '{func_name}' crashed with error: {e}")
                        result = json.dumps({"error": str(e)})
                    
                    # Append the tool's result back to the messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": result
                    })
            
            # 3. Send the newly gathered data back to OpenAI for a final answer
            final_response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return final_response.choices[0].message.content
            
        # If no tools were called, just return the text response directly
        return message.content

class ChatRequest(BaseModel):
    message: str
    this_activity_id: int | None = None