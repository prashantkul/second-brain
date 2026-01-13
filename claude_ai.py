"""
Claude AI integration - prompts and API calls for Second Brain Bot.
"""

import json

from config import anthropic_client, logger

# =============================================================================
# Prompts
# =============================================================================

CATEGORIZE_PROMPT = """You are analyzing a message to extract and categorize information for a personal knowledge management system.

Analyze this message and extract structured information:

---
MESSAGE:
{message}
---

Categorize into ONE of these categories:
- People: Information about a person, contact details, networking, meetings
- Research: Ideas, concepts, articles, things to learn or explore
- Links: URLs, tools, resources, websites to check out
- Tasks: Action items, todos, commitments, deadlines

Return ONLY a valid JSON object (no markdown, no explanation) with these fields:

{{
  "category": "People|Research|Links|Tasks",
  "title": "Brief descriptive title (max 50 characters)",
  "description": "Key details and context from the message",
  "priority": "High|Medium|Low",
  "person_name": "Name of person if category is People, otherwise empty string",
  "due_date": "YYYY-MM-DD if deadline mentioned, otherwise empty string",
  "tags": ["relevant", "keywords"],
  "action_items": "Any specific follow-up actions needed"
}}

Guidelines:
- If message contains a URL, likely category is Links unless it's about a person
- If message mentions "need to", "should", "must", "deadline" → likely Tasks
- If message mentions a person's name with context about them → People
- Default to Research for general information or ideas
- Set priority to High if urgent language used, Low for "sometime" or "maybe"
"""


DOCUMENT_ANALYSIS_PROMPT = """You are analyzing a research paper/document for a busy professional. Provide a comprehensive but actionable analysis.

DOCUMENT TITLE: {title}

DOCUMENT CONTENT:
{content}

Provide analysis in this JSON format:

{{
  "title": "Clear, descriptive title for this document",
  "category": "Research",
  "summary": "3-5 sentence executive summary of the key findings/arguments",
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "actionable_takeaways": ["specific action 1", "specific action 2", "specific action 3"],
  "relevance_assessment": "How this might relate to work in tech/business (2-3 sentences)",
  "time_estimates": {{
    "quick_skim": "X minutes - what you'll get",
    "thorough_read": "X minutes - what you'll get",
    "deep_study": "X minutes - what you'll get"
  }},
  "priority": "High|Medium|Low",
  "tags": ["relevant", "keywords"],
  "follow_up_questions": ["question to explore 1", "question to explore 2"],
  "related_concepts": ["concept 1", "concept 2"]
}}

Guidelines:
- Be specific and actionable, not generic
- Time estimates should be realistic based on document length/complexity
- Priority should be High if groundbreaking/urgent, Medium if useful, Low if nice-to-know
- Relevance should connect to practical applications
"""


QUERY_PROMPT = """You are a helpful assistant that answers questions based on the user's personal knowledge base (their "Second Brain").

The user is asking: {query}

Here are the relevant entries from their knowledge base:

{entries}

Instructions:
1. Search through the entries to find information relevant to the user's question
2. Synthesize a helpful answer based ONLY on what's in their knowledge base
3. If you find relevant entries, mention them by title
4. If nothing is relevant, say "I couldn't find anything in your Second Brain about this"
5. Be concise but helpful
6. At the end, list the most relevant entry titles (max 3) that the user might want to review

Format your response for Telegram (use markdown: *bold*, _italic_).
"""


DAILY_PROMPT = """Create a morning briefing from today's Second Brain entries.

ENTRIES FROM LAST 24 HOURS:
{entries}

Format for Telegram (keep under 800 characters, use markdown):

*TODAY'S PRIORITIES*
- Top tasks (High priority first)

*PEOPLE TO FOLLOW UP*
- Names and brief context

*LINKS TO REVIEW*
- Quick list

*QUICK INSIGHTS*
- One key research item

Be extremely concise. Skip empty categories. If no entries, say "Nothing new in the last 24 hours."
"""


WEEKLY_PROMPT = """Create a weekly review from this week's Second Brain entries.

ENTRIES FROM LAST 7 DAYS:
{entries}

Format for Telegram (use markdown, be comprehensive but concise):

*WEEK HIGHLIGHTS*
Key accomplishments

*PEOPLE*
Contacts and follow-ups needed

*RESEARCH THEMES*
Patterns in what you explored

*PENDING TASKS*
Carryover items

*FOCUS FOR NEXT WEEK*
Top 3 recommendations

Keep total under 1500 characters.
"""


