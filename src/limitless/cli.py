"""CLI for Limitless.

limitless evolve <skill>      — run GEPA optimization against a skill file
limitless publish <skill>     — publish a skill to the Git registry
limitless install <skill>     — install a skill from the registry
limitless search <query>      — search the registry
limitless init <name>         — scaffold a new skill directory
limitless watch               — start continuous evolution daemon (WIP)
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional


def _check_config():
    """Check environment and report issues."""
    issues = []

    if not (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    ):
        issues.append("no LLM API key found — set OPENAI_API_KEY or OPENROUTER_API_KEY")

    try:
        import gepa  # noqa: F401
    except ImportError:
        issues.append("gepa not installed — run: pip install gepa")

    return issues


def cmd_evolve(args):
    """Run the evolution loop against a skill file."""
    from limitless.evolution import evolve_skill, EvolutionConfig

    skill_path = Path(args.skill).expanduser()

    if not skill_path.exists():
        print(f"error: {skill_path} not found", file=sys.stderr)
        raise SystemExit(1)

    config = EvolutionConfig(
        n_iterations=args.iterations,
        max_metric_calls=args.max_calls,
        task_lm=args.task_lm,
        reflection_lm=args.reflection_lm,
        eval_source=args.eval_source,
    )

    print(f"evolving {skill_path.name}")
    print(f"  iterations: {args.iterations}")
    print(f"  max metric calls: {args.max_calls}")
    print(f"  task model: {args.task_lm}")
    print(f"  reflection model: {args.reflection_lm}")
    print(f"  eval source: {args.eval_source}")
    print()

    result = evolve_skill(
        str(skill_path),
        config=config,
    )

    if result.error:
        print(f"  error: {result.error}", file=sys.stderr)
        return

    delta = result.best_score - result.baseline_score
    direction = "↑" if delta > 0 else ("↓" if delta < 0 else "—")
    print(f"  baseline: {result.baseline_score:.3f}")
    print(f"  best:     {result.best_score:.3f} ({direction}{abs(delta):+.3f})")
    print(f"  metric calls: {result.metric_calls}")

    if delta > 0:
        print(f"\n  skill improved and saved to {skill_path}")


def cmd_publish(args):
    """Publish a skill to the registry."""
    from limitless.registry import publish_skill

    result = publish_skill(
        args.skill,
        push=not args.no_push,
    )

    if result["status"] == "error":
        print(f"error: {result.get('reason', 'unknown')}", file=sys.stderr)
        raise SystemExit(1)

    print(f"published {result['name']} {result['version']}")


def cmd_install(args):
    """Install a skill from the registry."""
    from limitless.registry import install_skill

    result = install_skill(
        args.skill,
        target_dir=args.target,
        version=args.version,
        pull=not args.offline,
    )

    if result["status"] == "error":
        print(f"error: {result.get('reason', 'unknown')}", file=sys.stderr)
        raise SystemExit(1)

    print(f"installed {result['name']} {result['version']}")
    print(f"  → {result['target']} ({result.get('files', 0)} files)")


def cmd_search(args):
    """Search the skill registry."""
    from limitless.registry import search_skills

    results = search_skills(args.query, pull=not args.offline)

    if not results:
        print(f"no skills found for '{args.query}'")
        print("  (registry may be empty or offline)")
        return

    print(f"{len(results)} skill(s) found for '{args.query}':\n")
    for r in results:
        print(f"  {r['name']} {r['version']}")
        if r["description"]:
            print(f"    {r['description']}")
        if r["tags"]:
            print(f"    tags: {r['tags']}")
        print()


def cmd_init(args):
    """Scaffold a new skill directory."""
    from limitless.registry import init_skill_dir

    tags = args.tags.split(",") if args.tags else None
    path = init_skill_dir(args.name, output_dir=args.output, tags=tags)
    print(f"created {path}/")
    print(f"  SKILL.md — edit this with your skill instructions")
    print(f"  metadata.yaml — name, version, tags, compatibility")
    print()
    print(f"  next: limitless evolve {path}/SKILL.md")


def cmd_watch(_args):
    """Start continuous evolution daemon."""
    print("limitless watch — continuous evolution daemon")
    print("  status: planned (phase 2)")
    print("  monitors agent execution logs and triggers evolution automatically")
    print()
    print("  to use manual evolution for now:")
    print("    limitless evolve path/to/SKILL.md --iterations 20")


def main():
    parser = argparse.ArgumentParser(
        prog="limitless",
        description="self-evolving agent framework — discover, refine, and share agent skills",
    )
    sub = parser.add_subparsers(dest="command")

    # evolve
    p = sub.add_parser("evolve", help="run GEPA optimization against a skill file")
    p.add_argument("skill", help="path to SKILL.md or skill directory")
    p.add_argument("--iterations", type=int, default=20, help="evolution cycles (default 20)")
    p.add_argument("--max-calls", type=int, default=200, help="max metric evaluations (default 200)")
    p.add_argument("--task-lm", default="openai/gpt-4.1-mini", help="model for task execution")
    p.add_argument("--reflection-lm", default="openai/gpt-4.1-mini", help="model for reading traces and proposing edits")
    p.add_argument("--eval-source", default="synthetic", choices=["synthetic", "sessiondb", "golden", "template"])

    # publish
    p = sub.add_parser("publish", help="publish a skill to the Git registry")
    p.add_argument("skill", help="path to skill directory with metadata.yaml")
    p.add_argument("--no-push", action="store_true", help="commit locally but do not push to remote")

    # install
    p = sub.add_parser("install", help="install a skill from the registry")
    p.add_argument("skill", help="skill name to install")
    p.add_argument("--version", help="specific version (default: latest)")
    p.add_argument("--target", default=".claude/skills", help="install directory (default: .claude/skills)")
    p.add_argument("--offline", action="store_true", help="skip git pull")

    # search
    p = sub.add_parser("search", help="search the skill registry")
    p.add_argument("query", help="search term")
    p.add_argument("--offline", action="store_true", help="skip git pull")

    # init
    p = sub.add_parser("init", help="scaffold a new skill directory")
    p.add_argument("name", help="skill name")
    p.add_argument("--output", default=".", help="parent directory (default: .)")
    p.add_argument("--tags", help="comma-separated tags")

    # watch
    sub.add_parser("watch", help="start continuous evolution daemon (WIP)")

    # parse
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    # Run health check for commands that need API keys
    api_commands = {"evolve"}
    if args.command in api_commands:
        issues = _check_config()
        if issues:
            print("pre-flight checks:", file=sys.stderr)
            for i in issues:
                print(f"  ⚠  {i}", file=sys.stderr)
            print(file=sys.stderr)
            if args.command == "evolve":
                print("evolution will use synthetic template data (no LLM required)")
                print("set API keys for full GEPA-powered optimization")
                print()

    # Dispatch
    dispatch = {
        "evolve": cmd_evolve,
        "publish": cmd_publish,
        "install": cmd_install,
        "search": cmd_search,
        "init": cmd_init,
        "watch": cmd_watch,
    }

    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
