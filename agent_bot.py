"""
Second Brain Telegram Bot - Agent SDK Version

Uses Claude Agent SDK with custom MCP tools for Notion integration.
Skills-based architecture for intelligent message processing.

Usage:
    python agent_bot.py
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta

import requests
import schedule
import time
import threading
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

from tools import create_second_brain_server

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_CODE")
DIGEST_BOT_TOKEN = os.environ.get("TELEGRAM_DIGEST_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("second_brain_agent")

# Track last processed message
last_update_id = 0

# Deep analysis Q&A cache
deep_analysis_cache = {
    "active": False,
    "title": None,
    "url": None,
    "summary": None,
    "timestamp": None
}

# Create MCP server
mcp_server = create_second_brain_server()

# System prompt for the agent
SYSTEM_PROMPT = """You are a Second Brain assistant integrated with Telegram and Notion.

Your capabilities:
1. Categorize messages into Tasks, People, Research, or Links
2. Analyze URLs and documents - fetch content, extract insights
3. Save to Notion - store entries with proper categorization
4. Search knowledge base - query saved entries
5. Generate digests - daily and weekly summaries

Quick Prefixes:
- t: or task: → Tasks
- p: or person: → People
- r: or research: → Research
- l: or link: → Links
- j: or job: → Jobs (analyze job posting, extract requirements, suggest skills)
- d: or deep: → Deep paper analysis
- rp: or research-potential: → Research potential analysis (is this worth pursuing?)
- rp-deep: → Deep research dive (literature, gaps, venues, roadmap)
- ! → High priority
- ? → Query knowledge base

