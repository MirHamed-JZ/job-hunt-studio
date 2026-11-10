"""Shared helpers for the Job Hunt Studio tools: read a workspace's jhs.yaml, find its files and resume tags.

Needs PyYAML (installed in the workspace .venv by /job-hunt-studio:setup). Run every tool from the workspace
folder (the one that holds jhs.yaml); the tools also find it from a subfolder.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
LEDGER = Path("docs") / "Evidence_Ledger.md"


class ConfigError(Exception):
    """jhs.yaml is missing or unreadable."""


def workspace_root(start: Path | None = None) -> Path:
    """The nearest folder at or above `start` (default: the current folder) that holds jhs.yaml."""
    here = (start or Path.cwd()).resolve()
    for folder in [here, *here.parents]:
        if (folder / "jhs.yaml").is_file():
            return folder
    raise ConfigError("No jhs.yaml in this folder or above it. Run /job-hunt-studio:setup in your workspace folder.")


class Config:
    def __init__(self, data: dict, root: Path):
        self.data = data or {}
        self.root = root

    def get(self, dotted: str, default=None):
        node = self.data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def is_set(self, dotted: str) -> bool:
        value = self.get(dotted)
        return value not in (None, "", [], {})

    @property
    def ledger_path(self) -> Path:
        return self.root / LEDGER

    def ledger_text(self) -> str:
        return self.ledger_path.read_text(encoding="utf-8")

    @property
    def base_tex(self) -> Path:
        return self.root / self.get("resume.base_tex", "resumes/base/Resume.tex")

    @property
    def tag_prefix(self) -> str:
        return self.get("resume.tag_prefix", "resume-approved-v") or "resume-approved-v"

    @property
    def output_name(self) -> str:
        name = self.get("resume.output_name") or ""
        if name:
            return name if name.lower().endswith(".pdf") else name + ".pdf"
        person = re.sub(r"[^A-Za-z0-9]+", "_", self.get("candidate.name", "") or "").strip("_")
        return f"{person or 'My'}_Resume.pdf"


def load(start: Path | None = None) -> Config:
    try:
        import yaml
    except ImportError as exc:  # the venv is missing or incomplete
        raise ConfigError("PyYAML is not installed. Run /job-hunt-studio:setup tools to create the workspace .venv.") from exc
    root = workspace_root(start)
    try:
        data = yaml.safe_load((root / "jhs.yaml").read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"jhs.yaml is not valid YAML: {exc}") from exc
    return Config(data if isinstance(data, dict) else {}, root)


def git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", check=check)


def approved_tags(root: Path, prefix: str) -> list[tuple[int, str]]:
    """(number, tag) for every approved-resume tag, oldest first."""
    out = git(root, "tag", "-l", f"{prefix}*").stdout.split()
    tags = []
    for tag in out:
        m = re.fullmatch(re.escape(prefix) + r"(\d+)", tag)
        if m:
            tags.append((int(m.group(1)), tag))
    return sorted(tags)


def latest_tag(root: Path, prefix: str) -> str | None:
    tags = approved_tags(root, prefix)
    return tags[-1][1] if tags else None


def pack_keywords(cfg: Config) -> dict:
    """The pack's keywords.yaml (titles, keywords, buzzwords, rubric emphasis), or {} when there is none."""
    pack = cfg.get("pack") or "none"
    path = PLUGIN_ROOT / "packs" / str(pack) / "keywords.yaml"
    if pack == "none" or not path.is_file():
        return {}
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
