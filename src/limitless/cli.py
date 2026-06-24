"""CLI for Limitless."""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(prog="limitless")
    subparsers = parser.add_subparsers(dest="command")

    evolve = subparsers.add_parser("evolve")
    evolve.add_argument("skill")
    evolve.add_argument("--iterations", type=int, default=20)
    evolve.add_argument("--eval-source", default="synthetic")
    evolve.add_argument("--task-lm", default="openai/gpt-4.1-mini")
    evolve.add_argument("--reflection-lm", default="openai/gpt-4.1-mini")

    publish = subparsers.add_parser("publish")
    publish.add_argument("skill")

    install = subparsers.add_parser("install")
    install.add_argument("skill")
    install.add_argument("--version")

    search = subparsers.add_parser("search")
    search.add_argument("query")

    subparsers.add_parser("watch")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    print(f"limitless {args.command} — scaffold. full GEPA integration in progress.")


if __name__ == "__main__":
    main()
