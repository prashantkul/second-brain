---
name: research-potential
description: Analyze research topic potential, identify opportunities, and kickoff deep literature review
---

# Research Potential Analysis Skill

When a user sends a message starting with `rp:` or `research-potential:` followed by a research topic/idea, analyze its potential comprehensively.

## Phase 1: Initial Potential Assessment

Provide analysis in this structure (Telegram-friendly):

```
*RESEARCH POTENTIAL ANALYSIS*

*Topic:* [Research topic/question]
*Field:* [Primary field - ML, NLP, Systems, etc.]

---

*Novelty Assessment:*
• Novelty Score: [1-10] - [Brief justification]
• What's new: [What makes this different from existing work]
• Risk: [Low/Medium/High] - [Why]

*Feasibility:*
• Technical complexity: [Low/Medium/High]
• Resource requirements: [Compute, data, expertise needed]
• Timeline estimate: [Rough estimate for initial results]

*Impact Potential:*
• Academic impact: [Low/Medium/High] - [Why]
• Industry relevance: [Low/Medium/High] - [Why]
• Community interest: [Trending/Growing/Niche/Declining]

---

*Quick Literature Pulse:*
• Related areas: [2-3 related research directions]
• Key papers to read: [2-3 seminal/recent papers]
• Active research groups: [1-2 groups working on similar topics]

---

*Verdict:* [PURSUE / EXPLORE MORE / PIVOT / PASS]
[1-2 sentence recommendation]

*If pursuing, suggested next steps:*
1. [Immediate action]
2. [Short-term action]
3. [Medium-term milestone]
```

## Phase 2: Deep Dive (If Verdict is PURSUE or user requests)

When user responds with "deep dive", "go deeper", "analyze further", or uses `rp-deep:` prefix:

```
*DEEP RESEARCH ANALYSIS*

*Topic:* [Research topic]

---

*LITERATURE LANDSCAPE*

*Foundational Papers:*
• [Paper 1] ([Year]) - [Why it's important]
• [Paper 2] ([Year]) - [Why it's important]
• [Paper 3] ([Year]) - [Why it's important]

*Recent Advances (Last 2 years):*
• [Paper 1] ([Year]) - [Key contribution]
• [Paper 2] ([Year]) - [Key contribution]
• [Paper 3] ([Year]) - [Key contribution]

*Survey Papers:*
• [Survey 1] - [Coverage]
• [Survey 2] - [Coverage]

---

*OPEN PROBLEMS & GAPS*

• [Problem 1]: [Description + why it matters]
• [Problem 2]: [Description + why it matters]
• [Problem 3]: [Description + why it matters]

*Unexplored Angles:*
• [Angle 1] - [Potential approach]
• [Angle 2] - [Potential approach]

---

*CONFERENCE FIT*

*Top Venues:*
• [Conference 1] - [Fit: Strong/Medium/Weak] - [Why]
• [Conference 2] - [Fit: Strong/Medium/Weak] - [Why]
• [Conference 3] - [Fit: Strong/Medium/Weak] - [Why]

*Workshop Opportunities:*
• [Workshop 1] - [Relevance]
• [Workshop 2] - [Relevance]

*Upcoming Deadlines:*
• [Conference] - [Deadline] - [Notes]

---

*COLLABORATION OPPORTUNITIES*

*Active Researchers:*
• [Researcher 1] @ [Institution] - [Their angle]
• [Researcher 2] @ [Institution] - [Their angle]

*Industry Labs:*
• [Lab 1] - [Their work in this area]
• [Lab 2] - [Their work in this area]

---

*RESEARCH ROADMAP*

*Phase 1 (1-2 months):*
• [Action items for initial exploration]

*Phase 2 (2-4 months):*
• [Actions for prototype/initial results]

*Phase 3 (4-6 months):*
• [Actions for paper-ready work]

*Key Milestones:*
• [Milestone 1] - [Target date/condition]
• [Milestone 2] - [Target date/condition]
```

## After Analysis

Save to Notion using `save_to_notion` with:
- title: "[Topic] - Research Potential"
- category: "Research"
- description: Verdict + key findings + next steps
- priority: Based on verdict (PURSUE=High, EXPLORE=Medium, etc.)
- tags: Field, "research-idea", verdict, relevant keywords
- source_url: Empty (user's own idea)

For deep dive, use `save_deep_analysis` with full structured content.

## Examples

**Input:** `rp: Using LLMs for automated theorem proving in Lean 4`
**Output:** Full potential assessment + recommendation

**Input:** `rp-deep: Efficient attention mechanisms for long-context understanding`
**Output:** Complete deep dive with literature, gaps, venues, roadmap

**Follow-up:** User says "go deeper" after initial assessment
**Output:** Phase 2 deep analysis
