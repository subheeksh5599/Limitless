# Limitless

An open-source framework that makes agents better by reading their own execution traces. No retraining the model. No benchmark datasets. No human annotation.

```
pip install limitless
```

```
limitless evolve path/to/SKILL.md --iterations 20
limitless publish path/to/skill/
limitless install python-debugging
limitless watch
```

## How

Agents produce execution traces. Those traces contain failure information — bad tool calls, error messages, reasoning gaps. A reflection model reads the trace, identifies what went wrong, and edits the skill file to fix it. If the edit improves performance on held-out examples, it sticks. If not, it gets discarded.

Built on [GEPA](https://github.com/gepa-ai/gepa) (ICLR 2026 Oral) and extending [EvoSkill](https://github.com/sentient-agi/EvoSkill).

## Install

```bash
git clone https://github.com/limitless/limitless.git
cd limitless
pip install -e ".[dev]"
```

## Stack

- **GEPA** — Reflective text evolution. Reads execution traces to diagnose failures. MIT.
- **EvoSkill** — Skill discovery from agent failures. Sentient Labs. Apache 2.0.
- **DSPy** — Programming model for LLM pipelines. Stanford NLP.

## License

Apache 2.0
