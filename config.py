"""Glbal configuration file for the project."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- file paths ---
LOG_FILE = "audit_log.jsonl"

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"

# --- Rate limiter ---
MAX_SUBMISSIONS_PER_DAY = 100  # Maximum number of submissions allowed a day
MAX_SUBMISSIONS_IN_TIME_WINDOW = 20  # Maximum number of submissions allowed in a 1 minute time window

# --- user content ---
MINIMUM_LENGTH = 20  # Minimum length of user content in characters
MAXIMUM_LENGTH = 10000  # Maximum length of user content in characters

