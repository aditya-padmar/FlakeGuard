"""Synthetic detection regressions: no real runners, subprocesses, or file writes."""
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, call

import pytest

from backend.harness.analyzer import TestAnalyzer as Analyzer
from backend.harness.executor import TestExecutor as Executor
from backend.models.detection import (
    TestExecution as Execution,
    TestRun as Run,
    TestStatus as Status,
)


TEST_NAME = "tests/test_synthetic.py::test_target"
OTHER_TEST = "tests/test_synthetic.py::test_other"
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
STATUSES = {
    "P": Status.PASSED,
    "F": Status.FAILED,
    "S": Status.SKIPPED,
    "E": Status.ERROR,
}


def make_runs(histories: dict[str, str]) -> list[Run]:
    """Build in-memory runs; '-' represents an absent execution, not a pass."""
    runs = []
    for index in range(max((len(history) for history in histories.values()), default=0)):
        timestamp = START + timedelta(seconds=index)
        run_id = f"synthetic-{index}"
        executions = []
        for name, history in histories.items():
            if index >= len(history) or history[index] == "-":
                continue
            status = STATUSES[history[index]]
            executions.append(Execution(
                test_name=name,
                file_path=name.split("::", 1)[0],
                status=status,
                duration=0.01 if status == Status.PASSED else 0.03,
                error_message=f"failure-{index + 1}" if status == Status.FAILED else None,
                timestamp=timestamp,
                run_id=run_id,
            ))
        runs.append(Run(
            run_id=run_id,
            repository="synthetic-repository",
            commit_sha="synthetic-commit",
            timestamp=timestamp,
            executions=executions,
            total_tests=len(executions),
            passed=sum(e.status == Status.PASSED for e in executions),
            failed=sum(e.status == Status.FAILED for e in executions),
            ordering_seed=100 + index,
            ordering=[e.test_name for e in executions],
            env_chaos={"SALES_REGION": "EU"} if index % 2 else {},
        ))
    return runs


def test_default_five_runs_detect_alternating_outcomes():
    runs = make_runs({TEST_NAME: "PFPFP"})
    result = Analyzer().analyze_runs(runs)

    assert result.total_test_runs == 5
    assert result.total_unique_tests == 1
    assert len(result.flaky_tests) == 1
    flaky = result.flaky_tests[0]
    assert flaky.test_name == TEST_NAME
    assert (flaky.pass_count, flaky.fail_count, flaky.total_runs) == (3, 2, 5)
    assert flaky.flake_rate == 0.4
    assert flaky.first_flagged_run == 2
    assert flaky.status_history == [Status.PASSED, Status.FAILED] * 2 + [Status.PASSED]
    assert flaky.recent_failures == ["failure-2", "failure-4"]
    assert flaky.passed_orderings == [100, 102, 104]
    assert flaky.failed_orderings == [101, 103]
    assert flaky.evidence["outcomes"] == ["passed", "failed", "passed", "failed", "passed"]
    assert flaky.evidence["correlates_with_env_chaos"] is True
    assert flaky.first_seen == START
    assert flaky.last_seen == START + timedelta(seconds=4)
    assert result.detection_confidence == flaky.confidence
    assert result.stable_tests == []
    assert result.rejected_tests == []


@pytest.mark.parametrize(
    ("history", "first_flagged_run"),
    [
        ("PF", 2),
        ("FP", 2),
        ("FPFPF", 2),
        ("PPPPF", 5),
        ("FFFFP", 5),
        ("PPPFFF", 4),
        ("PPPPPPPPPF", 10),
        ("FFFFFFFFFP", 10),
    ],
)
def test_mixed_evidence_is_flaky_even_with_a_single_minority_outcome(history, first_flagged_run):
    result = Analyzer(flake_threshold=0.9).analyze_runs(make_runs({TEST_NAME: history}))

    assert len(result.flaky_tests) == 1
    flaky = result.flaky_tests[0]
    passes, failures = history.count("P"), history.count("F")
    assert (flaky.pass_count, flaky.fail_count) == (passes, failures)
    assert flaky.flake_rate == round(failures / len(history), 4)
    assert flaky.first_flagged_run == first_flagged_run
    assert flaky.confidence == Analyzer._wilson_lower_bound(min(passes, failures), len(history))
    assert 0.0 < flaky.confidence < 0.5
    assert 0.0 < flaky.flakiness_score <= 100.0
    assert result.stable_tests == []
    assert result.rejected_tests == []


