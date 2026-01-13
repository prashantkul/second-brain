# Telegram Bot Setup Guide

## Step 1: Create Your Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat and send: `/newbot`
3. Follow the prompts:
   - **Bot name**: "Second Brain Daily" (display name)
   - **Username**: must end in `bot`, e.g., `mysecondbrain_bot`
4. BotFather will reply with your **Bot Token**:
   ```
   Use this token to access the HTTP API:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
5. **Save this token** - you'll need it for Zapier

## Step 2: Start a Chat with Your Bot

**Important**: You must message your bot first before it can message you.

1. Click the link BotFather provided, or search for your bot
2. Click **"Start"** or send any message
3. Your bot is now ready to receive messages from Zapier

## Step 3: Get Your Chat ID

Zapier needs your Chat ID to send messages to you.

### Method 1: Using @userinfobot
1. Search for **@userinfobot** on Telegram
2. Start a chat and send any message
3. It will reply with your user info including **Id**
4. This is your Chat ID

### Method 2: Using @RawDataBot
1. Search for **@RawDataBot** on Telegram
2. Forward any message to it
3. Look for `"from": {"id": 123456789}`
4. That number is your Chat ID

### Method 3: Using the API
1. Send a message to your bot
2. Open this URL in browser (replace TOKEN with your bot token):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Look for `"chat":{"id":123456789}`
4. That's your Chat ID

## Step 4: Configure in Zapier

1. In Zapier, add a **Telegram Bot** action
2. Connect using your **Bot Token**
3. For "Chat ID", enter your Chat ID from Step 3
4. Test the connection - you should receive a message

## Customizing Your Bot (Optional)

### Set a Description
Chat with @BotFather:
```
/setdescription
@your_bot_username
Your daily Second Brain digest - tasks, people, links, and insights.
```

### Set a Profile Picture
```
/setuserpic
@your_bot_username
[Upload an image]
```

### Set Commands (Optional)
```
/setcommands
@your_bot_username
today - Get today's summary
week - Get weekly review
status - Check system status
```

## Message Formatting

Telegram supports Markdown in messages. The daily digest will use:
- **Bold**: `*bold text*`
- _Italic_: `_italic text_`
- `Code`: `` `code` ``
- [Links]: `[text](url)`

## Troubleshooting

**Bot not responding?**
- Make sure you clicked "Start" on the bot
- Verify the bot token is correct
- Check that Zapier has the right Chat ID

**"Chat not found" error**
- You must message the bot before it can message you
- Double-check your Chat ID

**Messages not formatted correctly**
- Ensure Telegram action in Zapier uses "Markdown" parse mode
- Check for unescaped special characters

## Quick Reference

```
Bot Token: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
Chat ID: 123456789
Bot Username: @mysecondbrain_bot
```

Keep these for Zapier setup!

## Group Chat (Alternative)

If you want digests in a group chat instead:

1. Create a Telegram group
2. Add your bot to the group
3. Make the bot an admin (so it can post)
4. Get the group Chat ID (will be negative, like -1001234567890)
5. Use this group Chat ID in Zapier
