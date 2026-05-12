# Knowledge Base — Schema

This is an LLM-maintained knowledge base. The LLM writes and maintains all wiki content. The human curates sources, directs analysis, and asks questions. All data is stored as plain files in universal formats (markdown, images) — the human owns the data and can use any AI agent or tool over it.

## Directory Structure

```
/LLM Knowledge Base/
├── raw/                    # Immutable source documents (user curates, agents read)
│   ├── articles/           # Web articles, blog posts
│   ├── papers/             # Research papers, PDFs (converted to Markdown)
│   ├── notes/              # Personal notes, meeting notes
│   └── assets/             # Images, diagrams
├── wiki/                   # AI-generated knowledge (agents write, user reads)
│   ├── entities/           # People, companies, products
│   ├── concepts/           # Ideas, frameworks, theories
│   ├── sources/            # Summaries of raw documents
│   ├── topics/             # Thematic collections
│   ├── index.md            # Master catalog of all pages
│   ├── overview.md         # Top-level synthesis of themes and findings
│   └── log.md              # Chronological activity log
├── outputs/                # Query responses, analyses
│   ├── answers/            # Question responses with citations
│   ├── comparisons/        # Side-by-side comparisons
│   └── syntheses/          # Multi-source syntheses
└── AGENTS.md               # This file — the schema
```

## Wiki Conventions

### Page Format

Every wiki page must have YAML frontmatter:

```yaml
---
tags: [topic-a, topic-b]
date: YYYY-MM-DD
sources: 3
---
```

- `tags`: relevant topic tags
- `date`: creation date of the page
- `sources`: count of raw sources that contributed to this page

### Page Structure

Each page should follow this pattern:

```markdown
---
tags: [attention-mechanism, transformers]
date: 2026-01-15
sources: 2
---

# Page Title

## Summary
A clear and concise summary of the page content capturing the key ideas without missing critical points.

## Content
Main body with [[cross-references]] to related concepts and entities.
Document contradictions explicitly: if sources disagree, present both sides with citations.

## Sources
- [[raw/papers/paper-title.md]]
- [[raw/articles/article-name.md]]

## Related
- [[Related Concept]]
- [[Another Entity]]
```

### Links

Use `[[wikilinks]]` for all internal links. Never use `[text](path.md)` style.

### Special Files

- **`wiki/index.md`** — Content catalog. Every wiki page listed with a link, one-line summary, and metadata. Organized by category (entities, concepts, sources, topics). The LLM reads this first when answering queries.
- **`wiki/overview.md`** — Top-level synthesis page. A narrative tying together main themes, key findings, open questions. Not a table of contents — that's the index. Update whenever an ingest shifts the big picture.
- **`wiki/log.md`** — Append-only chronological record. Each entry uses format `## [YYYY-MM-DD] type | Title` where type is: `ingest`, `query`, `lint`, `update`. This is grep-friendly: `grep "^## \[" wiki/log.md | tail -5` shows last 5 entries.

## Workflows

### Ingest (Processing New Sources)

When a file is added to `raw/`:
1. **Read** the source document fully
2. **Discuss** key takeaways with the user — what matters, what's new, what contradicts existing knowledge
3. **Write** a summary page in `wiki/sources/` with YAML frontmatter
4. **Update** `wiki/index.md` with the new source entry
5. **Create or update** relevant entity/concept pages across the wiki — a single source may touch 10-15 pages
6. **Update** `wiki/overview.md` if the new source shifts the big picture
7. **Append** entry to `wiki/log.md` with format: `## [YYYY-MM-DD] ingest | Source Title`

Use coverage indicators: mark sections as `[coverage: high|medium|low -- N sources]` so users know when to trust wiki vs. check raw files.

### Query (Answering Questions)

When the user asks a question:
1. **Read** `wiki/index.md` first to locate relevant pages
2. **Read** the specific wiki articles needed
3. **Synthesize** an answer with citations using `[[wikilinks]]`. Structure answers in two parts:
   - **Technical Answer**: Precise, detailed explanation with proper terminology and depth
   - **Layman Answer**: Concrete, accessible explanation using analogies and simple language that makes the concept tangible
4. **Output** as markdown in `outputs/answers/` or requested format (slides, charts)
5. **File** valuable answers back into wiki as new pages — explorations should compound
6. **Append** entry to `wiki/log.md`: `## [YYYY-MM-DD] query | Question topic`

### Lint (Health Check)

Periodically (or on request):
1. **Scan** all wiki articles
2. **Check** for:
   - Contradictions between pages (document both sides)
   - Stale claims superseded by newer sources
   - Orphan pages with no inbound links
   - Missing cross-references
   - Broken links
   - Concepts mentioned but lacking their own page
   - Data gaps that could be filled with web search
3. **Suggest** new questions to investigate and new sources to seek
4. **Report** findings in `outputs/lint-report.md`
5. **Append** entry to `wiki/log.md`: `## [YYYY-MM-DD] lint | Health check`

### Quiz Generation (Creating Questions)

To generate quiz questions on a given topic:

1. **Read relevant wiki pages** — Read `wiki/index.md` to identify related pages, then read them comprehensively.

2. **Generate questions** — Create `{N_WRITTEN_QUESTIONS}` written questions and `{N_MCQ_QUESTIONS}` MCQ questions on `{TOPIC}`.

