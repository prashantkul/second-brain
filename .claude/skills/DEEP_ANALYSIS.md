---
name: deep-analysis
description: Comprehensive research paper and article analysis with academic + practical breakdown and follow-up Q&A
---

# Deep Analysis Skill

When a user sends a message starting with `d:` or `deep:` followed by a URL, perform comprehensive analysis.

## Analysis Format

Provide analysis in this EXACT structure (Telegram-friendly, use *bold* not # headers):

```
*DEEP ANALYSIS*

*Title:* [Paper/article title]
*Authors:* [If identifiable]
*Type:* [Empirical/Theoretical/Survey/System/Blog/Tutorial]

---

*ACADEMIC ANALYSIS*

*Problem:* [What problem does this address? 2-3 sentences]

*Methodology:* [Key techniques/methods used. 2-3 sentences]

*Key Contributions:*
• [Contribution 1]
• [Contribution 2]
• [Contribution 3]

*Results:* [Main findings. 2-3 sentences]

*Limitations:*
• [Limitation 1]
• [Limitation 2]

---

*PRACTICAL ANALYSIS*

*TL;DR:* [One sentence a busy engineer would appreciate]

*Why It Matters:* [Real-world implications. 2-3 sentences]

*Implementation Complexity:* [Easy/Medium/Hard] - [Brief reasoning]

*Use Cases:*
• [Practical application 1]
• [Practical application 2]
• [Practical application 3]

---

*META*

*Reading Time:* Skim: X min | Understand: X min | Deep study: X min
*Prerequisites:* [Concepts reader should know]
*Priority:* [High/Medium/Low] - [Why]
*Tags:* tag1, tag2, tag3

---

*Questions to Explore:*
• [Thought-provoking question 1]
• [Thought-provoking question 2]
• [Thought-provoking question 3]
```

## After Analysis

1. **Save to Notion** using `save_deep_analysis` (NOT save_to_notion!) with these EXACT parameters:
   - title: Paper title (string)
   - authors: Authors if known (string)
   - paper_type: "Empirical", "Theoretical", "Survey", etc. (string)
   - problem: The problem statement (string)
   - methodology: Methods used (string)
   - key_contributions: List of contributions (list of strings)
   - results: Main findings (string)
   - limitations: List of limitations (list of strings)
   - tldr: One-sentence summary (string)
   - why_it_matters: Real-world implications (string)
   - implementation_complexity: "Easy", "Medium", or "Hard" with reasoning (string)
   - use_cases: List of practical applications (list of strings)
   - reading_time: "Skim: X min | Understand: X min | Deep: X min" (string)
   - prerequisites: Concepts needed (string)
   - priority: "High", "Medium", or "Low" (string)
   - tags: Comma-separated tags like "machine learning, security, NLP" (string)
   - source_url: The original URL (string)
   - questions_to_explore: List of follow-up questions (list of strings)

2. **Enable Q&A Mode** by ending with:
   ```
   _Paper loaded for Q&A. Ask me anything about this paper!_
   _Type /exit to leave Q&A mode._
   ```

## Q&A Mode

After deep analysis, subsequent messages WITHOUT prefixes (t:, p:, r:, l:, d:, !) are treated as questions about the paper.

When answering follow-up questions:
- Reference specific parts of the paper
- Be concise but thorough
- Use Telegram formatting
- End with: `_Still in Q&A mode. Ask another question or /exit._`

## Exit Conditions

Q&A mode ends when user:
- Types `/exit`
- Sends a message with a category prefix
- Sends a new URL
- Sends a command (/daily, /help, etc.)

## Examples

**Input:** `d: https://arxiv.org/abs/2301.00001`
**Output:** Full deep analysis + saved to Notion + Q&A enabled

**Follow-up:** `What's the main algorithm?`
**Output:** Specific answer about the algorithm from the paper

**Follow-up:** `How does this compare to GPT-4?`
**Output:** Comparison based on paper content
