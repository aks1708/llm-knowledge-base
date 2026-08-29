#!/usr/bin/env python3
"""Terminal quiz application for the LLM Knowledge Base."""

import argparse
import json
import random
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

try:
    import termios
    import tty
except ImportError:  # non-POSIX fallback: letter entry still works
    termios = None
    tty = None

QUIZ_DIR = Path(__file__).resolve().parent
QUIZ_FILE = QUIZ_DIR / "test_questions.json"
RESULTS_FILE = QUIZ_DIR / "results.json"
SAVE_FILE = QUIZ_DIR / "progress.json"

LETTERS = ["A", "B", "C", "D"]
DIFFICULTY_ORDER = ["easy", "medium", "hard"]
DIFFICULTY_STYLE = {"easy": "green", "medium": "yellow", "hard": "red"}
SECTION_TAGLINE = {
    "easy": "Warm-up — core recall",
    "medium": "Applied understanding",
    "hard": "Deep reasoning — think carefully",
}

console = Console()


def load_quiz():
    if not QUIZ_FILE.exists():
        console.print(f"[bold red]No questions found at {QUIZ_FILE}[/]")
        console.print("Ask the LLM to generate a quiz first (see AGENTS.md — Quiz Generation).")
        sys.exit(1)

    try:
        data = json.loads(QUIZ_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON in {QUIZ_FILE}: {exc}[/]")
        sys.exit(1)

    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        console.print("[bold red]'questions' must be a non-empty list.[/]")
        sys.exit(1)

    errors = []
    for i, q in enumerate(questions, 1):
        label = f"Question {i}"
        if not q.get("question"):
            errors.append(f"{label}: missing 'question'")
        options = q.get("options")
        if not isinstance(options, list) or len(options) != 4:
            errors.append(f"{label}: must have exactly 4 options")
        if str(q.get("answer", "")).upper() not in LETTERS:
            errors.append(f"{label}: 'answer' must be one of A-D")
        if str(q.get("difficulty", "")).lower() not in DIFFICULTY_ORDER:
            errors.append(f"{label}: 'difficulty' must be easy, medium, or hard")

    if errors:
        for error in errors:
            console.print(f"[bold red]{error}[/]")
        sys.exit(1)

    # Shuffle options per question so the correct letter varies instead of clustering.
    for q in questions:
        options = q["options"]
        correct_text = options[LETTERS.index(str(q["answer"]).upper())]
        random.shuffle(options)
        q["answer"] = LETTERS[options.index(correct_text)]

    questions.sort(key=lambda q: DIFFICULTY_ORDER.index(q["difficulty"].lower()))
    return data.get("test_title", "Quiz"), questions


def show_banner(title, questions):
    counts = {d: sum(1 for q in questions if q["difficulty"].lower() == d) for d in DIFFICULTY_ORDER}
    breakdown = " · ".join(f"{counts[d]} {d}" for d in DIFFICULTY_ORDER if counts[d])
    banner = Panel(
        Group(
            Text("LLM KNOWLEDGE BASE", style="bold cyan", justify="center"),
            Text(title, justify="center", style="bold white"),
            Text(),
            Text(f"{len(questions)} multiple-choice questions — {breakdown}", justify="center", style="dim"),
            Text("↑/↓ move · Enter confirm · or press 1–4 / A–D · Ctrl+X exit", justify="center", style="dim"),
        ),
        box=box.DOUBLE,
        border_style="cyan",
        padding=(1, 4),
    )
    console.print(banner)


def show_section_banner(diff):
    style = DIFFICULTY_STYLE[diff]
    console.print()
    console.print(
        Panel(
            Text(f"{diff.upper()}  ·  {SECTION_TAGLINE[diff]}", justify="center", style=f"bold {style}"),
            box=box.ROUNDED,
            border_style=style,
            padding=(0, 3),
        )
    )
    console.print()


def _read_key():
    """Read one keypress: arrows return 'up'/'down', Ctrl+X returns 'exit', Esc returns 'esc'.

    Letters return uppercase. Returns '' when raw keypress reading is unavailable
    (interactive selection then falls back to typed input).
    """
    if termios is None or tty is None or not sys.stdin.isatty():
        return ""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x18":  # Ctrl+X — exit the quiz
            return "exit"
        if ch == "\x1b":  # escape sequence
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                return {"A": "up", "B": "down"}.get(ch3, "")
            return "esc"
        return ch.upper()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _render_question(q, index, total, score, diff, style, selected=0, hint=True):
    console.print(Rule(f"[bold {style}]Question {index} of {total}[/] · [bold {style}]{diff.upper()}[/]", style=style))
    console.print()
    options = Table.grid(padding=(0, 2))
    options.add_row()
    for i, (letter, text) in enumerate(zip(LETTERS, q["options"])):
        cursor = "[bold reverse] ▸ [/]" if i == selected else "   "
        hl = f"bold {style}" if i == selected else ""
        options.add_row(cursor, Text(f"{letter}.", style=f"bold {style}"), Text(text, style=hl))
        if i < len(LETTERS) - 1:
            options.add_row()
    body = [
        Text(q["question"], style="bold"),
        Text(),
        options,
        Text(),
        Text(f"Score so far: {score} correct", style="dim"),
    ]
    if hint:
        body.append(Text("↑/↓ move (or 1–4 / A–D pick) · Enter confirm · Ctrl+X exit and save", style="dim"))
    console.print(Panel(Group(*body), border_style=style, padding=(1, 2)))


def _typed_answer():
    """Typed fallback for terminals without raw keypress support. Returns 'A'-'D', or None to exit."""
    raw = input("  Your answer (A-D, X to exit): ").strip().upper()
    if raw in ("X", "Q", "QUIT"):
        if _confirm_dialog("Exit the quiz?", "Yes — save and exit", "No — keep answering"):
            return None
        return ""
    return raw if raw in LETTERS else ""


def _typed_confirm(prompt, suffix_yes="", suffix_no=""):
    suffix = suffix_yes if suffix_yes == suffix_no else f" / {suffix_no}"
    return input(f"  {prompt} (y/n) [{suffix_yes}{suffix}]: ").strip().lower() == "y"


def _confirm_dialog(title, yes_label, no_label, style="yellow", note=None):
    """Selectable yes/no confirmation with arrow-key toggle. Returns True for the 'yes' option."""
    sel = 0  # default: yes
    lines = [] if note is None else [Text.from_markup(note), Text()]
    lines += [Text(title, style="bold"), Text()]
    while True:
        console.clear()
        console.print(Panel(
            Group(
                *lines,
                Text(("▸ " if sel == 0 else "  ") + yes_label, style="bold cyan" if sel == 0 else ""),
                Text(("▸ " if sel == 1 else "  ") + no_label, style="bold cyan" if sel == 1 else ""),
                Text(),
                Text("↑/↓ toggle · Enter confirm (or y/n)", style="dim"),
            ),
            border_style=style,
            padding=(1, 2),
        ))
        key = _read_key()
        if key in ("up", "down"):
            sel = 1 - sel
        elif key in ("Y", "1"):
            return True
        elif key in ("N", "2"):
            return False
        elif key in ("\r", "\n"):
            return sel == 0
        elif key == "":  # typed fallback
            return _typed_confirm(title, yes_label, no_label)


def ask(q, index, total, score, section_start):
    diff = q["difficulty"].lower()
    style = DIFFICULTY_STYLE[diff]
    console.clear()
    if section_start:
        show_section_banner(diff)
    selected = 0
    while True:
        console.clear()
        if section_start:
            show_section_banner(diff)
        _render_question(q, index, total, score, diff, style, selected)
        key = _read_key()
        if key == "up":
            selected = (selected - 1) % 4
        elif key == "down":
            selected = (selected + 1) % 4
        elif key == "exit":
            if _confirm_dialog("Exit the quiz?", "Yes — save and exit", "No — keep answering"):
                return None
        elif key in ("1", "2", "3", "4"):
            return LETTERS[int(key) - 1]
        elif key in LETTERS:
            return key
        elif key in ("\r", "\n"):
            return LETTERS[selected]
        elif key == "":  # raw keypress reading unavailable — typed fallback
            choice = _typed_answer()
            if choice is not None and choice != "":
                return choice


def show_feedback(q, chosen):
    correct_letter = q["answer"].upper()
    diff = q["difficulty"].lower()
    style = DIFFICULTY_STYLE[diff]
    was_correct = chosen == correct_letter

    if was_correct:
        verdict_line = Text(f"✔ Correct — {correct_letter} is right.", style="bold green")
    else:
        verdict_line = Group(
            Text(f"✘ Incorrect — you chose {chosen}.", style="bold red"),
            Text(
                f"The correct answer is {correct_letter}. {q['options'][LETTERS.index(correct_letter)]}",
                style="green",
            ),
        )

    console.print(
        Panel(
            Group(
                verdict_line,
                Text(),
                Text(q.get("explanation", ""), style="italic"),
                Text(),
                Text(f"Review: {q.get('source_page', 'wiki')}", style="dim cyan"),
            ),
            title="Feedback",
            border_style=style,
            padding=(1, 2),
        )
    )
    console.input("\n[dim]Press Enter for the next question...[/]")


def bar(correct, total, style, width=16):
    filled = round(width * correct / total) if total else 0
    return Text("█" * filled + "░" * (width - filled), style=style)


def verdict_for(pct):
    if pct >= 90:
        return "Outstanding — you have mastered this material."
    if pct >= 75:
        return "Strong grasp — review the misses to close the gaps."
    if pct >= 50:
        return "Solid foundation — revisit the wiki pages cited above."
    return "Time to re-read the wiki — start with the sources cited above."


def build_payload(title, mode, records, started, completed, questions=None):
    total = len(records)
    correct = sum(1 for r in records if r["was_correct"])
    by_difficulty = {}
    for d in DIFFICULTY_ORDER:
        rows = [r for r in records if r["difficulty"] == d]
        if rows:
            by_difficulty[d] = {
                "correct": sum(1 for r in rows if r["was_correct"]),
                "total": len(rows),
            }
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "title": title,
        "mode": mode,
        "completed": completed,
        "score": {
            "correct": correct,
            "total": total,
            "percentage": round(correct / total * 100, 1) if total else 0.0,
        },
        "by_difficulty": by_difficulty,
        "duration_seconds": round(time.monotonic() - started),
        "answers": records,
    }
    if questions:
        payload["questions"] = questions
    return payload