@pytest.mark.parametrize("history", ["P", "F", "PPPPP", "FFFFF", "PSPES", "FSEFS"])
def test_single_outcome_evidence_is_not_flaky_or_certain(history):
    result = Analyzer().analyze_runs(make_runs({TEST_NAME: history}))

    assert result.flaky_tests == []
    assert result.stable_tests == ([TEST_NAME] if "P" in history else [])
    assert len(result.rejected_tests) == 1
    assert result.rejected_tests[0]["pass_count"] == history.count("P")
    assert result.rejected_tests[0]["fail_count"] == history.count("F")
    # This field averages confidence in detected flakes, not proof of stability.
    assert result.detection_confidence == 0.0


@pytest.mark.parametrize("history", ["SSSSS", "EEEEE", "SESES"])
def test_non_pass_fail_observations_provide_no_detection_evidence(history):
    result = Analyzer().analyze_runs(make_runs({TEST_NAME: history}))

    assert result.flaky_tests == []
    assert result.stable_tests == []
    assert result.detection_confidence == 0.0
    assert result.rejected_tests == [{
        "test_name": TEST_NAME,
        "reason": "no_pass_fail_evidence",
        "pass_count": 0,
        "fail_count": 0,
    }]


def test_empty_runs_have_zero_confidence():
    for runs in ([], make_runs({TEST_NAME: "-----"})):
        result = Analyzer().analyze_runs(runs)
        assert result.total_test_runs == len(runs)
        assert result.total_unique_tests == 0
        assert result.flaky_tests == []
        assert result.stable_tests == []
        assert result.rejected_tests == []
        assert result.detection_confidence == 0.0


def test_skips_and_errors_do_not_inflate_pass_fail_confidence():
    result = Analyzer().analyze_runs(make_runs({TEST_NAME: "SPESF"}))
    reference = Analyzer().analyze_runs(make_runs({TEST_NAME: "PF"}))

    assert len(result.flaky_tests) == 1
    flaky = result.flaky_tests[0]
    assert (flaky.pass_count, flaky.fail_count, flaky.total_runs) == (1, 1, 5)
    assert flaky.flake_rate == 0.5
    assert flaky.first_flagged_run == 5
    assert flaky.confidence == reference.flaky_tests[0].confidence
    assert flaky.flakiness_score == reference.flaky_tests[0].flakiness_score
    assert flaky.evidence["outcomes"] == ["skipped", "passed", "error", "skipped", "failed"]


def test_confidence_increases_with_balanced_repeat_evidence():
    confidences = [
        Analyzer().analyze_runs(make_runs({TEST_NAME: "PF" * repeats})).flaky_tests[0].confidence
        for repeats in (1, 3, 10)
    ]
    assert 0.0 < confidences[0] < confidences[1] < confidences[2] < 0.5


def test_summary_and_confidence_include_newly_detected_flakes():
    stable_name = "tests/test_synthetic.py::test_stable"
    analyzer = Analyzer()
    result = analyzer.analyze_runs(make_runs({
        OTHER_TEST: "PPPPPF",
        TEST_NAME: "PFPFPF",
        stable_name: "PPPPPP",
    }))

    assert [test.test_name for test in result.flaky_tests] == [TEST_NAME, OTHER_TEST]
    assert result.stable_tests == [stable_name]
    assert result.detection_confidence == round(
        sum(test.confidence for test in result.flaky_tests) / 2, 4
    )
    summary = analyzer.summary(result)
    assert summary["total_unique_tests"] == 3
    assert summary["flaky_count"] == 2
    assert summary["stable_count"] == 1
    assert summary["rejected_count_by_reason"] == {"always_passed": 1}


