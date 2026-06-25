# Limitless

[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![GEPA](https://img.shields.io/badge/engine-GEPA-6C47C7)](https://github.com/gepa-ai/gepa)
[![EvoSkill](https://img.shields.io/badge/extends-EvoSkill-6C47C7)](https://github.com/sentient-agi/EvoSkill)

Agents fail. Their execution traces contain the information needed to fix them. Limitless reads those traces, diagnoses the failure, edits the skill file, and keeps the edit if performance improves.

No model retraining. No benchmark dataset. No human annotation. Just execution traces, a reflection model, and targeted edits.


## Install

```bash
git clone https://github.com/subheeksh5599/Limitless.git
cd Limitless
pip install -e ".[dev]"
```

Requires Python 3.12+.

## CLI

```bash
# Evolve a skill file using GEPA
limitless evolve path/to/SKILL.md --iterations 20 --eval-source synthetic

# Publish a learned skill to the registry
limitless publish path/to/skill/

# Install a skill discovered by another agent
limitless install python-debugging

# Search the registry
limitless search "debugging"

# Start continuous evolution (watches execution logs)
limitless watch
```

## Commands

### `limitless evolve <skill>`

Runs the GEPA optimization loop against a skill file. A reflection model reads execution traces from failed runs, diagnoses the root cause, and proposes a targeted edit. If the edit improves performance on held-out examples, it sticks.

Options:
- `--iterations N` — number of evolution cycles (default 20)
- `--eval-source` — `synthetic`, `sessiondb`, or `golden`
- `--task-lm` — model for task execution (default `openai/gpt-4.1-mini`)
- `--reflection-lm` — model for reading traces and proposing edits (default `openai/gpt-4.1-mini`)

### `limitless publish <skill>`

Copies a skill directory into a Git-backed registry, commits it with version metadata, and pushes. Skills are directories containing `SKILL.md`, `metadata.yaml`, and optionally `README.md`.

The registry is just a Git repo. No server. No database. No API.

### `limitless install <skill>`

Pulls a skill from the registry into `.claude/skills/` (or any target directory). Installs the latest version by default. Use `--version v1.2.0` for a specific release.

### `limitless search <query>`

Searches the local clone of the registry by skill name, description, or tag. Returns matching metadata.

### `limitless watch`

Starts a background daemon that monitors agent execution logs. When failure patterns are detected, triggers the evolution loop automatically. Phase 2 of the roadmap.

## How it works

The loop has five stages:

1. **Execute** — run the agent on a task and capture the full trace (tool calls, outputs, errors, retries).
2. **Reflect** — a reflection model reads the trace and identifies the specific failure, not just that it failed but why.
3. **Mutate** — generate one targeted edit to the skill file to address the diagnosed failure.
4. **Evaluate** — run the mutated agent against held-out examples. Compare to baseline.
5. **Select** — keep the edit if it improves performance. Maintain a fixed-size frontier of best variants.

The model stays frozen throughout. Only the skill files change.

## Architecture

```
Execution Log → Reflection Model → Skill Edit
     ↑                                    ↓
     │                              Held-out Eval
     │                                    ↓
  Continuous                      Keep / Discard
  Monitor                                ↓
                                 Skill Registry
                                      ↓
                                 Other Agents
```

## Stack

| Component | Role | License |
|-----------|------|---------|
| GEPA | Reads execution traces, reflects on failures, proposes edits | MIT |
| EvoSkill | Skill discovery from agent failures, Pareto frontier selection | Apache 2.0 |
| DSPy | Programming model for LLM pipelines, signature abstraction | MIT |

## What Limitless adds

EvoSkill already discovers skills from failures and demonstrates cross-task transfer. Limitless adds:

- **Continuous evolution** — `limitless watch` monitors logs and triggers optimization without a deliberate `evoskill run` command. The agent improves through regular use.

- **Skill registry** — `limitless publish` / `install` / `search` over a Git repo. Skills discovered by one agent become available to all agents. No infrastructure overhead.

- **Cross-agent compatibility** — skills include metadata (`agent_compatibility`, `model_family`, `task_domain`) so agents can discover what applies to their current task.

## Results (from GEPA, the underlying engine)

- 55% → 82% resolve rate on Jinja coding tasks via auto-learned skills
- 32% → 89% on ARC-AGI via architecture discovered by GEPA
- 40% cloud cost savings vs expert scheduling heuristics
- +37pp NPS at Nubank (100M users, customer support agents)
- 90x cheaper than previous approach at Databricks
- 35x faster convergence than RL/GRPO (ICLR 2026)

GEPA is deployed in production at Shopify, Databricks, Google (ADK), Microsoft (MAI-Thinking-1), and Nubank.

## Contributing

The framework is early. The contribution surface:

- Adapters for agent harnesses beyond Claude Code (OpenCode, Codex, Goose, OpenHands already supported via EvoSkill)
- Eval dataset generators for skills without existing benchmarks
- Registry integration with package managers
- `limitless watch` — the continuous evolution daemon is scoped but not built

Apache 2.0. Same license as EvoSkill.
