---
name: shorts-research
description: Research domain knowledge for YouTube Shorts content. Defines source.md output format and research methodology.
user-invocable: false
---

# Shorts Research Methodology

This skill provides comprehensive instructions for the research sub-agent to produce a source-verified `source.md` file from a given topic. Every piece of information must have a verifiable URL source.

## Research Process

Follow these steps in order:

### Step 1: Analyze Topic and Generate Search Queries
- Analyze the given topic to extract 2-3 core concepts
- Generate 5-7 search queries mixing Korean and English terms
- Include news-specific queries (e.g., "[topic] 뉴스 2026")
- Include data/statistics queries (e.g., "[topic] 통계 데이터")
- Include YouTube-specific queries (e.g., "[topic] youtube analysis")
- Include general knowledge queries in both languages

### Step 2: Execute All Searches in Parallel
- Fire ALL WebSearch queries simultaneously using parallel tool calls
- Do NOT execute searches sequentially -- parallel execution is mandatory for speed
- Collect all results before proceeding to evaluation

### Step 3: Evaluate Source Quality and Relevance
- Filter out low-quality, paywalled, or irrelevant results
- Verify that each source URL is accessible and contains the claimed information
- Aim for a minimum of 5 diverse, high-quality sources
- Prioritize: official statistics > news agencies > expert blogs > social media
- Discard any information that cannot be traced to a specific URL

### Step 4: Synthesize into source.md Format
- Organize verified information into the source.md template below
- Every fact, number, and quote MUST include its source URL inline
- If a section has no verified data, write "No verified data found for this section" rather than leaving it empty or filling with unverified claims

### Step 5: Update metadata.json
- After source.md is fully written and verified, update metadata.json
- Set research step status to "completed" with timestamp and source count
- ONLY update metadata.json AFTER source.md is completely written (atomic completion)

## Critical Rules

These rules are absolute and non-negotiable:

1. **EVERY piece of information MUST have a URL source. NO exceptions.** If you cannot find a URL source for a claim, do not include it in source.md.
2. **EVERY number, statistic, or quote MUST cite its exact origin URL.** Inline citation format: `(Source: [URL])` or `([Source Name](URL))`.
3. **NEVER include unverified claims, hallucinated data, or information without a source.** This is the most critical rule. Violation makes the entire pipeline output unreliable.
4. **If a search returns no useful results, note the gap explicitly rather than filling it with unverified data.** Write: "No verified data found for [specific aspect]."
5. **Search in BOTH Korean and English for maximum coverage.** Korean sources capture local sentiment and data; English sources provide global context and technical depth.
6. **Aim for 5-8 diverse, high-quality sources minimum.** Diversity means: different publishers, different perspectives, different data types (news, statistics, expert opinion).

## source.md Output Format

Write the output file in exactly this format:

```markdown
# Research: [Topic]
**Researched:** [YYYY-MM-DDTHH:MM:SSZ timestamp]
**Sources:** [count] verified sources

## Key Insights (3-5)
- [Insight with source URL]
- [Insight with source URL]
- [Insight with source URL]

## Numerical Data
- [Stat]: [Value] ([Source URL])
- [Stat]: [Value] ([Source URL])

## Quotable Statements
- "[Exact quote]" -- [Speaker/Author], [Source URL]
- "[Exact quote]" -- [Speaker/Author], [Source URL]

## Analogy Material
- [Analogy idea for visual storytelling with source context]

## Visualization Ideas
- [Visual concept for shorts scenes based on research data]

## Public Opinion Summary
- [Sentiment/reaction summary with source URLs]

## Sources
1. [Title] - [URL] - [Date accessed: YYYY-MM-DD]
2. [Title] - [URL] - [Date accessed: YYYY-MM-DD]
3. [Title] - [URL] - [Date accessed: YYYY-MM-DD]
```

### Section Guidelines

- **Key Insights**: The 3-5 most important takeaways a scriptwriter needs. Each must link to its source.
- **Numerical Data**: Hard numbers that make content credible and engaging. Every number must have a source URL.
- **Quotable Statements**: Exact quotes from experts, officials, or notable figures. Include speaker name and source URL.
- **Analogy Material**: Creative comparisons or analogies suggested by the research data. These help scriptwriters craft engaging narration.
- **Visualization Ideas**: Visual concepts that could accompany narration in a shorts video. Based on the actual data/imagery found during research.
- **Public Opinion Summary**: What people are saying about this topic on social media, comments, forums. Include sentiment direction and source URLs.
- **Sources**: Complete bibliography with access dates for verification.

## Search Query Strategy

For any given topic, generate queries following this pattern:

1. **Core concept queries** (2 queries): Extract the main subject and search directly
   - Korean: "[주제] 핵심 정리"
   - English: "[topic] key facts overview"

2. **News queries** (1-2 queries): Recent developments and current events
   - Korean: "[주제] 뉴스 2026" or "[주제] 최신 소식"
   - English: "[topic] latest news"

3. **Data/Statistics queries** (1 query): Hard numbers and statistics
   - Korean: "[주제] 통계 데이터" or "[주제] 수치"
   - English: "[topic] statistics data"

4. **Opinion/Reaction queries** (1 query): Public sentiment and expert opinions
   - Korean: "[주제] 반응 여론" or "[주제] 의견"

### Query Limits
- Generate exactly 5-7 queries per topic
- Do NOT exceed 7 queries to avoid WebSearch rate limiting
- If a topic is narrow, prefer fewer high-quality queries over many generic ones

## Time Constraint

- **Total research time must not exceed 3 minutes.**
- If searches are slow or returning limited results, prioritize quality over quantity.
- **Minimum viable output**: 3 sources with Key Insights section complete.
- If the 3-minute limit approaches, finalize source.md with whatever verified data has been collected rather than continuing to search.
- Speed priority: parallel search execution > sequential follow-up searches

## metadata.json Update

After writing source.md completely, update the output directory's metadata.json with the research step status:

```json
{
  "steps": {
    "research": {
      "status": "completed",
      "completed_at": "[ISO 8601 timestamp, e.g., 2026-03-27T14:02:30Z]",
      "output": "source.md",
      "sources_count": "[number of verified sources in the Sources section]"
    }
  }
}
```

**Important**: Only set status to "completed" AFTER source.md has been fully written. If source.md writing fails or is incomplete, do NOT update metadata.json. This ensures idempotent re-runs: if research is interrupted, the next run will detect incomplete status and restart research.
