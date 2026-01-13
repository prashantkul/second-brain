"""
Message, URL, and document processing for Second Brain Bot.
"""

import re

import requests
from bs4 import BeautifulSoup

import time

from config import (
    PREFIXES, CATEGORY_EMOJI, logger,
    deep_analysis_cache, DEEP_ANALYSIS_CACHE_EXPIRY
)
from telegram import (
    send_capture_message,
    download_telegram_file,
    extract_text_from_pdf
)
from claude_ai import (
    categorize_with_claude,
    analyze_document_with_claude,
    deep_analyze_with_claude,
    answer_paper_question
)
from notion import save_to_notion, save_document_analysis_to_notion, save_deep_analysis_to_notion


# =============================================================================
# Prefix Parsing
# =============================================================================

def parse_prefixes(text):
    """Parse quick prefixes from message text.

    Prefixes:
    - t: or task: -> Tasks
    - p: or person: -> People
    - r: or research: -> Research
    - l: or link: -> Links
    - ! at start -> High priority
    - ? at start -> Query mode (ask your brain)

    Returns: (clean_text, category_override, priority_override, is_query)
    """
    clean_text = text.strip()
    category_override = None
    priority_override = None
    is_query = False

    # Check for query mode
    if clean_text.startswith("?"):
        return (clean_text[1:].strip(), None, None, True)

    # Check for high priority
    if clean_text.startswith("!"):
        priority_override = "High"
        clean_text = clean_text[1:].strip()

    # Check for category prefixes
    lower_text = clean_text.lower()
    for prefix, category in PREFIXES.items():
        if lower_text.startswith(prefix):
            category_override = category
            clean_text = clean_text[len(prefix):].strip()
            break

    return (clean_text, category_override, priority_override, is_query)


# =============================================================================
# URL Processing
# =============================================================================

def extract_urls(text):
    """Extract URLs from text."""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)


