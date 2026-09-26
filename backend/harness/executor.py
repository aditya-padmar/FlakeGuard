"""Test executor module for executing complete multi-run plans."""
import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import random

from backend.harness.analyzer import TestAnalyzer
from backend.models.detection import TestRun


@dataclass
class SingleRunConfig:
    run_index: int
    ordering_seed: int
    jitter_ms: int
    parallel: bool
    env_chaos: Dict[str, str]


class TestExecutor:
    """Executes every planned test run with controlled variation."""

    def __init__(self, runner: Any, analyzer: Optional[TestAnalyzer] = None):
        self.runner = runner
        self.analyzer = analyzer or TestAnalyzer()

    def build_run_plan(self, num_runs: int = 10, base_seed: int = 42) -> List[SingleRunConfig]:
        """Build deterministic RunPlan for N runs derived from base_seed."""
        jitter_cycle = [0, 15, 40, 5, 25, 10, 35, 20]

        # Keep clean and perturbed runs balanced and reproducible so both
        # environments are exercised without depending on random sampling luck.
        half_runs = num_runs // 2
        chaos_indices = set(random.Random(base_seed).sample(range(num_runs), half_runs))

        plan: List[SingleRunConfig] = []
        for i in range(num_runs):
            # Ordering seed derived deterministically from base_seed and i
            ordering_seed = (base_seed * 10007 + i * 31337) % 1000003
            jitter_ms = jitter_cycle[i % len(jitter_cycle)]
            parallel = ((i + 1) % 3 == 0)
            env_chaos = {"SALES_REGION": "EU"} if i in chaos_indices else {}

            plan.append(
                SingleRunConfig(
                    run_index=i,
                    ordering_seed=ordering_seed,
                    jitter_ms=jitter_ms,
                    parallel=parallel,
                    env_chaos=env_chaos,
                )
            )
        return plan

    async def execute_multiple_runs(
        self,
        num_runs: int = 10,
        batch_size: int = 3,
        base_seed: int = 42,
        test_pattern: Optional[str] = None,
        **kwargs,
    ) -> List[TestRun]:
        """Execute all requested runs in batches, without inferring early stability.

        A passing prefix cannot rule out failures in later planned variations.
        Analysis is left to the caller after execution, avoiding repeated analysis
        of growing partial results. The optional analyzer is retained for API compatibility.
        """
        plan = self.build_run_plan(num_runs=num_runs, base_seed=base_seed)
        accumulated_runs: List[TestRun] = []

        for batch_start in range(0, num_runs, batch_size):
            batch_configs = plan[batch_start:batch_start + batch_size]
            for config in batch_configs:
                has_chaos = bool(config.env_chaos)
                print(
                    f"[Run {config.run_index + 1}/{num_runs}] "
                    f"Seed: {config.ordering_seed} | "
                    f"Chaos: {has_chaos} | "
                    f"Parallel: {config.parallel}"
                )

                run = await asyncio.to_thread(
                    self.runner.run_tests,
                    run_index=config.run_index,
                    ordering_seed=config.ordering_seed,
                    jitter_ms=config.jitter_ms,
                    env_chaos=config.env_chaos,
                    parallel=config.parallel,
                    test_pattern=test_pattern,
                )
                accumulated_runs.append(run)

        return accumulated_runs

    def execute_single_run(
        self,
        test_pattern: Optional[str] = None,
        ordering_seed: Optional[int] = None,
        jitter_ms: int = 0,
        env_chaos: Optional[Dict[str, str]] = None,
        parallel: bool = False,
    ) -> TestRun:
        """Execute a single test run."""
        return self.runner.run_tests(
            run_index=0,
            ordering_seed=ordering_seed,
            jitter_ms=jitter_ms,
            env_chaos=env_chaos,
            parallel=parallel,
            test_pattern=test_pattern,
        )
