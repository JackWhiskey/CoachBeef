import json

from openai import AsyncOpenAI

from pydantic import BaseModel
from config import Config
from chart_model import DashboardModel, DashboardPlan
from db_model import DBActivity
from tools import get_activity_from_db, get_activity_list_over_time, get_activity_list_over_time, get_laps_and_splits, get_recent_similar_activities, get_summary_stats_over_time, get_time_series_streams, search_past_advice

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

dashboard_tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_time_series_streams",
            "description": "Fetches continuous minute-by-minute stream data (time, heart rate, pace) for an activity. Crucial for drawing continuous line charts like Heart Rate over time.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "activity_id": {
                        "type": "integer",
                        "description": "The Strava Activity ID"
                    }
                },
                "required": ["activity_id"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_laps_and_splits",
            "description": "Fetches the lap and split data for a specific activity. Use this to draw interval pace bar charts or lap comparisons.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "activity_id": {
                        "type": "integer", 
                        "description": "The Strava Activity ID"
                    }
                },
                "required": ["activity_id"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_similar_activities",
            "description": "Fetches recent activities of the same workout_type. Use this to draw trend lines comparing the current run to past runs.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "workout_type": {
                        "type": "string", 
                        "enum": [
                            "Run - Standard", 
                            "Run - Race", 
                            "Run - Long Run", 
                            "Run - Workout", 
                            "Ride - None",
                            "Ride - Race",
                            "Ride - Workout",
                            "Unknown"
                        ],
                    },
                    "limit": {
                        "type": "integer", 
                        "description": "How many past runs to fetch. Default is 5."
                    }
                },
                "required": ["workout_type", "limit"], 
                "additionalProperties": False
            }
        }
    }
]

dashboard_tool_functions = {
    "get_time_series_streams": get_time_series_streams,
    "get_laps_and_splits": get_laps_and_splits,
    "get_recent_similar_activities": get_recent_similar_activities
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

        # print(f"Initialized OpenAIManager with model {self.model}, tools {self.tools}, and system instruction: {self.system_instruction}")

    async def send_message_athlete_intelligence(self, user_text: str, context: str = "") -> str:
        pass

    async def generate_dashboard_plan(self, sys_prompt: str, user_prompt: str) -> str:
        try:
            plan_response = await self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages= [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=DashboardPlan
            )

            dashboard_plan = plan_response.choices[0].message.parsed
            print(f"AI Planner suggested: {[c.title for c in dashboard_plan.recommended_charts]}")
            return dashboard_plan
        except Exception as e:
            print(f"Error while creating dashboard plan: {e}")

    async def execute_dashboard_with_plan(self, sys_prompt: str, user_prompt: str, max_iterations: int):
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]

        iteration = 0
        while iteration < max_iterations:
            iteration+=1
            api_args = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "response_format": DashboardModel
            }
            if iteration < max_iterations:
                api_args["tools"] = dashboard_tools_schema

            response = await self.client.beta.chat.completions.parse(**api_args)
            message = response.choices[0].message

            # If the model wants to use tools, execute them and loop again!
            if message.tool_calls:
                messages.append(message) # Append the model's tool request to history
                
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    print(f"Executor fetching data with tool: {func_name}({args})")
                    
                    # Execute the matched Python function
                    if dashboard_tool_functions and func_name in dashboard_tool_functions:
                        try:
                            result = dashboard_tool_functions[func_name](**args)
                        except Exception as e:
                            result = json.dumps({"error": str(e)})
                    else:
                        result = json.dumps({"error": f"Tool '{func_name}' not found."})

                    # Feed the data back into the message array
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": str(result)
                    })
                # The while loop restarts here, sending the newly fetched data back to OpenAI
                
            else:
                # No more tool calls? The model finished drawing the charts!
                return message.parsed

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


    async def generate_dashboard_for_activity(self, activity: DBActivity):
         # 2. Construct the prompt with the raw data
        system_prompt = (
            "You are an expert sports data analyst. Based on the user's Strava activity data, "
            "generate a dashboard. If it's a long run, show Heart Rate over time. "
            "If it's an interval session, show a bar chart of pace per split. "
            "Return the EXACT JSON structure required by Apache ECharts."
        )
        
        user_prompt = f"Activity Type: {activity.type}\nDistance: {activity.distance}\nTime: {activity.moving_time}\n..."
        
        # 3. Use client.beta.chat.completions.parse to force structured JSON output!
        response = await self.client.beta.chat.completions.parse(
            model="gpt-4o-mini", # Standard model works well, but you can use gpt-4o for complex charting
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=DashboardModel,
        )
        
        # 4. Extract the cleanly parsed Python object
        dashboard_data = response.choices[0].message.parsed
        return dashboard_data


class ChatRequest(BaseModel):
    message: str
    this_activity_id: int | None = None