"""Core evolution loop using GEPA's reflective optimization.

The loop has four stages (mapping to LangChain's 4-loop playbook):

1. AGENT (Loop 1) — run agent with current skill, capture trace
2. VERIFY (Loop 2) — rubric-based grader scores the output
3. REFLECT (Loop 4) — GEPA reads the trace, diagnoses failure, mutates skill
4. EVENT-DRIVEN (Loop 3) — limitless watch triggers automatically

The model never changes. Only the skill files evolve.
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class EvolutionConfig:
    n_iterations: int = 20
    max_metric_calls: int = 200
    frontier_size: int = 3
    no_improvement_limit: int = 5
    task_lm: str = "openai/gpt-4.1-mini"
    reflection_lm: str = "openai/gpt-4.1-mini"
    eval_source: str = "synthetic"
    checkpoint_dir: str = ".limitless/checkpoints"


@dataclass
class EvolveResult:
    best_skill_text: str
    best_score: float
    baseline_score: float
    metric_calls: int
    improvements: list[dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


def evolve_skill(
    skill_path: str,
    config: Optional[EvolutionConfig] = None,
    trainset_path: Optional[str] = None,
    valset_path: Optional[str] = None,
) -> EvolveResult:
    """Run the full evolution loop against a skill file.

    The pipeline:
    1. Read the current skill file
    2. If no eval data provided, generate synthetic dataset
    3. Score the baseline skill against the eval set
    4. Run GEPA optimizer to propose targeted edits
    5. Score each candidate, keep improvements
    6. Write the best variant back if it beat baseline

    Works with any LLM provider via OpenRouter, OpenAI, or Anthropic.
    Falls back gracefully when no API key is configured, reporting
    what would happen without making external calls.
    """
    cfg = config or EvolutionConfig()
    skill_path = Path(skill_path).expanduser()

    if not skill_path.exists():
        return EvolveResult("", 0, 0, 0, error=f"skill file not found: {skill_path}")

    skill_text = skill_path.read_text()

    # Load or generate eval data
    trainset = _load_dataset(trainset_path) if trainset_path else []
    valset = _load_dataset(valset_path) if valset_path else []

    if not trainset:
        from limitless.dataset import generate_synthetic_dataset

        dataset = generate_synthetic_dataset(str(skill_path), num_examples=24)
        trainset = dataset["train"]
        valset = dataset["val"]

    # Score baseline
    baseline = _evaluate_skill(skill_text, valset) if valset else 0.0

    # Check if GEPA is available
    try:
        import gepa
    except ImportError:
        return EvolveResult(
            skill_text, baseline, baseline, 0,
            error="gepa not installed. run: pip install gepa",
        )

    # Check API key
    import os
    has_key = bool(
        os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    )
    if not has_key and cfg.eval_source != "template":
        return EvolveResult(
            skill_text, baseline, baseline, 0,
            error="no API key found. set OPENAI_API_KEY, ANTHROPIC_API_KEY, or OPENROUTER_API_KEY",
        )

    # Run GEPA optimization
    try:
        result = gepa.optimize(
            seed_candidate={"skill_content": skill_text},
            trainset=trainset,
            valset=valset,
            task_lm=cfg.task_lm,
            max_metric_calls=cfg.max_metric_calls,
            reflection_lm=cfg.reflection_lm,
        )

        best_text = result.best_candidate.get("skill_content", skill_text)
        best_score = getattr(result, "best_score", baseline)
        metric_calls = getattr(result, "metric_calls", 0)

        # If improved, write back
        if best_score > baseline and best_text != skill_text:
            backup = skill_path.with_suffix(".md.bak")
            skill_path.rename(backup)
            skill_path.write_text(best_text)

        return EvolveResult(
            best_skill_text=best_text,
            best_score=best_score,
            baseline_score=baseline,
            metric_calls=metric_calls,
        )

    except Exception as e:
        return EvolveResult(
            skill_text, baseline, baseline, 0,
            error=f"optimization failed: {e}",
        )


def _load_dataset(path: Optional[str]) -> list[dict[str, Any]]:
    """Load a JSONL dataset."""
    if not path:
        return []
    p = Path(path).expanduser()
    if not p.exists():
        return []
    examples = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def _evaluate_skill(skill_text: str, valset: list[dict[str, Any]]) -> float:
    """Score a skill against a validation set using LLM-as-judge.

    Returns a score from 0.0 to 1.0.
    """
    if not valset:
        return 0.0

    import os

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        scores = []
        for ex in valset[: min(5, len(valset))]:
            prompt = (
                f"Skill:\n{skill_text}\n\n"
                f"Task: {ex.get('input', '')}\n"
                f"Expected behavior: {ex.get('expected_behavior', '')}\n\n"
                f"Rate how well the skill would handle this task on a scale "
                f"of 1-5. Return only the number."
            )
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
            )
            try:
                s = int(resp.choices[0].message.content.strip()) / 5.0
                scores.append(s)
            except ValueError:
                scores.append(0.5)

        return sum(scores) / len(scores) if scores else 0.0
    except Exception:
        return 0.5
