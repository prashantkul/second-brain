# Second Brain - Claude Context

This file provides context for Claude sessions working on this project.

## Project Overview

A Telegram bot that acts as a "Second Brain" - capturing thoughts, links, research, and tasks, storing them in Notion, and providing intelligent analysis using Claude.

## Architecture

### Current Branch: `feature/agent-sdk`

The bot uses **Claude Agent SDK** with a skills-based architecture:

- **`agent_bot.py`** - Main entry point, Telegram polling, message routing
- **`tools.py`** - MCP (Model Context Protocol) tools for Notion/Telegram integration
- **`.claude/skills/`** - Skill definitions that guide Claude's behavior

### Key Components

1. **ClaudeSDKClient** - Used in `process_with_agent()` function
   - Import: `from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions`
   - Pattern: `async with ClaudeSDKClient(options=options) as client:`

2. **MCP Server** - Created in `tools.py` via `create_second_brain_server()`
   - Tools: `save_to_notion`, `save_deep_analysis`, `search_notion`, `get_recent_entries`, `send_telegram_message`

3. **Skills** (in `.claude/skills/`):
   - `SECOND_BRAIN.md` - Main categorization skill (t:, p:, r:, l: prefixes)
   - `DEEP_ANALYSIS.md` - Research paper analysis (d: prefix)
   - `JOB_ANALYSIS.md` - Job posting analysis (j: prefix)

## How to Test

### Environment Setup

```bash
# Use conda environment
conda activate second-brain

# Or use direct python path
/Users/prashantkulkarni/anaconda3/envs/second-brain/bin/python
```

### Running the Bot

```bash
# Start bot (from project directory)
conda activate second-brain
python agent_bot.py

# Or run in background
nohup python agent_bot.py > /tmp/agent_bot.log 2>&1 &

# Check logs
tail -f /tmp/agent_bot.log
```

### Stopping the Bot

```bash
pkill -9 -f "agent_bot.py"
```

### Testing Features via Telegram

| Feature | Command/Prefix | Example |
|---------|---------------|---------|
| Task | `t:` or `task:` | `t: Review proposal by Friday` |
| Person | `p:` or `person:` | `p: Met John from Acme Corp` |
| Research | `r:` or `research:` | `r: Look into vector databases` |
| Link | `l:` or `link:` | `l: https://example.com` |
| Job Analysis | `j:` or `job:` | `j: https://lever.co/job/...` |
| Deep Analysis | `d:` or `deep:` | `d: https://arxiv.org/abs/...` |
| Query | `?` | `? What do I know about AI?` |
| High Priority | `!` | `! Urgent: server down` |
| Daily Digest | `/daily` | - |
| Weekly Digest | `/weekly` | - |
| View Reminders | `/reminders` | - |
| Exit Q&A Mode | `/exit` | - |
| Help | `/help` | - |

### Task Due Dates & Reminders

Tasks support natural language due dates:
```
t: Review proposal by Friday 3pm
t: Call John in 2 hours
t: Submit report tomorrow morning
```

Reminders are sent automatically:
- 1 day before due time
- 1 hour before due time
- At due time

View upcoming tasks with `/reminders`.

### Testing Deep Analysis

1. Send: `d: https://arxiv.org/abs/2403.05181` (or any paper URL)
2. Bot enters Q&A mode after analysis
3. Ask follow-up questions about the paper
4. Send `/exit` to leave Q&A mode

### Testing Job Analysis

1. Send: `j: https://jobs.lever.co/company/role` (job posting URL)
2. Or paste job description: `job: [paste text]`
3. Bot extracts requirements, suggests skills to develop, saves to Notion

## Common Issues & Fixes

### Notion API Errors

**Error: "body.children.length should be ≤ 100"**
- Cause: Too many blocks in page body
- Fix: Limit list items, truncate children array to 100

**Error: Tags showing as individual characters**
- Cause: String being iterated instead of split
- Fix: Check `isinstance(tags, str)` and split by comma

### Bot Connection Issues

**Error: "ProcessTransport is not ready for writing"**
- Cause: Wrong SDK usage pattern
- Fix: Use `async with ClaudeSDKClient(options) as client:` pattern

### Telegram Formatting

- Use `*bold*` not `# headers` (Telegram doesn't render markdown headers)
- Use `•` bullet points not `-` dashes
- Keep messages under 4096 chars (auto-chunking in `send_telegram_message`)

## Environment Variables

Required in `.env`:
```
TELEGRAM_BOT_CODE=<capture bot token>
TELEGRAM_DIGEST_BOT_TOKEN=<digest bot token>
CHAT_ID=<your telegram chat id>
NOTION_TOKEN=<notion integration token>
NOTION_DATABASE_ID=<notion database id>
ANTHROPIC_API_KEY=<claude api key>
```

## Notion Schema

The Notion database should have these properties:
- **Title** (title)
- **Category** (select): Tasks, People, Research, Links, Jobs
- **Priority** (select): High, Medium, Low
- **Status** (select): New, In Progress, Done
- **Tags** (multi-select)
- **Source URL** (url)
- **Description** (rich text)

## Two Telegram Bots

1. **Capture Bot** (`TELEGRAM_BOT_CODE`) - Receives user messages, sends confirmations
2. **Digest Bot** (`TELEGRAM_DIGEST_BOT_TOKEN`) - Sends daily/weekly digests

## Scheduled Tasks

- Daily digest: 8:00 AM
- Weekly digest: Sunday 6:00 PM

## Test Harness (For Claude Code)

A dedicated test bot allows Claude Code to test changes without affecting the main bot.

### Test Bot Credentials (in .env)
```
TELEGRAM_TEST_BOT_TOKEN=<test bot token>
TEST_CHAT_ID=<test chat id>
```

### Using the Test Harness

```bash
# Send a message via test bot (appears in user's Telegram)
python test_harness.py send "Hello from test!"

# Test agent processing directly (no Telegram, just agent)
python test_harness.py test-agent "? What tasks do I have?"

# Test job analysis
python test_harness.py test-jobs "https://lever.co/job/..."

# Test deep analysis
python test_harness.py test-deep "https://arxiv.org/abs/..."

# Check for responses
python test_harness.py check-response

# Clean up test entries from Notion (deletes entries from last N hours)
python test_harness.py cleanup 1
```

### When to Use

- **`test-agent`**: Quick tests of agent logic, no Telegram involved
- **`send`**: Full integration test through Telegram
- **`test-jobs`/`test-deep`**: Test specific features

## Notion Cleanup Script

A utility script to maintain database hygiene.

### Commands

```bash
# Show database statistics and health check
python notion_cleanup.py stats

# Find and remove duplicate entries (by title similarity)
python notion_cleanup.py duplicates --dry-run
python notion_cleanup.py duplicates              # Interactive confirm

# Find and remove test data (entries with "test", "sample", etc.)
python notion_cleanup.py test-data --dry-run
python notion_cleanup.py test-data

# Archive old completed tasks (default: 30+ days)
python notion_cleanup.py completed-tasks --dry-run
python notion_cleanup.py completed-tasks --days 60

# Run all cleanups at once
python notion_cleanup.py all --dry-run
python notion_cleanup.py all
```

### Options

- `--dry-run`: Preview what would be deleted without making changes
- `--threshold 0.85`: Similarity threshold for duplicate detection (0-1)
- `--days 30`: Age threshold for completed tasks

## Git Workflow

- Main development on `feature/agent-sdk` branch
- Old modular code was removed (bot.py, config.py, telegram.py, etc.)
- Current architecture is single-file `agent_bot.py` + `tools.py`
