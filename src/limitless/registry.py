"""Skill registry backed by a Git repo. No server, no database."""

import subprocess
from pathlib import Path
from typing import Optional

DEFAULT_REGISTRY = "https://github.com/limitless/skill-registry"


def publish_skill(
    skill_path: str,
    registry_path: str = "~/.limitless/skill-registry",
    registry_url: str = DEFAULT_REGISTRY,
) -> dict[str, str]:
    """Copy a skill into the registry, commit, and push."""
    import shutil
    import yaml

    registry = Path(registry_path).expanduser()
    if not registry.exists():
        subprocess.run(["git", "clone", registry_url, str(registry)], check=True)

    skill_dir = Path(skill_path)
    meta_path = skill_dir / "metadata.yaml"
    if not meta_path.exists():
        return {"status": "error", "reason": "metadata.yaml not found"}

    with open(meta_path) as f:
        meta = yaml.safe_load(f)

    dest = registry / skill_dir.name / f"v{meta['version']}"
    dest.mkdir(parents=True, exist_ok=True)
    for f in skill_dir.iterdir():
        shutil.copy2(f, dest / f.name)

    subprocess.run(["git", "-C", str(registry), "add", str(dest)], check=True)
    subprocess.run(
        ["git", "-C", str(registry), "commit", "-m", f"publish: {skill_dir.name} v{meta['version']}"],
        check=True,
    )
    subprocess.run(["git", "-C", str(registry), "push"], check=True)

    return {"status": "published", "name": skill_dir.name, "version": f"v{meta['version']}"}


def install_skill(
    skill_name: str,
    target_dir: str = ".claude/skills",
    registry_path: str = "~/.limitless/skill-registry",
    version: Optional[str] = None,
) -> dict[str, str]:
    """Install a skill from the registry into a project."""
    import shutil

    registry = Path(registry_path).expanduser()
    skill_reg = registry / skill_name
    if not skill_reg.exists():
        return {"status": "error", "reason": f"skill '{skill_name}' not found"}

    if version is None:
        versions = sorted(
            [d for d in skill_reg.iterdir() if d.is_dir() and d.name.startswith("v")],
            key=lambda d: [int(n) for n in d.name[1:].split(".")],
        )
        if not versions:
            return {"status": "error", "reason": "no versions found"}
        version_dir = versions[-1]
    else:
        version_dir = skill_reg / version
        if not version_dir.exists():
            return {"status": "error", "reason": f"version {version} not found"}

    target = Path(target_dir) / skill_name
    target.mkdir(parents=True, exist_ok=True)
    for f in version_dir.iterdir():
        shutil.copy2(f, target / f.name)

    return {"status": "installed", "name": skill_name, "version": version_dir.name, "target": str(target)}


def search_skills(
    query: str,
    registry_path: str = "~/.limitless/skill-registry",
) -> list[dict[str, str]]:
    """Search the registry by name, description, or tag."""
    import yaml

    registry = Path(registry_path).expanduser()
    if not registry.exists():
        return []

    results = []
    q = query.lower()

    for skill_dir in registry.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        versions = sorted(
            [d for d in skill_dir.iterdir() if d.is_dir() and d.name.startswith("v")],
            key=lambda d: [int(n) for n in d.name[1:].split(".")],
        )
        if not versions:
            continue

        meta_path = versions[-1] / "metadata.yaml"
        if not meta_path.exists():
            continue

        with open(meta_path) as f:
            meta = yaml.safe_load(f)

        if (
            q in skill_dir.name.lower()
            or q in meta.get("description", "").lower()
            or any(q in t.lower() for t in meta.get("tags", []))
        ):
            results.append(meta)

    return results