def save_results(payload):
    RESULTS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def question_ids(questions):
    return [str(q.get("id", i + 1)) for i, q in enumerate(questions)]


def load_progress(title, questions):
    """Load saved progress if it matches the current quiz, else None and clear stale file."""
    if not SAVE_FILE.exists():
        return None
    try:
        payload = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = None
    if payload and payload.get("title") == title and payload.get("question_ids") == question_ids(questions):
        return payload
    SAVE_FILE.unlink(missing_ok=True)
    return None


def save_progress(title, mode, questions, resume_index, records):
    SAVE_FILE.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "title": title,
        "mode": mode,
        "question_ids": question_ids(questions),
        "resume_index": resume_index,
        "answers": records,
    }, indent=2), encoding="utf-8")


def render_results(payload):
    score = payload["score"]
    pct = score["percentage"]
    console.clear()
    console.print(Rule("[bold cyan]Quiz Results[/]", style="cyan"))
    console.print(
        Panel(
            Group(
                Text(f"{score['correct']} / {score['total']}", justify="center", style="bold"),
                Text(f"{pct:.0f}%", justify="center", style="dim"),
                Text(),
                Text(verdict_for(pct), justify="center", style="italic"),
            ),
            box=box.DOUBLE,
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()

    table = Table(box=box.SIMPLE_HEAVY, title="By difficulty")
    table.add_column("Difficulty")
    table.add_column("Score", justify="center")
    table.add_column("")
    for d in DIFFICULTY_ORDER:
        stats = payload["by_difficulty"].get(d)
        if not stats:
            continue
        style = DIFFICULTY_STYLE[d]
        table.add_row(
            Text(d.upper(), style=f"bold {style}"),
            f"{stats['correct']}/{stats['total']}",
            bar(stats["correct"], stats["total"], style),
        )
    console.print(table)
    console.print()

    review = Table(box=box.SIMPLE, title="Answer review")
    review.add_column("#", justify="right", style="dim")
    review.add_column("Difficulty")
    review.add_column("Yours", justify="center")
    review.add_column("Correct", justify="center")
    review.add_column("Result", justify="center")
    for i, r in enumerate(payload["answers"], 1):
        style = DIFFICULTY_STYLE[r["difficulty"]]
        review.add_row(
            str(i),
            Text(r["difficulty"].upper(), style=style),
            r["selected"],
            r["correct_answer"],
            "[green]✔[/]" if r["was_correct"] else "[red]✘[/]",
        )
    console.print(review)


def run_quiz(mode):
    title, questions = load_quiz()
    show_banner(title, questions)

    saved = load_progress(title, questions)
    records = []
    start_index = 0
    if saved:
        n = len(saved["answers"])
        resume = _confirm_dialog(
            "Resume where you left off?",
            "Yes — resume",
            "No — start fresh",
            style="cyan",
            note=f"Saved progress found: {n} of {len(questions)} questions answered.",
        )
        if resume:
            records = saved["answers"]
            start_index = saved["resume_index"]
            if saved.get("mode") != mode:
                mode = saved.get("mode", mode)
                console.print(f"[dim]Resuming in {mode} mode (saved).[/]")
        else:
            SAVE_FILE.unlink(missing_ok=True)

    console.input("\n[dim]Press Enter to start · answer with arrow keys + Enter, or press 1–4 / A–D[/]")

    started = time.monotonic()
    current_diff = None
    exited_early = False

    for pos in range(start_index, len(questions)):
        q = questions[pos]
        diff = q["difficulty"].lower()
        choice = ask(q, pos + 1, len(questions), sum(1 for r in records if r["was_correct"]), diff != current_diff)
        current_diff = diff
        if choice is None:
            exited_early = True
            break
        was_correct = choice == q["answer"].upper()
        if mode == "study":
            show_feedback(q, choice)
        records.append(
            {
                "id": str(q.get("id", pos + 1)),
                "difficulty": diff,
                "question": q["question"],
                "selected": choice,
                "correct_answer": q["answer"].upper(),
                "was_correct": was_correct,
            }
        )

    if exited_early:
        save_progress(title, mode, questions, len(records), records)
        console.print(
            f"\n[yellow]Progress saved[/] — {len(records)} of {len(questions)} answered.\n"
            "[dim]Run the quiz again to resume where you left off.[/]"
        )
        return

    SAVE_FILE.unlink(missing_ok=True)
    payload = build_payload(title, mode, records, started, completed=True)
    save_results(payload)
    render_results(payload)

    duration = payload["duration_seconds"]
    console.print()
    console.print(f"[dim]Duration: {duration // 60:02d}:{duration % 60:02d} · Results saved to quiz_app/results.json[/]")
    console.print("[dim]Ask the LLM to 'evaluate my quiz answers' for a detailed breakdown.[/]")


def load_questions_for_review(payload):
    """Return question dicts matching the saved answers — from the payload itself
    (new-format results) or re-matched by id from the current quiz file."""
    questions = payload.get("questions")
    if isinstance(questions, list) and questions:
        return questions
    if not QUIZ_FILE.exists():
        return []
    try:
        return json.loads(QUIZ_FILE.read_text(encoding="utf-8")).get("questions", [])
    except json.JSONDecodeError:
        return []


def coach_report(payload):
    """Derive (strength_rows, weakness_rows, tips) from results + quiz file."""
    qmap = {str(q.get("id", i + 1)): q for i, q in enumerate(load_questions_for_review(payload))}
    by_page = {}
    for r in payload["answers"]:
        page = qmap.get(str(r["id"]), {}).get("source_page", "(unknown)")
        stats = by_page.setdefault(page, {"correct": 0, "total": 0, "misses": []})
        stats["total"] += 1
        if r["was_correct"]:
            stats["correct"] += 1
        else:
            stats["misses"].append(r)

    ordered = sorted(
        by_page.items(),
        key=lambda kv: (kv[1]["correct"] / kv[1]["total"], -kv[1]["total"]),
    )
    strengths = [(page, s) for page, s in ordered if not s["misses"]]
    weaknesses = [(page, s) for page, s in ordered if s["misses"]]

    tips = []
    n = len(payload["answers"])
    if n:
        pace = payload["duration_seconds"] / n
        if pace < 5:
            tips.append(f"Very fast pace ({pace:.0f}s/question) — consider slowing down on harder questions.")
        misses = [r for r in payload["answers"] if not r["was_correct"]]
        if misses:
            common, count = Counter(r["selected"] for r in misses).most_common(1)[0]
            if count >= max(3, len(misses) // 2):
                tips.append(
                    f"Answer pattern: '{common}' chosen on {count} of {len(misses)} misses — "
                    "a default first-plausible-option habit; re-read the question before committing."
                )
    return strengths, weaknesses, tips


def render_coach(payload):
    strengths, weaknesses, tips = coach_report(payload)
    score = payload["score"]
    console.print(Rule("[bold magenta]Coach — strengths & where to improve[/]", style="magenta"))
    if not strengths and not weaknesses:
        console.print("[dim]No per-question source data available for coaching.[/]")
        return

    if strengths:
        names = ", ".join(Path(p).stem.replace('-', ' ') for p, _ in strengths)
        body = [
            Text(
                f"You show a solid grasp of {len(strengths)} area{'s' if len(strengths) != 1 else ''} — {names}. "
                "These pages need no further review:",
                style="bold green",
            ),
            Text(),
        ]
        for page, s in strengths:
            body.append(Text(f"   • {page}", style="green"))
    else:
        body = [Text("Every page had misses this round — re-read the sources below and retry.", style="yellow")]
    console.print(Panel(Group(*body), border_style="green", title="Strengths", padding=(1, 2)))

    if weaknesses:
        all_questions = load_questions_for_review(payload)
        missed = [m for _, s in weaknesses for m in s["misses"]]
        lines = [
            Text(
                f"{score['correct']}/{score['total']} this round — the gaps cluster in "
                f"{len(weaknesses)} area{'s' if len(weaknesses) != 1 else ''}: "
                + ", ".join(Path(p).stem.replace('-', ' ') for p, _ in weaknesses)
                + ". Re-read the pages below, focusing on the concepts behind each miss, then retake the quiz.",
                style="bold",
            ),
            Text(),
        ]
        for page, s in sorted(weaknesses, key=lambda kv: -len(kv[1]["misses"])):
            count = len(s["misses"])
            lines.append(Text(
                f"• {page}  ({count} miss{'es' if count != 1 else ''})",
                style="bold cyan" if count > 1 else "cyan",
            ))
        console.print(Panel(Group(*lines), border_style="red", title="Focus next", padding=(1, 2)))

    if tips:
        console.print(Panel(
            Group(*[Text(f"† {t}", style="yellow") for t in tips]),
            title="Study tips", border_style="yellow", padding=(1, 2),
        ))


def review_results():
    if not RESULTS_FILE.exists():
        console.print("[yellow]No results yet — run the quiz first.[/]")
        return
    try:
        payload = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Could not parse results file: {exc}[/]")
        return
    if not payload.get("completed", False):
        console.print("[yellow]Last attempt is incomplete — finish the quiz to get a coached review.[/]")
    render_results(payload)
    if payload.get("completed", False):
        console.print()
        render_coach(payload)
    duration = payload.get("duration_seconds", 0)
    console.print(
        f"\n[dim]Taken {payload.get('timestamp', 'unknown')} · mode: {payload.get('mode', 'study')} · "
        f"duration {duration // 60:02d}:{duration % 60:02d}[/]"
    )


def run_quiz(mode):
    title, questions = load_quiz()
    show_banner(title, questions)

    saved = load_progress(title, questions)
    records = []
    start_index = 0
    if saved:
        n = len(saved["answers"])
        resume = _confirm_dialog(
            "Resume where you left off?",
            "Yes — resume",
            "No — start fresh",
            style="cyan",
            note=f"Saved progress found: {n} of {len(questions)} questions answered.",
        )
        if resume:
            records = saved["answers"]
            start_index = saved["resume_index"]
            if saved.get("mode") != mode:
                mode = saved.get("mode", mode)
                console.print(f"[dim]Resuming in {mode} mode (saved).[/]")
        else:
            SAVE_FILE.unlink(missing_ok=True)

    console.input("\n[dim]Press Enter to start · answer with arrow keys + Enter, or press 1–4 / A–D[/]")

    started = time.monotonic()
    current_diff = None
    exited_early = False

    for pos in range(start_index, len(questions)):
        q = questions[pos]
        diff = q["difficulty"].lower()
        choice = ask(q, pos + 1, len(questions), sum(1 for r in records if r["was_correct"]), diff != current_diff)
        current_diff = diff
        if choice is None:
            exited_early = True
            break
        was_correct = choice == q["answer"].upper()
        if mode == "study":
            show_feedback(q, choice)
        records.append(
            {
                "id": str(q.get("id", pos + 1)),
                "difficulty": diff,
                "question": q["question"],
                "selected": choice,
                "correct_answer": q["answer"].upper(),
                "was_correct": was_correct,
            }
        )

    if exited_early:
        save_progress(title, mode, questions, len(records), records)
        console.print(
            f"\n[yellow]Progress saved[/] — {len(records)} of {len(questions)} answered.\n"
            "[dim]Run the quiz again to resume where you left off.[/]"
        )
        return

    SAVE_FILE.unlink(missing_ok=True)
    payload = build_payload(title, mode, records, started, completed=True, questions=questions)
    save_results(payload)
    render_results(payload)
    console.print()
    render_coach(payload)

    duration = payload["duration_seconds"]
    console.print()
    console.print(f"[dim]Duration: {duration // 60:02d}:{duration % 60:02d} · Results saved to quiz_app/results.json[/]")


def main():
    parser = argparse.ArgumentParser(description="Terminal quiz app for the LLM Knowledge Base")
    parser.add_argument(
        "--mode",
        choices=["study", "exam"],
        default="study",
        help="study shows instant feedback; exam reveals answers at the end (default: study)",
    )
    parser.add_argument("--review", action="store_true", help="review results from the last attempt")
    args = parser.parse_args()

    if args.review:
        review_results()
    else:
        run_quiz(args.mode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Quiz interrupted — use Ctrl+X to save progress before exiting.[/]")
        sys.exit(130)