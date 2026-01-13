# Second Brain

A personal knowledge management system powered by Claude AI. Capture thoughts, analyze research papers, and query your knowledge base - all through Telegram.

## How It Works

```
Telegram → Claude AI → Notion
    ↑                     ↓
    ← Daily/Weekly Digests ←
```

1. **Capture**: Send messages, URLs, or PDFs to your Telegram bot
2. **Analyze**: Claude AI categorizes and extracts insights
3. **Store**: Structured data saved to Notion database
4. **Review**: Automated daily briefs and weekly summaries

## Features

| Feature | Description |
|---------|-------------|
| **Smart Categorization** | Auto-categorize into People, Research, Links, or Tasks |
| **Quick Prefixes** | `t:` `p:` `r:` `l:` for instant categorization |
| **URL Analysis** | Auto-fetch and summarize articles/papers |
| **PDF Processing** | Extract and analyze uploaded documents |
| **Deep Paper Analysis** | Comprehensive research paper breakdown with Q&A |
| **Knowledge Query** | Ask questions about your saved knowledge |
| **Daily Digest** | Morning briefing at 8:00 AM |
| **Weekly Summary** | Week review on Sunday 6:00 PM |

## Quick Start

### Prerequisites
- Python 3.9+
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
python bot.py
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
| `/deep <url>` | Deep analysis of paper/article |
| `/daily` | Generate today's digest |
| `/weekly` | Generate weekly summary |
| `/exit` | Exit paper Q&A mode |
| `/help` | Show all commands |

### Deep Analysis + Q&A
```
You: d: https://arxiv.org/abs/2301.00001
Bot: [Comprehensive analysis in 3 messages]
     Paper loaded for Q&A...

You: What's the main algorithm?
Bot: [Answer based on paper content]

You: /exit
Bot: Exited paper Q&A mode.
```

## Architecture

```
second-brain/
├── bot.py              # Main entry point, command routing
├── config.py           # Environment vars, constants
├── telegram.py         # Telegram API functions
├── claude_ai.py        # AI prompts and Claude API
├── notion.py           # Notion API functions
├── processors.py       # Message/URL/document processing
├── query.py            # Knowledge base queries
├── digest.py           # Daily/weekly summaries
├── requirements.txt    # Python dependencies
└── docs/               # Setup guides
```

## Cloud Deployment Options

### Option 1: Railway (Recommended)
Simple deployment with free tier available.

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Add environment variables in Railway dashboard.

### Option 2: Render
Free tier with automatic deploys from GitHub.

1. Connect GitHub repo to [Render](https://render.com)
2. Create new "Background Worker"
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python bot.py`
5. Add environment variables

### Option 3: Fly.io
Global deployment with generous free tier.

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly secrets set TELEGRAM_BOT_CODE=xxx ANTHROPIC_API_KEY=xxx ...
fly deploy
```

### Option 4: AWS EC2 / DigitalOcean
For full control, use a small VPS:

```bash
# On server
git clone https://github.com/prashantkul/second-brain.git
cd second-brain
pip install -r requirements.txt

# Run with systemd or screen
screen -S secondbrain
python bot.py
# Ctrl+A, D to detach
```

### Option 5: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
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

**Claude API errors?**
- Verify API key is valid
- Check you have API credits

**PDF extraction issues?**
- Scanned PDFs won't work (no OCR)
- Very large PDFs may be truncated

## License

MIT
