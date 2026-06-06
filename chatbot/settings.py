"""
Chatbot Settings
Load environment variables for chatbot configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase REST API (primary - uses HTTPS, works on Railway)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# PostgreSQL connection (fallback for SQL execution)
PG_DSN = os.getenv("PG_DSN")

# Validate Supabase settings
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_KEY not set")
    print("Falling back to PG_DSN for all database operations")
    if not PG_DSN:
        raise ValueError("Either (SUPABASE_URL + SUPABASE_KEY) or PG_DSN must be configured")

# Anthropic API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("Warning: ANTHROPIC_API_KEY not set (required for chat functionality)")

# Claude model selection
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")

# LINE configuration
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_DESTINATION_USER_ID = os.getenv("LINE_DESTINATION_USER_ID", "Ub5928af25c0550217c9ec9d828f51f98")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# Optional: Webhook verification
if not LINE_CHANNEL_ACCESS_TOKEN:
    print("Warning: LINE_CHANNEL_ACCESS_TOKEN not set")
if not LINE_CHANNEL_SECRET:
    print("Warning: LINE_CHANNEL_SECRET not set (webhook signature verification disabled)")