Telegram Formatting (IMPORTANT):
- Use *bold* for emphasis (NOT markdown headers like # or ##)
- Use _italic_ for secondary emphasis
- Use `code` for technical terms
- Keep messages concise - Telegram has a 4096 char limit

When generating DAILY/WEEKLY DIGESTS, use this clean format:

*Daily Digest* - [Date]

*Tasks* ([count])
• [Task name](notion_url) - Priority

*People* ([count])
• [Person](notion_url) - Context

*Research* ([count])
• [Title](notion_url) - Priority

*Links* ([count])
• [Title](notion_url) - Priority

_[count] total entries | Key theme: [theme]_

Rules for digests:
- ALWAYS include Notion links as markdown: [Title](url)
- NO emoji spam - use sparingly or not at all
- NO # or ## headers - Telegram doesn't render them
- Use bullet points (•) not dashes
- Group by category, show count in parentheses
- Keep each item to ONE line with clickable link
- End with a brief summary line in italics

When analyzing URLs/documents:
- Provide summary, key insights, actionable takeaways
- Estimate reading time
- Assign appropriate priority and tags
- Confirm saves with Notion URL
"""


def send_telegram_message(text, bot_token):
    """Send a message via Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    # Split long messages
    max_len = 4000
    chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]

    for chunk in chunks:
        payload = {
            "chat_id": CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Error sending message: {e}")


def send_capture_message(text):
    """Send via Capture Bot."""
    send_telegram_message(text, TELEGRAM_BOT_TOKEN)


def send_digest_message(text):
    """Send via Digest Bot."""
    send_telegram_message(text, DIGEST_BOT_TOKEN)


def get_telegram_updates(offset=None):
    """Get new messages from Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json()
    except Exception as e:
        logger.error(f"Error getting updates: {e}")
        return None


async def process_with_agent(message_text: str, context: str = "", model: str = None) -> str:
    """Process a message using Claude Agent SDK.

    Args:
        message_text: The user's message
        context: Additional context for the agent
        model: Optional model override (e.g., "opus" for high-quality analysis)
    """

    # Build the prompt with context
    prompt = message_text
    if context:
        prompt = f"{context}\n\nUser message: {message_text}"

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"second-brain": mcp_server},
        allowed_tools=[
            "mcp__second-brain__save_to_notion",
            "mcp__second-brain__save_deep_analysis",
            "mcp__second-brain__search_notion",
            "mcp__second-brain__get_recent_entries",
            "mcp__second-brain__send_telegram_message",
            "WebFetch",  # Built-in URL fetching
        ],
        max_turns=10,
        cwd=str(Path(__file__).parent),
        setting_sources=["project"],  # Load skills from .claude/skills/
        model=model,  # Use specified model (None = default, "opus" = high quality)
    )

    response_text = ""

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            async for message in client.receive_response():
                # Extract text from response messages
                if hasattr(message, 'result'):
                    response_text = message.result
                elif hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            response_text += block.text
    except Exception as e:
        import traceback
        logger.error(f"Agent error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        response_text = f"Error processing message: {str(e)}"

    return response_text


def is_qa_mode_active():
    """Check if Q&A mode is active and not expired (1 hour timeout)."""
    global deep_analysis_cache
    if not deep_analysis_cache["active"]:
        return False
    if deep_analysis_cache["timestamp"]:
        elapsed = datetime.now() - deep_analysis_cache["timestamp"]
        if elapsed > timedelta(hours=1):
            deep_analysis_cache["active"] = False
            return False
    return True


def exit_qa_mode():
    """Exit Q&A mode."""
    global deep_analysis_cache
    deep_analysis_cache = {
        "active": False,
        "title": None,
        "url": None,
        "summary": None,
        "timestamp": None
    }


def enter_qa_mode(title: str, url: str, summary: str):
    """Enter Q&A mode for a paper."""
    global deep_analysis_cache
    deep_analysis_cache = {
        "active": True,
        "title": title,
        "url": url,
        "summary": summary,
        "timestamp": datetime.now()
    }


def should_exit_qa_mode(message_text: str) -> bool:
    """Check if message should exit Q&A mode."""
    # Commands exit Q&A
    if message_text.startswith("/"):
        return True
    # Prefixes exit Q&A
    prefixes = ("t:", "task:", "p:", "person:", "r:", "research:", "l:", "link:", "d:", "deep:", "!")
    if message_text.lower().startswith(prefixes):
        return True
    # New URL exits Q&A
    if "http://" in message_text or "https://" in message_text:
        return True
    return False


async def handle_message(message_text: str):
    """Handle an incoming Telegram message."""
    global deep_analysis_cache
    logger.info(f"Processing: {message_text[:50]}...")

    # Handle commands
    if message_text.startswith("/"):
        cmd = message_text.lower().strip().split()[0]

        if cmd == "/help":
            help_text = """*Second Brain Agent Bot*

*Prefixes:*
`t:` Task | `p:` Person | `r:` Research | `l:` Link
`j:` Job analysis | `d:` Deep paper analysis
`rp:` Research potential | `rp-deep:` Deep research dive
`!` High priority | `?` Query

*Commands:*
`/daily` - Today's digest
`/weekly` - Weekly summary
`/exit` - Exit Q&A mode
`/help` - This message

*Examples:*
`t: Review proposal by Friday`
`d: https://arxiv.org/abs/...`
`rp: Using LLMs for theorem proving`
`j: https://lever.co/job/...`
`? What do I know about AI?`
"""
            send_capture_message(help_text)
            return

        elif cmd == "/exit":
            if is_qa_mode_active():
                title = deep_analysis_cache.get("title", "paper")
                exit_qa_mode()
                send_capture_message(f"_Exited Q&A mode for: {title}_")
            else:
                send_capture_message("_Not in Q&A mode._")
            return

        elif cmd in ["/daily", "/today"]:
            exit_qa_mode()  # Exit Q&A mode
            send_capture_message("Generating daily digest...")
            response = await process_with_agent(
                "Generate a daily digest of entries from the last 24 hours. "
                "Use get_recent_entries with days=1, then summarize by category."
            )
            send_digest_message(response)
            return

        elif cmd in ["/weekly", "/week"]:
            exit_qa_mode()  # Exit Q&A mode
            send_capture_message("Generating weekly summary...")
            response = await process_with_agent(
                "Generate a weekly summary of entries from the last 7 days. "
                "Use get_recent_entries with days=7, then provide insights and recommendations."
            )
            send_digest_message(response)
            return

        elif cmd == "/start":
            send_capture_message(
                "*Welcome to Second Brain Agent!*\n\n"
                "Send me anything to save it to your knowledge base.\n"
                "Type /help for more info."
            )
            return

    # Check if in Q&A mode and should stay
    if is_qa_mode_active() and not should_exit_qa_mode(message_text):
        # This is a follow-up question about the paper
        send_capture_message("_Answering from paper context..._")
        context = (
            f"The user is in Q&A mode for a paper they just analyzed.\n"
            f"Paper: {deep_analysis_cache['title']}\n"
            f"URL: {deep_analysis_cache['url']}\n"
            f"Summary: {deep_analysis_cache['summary']}\n\n"
            f"Answer their question based on the paper. If needed, use WebFetch to get more details from the URL.\n"
            f"End with: _Still in Q&A mode. Ask another question or /exit._"
        )
        response = await process_with_agent(message_text, context)
        if response:
            send_capture_message(response)
        return

    # Exit Q&A mode if needed
    if is_qa_mode_active() and should_exit_qa_mode(message_text):
        exit_qa_mode()

    # Determine context and model based on prefix
    context = ""
    is_deep_analysis = False
    use_model = None  # Default model

    if message_text.startswith("?"):
        context = "The user is querying their knowledge base. Search Notion and synthesize an answer."
    elif message_text.lower().startswith("rp-deep:"):
        # Two-stage analysis: Sonnet first, then Opus only if worth pursuing
        topic = message_text.split(":", 1)[1].strip() if ":" in message_text else message_text
        send_capture_message("_Stage 1: Quick assessment with Sonnet..._")

        # Stage 1: Quick assessment with Sonnet
        stage1_context = (
            "Do a QUICK research potential assessment. Be concise. "
            "Evaluate novelty, feasibility, and impact. "
            "End with a clear verdict: PURSUE, EXPLORE MORE, PIVOT, or PASS. "
            "Do NOT save to Notion yet - just analyze and give verdict."
        )
        stage1_response = await process_with_agent(f"rp: {topic}", stage1_context, model=None)

        # Check if worth pursuing with Opus
        verdict_lower = stage1_response.lower() if stage1_response else ""
        should_use_opus = "pursue" in verdict_lower or "explore more" in verdict_lower

        if should_use_opus:
            send_capture_message(f"_Verdict suggests potential! Stage 2: Deep dive with Opus (~$1-2)..._")
            use_model = "opus"
            context = (
                "The user wants a DEEP RESEARCH DIVE on this topic. Use the research-potential skill Phase 2 format. "
                "Include: foundational papers, recent advances, open problems, conference fit, collaboration opportunities, "
                "and a detailed research roadmap. Save to Notion using save_deep_analysis with category 'Research'. "
                f"Previous quick assessment:\n{stage1_response[:1000]}"
            )
        else:
            send_capture_message("_Verdict: Not worth deep dive. Saving quick assessment only._")
            # Send Stage 1 response and save to Notion
            if stage1_response:
                send_capture_message(stage1_response)
            context = (
                "Save this research assessment to Notion with category 'Research' and priority based on verdict. "
                f"Assessment:\n{stage1_response}"
            )
            response = await process_with_agent(f"Save research assessment for: {topic}", context)
            if response and not response.startswith("Message sent"):
                send_capture_message(response)
            return
    elif message_text.lower().startswith(("rp:", "research-potential:")):
        send_capture_message("_Analyzing research potential..._")
        context = (
            "The user wants to evaluate RESEARCH POTENTIAL of this topic/idea. Use the research-potential skill. "
            "Assess: novelty, feasibility, impact potential, quick literature pulse. "
            "Give a verdict (PURSUE/EXPLORE MORE/PIVOT/PASS) with next steps. "
            "Save to Notion with category 'Research' and appropriate priority based on verdict."
        )
    elif message_text.lower().startswith(("j:", "job:")):
        send_capture_message("_Analyzing job posting..._")
        context = (
            "The user wants to analyze a JOB POSTING. Use the job-analysis skill. "
            "Extract: company, role, key requirements, required skills, nice-to-have skills. "
            "Then suggest skills to develop based on gaps. Save to Notion with category 'Jobs'."
        )
    elif message_text.lower().startswith(("d:", "deep:")):
        is_deep_analysis = True
        send_capture_message("_Deep paper analysis..._")
        context = (
            "The user wants DEEP ANALYSIS of this paper/article. "
            "Use the deep-analysis skill format. "
            "After analysis, save to Notion using save_document_to_notion."
        )
    elif "http" in message_text:
        send_capture_message("_Processing URL..._")
        context = "The user shared a URL. Fetch the content, analyze it, and save to Notion with proper categorization."
    else:
        send_capture_message("_Processing..._")

    response = await process_with_agent(message_text, context, model=use_model)

    # If deep analysis, enter Q&A mode
    if is_deep_analysis and response:
        # Extract title from response (first line after "Title:")
        title = "Analyzed Paper"
        url = ""
        for word in message_text.split():
            if word.startswith("http"):
                url = word
                break

        # Try to extract title from response
        if "*Title:*" in response:
            try:
                title_line = response.split("*Title:*")[1].split("\n")[0].strip()
                title = title_line
            except:
                pass

        # Enter Q&A mode
        summary = response[:500] if response else ""
        enter_qa_mode(title, url, summary)
        logger.info(f"Entered Q&A mode for: {title}")

    # Send response (agent may have already sent via tool)
    if response and not response.startswith("Message sent"):
        send_capture_message(response)


def run_scheduler():
    """Run scheduled tasks."""
    while True:
        schedule.run_pending()
        time.sleep(60)


async def main_loop():
    """Main async bot loop."""
    global last_update_id

    logger.info("=" * 50)
    logger.info("Second Brain Agent Bot Starting...")
    logger.info("=" * 50)

    # Setup scheduled digests
    def sync_daily():
        async def _daily():
            response = await process_with_agent(
                "Generate a daily digest of entries from the last 24 hours. "
                "Use get_recent_entries with days=1, then summarize by category."
            )
            if response:
                send_digest_message(response)
        asyncio.run(_daily())

    def sync_weekly():
        async def _weekly():
            response = await process_with_agent(
                "Generate a weekly summary of entries from the last 7 days. "
                "Use get_recent_entries with days=7, then provide insights and recommendations."
            )
            if response:
                send_digest_message(response)
        asyncio.run(_weekly())

    schedule.every().day.at("08:00").do(sync_daily)
    schedule.every().sunday.at("18:00").do(sync_weekly)

    # Start scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Startup messages
    send_capture_message("*Agent Bot is online!*\n\nPowered by Claude Agent SDK.\nType /help for commands.")

    logger.info("Bot is running. Press Ctrl+C to stop.")

    # Main polling loop
    while True:
        try:
            updates = get_telegram_updates(
                offset=last_update_id + 1 if last_update_id else None
            )

            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    last_update_id = update["update_id"]

                    message = update.get("message", {})
                    chat_id = str(message.get("chat", {}).get("id", ""))

                    if chat_id == CHAT_ID:
                        # Handle document
                        document = message.get("document")
                        if document:
                            file_name = document.get("file_name", "unknown")
                            caption = message.get("caption", "")
                            await handle_message(
                                f"Analyze this document: {file_name}. Caption: {caption}"
                            )
                            continue

                        # Handle text
                        text = message.get("text", "")
                        if text:
                            await handle_message(text)

        except KeyboardInterrupt:
            logger.info("\nShutting down...")
            send_capture_message("_Agent Bot is offline._")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)


def main():
    """Entry point."""
    # Validate config
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_CODE")
    if not CHAT_ID:
        missing.append("CHAT_ID")
    if not os.environ.get("NOTION_TOKEN"):
        missing.append("NOTION_TOKEN")
    if not os.environ.get("NOTION_DATABASE_ID"):
        missing.append("NOTION_DATABASE_ID")

    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        return

    asyncio.run(main_loop())


if __name__ == "__main__":
    main()
