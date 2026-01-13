---
name: job-analysis
description: Analyze job postings, extract requirements, and suggest skills to develop
---

# Job Analysis Skill

When a user sends a message starting with `j:` or `job:` followed by a job posting URL or text, analyze it comprehensively.

## Analysis Format

Provide analysis in this structure (Telegram-friendly):

```
*JOB ANALYSIS*

*Company:* [Company name]
*Role:* [Job title]
*Location:* [Location / Remote status]
*Level:* [Entry/Mid/Senior/Lead/Principal]

---

*Key Requirements:*
• [Requirement 1]
• [Requirement 2]
• [Requirement 3]

*Required Skills:*
• [Skill 1] - [Years/proficiency expected]
• [Skill 2] - [Years/proficiency expected]
• [Skill 3] - [Years/proficiency expected]

*Nice-to-Have:*
• [Optional skill 1]
• [Optional skill 2]

---

*Skills to Develop:*
Based on common gaps, consider learning:
• [Skill suggestion 1] - [Why useful for this role]
• [Skill suggestion 2] - [Why useful for this role]
• [Skill suggestion 3] - [Why useful for this role]

*Resources:*
• [Course/book/project suggestion 1]
• [Course/book/project suggestion 2]

---

*Fit Assessment:*
[Brief assessment of role - what type of candidate they're looking for, culture signals, growth potential]

*Red Flags:* [Any concerns about the posting, if any]
*Green Flags:* [Positive signals about the role/company]
```

## After Analysis

Save to Notion using `save_to_notion` with:
- title: "[Company] - [Role]"
- category: "Jobs"
- description: Key requirements summary + skills to develop
- priority: Based on fit/interest
- tags: Comma-separated relevant tags (e.g., "ML, Remote, Senior, Startup")
- source_url: The job posting URL

## Examples

**Input:** `j: https://jobs.lever.co/company/software-engineer`
**Output:** Full job analysis + saved to Notion

**Input:** `job: [pasted job description text]`
**Output:** Analysis of the pasted job description
