"""The documents and skills point at things that exist: skill names, preflight entries, plugin files, links.

Run from the plugin folder: python -m unittest discover tests
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

SKILLS = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))
TEXT_FILES = [ROOT / "README.md", ROOT / "CHANGELOG.md", *sorted((ROOT / "docs").glob("*.md")),
              *sorted((ROOT / "skills").rglob("*.md")), *sorted((ROOT / "agents").glob("*.md")),
              *sorted((ROOT / "templates").rglob("*.md")), *sorted((ROOT / "packs").rglob("*.md")),
              *sorted((ROOT / "examples").rglob("*.md")), ROOT / "evals" / "README.md"]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def slug(heading: str) -> str:
    """GitHub's anchor for a heading."""
    s = re.sub(r"[`*_\[\]()]", "", heading.strip().lower())
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


class Consistency(unittest.TestCase):
    def test_every_skill_has_a_name_and_description(self):
        for name in SKILLS:
            with self.subTest(name):
                text = read(ROOT / "skills" / name / "SKILL.md")
                front = text.split("---")[1]
                self.assertRegex(front, rf"(?m)^name: {re.escape(name)}$")
                self.assertRegex(front, r"(?m)^description: .{40,}")

    def test_skill_names_in_text_exist(self):
        for path in TEXT_FILES:
            for name in re.findall(r"/job-hunt-studio:([a-z][a-z-]*)", read(path)):
                with self.subTest(file=path.relative_to(ROOT).as_posix(), skill=name):
                    self.assertIn(name, SKILLS)

    def test_readme_lists_every_skill(self):
        readme = read(ROOT / "README.md")
        for name in SKILLS:
            with self.subTest(name):
                self.assertIn(f"`{name}", readme)

    def test_preflight_entries_exist(self):
        from preflight import NEEDS

        for path in (ROOT / "skills").rglob("SKILL.md"):
            for entry in re.findall(r"preflight\.py ([a-z][a-z-]*)", read(path)):
                with self.subTest(file=path.parent.name, entry=entry):
                    self.assertIn(entry, NEEDS)

    def test_plugin_paths_in_skills_exist(self):
        for path in (ROOT / "skills").rglob("*.md"):
            text = read(path)
            for ref in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s`)\"']+)", text):
                ref = ref.rstrip(".,;:")
                fixed = ref.split("<")[0]  # a placeholder such as packs/<pack>/ checks only its fixed part
                with self.subTest(file=path.relative_to(ROOT).as_posix(), ref=ref):
                    self.assertTrue((ROOT / fixed).exists(), ref)
            for ref in re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([^\s`)\"']+)", text):
                ref = ref.rstrip(".,;:")
                with self.subTest(file=path.relative_to(ROOT).as_posix(), ref=ref):
                    self.assertTrue((path.parent / ref).exists(), ref)

    def test_relative_links_and_anchors_resolve(self):
        for path in [ROOT / "README.md", ROOT / "CHANGELOG.md", *sorted((ROOT / "docs").glob("*.md")),
                     *sorted((ROOT / "packs").rglob("README.md")), ROOT / "examples" / "persona" / "README.md",
                     ROOT / "templates" / "resume" / "README.md", ROOT / "evals" / "README.md"]:
            for target in re.findall(r"\]\(([^)\s]+)\)", read(path)):
                if re.match(r"[a-z]+:", target):
                    continue
                file_part, _, anchor = target.partition("#")
                dest = (path.parent / file_part).resolve() if file_part else path
                with self.subTest(file=path.relative_to(ROOT).as_posix(), link=target):
                    self.assertTrue(dest.exists(), target)
                    if anchor and dest.is_file() and dest.suffix == ".md":
                        headings = re.findall(r"(?m)^#{1,6} (.+)$", read(dest))
                        self.assertIn(anchor, [slug(h) for h in headings])


if __name__ == "__main__":
    unittest.main()
