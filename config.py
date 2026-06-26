"""Glbal configuration file for the project."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"

# --- Rate limiter ---
MAX_SUBMISSIONS = 10  # Maximum number of submissions allowed within the time window
MAX_SUBMISSIONS_WINDOW = 3  # Time window in minutes for rate limiting

# --- user content ---
MINIMUM_LENGTH = 20  # Minimum length of user content in characters
MAXIMUM_LENGTH = 10000  # Maximum length of user content in characters