DEEP_ANALYSIS_PROMPT = """You are an expert research analyst providing comprehensive paper analysis for a technical professional.

PAPER TITLE: {title}

PAPER CONTENT:
{content}

Provide a thorough analysis in this JSON format:

{{
  "title": "Paper title",
  "authors_and_affiliation": "Authors and their institutions if identifiable",

  "academic_analysis": {{
    "problem_statement": "What problem does this paper address? (2-3 sentences)",
    "methodology": "How do they approach it? Key techniques/methods used (3-4 sentences)",
    "key_contributions": ["contribution 1", "contribution 2", "contribution 3"],
    "results_summary": "Main findings and their significance (2-3 sentences)",
    "limitations": ["limitation 1", "limitation 2"],
    "future_work": ["suggested direction 1", "suggested direction 2"],
    "technical_depth": "High|Medium|Low"
  }},

  "practical_analysis": {{
    "tldr": "One-sentence summary a busy engineer would appreciate",
    "why_it_matters": "Real-world implications (2-3 sentences)",
    "implementation_complexity": "Easy|Medium|Hard",
    "implementation_notes": "Key considerations if you wanted to implement this",
    "use_cases": ["practical application 1", "practical application 2", "practical application 3"],
    "code_or_pseudocode": "Any pseudocode or key algorithm steps worth noting (or 'N/A')"
  }},

  "meta": {{
    "paper_type": "Empirical|Theoretical|Survey|System|Benchmark",
    "field": "ML|NLP|CV|Systems|Security|Other",
    "prerequisites": ["concept you should know 1", "concept 2"],
    "related_papers_mentioned": ["paper 1", "paper 2"],
    "time_estimates": {{
      "skim": "X min",
      "understand": "X min",
      "deep_study": "X min"
    }},
    "priority": "High|Medium|Low",
    "tags": ["tag1", "tag2", "tag3"]
  }},

  "questions_to_explore": ["thought-provoking question 1", "question 2", "question 3"]
}}

Guidelines:
- Be specific and actionable, not generic
- Technical depth: High = heavy math/theory, Medium = some technical details, Low = accessible
- Implementation complexity: Easy = can prototype in a day, Medium = week of work, Hard = significant engineering
- Priority: High = groundbreaking/must-read, Medium = useful, Low = nice-to-know
"""


PAPER_QA_PROMPT = """You are answering a follow-up question about a research paper the user just analyzed.

PAPER TITLE: {title}

PAPER CONTENT (for reference):
{content}

PREVIOUS ANALYSIS SUMMARY:
{analysis_summary}

USER QUESTION: {question}

Instructions:
1. Answer the question based on the paper content
2. Be specific and cite relevant parts of the paper when possible
3. If the question cannot be answered from the paper, say so
4. Keep response concise but thorough

Format for Telegram (use *bold*, _italic_). Keep under 1000 characters.
"""


# =============================================================================
# Claude API Functions
# =============================================================================

def _parse_json_response(result_text):
    """Parse JSON from Claude response, handling markdown code blocks."""
    if result_text.startswith("```"):
        result_text = result_text.split("```")[1]
        if result_text.startswith("json"):
            result_text = result_text[4:]
    return json.loads(result_text)


def categorize_with_claude(message_text):
    """Use Claude to categorize and extract info from a message."""
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": CATEGORIZE_PROMPT.format(message=message_text)}
            ]
        )

        result_text = response.content[0].text.strip()
        return _parse_json_response(result_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return None
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None


def analyze_document_with_claude(content, title="Untitled Document"):
    """Use Claude to analyze a document and extract structured insights."""
    try:
        # Truncate content if too long (Claude has context limits)
        max_chars = 100000  # ~25k tokens
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[Document truncated due to length...]"

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": DOCUMENT_ANALYSIS_PROMPT.format(title=title, content=content)}
            ]
        )

        result_text = response.content[0].text.strip()
        return _parse_json_response(result_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in document analysis: {e}")
        return None
    except Exception as e:
        logger.error(f"Claude API error in document analysis: {e}")
        return None


def query_with_claude(query, entries_text):
    """Use Claude to answer a query based on knowledge base entries."""
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": QUERY_PROMPT.format(query=query, entries=entries_text)}
            ]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}")
        return None


def generate_summary(entries_text, prompt_template):
    """Generate summary using Claude."""
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt_template.format(entries=entries_text)}
            ]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return None


def deep_analyze_with_claude(content, title="Untitled Paper"):
    """Use Claude to perform deep analysis of a research paper."""
    try:
        # Truncate content if too long
        max_chars = 100000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[Document truncated due to length...]"

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": DEEP_ANALYSIS_PROMPT.format(title=title, content=content)}
            ]
        )

        result_text = response.content[0].text.strip()
        return _parse_json_response(result_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in deep analysis: {e}")
        return None
    except Exception as e:
        logger.error(f"Claude API error in deep analysis: {e}")
        return None


def answer_paper_question(question, title, content, analysis_summary):
    """Use Claude to answer a follow-up question about a paper."""
    try:
        # Truncate content for Q&A (keep it shorter)
        max_chars = 50000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[Truncated...]"

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": PAPER_QA_PROMPT.format(
                    title=title,
                    content=content,
                    analysis_summary=analysis_summary,
                    question=question
                )}
            ]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Error answering paper question: {e}")
        return None
