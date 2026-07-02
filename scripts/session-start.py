#!/usr/bin/env python3
"""
Directions SessionStart Hook

Checks if the current project uses Directions and loads context automatically.
Returns a system message with project state for Claude to use.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime


def find_project_root():
    """Find the project root from current working directory."""
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def read_file_safely(path: Path) -> str | None:
    """Read file contents or return None if not found."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError):
        return None


def extract_current_phase(content: str) -> str | None:
    """Extract current phase from PROJECT_STATE.md content."""
    for line in content.split("\n"):
        if line.startswith("**Phase:**") or line.startswith("Phase:"):
            return line.split(":", 1)[1].strip().strip("*")
        if "current phase" in line.lower():
            return line.split(":", 1)[1].strip() if ":" in line else None
    return None


def extract_current_focus(content: str) -> str | None:
    """Extract current focus from PROJECT_STATE.md content."""
    for line in content.split("\n"):
        if line.startswith("**Focus:**") or line.startswith("Focus:"):
            return line.split(":", 1)[1].strip().strip("*")
        if "current focus" in line.lower():
            return line.split(":", 1)[1].strip() if ":" in line else None
    return None


def extract_blockers(content: str) -> list[str]:
    """Extract blockers from PROJECT_STATE.md content."""
    blockers = []
    in_blockers = False

    for line in content.split("\n"):
        if "blocker" in line.lower() and "#" in line:
            in_blockers = True
            continue
        if in_blockers:
            if line.startswith("#"):
                break
            if line.strip().startswith("-") or line.strip().startswith("*"):
                blocker = line.strip().lstrip("-*").strip()
                if blocker and blocker.lower() != "none":
                    blockers.append(blocker)

    return blockers


def get_latest_session(sessions_dir: Path) -> tuple[str | None, str | None]:
    """Get the most recent session log filename and summary."""
    if not sessions_dir.exists():
        return None, None

    session_files = sorted(
        [f for f in sessions_dir.glob("*.md") if f.name != "_index.md"],
        reverse=True
    )

    if not session_files:
        return None, None

    latest = session_files[0]
    content = read_file_safely(latest)

    # Try to extract first meaningful line as summary
    summary = None
    if content:
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 10:
                summary = line[:100] + "..." if len(line) > 100 else line
                break

    return latest.name, summary


def find_state_file(project_root: Path) -> Path | None:
    """Locate PROJECT_STATE.md — the 'is Directions set up?' sentinel.

    Installed projects keep it in docs/ (scaffolded by /setup); the Directions
    master repo keeps it at the root. Universal docs are never copied into
    projects, so docs/00_base.md must NOT be used as the sentinel.
    """
    for candidate in (
        project_root / "docs" / "PROJECT_STATE.md",
        project_root / "PROJECT_STATE.md",
    ):
        if candidate.exists():
            return candidate
    return None


def build_context_message(base_dir: Path) -> str:
    """Build the context message for a Directions project.

    base_dir is the directory containing PROJECT_STATE.md and sessions/
    (docs/ in installed projects, repo root in the master repo).
    """
    # Read PROJECT_STATE.md
    state_content = read_file_safely(base_dir / "PROJECT_STATE.md")

    phase = None
    focus = None
    blockers = []

    if state_content:
        phase = extract_current_phase(state_content)
        focus = extract_current_focus(state_content)
        blockers = extract_blockers(state_content)

    # Get latest session
    latest_session, session_summary = get_latest_session(base_dir / "sessions")

    # Build message parts
    parts = ["This project uses **Directions** for documentation and workflow."]

    if phase:
        parts.append(f"**Current Phase:** {phase}")

    if focus:
        parts.append(f"**Current Focus:** {focus}")

    if blockers:
        parts.append(f"**Blockers:** {', '.join(blockers)}")

    if latest_session:
        parts.append(f"**Last Session:** {latest_session}")
        if session_summary:
            parts.append(f"  _{session_summary}_")

    parts.append("")
    parts.append("Use `/status` for full details or `/log` to update the session log.")

    return "\n".join(parts)


def build_non_directions_message() -> str:
    """Build message for non-Directions projects."""
    return "What would you like to do?\n\n| Command | What it does |\n|---------|------------|\n| `/setup` | Detect project state, set up or migrate Directions |\n| `/status` | Check current phase, focus, blockers, last session |\n| `/log` | Create or update today's session log |\n| `/decide` | Record an architectural/design decision |\n| `/interview` | Run the full discovery interview |\n| `/learned` | Add a term to your personal glossary |\n| `/reorg` | Reorganize folder structure (numbered folders) |\n| `/update-directions` | Pull latest Directions from GitHub |\n\nOr just tell me what you're working on."


def main():
    project_root = Path(find_project_root())
    state_file = find_state_file(project_root)

    if state_file:
        context = build_context_message(state_file.parent)
    else:
        context = build_non_directions_message()

    # SessionStart hook output: additionalContext is injected into the session.
    # (The old {"message": ...} key is not a recognized hook output and was ignored.)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
