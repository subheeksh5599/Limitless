"""Core evolution loop using GEPA's reflective optimization."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import gepa


@dataclass
class EvolutionConfig:
    max_iterations: int = 20
    frontier_size: int = 3
    max_metric_calls: int = 200
    no_improvement_limit: int = 5
    reflection_lm: str = "openai/gpt-4.1-mini"
    task_lm: str = "openai/gpt-4.1-mini"
    checkpoint_dir: str = ".limitless/checkpoints"


@dataclass
class EvolutionState:
    iteration: int = 0
    best_score: float = 0.0
    evaluations_since_improvement: int = 0
    frontier: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)


def evolve_skill(
    skill_path: str,
    trainset: list[Any],
    valset: list[Any],
    config: Optional[EvolutionConfig] = None,
) -> dict[str, Any]:
    """Evolve a skill file using GEPA.

    Reads the current SKILL.md, wraps it as an optimizable text
    parameter, and runs the GEPA optimizer against eval data.
    """
    cfg = config or EvolutionConfig()
    skill_text = Path(skill_path).read_text()

    seed = {"skill_content": skill_text}

    result = gepa.optimize(
        seed_candidate=seed,
        trainset=trainset,
        valset=valset,
        task_lm=cfg.task_lm,
        max_metric_calls=cfg.max_metric_calls,
        reflection_lm=cfg.reflection_lm,
    )

    return {
        "best_skill": result.best_candidate["skill_content"],
        "best_score": result.best_score,
        "baseline_score": result.baseline_score,
        "metric_calls": result.metric_calls,
        "history": getattr(result, "history", []),
    }
