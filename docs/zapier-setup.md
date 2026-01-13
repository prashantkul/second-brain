# Zapier Setup Guide

## Prerequisites

Before starting, ensure you have:
- [ ] Notion Integration Token ([see guide](notion-setup.md))
- [ ] Notion Database ID ([see guide](notion-setup.md))
- [ ] Telegram Bot Token ([see guide](telegram-setup.md))
- [ ] Telegram Chat ID ([see guide](telegram-setup.md))
- [ ] Zapier account (Starter plan or higher)

---

## Zap 1: Google Chat → Notion Ingestion

This Zap captures messages and saves them to Notion.

### Step 1: Trigger - Google Chat

1. Click **"Create Zap"**
2. Search for **"Google Chat"**
3. Select trigger: **"New Message Posted to Space"**
4. Connect your Google Workspace account
5. Select the Space you want to monitor
6. Test the trigger

### Step 2: AI Analysis

1. Click **"+"** to add a step
2. Search for **"ChatGPT"** (or your preferred AI)
3. Select **"Conversation"**
4. Connect your OpenAI account
5. Configure:
   - **User Message**: Copy the prompt from `/prompts/categorize.txt`
   - Replace `{{message_text}}` with the Google Chat message field
   - **Model**: gpt-4 or gpt-3.5-turbo
6. Test the step

### Step 3: Parse JSON (Code Step)

1. Click **"+"** to add a step
2. Search for **"Code by Zapier"**
3. Select **"Run JavaScript"**
4. Input Data:
   - `ai_response`: Map to ChatGPT response
5. Code:
   ```javascript
   const response = inputData.ai_response;
   try {
     const data = JSON.parse(response);
     return data;
   } catch (e) {
     return {
       category: "Research",
       title: "Uncategorized item",
       description: response,
       priority: "Low",
       person_name: "",
       due_date: "",
       tags: "",
       action_items: ""
     };
   }
   ```
6. Test the step

### Step 4: Create Notion Entry

1. Click **"+"** to add a step
2. Search for **"Notion"**
3. Select **"Create Database Item"**
4. Connect your Notion account
5. Select your **"Second Brain"** database
6. Map fields:

| Notion Property | Zapier Field |
|-----------------|--------------|
| Title | `title` from Code step |
| Category | `category` from Code step |
| Description | `description` from Code step |
| Priority | `priority` from Code step |
| Person Name | `person_name` from Code step |
| Due Date | `due_date` from Code step |
| Tags | `tags` from Code step |
| Status | Set to "New" |
| Source | Google Chat message link |

7. Test the step
8. Turn on the Zap

---

## Zap 2: Daily Telegram Digest

This Zap sends your morning briefing via Telegram.

### Step 1: Trigger - Schedule

1. Click **"Create Zap"**
2. Search for **"Schedule by Zapier"**
3. Select **"Every Day"**
4. Set time: **8:00 AM** (your timezone)
5. Test trigger

### Step 2: Query Notion

1. Click **"+"** to add a step
2. Search for **"Notion"**
3. Select **"Find Database Item"**
4. Connect Notion
5. Select **"Second Brain"** database
6. Add filter:
   - Created time is after: `{{zap_meta_human_now}} - 1 day`
   - Or use "Last 24 hours" option if available
7. Test step

### Step 3: Loop (if multiple entries)

1. Click **"+"** to add a step
2. Search for **"Looping by Zapier"**
3. Select **"Create Loop From Line Items"**
4. Map the Notion results
5. This creates one output with all entries

### Step 4: AI Summary

1. Click **"+"** to add a step
2. Search for **"ChatGPT"**
3. Select **"Conversation"**
4. Configure:
   - **User Message**: Copy prompt from `/prompts/daily-digest.txt`
   - Replace `{{notion_entries}}` with loop output
5. Test step

### Step 5: Send Telegram Message

1. Click **"+"** to add a step
2. Search for **"Telegram Bot"**
3. Select **"Send Message"**
4. Connect with your Bot Token
5. Configure:
   - **Chat ID**: Your personal Chat ID
   - **Text**: AI summary output
   - **Parse Mode**: Markdown
6. Test step
7. Turn on the Zap

---

## Zap 3: Weekly Email Summary

This Zap sends your weekly review via email.

### Step 1: Trigger - Schedule

1. Click **"Create Zap"**
2. Search for **"Schedule by Zapier"**
3. Select **"Every Week"**
4. Set: **Sunday at 6:00 PM**
5. Test trigger

### Step 2: Query Notion (7 days)

1. Add **"Notion"** → **"Find Database Item"**
2. Filter: Created time is after `{{zap_meta_human_now}} - 7 days`
3. Test step

### Step 3: Loop & Format

1. Add **"Looping by Zapier"** → **"Create Loop From Line Items"**
2. Map all Notion entries
3. Test step

### Step 4: AI Summary

1. Add **"ChatGPT"** → **"Conversation"**
2. Use prompt from `/prompts/weekly-summary.txt`
3. Replace `{{notion_entries}}` with loop output
4. Test step

### Step 5: Send Email

1. Add **"Gmail"** (or your email service)
2. Select **"Send Email"**
3. Configure:
   - **To**: Your email address
   - **Subject**: "Second Brain - Week in Review"
   - **Body**: AI summary output (HTML format)
4. Test step
5. Turn on the Zap

---

## Testing Your Setup

### Test 1: Ingestion
1. Send a message in your monitored Google Chat space:
   ```
   Need to follow up with John about the Q1 proposal by Friday.
   Also check out this tool: https://example.com/tool
   ```
2. Wait 1-2 minutes
3. Check Notion - should see 1-2 new entries

### Test 2: Daily Digest
1. In Zapier, go to Zap 2
2. Click "Run" to test manually
3. Check Telegram - should receive digest

### Test 3: Weekly Summary
1. In Zapier, go to Zap 3
2. Click "Run" to test manually
3. Check email - should receive summary

---

## Troubleshooting

### "No items found" in Notion query
- Verify database has entries within the time range
- Check the date filter formula
- Try removing the filter and testing

### AI response isn't valid JSON
- Add error handling in the Code step
- Check that the prompt explicitly asks for JSON
- Try a more capable model (gpt-4)

### Telegram message not received
- Verify Chat ID is correct
- Ensure you've messaged the bot first
- Check bot token is valid

### Zap keeps failing
- Check Zapier task history for error details
- Verify all connections are active
- Test each step individually

---

## Cost Optimization

### Reduce Zapier Tasks
- Use filters to only process relevant messages
- Batch Notion queries where possible
- Run digests less frequently if needed

### Estimated Monthly Usage
- Ingestion: ~50-100 tasks (depends on message volume)
- Daily Digest: ~60 tasks (2 per day × 30 days)
- Weekly Summary: ~8 tasks (2 per week × 4 weeks)
- **Total**: ~120-170 tasks/month (fits in Starter plan)

---

## Quick Reference

| Zap | Trigger | Key Apps |
|-----|---------|----------|
| Ingestion | Google Chat message | Chat → ChatGPT → Code → Notion |
| Daily | 8:00 AM | Schedule → Notion → ChatGPT → Telegram |
| Weekly | Sunday 6 PM | Schedule → Notion → ChatGPT → Gmail |
