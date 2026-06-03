import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Load environment variables from the .env file
load_dotenv(dotenv_path=ENV_PATH)


class Config:

    print(f"Loading Strava API credentials from .env file at: {ENV_PATH}")
    STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
    STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
    STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
    STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

    if (
        not STRAVA_CLIENT_ID
        or not STRAVA_CLIENT_SECRET
        or not STRAVA_ACCESS_TOKEN
        or not STRAVA_REFRESH_TOKEN
    ):
        raise ValueError(
            f"Missing Strava API credentials. Check your .env file. Tried looking in: {ENV_PATH}"
        )
    else:
        print("Strava API credentials loaded successfully by config.")

    print (f"Loading OpenAI API key from .env file at: {ENV_PATH}")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    if not OPENAI_API_KEY:
        raise ValueError(
            f"Missing OpenAI API key. Check your .env file. Tried looking in: {ENV_PATH}"
        )
    else:
        print("OpenAI API key loaded successfully by config.")

    # print (f"Loading Gemini API key from .env file at: {ENV_PATH}")
    # GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # if not GEMINI_API_KEY:
    #     raise ValueError(
    #         f"Missing Gemini API key. Check your .env file. Tried looking in: {ENV_PATH}"
    #     )
    # else:
    #     print("Gemini API key loaded successfully by config.")