3. **Question quality**:
   - Design open-ended, clear, and focused inquiries that promote deep thinking rather than
   simple recall
   - Use open questions (how, why, what) to encourage discussion and exploration
   - Avoid leading questions that guide toward a predetermined answer
   - Structure inquiries sequentially from simple to complex to deepen insight progressively
   - Test different cognitive levels: recall, understanding, application, analysis, synthesis, evaluation
   - Ensure questions are specific and unambiguous while allowing for nuanced responses
   - Avoid yes/no questions for written format — they limit depth of response
   - For MCQs: provide 4 options with exactly one correct answer, but design distractors that test understanding of common misconceptions
   - Reference specific wiki pages where answers can be found
   - Questions should require connecting concepts across multiple wiki pages when appropriate

4. **Structure requirements**:
   - Write to `quiz_app/test_questions.json` using `quiz_app/questions_template.json`
   - Leave all answer fields blank
   - Include `source_page` field indicating which wiki page contains the answer

5. **Replace placeholders**:
   - `{N_WRITTEN_QUESTIONS}`: Number of written questions 
   - `{N_MCQ_QUESTIONS}`: Number of MCQ questions
   - `{TOPIC}`: The topic to generate questions about (e.g., "attention mechanisms")

### Quiz Evaluation (Evaluating Answers)

To evaluate user answers in `quiz_app/test_questions.json`:

1. **Read relevant wiki pages** — For each question, read the wiki page(s) in the `source_page` field.

2. **Evaluate each answer** using this framework:
   - **Accuracy**: Factually correct based on wiki content?
   - **Completeness**: Covers all key aspects?
   - **Precision**: Specific and targeted?
   - **Understanding**: Conceptual grasp or just memorization?

3. **Provide feedback** for each question:
   - State correct, partially correct, or incorrect
   - Identify gaps or misconceptions
   - Provide a model answer with wiki citations

4. **Scoring**:
   - Fully correct: All key points, no errors
   - Partially correct: Some correct elements but misses aspects or has minor errors
   - Incorrect: Fundamentally wrong or misses core concept

5. **Identify patterns** — Note recurring misunderstandings, suggest wiki pages to review, recommend follow-up topics.

6. **Strict knowledge boundary** — Rely exclusively on the wiki. If insufficient information, flag as "insufficient information in wiki" and suggest raw sources to ingest.

## Golden Rule

**Agents write the wiki. User reads the wiki.**

The user rarely edits wiki files directly. The wiki is agent territory. The user focuses on sourcing, exploring, and asking questions.

The key insight: the wiki is a persistent, compounding artifact. Cross-references are already there. Contradictions flagged. Synthesis reflects everything read. Each source enriches the whole.

## Raw Source Naming Convention

Files in `raw/` follow: `YYYY-MM-DD_short-slug.md`
- Date prefix for chronological sorting
- Short descriptive slug (2-4 words)
- Use `.md` for articles, keep original extension for PDFs

## Growth Management

Append-only wikis become unwieldy over time. To keep the wiki healthy:

- **Budget per file**: Keep `wiki/overview.md` under ~60 lines, `wiki/log.md` under ~80 lines. If a concept page exceeds ~100 lines, consider splitting it.
- **Log compaction**: When `wiki/log.md` exceeds its budget, compress entries older than 30 days into one-line-per-week summaries.
- **Coverage evolution**: When new sources supersede old claims, update the claim in-place and note the change — don't just append.
- **Periodic pruning**: During lint, identify pages that are redundant or have been fully absorbed into other pages. Merge or archive them.

## Search Tooling

At small scale (~100 sources), reading `wiki/index.md` first is sufficient. As the wiki grows:

- Use `grep` for quick searches: `grep -r "term" wiki/`
- Use `find` for file discovery: `find raw/ -name "*.md" | head -20`
- Use [Obsidian Web Clipper](https://obsidian.md/clipper) to quickly convert web articles to markdown for `raw/`
- Use [Dataview plugin](https://github.com/blacksmithgu/obsidian-dataview) to dynamically query your YAML frontmatter (tags, sources, date)
- Use [Marp](https://marp.app/) extensions in Obsidian if you want the LLM to output presentation slide decks

## Version Control

The wiki is just a git repo of markdown files. You get version history, branching, and diffing for free. Commit after each ingest session.

## Important Rules

| Rule | Why |
|------|-----|
| **Never modify files in `raw/`** | They are immutable source documents — the source of truth |
| **Always update `wiki/index.md`** | Keeps the catalog current for queries |
| **Always append to `wiki/log.md`** | Creates chronological record of all operations |
| **Use `[[wikilinks]]` exclusively** | Enables Obsidian graph view, consistent linking |
| **Add YAML frontmatter** | Enables filtering, sorting, metadata tracking |
| **Note contradictions explicitly** | Preserves nuance, shows evolution of understanding |
| **Don't invent information** | If mentioned but unexplained, flag as a gap to research |
| **Image handling** | LLMs can't read markdown with inline images in one pass. Read text first, then view referenced images separately for context |

## Goals

Build a compounding knowledge base for research, learning, and insight generation. Each source ingested should make the entire wiki more valuable, not just add an isolated page.