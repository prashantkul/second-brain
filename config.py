"""
Configuration and shared resources for Second Brain Bot.
"""

import os
import logging
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# =============================================================================
# Environment Variables
# =============================================================================

CAPTURE_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_CODE")
DIGEST_BOT_TOKEN = os.environ.get("TELEGRAM_DIGEST_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("second_brain")

# =============================================================================
# API Clients
# =============================================================================

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# =============================================================================
# Constants
# =============================================================================

PREFIXES = {
    "t:": "Tasks",
    "task:": "Tasks",
    "p:": "People",
    "person:": "People",
    "r:": "Research",
    "research:": "Research",
    "l:": "Links",
    "link:": "Links",
    "d:": "DeepAnalysis",
    "deep:": "DeepAnalysis",
}

# =============================================================================
# Deep Analysis Cache (for follow-up Q&A)
# =============================================================================

deep_analysis_cache = {
    "content": None,
    "analysis": None,
    "title": None,
    "timestamp": None
}

# Cache expiry time in seconds (1 hour)
DEEP_ANALYSIS_CACHE_EXPIRY = 3600

CATEGORY_EMOJI = {
    "People": "👤",
    "Research": "🔬",
    "Links": "🔗",
    "Tasks": "✅"
}

# =============================================================================
# Validation
# =============================================================================

def validate_config():
    """Validate required environment variables are set."""
    missing = []
    if not CAPTURE_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_CODE")
    if not DIGEST_BOT_TOKEN:
        missing.append("TELEGRAM_DIGEST_BOT_TOKEN")
    if not CHAT_ID:
        missing.append("CHAT_ID")
    if not NOTION_TOKEN:
        missing.append("NOTION_TOKEN")
    if not NOTION_DATABASE_ID:
        missing.append("NOTION_DATABASE_ID")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")

    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        return False
    return True
