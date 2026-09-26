"""Test run analyzer for detecting flaky tests using entropy scoring and evidence generation."""
from collections import defaultdict
from datetime import datetime, timezone
import math
from typing import Dict, List, Optional
import uuid

from backend.models.detection import (
    DetectionResult,
    FlakyTest,
    TestExecution,
    TestRun,
    TestStatus,
)


class TestAnalyzer:
    """Analyzes test runs using entropy-based flakiness scoring and evidence extraction."""

    def __init__(self, flake_threshold: float = 0.1):
        """
        Initialize analyzer.

        Args:
            flake_threshold: Backwards-compatible parameter (retained for API compatibility).
        """
        self.flake_threshold = flake_threshold

    def analyze_runs(self, runs: List[TestRun]) -> DetectionResult:
        """
        Analyze multiple test runs synchronously to detect flaky tests.
        """
        if not runs:
            now = datetime.now(timezone.utc)
            return DetectionResult(
                detection_id=str(uuid.uuid4()),
                repository="unknown",
                analysis_period_start=now,
                analysis_period_end=now,
                total_test_runs=0,
                flaky_tests=[],
                detection_confidence=0.0,
                stable_tests=[],
                rejected_tests=[],
                total_unique_tests=0,
            )

        # Collect all unique test executions preserving chronological run order
        test_runs_map: Dict[str, List[tuple[TestRun, TestExecution]]] = defaultdict(list)
        all_unique_tests: set[str] = set()

        for run in runs:
            for execution in run.executions:
                all_unique_tests.add(execution.test_name)
                test_runs_map[execution.test_name].append((run, execution))

        flaky_tests: List[FlakyTest] = []
        stable_tests: List[str] = []
        rejected_tests: List[Dict[str, object]] = []

        for test_name, pairs in test_runs_map.items():
            file_path = pairs[0][1].file_path if pairs else ""

            # Filter out skipped and error for pass/fail calculations
            valid_pairs = [
                (r, e) for r, e in pairs
                if e.status in (TestStatus.PASSED, TestStatus.FAILED)
            ]

            pass_count = sum(1 for _, e in valid_pairs if e.status == TestStatus.PASSED)
            fail_count = sum(1 for _, e in valid_pairs if e.status == TestStatus.FAILED)
            unweighted_n = pass_count + fail_count

            # 4. RECENCY WEIGHTING
            # weight execution i by w = 0.5 ** ((N - 1 - i) / 3)
            # Recompute p from weighted pass/fail totals, then compute score from weighted p
            n_valid = len(valid_pairs)
            weighted_passes = 0.0
            weighted_fails = 0.0
            for i, (_, e) in enumerate(valid_pairs):
                w = 0.5 ** ((n_valid - 1 - i) / 3.0)
                if e.status == TestStatus.PASSED:
                    weighted_passes += w
                elif e.status == TestStatus.FAILED:
                    weighted_fails += w

            weighted_total = weighted_passes + weighted_fails
            p_weighted = (weighted_passes / weighted_total) if weighted_total > 0 else 0.0

            # 2 & 3. Entropy & flakiness_score from weighted p
            if p_weighted <= 0.0 or p_weighted >= 1.0:
                weighted_entropy = 0.0
            else:
                weighted_entropy = (
                    -p_weighted * math.log2(p_weighted)
                    - (1.0 - p_weighted) * math.log2(1.0 - p_weighted)
                )
            flakiness_score = round(100.0 * weighted_entropy, 2)

            # Observing both outcomes establishes flakiness after at least two
            # executions. Sample size affects confidence, not the observed label.
            if pass_count > 0 and fail_count > 0:
                # Confidence: Wilson score 95% lower bound on minority outcome rate.
                # This remains conservative when only a few executions are available.
                k = min(pass_count, fail_count)
                confidence = self._wilson_lower_bound(k, unweighted_n)

                # first_flagged_run: earliest observation with both a pass and a failure
                first_flagged_run = self._compute_first_flagged_run(pairs)

                # 8. EVIDENCE
                evidence, failed_orderings, passed_orderings = self._extract_evidence(pairs)

                recent_failures = [
                    e.error_message
                    for _, e in pairs
                    if e.status == TestStatus.FAILED and e.error_message
                ][:5]

                all_timestamps = [e.timestamp for _, e in pairs]

                flaky_test = FlakyTest(
                    test_name=test_name,
                    file_path=file_path,
                    first_seen=min(all_timestamps) if all_timestamps else datetime.now(timezone.utc),
                    last_seen=max(all_timestamps) if all_timestamps else datetime.now(timezone.utc),
                    total_runs=len(pairs),
                    pass_count=pass_count,
                    fail_count=fail_count,
                    flake_rate=round(fail_count / unweighted_n, 4) if unweighted_n > 0 else 0.0,
                    recent_failures=recent_failures,
                    status_history=[e.status for _, e in pairs],
                    flakiness_score=flakiness_score,
                    confidence=confidence,
                    first_flagged_run=first_flagged_run,
                    failed_orderings=failed_orderings,
                    passed_orderings=passed_orderings,
                    evidence=evidence,
                )
                flaky_tests.append(flaky_test)
            else:
                # No mixed pass/fail evidence. "Stable" means observed passing,
                # not proof that further planned executions can be skipped.
                if unweighted_n == 0:
                    reason = "no_pass_fail_evidence"
                elif fail_count == 0:
                    reason = "always_passed"
                    stable_tests.append(test_name)
                else:
                    reason = "always_failed_insufficient_runs"

                rejected_tests.append({
                    "test_name": test_name,
                    "reason": reason,
                    "pass_count": pass_count,
                    "fail_count": fail_count,
                })

        # 9. Sort flaky_tests by flakiness_score DESC, then confidence DESC
        flaky_tests.sort(key=lambda t: (t.flakiness_score, t.confidence), reverse=True)
        stable_tests.sort()

        # Mean confidence in detected flakes, not confidence that a suite is clean.
        # No detected flakes (including no usable observations) provides no such evidence.
        if flaky_tests:
            mean_conf = round(sum(t.confidence for t in flaky_tests) / len(flaky_tests), 4)
        else:
            mean_conf = 0.0

        all_run_timestamps = [r.timestamp for r in runs]
        start_time = min(all_run_timestamps)
        end_time = max(all_run_timestamps)

        result = DetectionResult(
            detection_id=str(uuid.uuid4()),
            repository=runs[0].repository if runs else "unknown",
            analysis_period_start=start_time,
            analysis_period_end=end_time,
            total_test_runs=len(runs),
            flaky_tests=flaky_tests,
            detection_confidence=mean_conf,
            timestamp=datetime.now(timezone.utc),
            stable_tests=stable_tests,
            rejected_tests=rejected_tests,
            total_unique_tests=len(all_unique_tests),
        )
        return result

    @staticmethod
    def _wilson_lower_bound(k: int, n: int, z: float = 1.95996) -> float:
        """Wilson score 95% lower bound on proportion p = k/n."""
        if n <= 0 or k <= 0:
            return 0.0
        p_hat = k / n
        z2 = z * z
        denominator = 1.0 + z2 / n
        center = p_hat + z2 / (2.0 * n)
        spread = z * math.sqrt((p_hat * (1.0 - p_hat) / n) + (z2 / (4.0 * (n * n))))
        lower_bound = (center - spread) / denominator
        return max(0.0, min(1.0, round(lower_bound, 4)))

    @staticmethod
    def _compute_first_flagged_run(pairs: List[tuple[TestRun, TestExecution]]) -> Optional[int]:
        """Compute 1-based observation index where both outcomes were first seen."""
        cum_p = 0
        cum_f = 0
        for run_idx, (_, execution) in enumerate(pairs, start=1):
            if execution.status == TestStatus.PASSED:
                cum_p += 1
            elif execution.status == TestStatus.FAILED:
                cum_f += 1
            if cum_p > 0 and cum_f > 0:
                return run_idx
        return None

    @staticmethod
    def _extract_evidence(
        pairs: List[tuple[TestRun, TestExecution]],
    ) -> tuple[Dict[str, object], List[int], List[int]]:
        """Extract rich evidence dict for AI root cause attribution."""
        outcomes: List[str] = [e.status.value for _, e in pairs]

        failed_orderings: List[int] = [
            r.ordering_seed
            for r, e in pairs
            if e.status == TestStatus.FAILED and r.ordering_seed is not None
        ]
        passed_orderings: List[int] = [
            r.ordering_seed
            for r, e in pairs
            if e.status == TestStatus.PASSED and r.ordering_seed is not None
        ]

        # Correlates with env chaos check
        valid_chaos_pairs = [
            (bool(r.env_chaos), e.status)
            for r, e in pairs
            if e.status in (TestStatus.PASSED, TestStatus.FAILED)
        ]
        has_chaos = any(c for c, _ in valid_chaos_pairs)
        has_clean = any(not c for c, _ in valid_chaos_pairs)
        if has_chaos and has_clean:
            correlates_with_env_chaos = (
                all(s == TestStatus.FAILED for c, s in valid_chaos_pairs if c)
                and all(s == TestStatus.PASSED for c, s in valid_chaos_pairs if not c)
            )
        else:
            correlates_with_env_chaos = False

        # Ordering predecessor / successor analysis
        target_name = pairs[0][1].test_name

        # Prefer serial runs for in-process ordering analysis where order is deterministic
        serial_pairs = [(r, e) for r, e in pairs if not r.parallel]
        eval_pairs = serial_pairs if len(serial_pairs) >= 2 else pairs

        failing_predecessors: List[set[str]] = []
        passing_predecessors: List[set[str]] = []
        failing_successors: List[set[str]] = []
        passing_successors: List[set[str]] = []

        for r, e in eval_pairs:
            if not r.ordering or target_name not in r.ordering:
                continue
            idx = r.ordering.index(target_name)
            preds = set(r.ordering[:idx])
            succs = set(r.ordering[idx + 1:])
            if e.status == TestStatus.FAILED:
                failing_predecessors.append(preds)
                failing_successors.append(succs)
            elif e.status == TestStatus.PASSED:
                passing_predecessors.append(preds)
                passing_successors.append(succs)

        always_followed_by = None
        if failing_predecessors:
            common_fail_preds = set.intersection(*failing_predecessors)
            any_pass_preds = set.union(*passing_predecessors) if passing_predecessors else set()
            cand_fail_preds = common_fail_preds - any_pass_preds
            if cand_fail_preds:
                always_followed_by = sorted(list(cand_fail_preds))[0]

        if not always_followed_by and failing_successors:
            common_fail_succs = set.intersection(*failing_successors)
            any_pass_succs = set.union(*passing_successors) if passing_successors else set()
            cand_fail_succs = common_fail_succs - any_pass_succs
            if cand_fail_succs:
                always_followed_by = sorted(list(cand_fail_succs))[0]

        never_followed_by = None
        if passing_predecessors:
            common_pass_preds = set.intersection(*passing_predecessors)
            any_fail_preds = set.union(*failing_predecessors) if failing_predecessors else set()
            cand_pass_preds = common_pass_preds - any_fail_preds
            if cand_pass_preds:
                never_followed_by = sorted(list(cand_pass_preds))[0]

        if not never_followed_by and passing_successors:
            common_pass_succs = set.intersection(*passing_successors)
            any_fail_succs = set.union(*failing_successors) if failing_successors else set()
            cand_pass_succs = common_pass_succs - any_fail_succs
            if cand_pass_succs:
                never_followed_by = sorted(list(cand_pass_succs))[0]

        # Duration metrics
        all_durations_ms = [e.duration * 1000.0 for _, e in pairs]
        pass_durations_ms = [e.duration * 1000.0 for _, e in pairs if e.status == TestStatus.PASSED]
        fail_durations_ms = [e.duration * 1000.0 for _, e in pairs if e.status == TestStatus.FAILED]

        evidence: Dict[str, object] = {
            "outcomes": outcomes,
            "failed_orderings": failed_orderings,
            "passed_orderings": passed_orderings,
            "correlates_with_env_chaos": correlates_with_env_chaos,
            "always_followed_by": always_followed_by,
            "never_followed_by": never_followed_by,
            "min_duration_ms": round(min(all_durations_ms), 2) if all_durations_ms else 0.0,
            "max_duration_ms": round(max(all_durations_ms), 2) if all_durations_ms else 0.0,
        }

        if pass_durations_ms:
            evidence["mean_duration_pass"] = round(sum(pass_durations_ms) / len(pass_durations_ms), 2)
        if fail_durations_ms:
            evidence["mean_duration_fail"] = round(sum(fail_durations_ms) / len(fail_durations_ms), 2)

        return evidence, failed_orderings, passed_orderings

    def summary(self, result: DetectionResult) -> Dict[str, object]:
        """
        Return a JSON-serializable dictionary summarizing detection analysis.
        """
        rejected_by_reason: Dict[str, int] = defaultdict(int)
        for item in result.rejected_tests:
            reason = str(item.get("reason", "unknown"))
            rejected_by_reason[reason] += 1

        mean_flakiness = (
            round(sum(t.flakiness_score for t in result.flaky_tests) / len(result.flaky_tests), 2)
            if result.flaky_tests
            else 0.0
        )

        flaky_by_file: Dict[str, int] = defaultdict(int)
        for t in result.flaky_tests:
            flaky_by_file[t.file_path] += 1

        return {
            "total_unique_tests": result.total_unique_tests,
            "flaky_count": len(result.flaky_tests),
            "stable_count": len(result.stable_tests),
            "rejected_count_by_reason": dict(rejected_by_reason),
            "mean_flakiness_score": mean_flakiness,
            "flaky_distribution_by_file": dict(flaky_by_file),
        }
