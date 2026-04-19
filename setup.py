#!/usr/bin/env python3
"""Setup script for LLM Knowledge Base."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and report status."""
    print(f"\n{'=' * 50}")
    print(f"{description}...")
    print(f"{'=' * 50}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        print(f"✓ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False


def create_directories() -> None:
    """Create the knowledge base directory structure."""
    dirs = [
        "raw/articles",
        "raw/papers",
        "raw/notes",
        "raw/assets",
        "wiki/entities",
        "wiki/concepts",
        "wiki/sources",
        "wiki/topics",
        "outputs/answers",
        "outputs/comparisons",
        "outputs/syntheses",
    ]

    print(f"\n{'=' * 50}")
    print("Creating directory structure...")
    print(f"{'=' * 50}")

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {dir_path}/")

    print(f"\n✓ Directory structure created")


def create_wiki_files() -> None:
    """Create index.md and log.md in the wiki directory."""
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'=' * 50}")
    print("Creating wiki files...")
    print(f"{'=' * 50}")

    # Create index.md
    index_content = f"""---
tags: [catalog]
date: {today}
sources: 0
---

# LLM Knowledge Base Index

## Entities
*No entities yet*

## Concepts
*No concepts yet*

## Sources
*No sources yet*

## Topics
*No topics yet*
"""
    Path("wiki/index.md").write_text(index_content)
    print(f"  ✓ wiki/index.md")

    # Create log.md
    log_content = f"""# LLM Knowledge Base Activity Log

## [{today}] setup | Initialize wiki structure
Created index.md and log.md to establish the LLM Knowledge Base structure.
"""
    Path("wiki/log.md").write_text(log_content)
    print(f"  ✓ wiki/log.md")

    print(f"\n✓ Wiki files created")


def install_dependencies() -> bool:
    """Install requirements.txt if it exists."""
    req_file = Path("requirements.txt")

    if not req_file.exists():
        print(f"\n⚠ No requirements.txt found, skipping pip install")
        return True

    return run_command([sys.executable, "-m", "pip", "install", "-qr", "requirements.txt"], "Installing dependencies")


def main() -> int:
    """Main setup entry point."""
    print("=" * 50)
    print("LLM Knowledge Base Setup")
    print("=" * 50)

    # Create directories
    create_directories()

    # Create wiki files
    create_wiki_files()

    # Install dependencies
    if not install_dependencies():
        print("\n✗ Setup failed: Could not install dependencies")
        return 1

    print(f"\n{'=' * 50}")
    print("✓ Setup complete!")
    print(f"{'=' * 50}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
