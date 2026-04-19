# Personal LLM Knowledge Base

Based on [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## Quick Start

### 1. Create and Activate Virtual Environment
```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate it
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows
```

### 2. Run Setup
```bash
python3 setup.py
```

This installs dependencies and creates the directory structure.

### 3. Add Sources to `raw/`
- Save articles, papers, notes, images
- Use Obsidian Web Clipper for web content
- This is your immutable source of truth

### 4. Tell the LLM to Ingest
Ask the LLM to process a new source. Example:
```
"Please ingest raw/articles/my-article.md"
```

### 5. Explore the Wiki
- Read generated summaries in `wiki/`
- Ask questions against the knowledge base
- Check `wiki/index.md` for navigation

### 6. Query and Save
Ask questions, then save valuable outputs:
```
"Save this answer to outputs/answers/my-question.md"
```

## Directory Structure

```
raw/                    - Your source documents (you curate)
├── articles/           - Web articles, blog posts
├── papers/             - Research papers or PDFS (that are converted to Markdown first)
├── notes/              - Personal notes, meeting notes
└── assets/             - Images, diagrams

wiki/                   - LLM-generated knowledge (LLM maintains)
├── entities/           - People, companies, products
├── concepts/           - Ideas, frameworks, theories
├── sources/            - Summaries of raw documents
├── topics/             - Thematic collections
├── index.md            - Master catalog of all pages
└── log.md              - Chronological activity log

outputs/                - Query responses and analyses
├── answers/            - Question responses with citations
├── comparisons/        - Side-by-side comparisons
└── syntheses/          - Multi-source syntheses

AGENTS.md               - Instructions for the coding agent
```

### Agent Configuration Note

The `AGENTS.md` file may need to be renamed based on your AI tool:

- **Antigravity** → Rename to `GEMINI.md`
- **OpenCode, Cursor, Windsurf** → Keep as `AGENTS.md`
- **Claude Code** → Rename to `CLAUDE.md`

## Golden Rule

**The LLM writes the wiki. You read the wiki.**

Focus on sourcing and asking questions. Let the LLM handle the organizing, cross-referencing, and maintenance.

## Tools

- **Obsidian**: Best for viewing the wiki (graph view, backlinks)
- **Obsidian Web Clipper**: Browser extension for saving articles
- **pdf2md.py**: Convert PDFs to markdown before ingesting
  ```bash
  python3 pdf2md.py <path-or-url>
  ```
  Path can be a local file or a URL to a PDF.

- **quiz_app**: Interactive quiz application for testing knowledge
  ```bash
  python3 -m quiz_app.main
  ```
  Note: Before running, ensure you have prompted the LLM to generate quiz questions for your desired topic. The app reads questions from `quiz_app/test_questions.json`.

- **LLM**: Your knowledge base maintainer

## Getting Started Tips

1. Start with one topic you're researching
2. Add 5-10 sources to `raw/`
3. Have your LLM ingest them one at a time
4. Read the generated wiki pages
5. Ask questions and explore connections
6. Run a "lint" periodically to check for gaps

## Tips

- **Download images locally** - Use Obsidian's "Download attachments" feature so LLM can view them
- **Use the graph view** - Obsidian's graph view shows connections between concepts
- **One source at a time** - Stay involved, check summaries as you go
- **File good answers** - Save valuable query outputs back to the wiki
- **Run health checks** - Periodically ask LLM to "lint" the wiki for gaps