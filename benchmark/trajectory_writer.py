"""
Utilities for saving per-task MCP-Bench agent trajectories.
"""

import re
from pathlib import Path
from typing import Union


PathLike = Union[str, Path]


def sanitize_path_component(value: str) -> str:
    """Return a filesystem-safe path component."""
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._")
    return sanitized or "unknown"


def build_trajectory_path(output_dir: PathLike, model_name: str, task_id: str) -> Path:
    """Build the destination path for a task trajectory file."""
    return (
        Path(output_dir)
        / sanitize_path_component(model_name)
        / f"{sanitize_path_component(task_id)}.txt"
    )


def write_task_trajectory(
    output_dir: PathLike,
    task_id: str,
    model_name: str,
    server_name: str,
    task_description: str,
    trajectory_text: str,
) -> str:
    """Write a per-task trajectory text file and return its path."""
    trajectory_path = build_trajectory_path(output_dir, model_name, task_id)
    trajectory_path.parent.mkdir(parents=True, exist_ok=True)

    content = "\n".join([
        f"Task ID: {task_id}",
        f"Model: {model_name}",
        f"Server: {server_name}",
        "",
        "Task Description:",
        task_description or "",
        "",
        "--- TRAJECTORY ---",
        trajectory_text or "",
        "",
    ])
    trajectory_path.write_text(content, encoding="utf-8")
    return str(trajectory_path)
