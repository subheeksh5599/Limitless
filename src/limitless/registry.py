"""Skill registry backed by a Git repo. No server, no database.

A registry is a Git repository with a structured directory tree:

    skill-registry/
      python-debugging/
        v1.0.0/
          SKILL.md
          metadata.yaml
          README.md
        v1.1.0/
          SKILL.md
          metadata.yaml
          README.md
      github-code-review/
        v2.0.0/
          ...

The registry URL is configurable. Default points to the community registry.
"""

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

DEFAULT_REGISTRY_URL = "https://github.com/subheeksh5599/skill-registry"
DEFAULT_REGISTRY_NAME = "skill-registry"


def _ensure_registry(path: str, url: str) -> Path:
    """Clone the registry if it does not exist locally.

    Returns the path to the local registry clone.
    Returns None if the clone fails and the directory does not exist.
    """
    p = Path(path).expanduser()
    if p.exists():
        subprocess.run(["git", "-C", str(p), "pull"], capture_output=True)
        return p

    p.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", url, str(p)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return p


def _ensure_yaml():
    if yaml is None:
        print("pyyaml required for registry operations: pip install pyyaml", file=sys.stderr)
        raise SystemExit(1)


def publish_skill(
    skill_path: str,
    registry_path: str = f"~/.limitless/{DEFAULT_REGISTRY_NAME}",
    registry_url: str = DEFAULT_REGISTRY_URL,
    push: bool = True,
) -> dict[str, str]:
    """Publish a skill directory to the registry.

    The skill directory must contain:
    - SKILL.md (the skill instructions)
    - metadata.yaml (name, version, description, tags, etc.)

    Returns a dict with keys: status, name, version, registry_url.
    """
    _ensure_yaml()

    skill_dir = Path(skill_path).expanduser()
    if not skill_dir.is_dir():
        return {"status": "error", "reason": f"not a directory: {skill_path}"}

    meta_path = skill_dir / "metadata.yaml"
    if not meta_path.exists():
        return {"status": "error", "reason": "metadata.yaml not found in skill directory"}

    with open(meta_path) as f:
        meta = yaml.safe_load(f)  # type: ignore

    skill_name = meta.get("name", skill_dir.name)
    version = meta.get("version", "0.1.0")

    registry = _ensure_registry(registry_path, registry_url)
    if registry is None:
        return {"status": "error", "reason": f"registry not reachable at {registry_url}"}

    dest = registry / skill_name / f"v{version}"
    dest.mkdir(parents=True, exist_ok=True)

    for f in skill_dir.iterdir():
        shutil.copy2(f, dest / f.name)

    subprocess.run(["git", "-C", str(registry), "add", str(dest)], check=True)

    status = subprocess.run(
        ["git", "-C", str(registry), "status", "--porcelain"],
        capture_output=True, text=True,
    )
    if not status.stdout.strip():
        return {"status": "unchanged", "name": skill_name, "version": f"v{version}"}

    subprocess.run(
        ["git", "-C", str(registry), "commit", "-m",
         f"publish: {skill_name} v{version}"],
        check=True,
    )

    if push:
        subprocess.run(["git", "-C", str(registry), "push"], check=True)

    return {"status": "published", "name": skill_name, "version": f"v{version}"}


def install_skill(
    skill_name: str,
    target_dir: str = ".claude/skills",
    registry_path: str = f"~/.limitless/{DEFAULT_REGISTRY_NAME}",
    registry_url: str = DEFAULT_REGISTRY_URL,
    version: Optional[str] = None,
    pull: bool = True,
) -> dict[str, str]:
    """Install a skill from the registry into a project.

    If version is None, installs the latest version.
    """
    registry = _ensure_registry(registry_path, registry_url)
    if registry is None:
        return {"status": "error", "reason": f"registry not reachable at {registry_url}"}

    if pull:
        subprocess.run(["git", "-C", str(registry), "pull"], capture_output=True)

    skill_reg = registry / skill_name
    if not skill_reg.exists():
        # Try fuzzy match
        matches = [
            d.name for d in registry.iterdir()
            if d.is_dir() and skill_name.lower() in d.name.lower()
        ]
        if matches:
            skill_reg = registry / matches[0]
        else:
            return {"status": "error", "reason": f"skill '{skill_name}' not found"}

    if version:
        version_dir = skill_reg / version
    else:
        versions = sorted(
            [d for d in skill_reg.iterdir() if d.is_dir() and d.name.startswith("v")],
            key=lambda d: [int(n) for n in d.name[1:].split(".")],
        )
        version_dir = versions[-1] if versions else None

    if not version_dir or not version_dir.exists():
        return {"status": "error", "reason": f"version not found"}

    target = Path(target_dir) / skill_reg.name
    target.mkdir(parents=True, exist_ok=True)

    count = 0
    for f in version_dir.iterdir():
        shutil.copy2(f, target / f.name)
        count += 1

    return {
        "status": "installed",
        "name": skill_reg.name,
        "version": version_dir.name,
        "target": str(target),
        "files": str(count),
    }


def search_skills(
    query: str,
    registry_path: str = f"~/.limitless/{DEFAULT_REGISTRY_NAME}",
    registry_url: str = DEFAULT_REGISTRY_URL,
    pull: bool = True,
) -> list[dict[str, str]]:
    """Search the registry for skills matching a query.

    Matches against skill name, description, and tags.
    """
    _ensure_yaml()

    registry = _ensure_registry(registry_path, registry_url)
    if registry is None:
        return []

    if pull:
        subprocess.run(["git", "-C", str(registry), "pull"], capture_output=True)

    q = query.lower()
    results = []

    for skill_dir in sorted(registry.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue

        versions = sorted(
            [d for d in skill_dir.iterdir() if d.is_dir() and d.name.startswith("v")],
            key=lambda d: [int(n) for n in d.name[1:].split(".")],
        )
        if not versions:
            continue

        latest_meta = versions[-1] / "metadata.yaml"
        if not latest_meta.exists():
            continue

        with open(latest_meta) as f:
            meta = yaml.safe_load(f)  # type: ignore

        if (
            q in skill_dir.name.lower()
            or q in meta.get("description", "").lower()
            or any(q in t.lower() for t in meta.get("tags", []))
        ):
            results.append({
                "name": skill_dir.name,
                "version": versions[-1].name,
                "description": meta.get("description", ""),
                "tags": ", ".join(meta.get("tags", [])),
            })

    return results


def init_skill_dir(
    name: str,
    output_dir: str = ".",
    tags: Optional[list[str]] = None,
) -> str:
    """Create a new skill directory with SKILL.md and metadata.yaml."""
    _ensure_yaml()

    skill_dir = Path(output_dir) / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        skill_md.write_text(f"# {name}\n\nDescribe what this skill does and how to use it.\n")

    readme = skill_dir / "README.md"
    if not readme.exists():
        readme.write_text(f"# {name}\n\n")

    meta = {
        "name": name,
        "version": "0.1.0",
        "description": "",
        "tags": tags or [],
        "domain": "",
        "agent_compatibility": ["claude-code"],
        "author": "",
    }
    meta_path = skill_dir / "metadata.yaml"
    if not meta_path.exists():
        with open(meta_path, "w") as f:
            yaml.dump(meta, f, default_flow_style=False)  # type: ignore

    return str(skill_dir)