def fetch_url_content(url):
    """Fetch content from a URL. Returns (content_type, content, title)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        # First, do a HEAD request to check content type
        head_response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        content_type = head_response.headers.get("Content-Type", "").lower()

        # Handle arXiv abstract pages - convert to PDF URL
        if "arxiv.org/abs/" in url:
            pdf_url = url.replace("/abs/", "/pdf/") + ".pdf"
            return fetch_url_content(pdf_url)

        # Handle direct PDF links
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code == 200:
                text = extract_text_from_pdf(response.content)
                # Try to extract title from URL
                title = url.split("/")[-1].replace(".pdf", "").replace("-", " ").replace("_", " ")
                return ("pdf", text, title)
            return (None, None, None)

        # Handle HTML pages
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string or ""

            # Try to find the main content
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Look for article content or main content
            article = soup.find("article") or soup.find("main") or soup.find(class_=re.compile("article|content|post"))

            if article:
                text = article.get_text(separator="\n", strip=True)
            else:
                # Fall back to body
                body = soup.find("body")
                text = body.get_text(separator="\n", strip=True) if body else soup.get_text(separator="\n", strip=True)

            # Clean up excessive whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)

            return ("html", text, title)

        return (None, None, None)

    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return (None, None, None)


def process_url(url, original_message=""):
    """Process a URL: fetch content, analyze with Claude, save to Notion."""
    logger.info(f"Processing URL: {url}")

    send_capture_message(f"Fetching content from URL...\n\n{url[:50]}...")

    # Fetch content
    content_type, content, title = fetch_url_content(url)

    if not content or len(content.strip()) < 100:
        # If we couldn't fetch content, just save as a link
        logger.warning(f"Couldn't extract content from URL: {url}")
        data = {
            "title": title or url[:50],
            "category": "Links",
            "description": original_message or f"Link to: {url}",
            "priority": "Medium",
            "source": url,
            "tags": ["to-read"]
        }
        result = save_to_notion(data)
        if result:
            send_capture_message(f"*Saved as Link*\n\nCouldn't fetch full content, saved URL for later.\n\n_{url}_")
        return

    send_capture_message(f"Content fetched ({content_type}). Analyzing with Claude...")

    # Analyze with Claude
    analysis = analyze_document_with_claude(content, title=title or url)

    if not analysis:
        # Fallback - save as simple link
        data = {
            "title": title or url[:50],
            "category": "Links",
            "description": content[:500] if content else original_message,
            "priority": "Medium",
            "source": url,
            "tags": ["to-read"]
        }
        save_to_notion(data)
        send_capture_message(f"*Saved as Link*\n\nAnalysis failed, but content saved.\n\n_{title or url}_")
        return

    # Add source URL to analysis
    analysis["source"] = url

    # Save to Notion
    result = save_document_analysis_to_notion(analysis)

    if result:
        # Get Notion URL from result
        notion_url = result.get("url", "")

        response = f"*Paper/Article Analyzed*\n\n"
        response += f"*{analysis.get('title')}*\n"
        response += f"Priority: {analysis.get('priority')}\n\n"

        response += f"*Summary:*\n{analysis.get('summary', '')[:300]}...\n\n"

        if analysis.get("time_estimates"):
            estimates = analysis.get("time_estimates", {})
            response += f"*Time to Read:*\n"
            if estimates.get("quick_skim"):
                response += f"- Skim: {estimates['quick_skim']}\n"
            if estimates.get("thorough_read"):
                response += f"- Thorough: {estimates['thorough_read']}\n"

        if analysis.get("actionable_takeaways"):
            response += f"\n*Top Actions:*\n"
            for i, action in enumerate(analysis.get("actionable_takeaways", [])[:2], 1):
                response += f"{i}. {action}\n"

        if notion_url:
            response += f"\n[Open in Notion]({notion_url})"

        send_capture_message(response)
    else:
        send_capture_message("Analyzed but failed to save to Notion. Please check logs.")


# =============================================================================
# Document Processing
# =============================================================================

def process_document(file_id, file_name, caption=None):
    """Process an uploaded document: extract text, analyze with Claude, save to Notion."""
    logger.info(f"Processing document: {file_name}")

    send_capture_message(f"Received *{file_name}*\n\nAnalyzing with Claude... This may take a moment.")

    # Download file
    file_content = download_telegram_file(file_id)
    if not file_content:
        send_capture_message("Failed to download the file. Please try again.")
        return

    # Extract text based on file type
    text_content = None
    if file_name.lower().endswith(".pdf"):
        text_content = extract_text_from_pdf(file_content)
    elif file_name.lower().endswith((".txt", ".md")):
        text_content = file_content.decode("utf-8", errors="ignore")
    else:
        send_capture_message(f"Sorry, I can only process PDF and text files for now. Received: {file_name}")
        return

    if not text_content or len(text_content.strip()) < 100:
        send_capture_message("Couldn't extract enough text from the document. It might be scanned/image-based.")
        return

    # Analyze with Claude
    analysis = analyze_document_with_claude(text_content, title=file_name)
    if not analysis:
        send_capture_message("Failed to analyze the document. Please try again.")
        return

    # Save to Notion
    result = save_document_analysis_to_notion(analysis)
    if result:
        # Get Notion URL from result
        notion_url = result.get("url", "")

        # Build response message
        response = f"*Document Analyzed & Saved*\n\n"
        response += f"*{analysis.get('title')}*\n"
        response += f"Priority: {analysis.get('priority')}\n\n"

        response += f"*Summary:*\n{analysis.get('summary', '')[:300]}...\n\n"

        if analysis.get("time_estimates"):
            estimates = analysis.get("time_estimates", {})
            response += f"*Time to Read:*\n"
            if estimates.get("quick_skim"):
                response += f"- Skim: {estimates['quick_skim']}\n"
            if estimates.get("thorough_read"):
                response += f"- Thorough: {estimates['thorough_read']}\n"

        if analysis.get("actionable_takeaways"):
            response += f"\n*Top Actions:*\n"
            for i, action in enumerate(analysis.get("actionable_takeaways", [])[:2], 1):
                response += f"{i}. {action}\n"

        if notion_url:
            response += f"\n[Open in Notion]({notion_url})"

        send_capture_message(response)
    else:
        send_capture_message("Analyzed but failed to save to Notion. Please check logs.")


# =============================================================================
# Message Processing
# =============================================================================

def process_text_message(clean_text, category_override=None, priority_override=None):
    """Process a regular text message: categorize and save to Notion."""
    # Check for URLs - if found, process as document/article
    urls = extract_urls(clean_text)
    if urls:
        # Process the first URL found
        process_url(urls[0], original_message=clean_text)
        return

    # Regular text message - categorize with Claude
    data = categorize_with_claude(clean_text)
    if not data:
        send_capture_message("Sorry, I couldn't process that message. Please try again.")
        return

    # Apply prefix overrides
    if category_override:
        data["category"] = category_override
    if priority_override:
        data["priority"] = priority_override

    # Save to Notion
    result = save_to_notion(data)
    if result:
        notion_url = result.get("url", "")

        emoji = CATEGORY_EMOJI.get(data.get("category"), "📝")

        # Show if prefix was used
        prefix_note = ""
        if category_override or priority_override:
            prefix_note = " _(via prefix)_"

        response = f"{emoji} *Saved to Second Brain*{prefix_note}\n\n"
        response += f"*{data.get('title')}*\n"
        response += f"Category: {data.get('category')}\n"
        response += f"Priority: {data.get('priority')}"

        if data.get("action_items"):
            response += f"\n\n_Action: {data.get('action_items')}_"

        if notion_url:
            response += f"\n\n[Open in Notion]({notion_url})"

        send_capture_message(response)
    else:
        send_capture_message("Categorized but failed to save to Notion. Please check logs.")


# =============================================================================
# Deep Analysis Processing
# =============================================================================

def is_deep_analysis_cache_valid():
    """Check if the deep analysis cache is still valid."""
    if not deep_analysis_cache["timestamp"]:
        return False
    elapsed = time.time() - deep_analysis_cache["timestamp"]
    return elapsed < DEEP_ANALYSIS_CACHE_EXPIRY


def clear_deep_analysis_cache():
    """Clear the deep analysis cache."""
    deep_analysis_cache["content"] = None
    deep_analysis_cache["analysis"] = None
    deep_analysis_cache["title"] = None
    deep_analysis_cache["timestamp"] = None


def set_deep_analysis_cache(content, analysis, title):
    """Set the deep analysis cache."""
    deep_analysis_cache["content"] = content
    deep_analysis_cache["analysis"] = analysis
    deep_analysis_cache["title"] = title
    deep_analysis_cache["timestamp"] = time.time()


def process_deep_analysis(url):
    """Process a URL with deep analysis."""
    logger.info(f"Deep analyzing URL: {url}")

    send_capture_message(f"*Deep Analysis Mode*\n\nFetching content from:\n{url[:60]}...")

    # Fetch content
    content_type, content, title = fetch_url_content(url)

    if not content or len(content.strip()) < 100:
        send_capture_message("Couldn't fetch enough content from the URL for deep analysis.")
        return

    send_capture_message(f"Content fetched ({content_type}). Running deep analysis with Claude...\n\n_This may take a moment._")

    # Deep analyze with Claude
    analysis = deep_analyze_with_claude(content, title=title or url)

    if not analysis:
        send_capture_message("Deep analysis failed. Please try again.")
        return

    # Add source URL
    analysis["source"] = url

    # Cache for Q&A
    set_deep_analysis_cache(content, analysis, analysis.get("title", title))

    # Save to Notion
    result = save_deep_analysis_to_notion(analysis)
    notion_url = result.get("url", "") if result else ""

    # Send multi-part response
    _send_deep_analysis_response(analysis, notion_url)


def process_deep_document(file_id, file_name):
    """Process an uploaded document with deep analysis."""
    logger.info(f"Deep analyzing document: {file_name}")

    send_capture_message(f"*Deep Analysis Mode*\n\nProcessing: *{file_name}*\n\n_This may take a moment._")

    # Download file
    file_content = download_telegram_file(file_id)
    if not file_content:
        send_capture_message("Failed to download the file. Please try again.")
        return

    # Extract text
    text_content = None
    if file_name.lower().endswith(".pdf"):
        text_content = extract_text_from_pdf(file_content)
    elif file_name.lower().endswith((".txt", ".md")):
        text_content = file_content.decode("utf-8", errors="ignore")
    else:
        send_capture_message(f"Deep analysis only supports PDF and text files. Received: {file_name}")
        return

    if not text_content or len(text_content.strip()) < 100:
        send_capture_message("Couldn't extract enough text from the document.")
        return

    # Deep analyze
    analysis = deep_analyze_with_claude(text_content, title=file_name)

    if not analysis:
        send_capture_message("Deep analysis failed. Please try again.")
        return

    # Cache for Q&A
    set_deep_analysis_cache(text_content, analysis, analysis.get("title", file_name))

    # Save to Notion
    result = save_deep_analysis_to_notion(analysis)
    notion_url = result.get("url", "") if result else ""

    # Send response
    _send_deep_analysis_response(analysis, notion_url)


def _send_deep_analysis_response(analysis, notion_url):
    """Send the deep analysis response in multiple messages."""
    title = analysis.get("title", "Untitled")
    academic = analysis.get("academic_analysis", {})
    practical = analysis.get("practical_analysis", {})
    meta = analysis.get("meta", {})

    # Message 1: Header + TL;DR + Academic Summary
    msg1 = f"*Deep Analysis Complete*\n\n"
    msg1 += f"*{title}*\n\n"
    msg1 += f"*TL;DR:* {practical.get('tldr', 'N/A')}\n\n"
    msg1 += f"*Problem:* {academic.get('problem_statement', 'N/A')}\n\n"
    msg1 += f"*Methodology:* {academic.get('methodology', 'N/A')[:200]}..."

    send_capture_message(msg1)

    # Message 2: Key Contributions + Practical
    msg2 = f"*Key Contributions:*\n"
    for contrib in academic.get("key_contributions", [])[:3]:
        msg2 += f"- {contrib}\n"

    msg2 += f"\n*Why It Matters:* {practical.get('why_it_matters', 'N/A')}\n\n"
    msg2 += f"*Implementation:* {practical.get('implementation_complexity', 'N/A')} complexity\n"
    msg2 += f"{practical.get('implementation_notes', '')[:150]}..."

    send_capture_message(msg2)

    # Message 3: Meta + Q&A prompt
    time_est = meta.get("time_estimates", {})
    msg3 = f"*Reading Time:*\n"
    msg3 += f"- Skim: {time_est.get('skim', 'N/A')}\n"
    msg3 += f"- Understand: {time_est.get('understand', 'N/A')}\n"
    msg3 += f"- Deep study: {time_est.get('deep_study', 'N/A')}\n\n"

    msg3 += f"*Type:* {meta.get('paper_type', 'N/A')} | *Field:* {meta.get('field', 'N/A')}\n"
    msg3 += f"*Technical Depth:* {academic.get('technical_depth', 'N/A')}\n"
    msg3 += f"*Priority:* {meta.get('priority', 'Medium')}\n"

    if meta.get("tags"):
        msg3 += f"*Tags:* {', '.join(meta.get('tags', []))}\n"

    if notion_url:
        msg3 += f"\n[Open in Notion]({notion_url})\n"

    msg3 += f"\n---\n_Paper loaded for Q&A. Ask me anything about this paper!_\n"
    msg3 += f"_Send any message to ask, or use a prefix (t:, p:, etc.) to save something new._"

    send_capture_message(msg3)


def process_paper_question(question):
    """Process a follow-up question about the cached paper."""
    if not is_deep_analysis_cache_valid():
        send_capture_message("No paper loaded for Q&A. Use `d: <url>` or `/deep <url>` to analyze a paper first.")
        return

    title = deep_analysis_cache["title"]
    send_capture_message(f"Searching *{title[:30]}...* for answer...")

    # Build analysis summary for context
    analysis = deep_analysis_cache["analysis"]
    academic = analysis.get("academic_analysis", {})
    practical = analysis.get("practical_analysis", {})

    analysis_summary = f"""
TL;DR: {practical.get('tldr', '')}
Problem: {academic.get('problem_statement', '')}
Methodology: {academic.get('methodology', '')}
Key Contributions: {', '.join(academic.get('key_contributions', []))}
Results: {academic.get('results_summary', '')}
"""

    # Get answer from Claude
    answer = answer_paper_question(
        question=question,
        title=title,
        content=deep_analysis_cache["content"],
        analysis_summary=analysis_summary
    )

    if answer:
        response = f"*Re: {title[:25]}...*\n\n{answer}"
        send_capture_message(response)
    else:
        send_capture_message("Couldn't find an answer. Try rephrasing your question.")
