# Second Brain

A personal knowledge management system powered by Claude Agent SDK. Capture thoughts, analyze research papers, and query your knowledge base - all through Telegram.

## Introduction

Second Brain is a Telegram bot that serves as your intelligent knowledge companion. It captures thoughts, links, research, and tasks directly from Telegram conversations and stores everything in Notion with automatic categorization. Built on the Claude Agent SDK with a skills-based architecture, it goes beyond simple note-taking to provide deep analysis of research papers, job posting insights with personalized skill recommendations, and automated daily and weekly digests to keep you informed.

## Benefits

- **Frictionless Capture**: Send anything to Telegram and let the AI handle categorization and storage
- **Intelligent Organization**: Automatic tagging and structuring in Notion eliminates manual filing
- **Research Acceleration**: Deep analysis extracts key insights from papers and articles
- **Career Intelligence**: Job posting analysis identifies skill gaps and growth opportunities
- **Proactive Recall**: Scheduled digests surface relevant knowledge when you need it
- **Natural Interaction**: Query your entire knowledge base using conversational language

## How It Works

```
Telegram → Claude Agent SDK → Notion
    ↑                           ↓
    ← Daily/Weekly Digests ←
```

1. **Capture**: Send messages, URLs, or PDFs to your Telegram bot
2. **Analyze**: Claude Agent autonomously categorizes and extracts insights
3. **Store**: Structured data saved to Notion database
4. **Review**: Automated daily briefs and weekly summaries

## Features

| Feature | Description |
|---------|-------------|
| **Smart Categorization** | Auto-categorize into People, Research, Links, or Tasks |
| **Quick Prefixes** | `t:` `p:` `r:` `l:` for instant categorization |
| **URL Analysis** | Auto-fetch and summarize articles/papers |
| **Deep Paper Analysis** | Comprehensive research paper breakdown |
| **Knowledge Query** | Ask questions about your saved knowledge |
| **Daily Digest** | Morning briefing at 8:00 AM |
| **Weekly Summary** | Week review on Sunday 6:00 PM |

## Quick Start

### Prerequisites
- Python 3.9+
- [Claude Code CLI](https://claude.ai/code) installed
- [Notion account](https://notion.so) with API access
- [Telegram account](https://telegram.org)
- [Anthropic API key](https://console.anthropic.com)

### Installation

```bash
# Clone the repository
git clone https://github.com/prashantkul/second-brain.git
cd second-brain

# Create conda environment
conda create -n second-brain python=3.11
conda activate second-brain

# Install dependencies
pip install -r requirements.txt

# Install Claude Code CLI (required for Agent SDK)
curl -fsSL https://claude.ai/install.sh | bash

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` with your credentials:

```env
TELEGRAM_BOT_CODE=your_capture_bot_token
TELEGRAM_DIGEST_BOT_TOKEN=your_digest_bot_token
CHAT_ID=your_telegram_chat_id
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Setup Guides
- [Notion Setup](docs/notion-setup.md) - Create database and integration
- [Telegram Setup](docs/telegram-setup.md) - Create bots and get tokens

### Run

```bash
conda activate second-brain
python agent_bot.py
```

## Usage

### Prefixes
| Prefix | Category | Example |
|--------|----------|---------|
| `t:` | Task | `t: Review proposal by Friday` |
| `p:` | Person | `p: John, CTO at Acme` |
| `r:` | Research | `r: Ideas about AI agents` |
| `l:` | Link | `l: Check out example.com` |
| `d:` | Deep Analysis | `d: https://arxiv.org/abs/...` |
| `!` | High Priority | `!t: Urgent deadline` |
| `?` | Query Brain | `? What do I know about AI?` |

### Commands
| Command | Description |
|---------|-------------|
| `/daily` | Generate today's digest |
| `/weekly` | Generate weekly summary |
| `/help` | Show all commands |
| `/start` | Welcome message |

## Architecture

```
second-brain/
├── agent_bot.py           # Main entry point (Agent SDK)
├── tools.py               # MCP tools for Notion & Telegram
├── .claude/
│   └── skills/
│       └── SECOND_BRAIN.md  # Agent skill definition
├── requirements.txt       # Python dependencies
├── scripts/               # Setup utilities
├── templates/             # Notion database template
└── docs/                  # Setup guides
```

### Agent SDK Benefits
- **Autonomous execution**: Claude decides which tools to use
- **Built-in tools**: WebFetch, file operations, search
- **MCP integration**: Custom tools via Model Context Protocol
- **Simplified code**: ~400 lines vs ~1400 lines (direct API)

## Cloud Deployment Options

### Option 1: Railway (Recommended)
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```
Add environment variables in Railway dashboard.

### Option 2: Render
1. Connect GitHub repo to [Render](https://render.com)
2. Create new "Background Worker"
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python agent_bot.py`
5. Add environment variables

### Option 3: Fly.io
```bash
curl -L https://fly.io/install.sh | sh
fly launch
fly secrets set TELEGRAM_BOT_CODE=xxx ANTHROPIC_API_KEY=xxx ...
fly deploy
```

### Option 4: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN curl -fsSL https://claude.ai/install.sh | bash
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "agent_bot.py"]
```

```bash
docker build -t second-brain .
docker run -d --env-file .env second-brain
```

## Troubleshooting

**Bot not responding?**
- Check bot token is correct
- Ensure you've started a chat with the bot (`/start`)
- Verify CHAT_ID matches your Telegram chat

**Notion errors?**
- Verify integration has access to database
- Check database ID is correct (not the page URL)

**Agent SDK errors?**
- Ensure Claude Code CLI is installed (`claude --version`)
- Verify ANTHROPIC_API_KEY is set

## License

MIT
