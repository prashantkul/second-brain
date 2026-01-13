# Notion Setup Guide

## Step 1: Create a Notion Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Configure:
   - **Name**: "Second Brain"
   - **Associated workspace**: Select your workspace
   - **Capabilities**:
     - Read content ✓
     - Update content ✓
     - Insert content ✓
4. Click **Submit**
5. Copy the **Internal Integration Token** (starts with `secret_`)

> Save this token - you'll need it for Zapier

## Step 2: Create the Database

### Option A: Manual Setup

1. Create a new page in Notion
2. Type `/database` and select **"Database - Full page"**
3. Name it **"Second Brain"**
4. Add these properties:

| Property | Type | Configuration |
|----------|------|---------------|
| Title | Title | (default) |
| Category | Select | Options: People, Research, Links, Tasks |
| Description | Text | - |
| Source | URL | - |
| Status | Select | Options: New, In Progress, Done |
| Priority | Select | Options: High, Medium, Low |
| Due Date | Date | - |
| Person Name | Text | - |
| Tags | Multi-select | Options: follow-up, networking, learning, tool, article, idea, urgent, reference |
| Created | Created time | (auto) |

### Option B: Duplicate Template

1. Open this template: [Notion Template Link - create your own]
2. Click **"Duplicate"** in the top right
3. Select your workspace

## Step 3: Connect Integration to Database

**Important**: The integration needs explicit access to your database.

1. Open your Second Brain database
2. Click the **"..."** menu (top right)
3. Click **"Connections"** → **"Add connections"**
4. Search for **"Second Brain"** (your integration name)
5. Click to connect

## Step 4: Get Database ID

You'll need the database ID for Zapier:

1. Open your database in Notion
2. Look at the URL:
   ```
   https://notion.so/your-workspace/DATABASE_ID?v=...
   ```
3. The database ID is the 32-character string after your workspace name
4. Example: `https://notion.so/myworkspace/a1b2c3d4e5f6...` → ID is `a1b2c3d4e5f6...`

## Step 5: Test the Connection

Before moving to Zapier, verify your integration works:

1. Go to your database
2. Manually add a test entry
3. If you can add entries, the setup is correct

## Database Views (Recommended)

Create these views for better organization:

### All Entries (Table)
- Default view showing everything
- Sort by Created (newest first)

### By Category (Board)
- Kanban view grouped by Category
- Great for visual overview

### Tasks (Table)
- Filter: Category = Tasks
- Sort by Due Date (ascending)
- Shows only tasks with deadlines first

### People (Gallery)
- Filter: Category = People
- Shows contacts in card format

## Troubleshooting

**"Integration not found"**
- Make sure you created the integration in the correct workspace
- Check that you copied the full token

**"Cannot access database"**
- You must explicitly share the database with the integration
- Go to database → ... → Connections → Add your integration

**Zapier can't find database**
- Verify the database ID is correct
- Ensure integration has access to the database
- Try disconnecting and reconnecting Notion in Zapier

## Quick Reference

```
Integration Token: secret_xxxxxxxxxxxxxxxxxxxxxxxx
Database ID: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Keep these safe for Zapier setup!
