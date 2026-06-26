"""Synthetic evaluation data generator for agent skills.

When no benchmark dataset exists for a skill, this module generates
realistic test cases using a strong model so the evolution loop can
still run. The generated data is split into train/val/holdout.
"""

import json
from pathlib import Path
from typing import Optional


SYNTHETIC_PROMPT = """You are generating evaluation data for an AI agent skill.

The skill is described below. Generate {n} realistic test cases that
would measure whether the agent correctly applies this skill.

Each test case must have:
- "input": a realistic task or question the agent would receive
- "expected_behavior": a description of what the agent should do
  (not an exact output — describe the expected behavior)

The test cases should cover:
- Common use cases (60%)
- Edge cases (20%)
- Failure modes where the agent might apply the skill incorrectly (20%)

Return a JSON array of objects with "input" and "expected_behavior" keys.

Skill description:
{skill_text}"""


def generate_synthetic_dataset(
    skill_path: str,
    num_examples: int = 30,
    model: Optional[str] = None,
) -> dict[str, list[dict[str, str]]]:
    """Generate synthetic train/val/holdout splits for a skill file.

    Uses a strong LLM to generate realistic test cases based on the
    skill description. Returns train/val/holdout splits.

    If no API key is configured, falls back to a set of generic
    template-based examples derived from the skill filename.
    """
    import os

    skill_text = Path(skill_path).read_text()
    skill_name = Path(skill_path).stem

    has_api_key = bool(
        os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    )

    if has_api_key and model:
        examples = _llm_generate(skill_text, num_examples, model)
    else:
        examples = _template_generate(skill_name, skill_text, num_examples)

    split = int(len(examples) * 0.6)
    val_split = int(len(examples) * 0.8)

    return {
        "train": examples[:split],
        "val": examples[split:val_split],
        "holdout": examples[val_split:],
    }


def _llm_generate(skill_text: str, n: int, model: str) -> list[dict[str, str]]:
    """Use an LLM to generate realistic test cases."""
    import os

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        response = client.chat.completions.create(
            model=model or "gpt-4.1-mini",
            messages=[
                {"role": "user", "content": SYNTHETIC_PROMPT.format(n=n, skill_text=skill_text)},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("test_cases", data.get("examples", []))
    except Exception:
        return _template_generate("skill", skill_text, n)


def _template_generate(name: str, text: str, n: int) -> list[dict[str, str]]:
    """Fallback: generate template-based examples from the skill name and content."""
    examples = []

    keywords = name.replace("-", " ").replace("_", " ").lower()
    domain_words = [w for w in keywords.split() if len(w) > 2]

    templates = [
        "Apply {skill} to: {scenario}",
        "Use {skill} to handle: {scenario}",
        "A user asks: {scenario}. Use {skill}.",
        "Fix this using {skill}: {scenario}",
        "Explain how you would use {skill} for: {scenario}",
    ]

    expected_behaviors = [
        "The agent should follow the skill procedure and produce a correct output",
        "The agent should correctly apply the skill steps without skipping any",
        "The agent should invoke the skill and follow its instructions precisely",
        "The agent should diagnose the issue and apply the skill correctly",
        "The agent should describe the application of the skill accurately",
    ]

    scenarios = [
        "a simple straightforward case",
        "a moderately complex scenario with multiple steps",
        "an edge case where the standard procedure might not apply directly",
        f"a situation where {domain_words[0] if domain_words else 'the task'} needs careful handling",
        "a case with incomplete information where the agent should ask for clarification",
    ]

    for i in range(min(n, 20)):
        tpl = templates[i % len(templates)]
        expected = expected_behaviors[i % len(expected_behaviors)]
        s = scenarios[i % len(scenarios)]
        skill_ref = name.replace("-", " ").replace("_", " ")
        inp = tpl.replace("{skill}", skill_ref).replace("{scenario}", s)
        exp = expected.replace("{skill}", skill_ref)
        examples.append({
            "input": inp,
            "expected_behavior": exp,
        })

    return examples


def save_dataset(
    dataset: dict[str, list[dict[str, str]]],
    output_dir: str,
) -> dict[str, str]:
    """Save train/val/holdout splits to JSONL files."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths = {}
    for split_name, examples in dataset.items():
        path = out / f"{split_name}.jsonl"
        with open(path, "w") as f:
            for ex in examples:
                f.write(json.dumps(ex) + "\n")
        paths[split_name] = str(path)

    return paths