@pytest.mark.parametrize("batch_size", [1, 3, 4, 10])
def test_executor_preserves_late_failures(batch_size):
    planned_runs = make_runs({TEST_NAME: "PPPFFF"})
    runner = Mock()
    runner.run_tests.side_effect = planned_runs
    executor = Executor(runner)

    runs = asyncio.run(executor.execute_multiple_runs(num_runs=6, batch_size=batch_size))

    assert runs == planned_runs
    assert runner.run_tests.call_count == 6
    result = Analyzer().analyze_runs(runs)
    assert len(result.flaky_tests) == 1
    assert result.flaky_tests[0].first_flagged_run == 4
    assert result.flaky_tests[0].pass_count == result.flaky_tests[0].fail_count == 3


@pytest.mark.parametrize("history", ["PPPPP", "FFFFF", "PFPFP", "SSSSS", "EEEEE", "-----"])
def test_executor_consumes_requested_runs_regardless_of_initial_outcomes(history):
    planned_runs = make_runs({TEST_NAME: history})
    runner = Mock()
    runner.run_tests.side_effect = planned_runs

    runs = asyncio.run(Executor(runner).execute_multiple_runs(num_runs=len(planned_runs)))

    assert runs == planned_runs
    assert runner.run_tests.call_count == len(planned_runs)


@pytest.mark.parametrize("late_history", ["PPPPPF", "----PF"])
def test_an_early_flake_does_not_hide_other_tests_late_failures(late_history):
    planned_runs = make_runs({TEST_NAME: "PFPFPF", OTHER_TEST: late_history})
    runner = Mock()
    runner.run_tests.side_effect = planned_runs

    runs = asyncio.run(Executor(runner).execute_multiple_runs(num_runs=6, batch_size=2))

    assert len(runs) == 6
    assert {test.test_name for test in Analyzer().analyze_runs(runs).flaky_tests} == {
        TEST_NAME, OTHER_TEST,
    }


def test_executor_does_not_analyze_partial_results():
    planned_runs = make_runs({TEST_NAME: "PFPFP"})
    runner = Mock()
    runner.run_tests.side_effect = planned_runs
    analyzer = Mock(spec=Analyzer)
    analyzer.analyze_runs.side_effect = AssertionError("Analysis belongs to the caller after execution")
    executor = Executor(runner, analyzer=analyzer)

    runs = asyncio.run(executor.execute_multiple_runs(num_runs=5, batch_size=1))

    assert runs == planned_runs
    assert executor.analyzer is analyzer
    analyzer.analyze_runs.assert_not_called()


def test_executor_preserves_plan_and_runner_arguments():
    planned_runs = make_runs({TEST_NAME: "PPPPP"})
    runner = Mock()
    runner.run_tests.side_effect = planned_runs
    executor = Executor(runner)
    plan = executor.build_run_plan(num_runs=5, base_seed=17)
    assert plan == executor.build_run_plan(num_runs=5, base_seed=17)

    runs = asyncio.run(executor.execute_multiple_runs(
        num_runs=5, batch_size=2, base_seed=17, test_pattern=TEST_NAME,
    ))

    assert runs == planned_runs
    assert runner.run_tests.call_args_list == [
        call(
            run_index=config.run_index,
            ordering_seed=config.ordering_seed,
            jitter_ms=config.jitter_ms,
            env_chaos=config.env_chaos,
            parallel=config.parallel,
            test_pattern=TEST_NAME,
        )
        for config in plan
    ]


def test_single_run_interface_is_preserved():
    run = make_runs({TEST_NAME: "P"})[0]
    runner = Mock()
    runner.run_tests.return_value = run

    assert Executor(runner).execute_single_run(
        test_pattern=TEST_NAME,
        ordering_seed=17,
        jitter_ms=15,
        env_chaos={"SALES_REGION": "EU"},
        parallel=True,
    ) is run
    runner.run_tests.assert_called_once_with(
        run_index=0,
        ordering_seed=17,
        jitter_ms=15,
        env_chaos={"SALES_REGION": "EU"},
        parallel=True,
        test_pattern=TEST_NAME,
    )
