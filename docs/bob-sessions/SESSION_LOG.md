
### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 19:28:06 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestOrderingIssues::test_second` (2026-09-25 19:28:06 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.75, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found order_naming pattern: 'def test_second(self):'; Line 2: Found order_naming pattern: '"""Test that depends on test_first running before it."""'; Line 3: Found shared_state pattern: 'calc = get_shared_calculator()'.
- **Evidence Count**: 7 items identified

### Session: `TestStateLeakage::test_global_mutation` (2026-09-25 19:28:06 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.95, 'state_leakage': 1.0, 'environment': 0.0}`
- **Reasoning**: State leakage detected (100%): Line 2: Found global_mutation pattern: '"""Test that mutates global state."""'; Line 3: Found shared_instance pattern: 'calc = get_shared_calculator()'; Line 4: Found state_mutation pattern: 'calc.clear()'.
- **Evidence Count**: 7 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 19:28:06 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 19:47:25 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestOrderingIssues::test_second` (2026-09-25 19:47:25 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.75, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found order_naming pattern: 'def test_second(self):'; Line 2: Found order_naming pattern: '"""Test that depends on test_first running before it."""'; Line 3: Found shared_state pattern: 'calc = get_shared_calculator()'.
- **Evidence Count**: 7 items identified

### Session: `TestStateLeakage::test_global_mutation` (2026-09-25 19:47:25 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.95, 'state_leakage': 1.0, 'environment': 0.0}`
- **Reasoning**: State leakage detected (100%): Line 2: Found global_mutation pattern: '"""Test that mutates global state."""'; Line 3: Found shared_instance pattern: 'calc = get_shared_calculator()'; Line 4: Found state_mutation pattern: 'calc.clear()'.
- **Evidence Count**: 7 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 19:47:25 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 19:56:58 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestOrderingIssues::test_second` (2026-09-25 19:56:58 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.75, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found order_naming pattern: 'def test_second(self):'; Line 2: Found order_naming pattern: '"""Test that depends on test_first running before it."""'; Line 3: Found shared_state pattern: 'calc = get_shared_calculator()'.
- **Evidence Count**: 7 items identified

### Session: `TestStateLeakage::test_global_mutation` (2026-09-25 19:56:58 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.95, 'state_leakage': 1.0, 'environment': 0.0}`
- **Reasoning**: State leakage detected (100%): Line 2: Found global_mutation pattern: '"""Test that mutates global state."""'; Line 3: Found shared_instance pattern: 'calc = get_shared_calculator()'; Line 4: Found state_mutation pattern: 'calc.clear()'.
- **Evidence Count**: 7 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 19:56:58 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:02:17 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestOrderingIssues::test_second` (2026-09-25 20:02:30 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.75, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found order_naming pattern: 'def test_second(self):'; Line 2: Found order_naming pattern: '"""Test that depends on test_first running before it."""'; Line 3: Found shared_state pattern: 'calc = get_shared_calculator()'.
- **Evidence Count**: 7 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:22:05 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:22:05 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `test_completely_opaque` (2026-09-25 20:22:05 UTC)
- **Verdict**: `UNKNOWN` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Classified as unknown based on parallel subagent pattern analysis.
- **Evidence Count**: 0 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:22:05 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:22:05 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `TestSample::test_example` (2026-09-25 20:22:05 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.85, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 13: Found time_measurement pattern: 'start = time.time()'; Line 17: Found time_measurement pattern: 'elapsed = time.time() - start'; Line 20: Found timing_assertion pattern: 'assert elapsed < 0.001, f"Operation took too long: {elapsed}s"'.
- **Evidence Count**: 5 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:24:43 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestOrderingIssues::test_second` (2026-09-25 20:24:43 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.75, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found order_naming pattern: 'def test_second(self):'; Line 2: Found order_naming pattern: '"""Test that depends on test_first running before it."""'; Line 3: Found shared_state pattern: 'calc = get_shared_calculator()'.
- **Evidence Count**: 7 items identified

### Session: `TestStateLeakage::test_global_mutation` (2026-09-25 20:24:43 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.95, 'state_leakage': 1.0, 'environment': 0.0}`
- **Reasoning**: State leakage detected (100%): Line 2: Found global_mutation pattern: '"""Test that mutates global state."""'; Line 3: Found shared_instance pattern: 'calc = get_shared_calculator()'; Line 4: Found state_mutation pattern: 'calc.clear()'.
- **Evidence Count**: 7 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:24:43 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:24:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:24:54 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `test_completely_opaque` (2026-09-25 20:24:54 UTC)
- **Verdict**: `UNKNOWN` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Classified as unknown based on parallel subagent pattern analysis.
- **Evidence Count**: 0 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:24:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:24:54 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `TestSample::test_example` (2026-09-25 20:24:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.85, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 13: Found time_measurement pattern: 'start = time.time()'; Line 17: Found time_measurement pattern: 'elapsed = time.time() - start'; Line 20: Found timing_assertion pattern: 'assert elapsed < 0.001, f"Operation took too long: {elapsed}s"'.
- **Evidence Count**: 5 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:24:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:25:32 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:25:32 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `test_completely_opaque` (2026-09-25 20:25:32 UTC)
- **Verdict**: `UNKNOWN` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Classified as unknown based on parallel subagent pattern analysis.
- **Evidence Count**: 0 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:25:32 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:25:32 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `TestSample::test_example` (2026-09-25 20:25:32 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.85, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 13: Found time_measurement pattern: 'start = time.time()'; Line 17: Found time_measurement pattern: 'elapsed = time.time() - start'; Line 20: Found timing_assertion pattern: 'assert elapsed < 0.001, f"Operation took too long: {elapsed}s"'.
- **Evidence Count**: 5 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:25:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:25:54 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `test_completely_opaque` (2026-09-25 20:25:54 UTC)
- **Verdict**: `UNKNOWN` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Classified as unknown based on parallel subagent pattern analysis.
- **Evidence Count**: 0 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:25:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:25:54 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `TestSample::test_example` (2026-09-25 20:25:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.85, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 13: Found time_measurement pattern: 'start = time.time()'; Line 17: Found time_measurement pattern: 'elapsed = time.time() - start'; Line 20: Found timing_assertion pattern: 'assert elapsed < 0.001, f"Operation took too long: {elapsed}s"'.
- **Evidence Count**: 5 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:30:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:30:19 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `test_completely_opaque` (2026-09-25 20:30:19 UTC)
- **Verdict**: `UNKNOWN` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Classified as unknown based on parallel subagent pattern analysis.
- **Evidence Count**: 0 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:30:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:30:19 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `TestSample::test_example` (2026-09-25 20:30:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.85, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 13: Found time_measurement pattern: 'start = time.time()'; Line 17: Found time_measurement pattern: 'elapsed = time.time() - start'; Line 20: Found timing_assertion pattern: 'assert elapsed < 0.001, f"Operation took too long: {elapsed}s"'.
- **Evidence Count**: 5 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:30:32 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:30:32 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `test_completely_opaque` (2026-09-25 20:30:32 UTC)
- **Verdict**: `UNKNOWN` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Classified as unknown based on parallel subagent pattern analysis.
- **Evidence Count**: 0 items identified

### Session: `TestTimingIssues::test_sleep_based` (2026-09-25 20:30:32 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.8, 'ordering': 0.0, 'state_leakage': 0.45, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (80%): Line 6: Found sleep pattern: 'time.sleep(0.01)'.
- **Evidence Count**: 3 items identified

### Session: `TestEnvironmentIssues::test_random_failure` (2026-09-25 20:30:32 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found random_value pattern: 'if random.random() < 0.3:  # 30% failure rate'.
- **Evidence Count**: 3 items identified

### Session: `TestSample::test_example` (2026-09-25 20:30:32 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.85, 'environment': 0.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 13: Found time_measurement pattern: 'start = time.time()'; Line 17: Found time_measurement pattern: 'elapsed = time.time() - start'; Line 20: Found timing_assertion pattern: 'assert elapsed < 0.001, f"Operation took too long: {elapsed}s"'.
- **Evidence Count**: 5 items identified

### Session: `TestTimingIssues::test_worker_thread_race` (2026-09-26 01:34:10 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 0.6}`
- **Reasoning**: High probability of timing flakiness (100%): Line 7: Found sleep pattern: 'time.sleep(random.uniform(0.0, 0.06))'; Line 14: Found timeout pattern: 'done.wait(timeout=0.03)'.
- **Evidence Count**: 4 items identified

### Session: `TestEnvironmentIssues::test_region_dependent_totals` (2026-09-26 01:34:10 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.8}`
- **Reasoning**: Environment/network dependency detected (80%): Line 3: Found env_variable pattern: 'region = os.environ.get("SALES_REGION", "US")'.
- **Evidence Count**: 3 items identified

### Session: `test_completely_opaque` (2026-09-26 01:34:10 UTC)
- **Verdict**: `UNKNOWN` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Classified as unknown based on parallel subagent pattern analysis.
- **Evidence Count**: 0 items identified

### Session: `TestTimingIssues::test_worker_thread_race` (2026-09-26 01:34:10 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 0.6}`
- **Reasoning**: High probability of timing flakiness (100%): Line 7: Found sleep pattern: 'time.sleep(random.uniform(0.0, 0.06))'; Line 14: Found timeout pattern: 'done.wait(timeout=0.03)'.
- **Evidence Count**: 4 items identified

### Session: `TestEnvironmentIssues::test_region_dependent_totals` (2026-09-26 01:34:10 UTC)
- **Verdict**: `ENVIRONMENT` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.55}`
- **Reasoning**: Environment/network dependency detected (55%): Line 3: Found env_variable pattern: 'region = os.environ.get("SALES_REGION", "US")'.
- **Evidence Count**: 2 items identified

### Session: `TestSample::test_example` (2026-09-26 01:34:10 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 0.6}`
- **Reasoning**: High probability of timing flakiness (75%): Line 17: Found sleep pattern: 'time.sleep(random.uniform(0.0, 0.06))'; Line 24: Found timeout pattern: 'done.wait(timeout=0.03)'.
- **Evidence Count**: 3 items identified

### Session: `TestTimingIssues::test_worker_thread_race` (2026-09-26 07:11:43 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 0.6}`
- **Reasoning**: High probability of timing flakiness (100%): Line 7: Found sleep pattern: 'time.sleep(random.uniform(0.0, 0.06))'; Line 14: Found timeout pattern: 'done.wait(timeout=0.03)'.
- **Evidence Count**: 4 items identified

### Session: `TestEnvironmentIssues::test_region_dependent_totals` (2026-09-26 07:11:43 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.8}`
- **Reasoning**: Environment/network dependency detected (80%): Line 3: Found env_variable pattern: 'region = os.environ.get("SALES_REGION", "US")'.
- **Evidence Count**: 3 items identified

### Session: `test_completely_opaque` (2026-09-26 07:11:43 UTC)
- **Verdict**: `UNKNOWN` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Classified as unknown based on parallel subagent pattern analysis.
- **Evidence Count**: 0 items identified

### Session: `TestTimingIssues::test_worker_thread_race` (2026-09-26 07:11:43 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 0.6}`
- **Reasoning**: High probability of timing flakiness (100%): Line 7: Found sleep pattern: 'time.sleep(random.uniform(0.0, 0.06))'; Line 14: Found timeout pattern: 'done.wait(timeout=0.03)'.
- **Evidence Count**: 4 items identified

### Session: `TestEnvironmentIssues::test_region_dependent_totals` (2026-09-26 07:11:43 UTC)
- **Verdict**: `ENVIRONMENT` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.55}`
- **Reasoning**: Environment/network dependency detected (55%): Line 3: Found env_variable pattern: 'region = os.environ.get("SALES_REGION", "US")'.
- **Evidence Count**: 2 items identified

### Session: `TestSample::test_example` (2026-09-26 07:11:43 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 0.6}`
- **Reasoning**: High probability of timing flakiness (75%): Line 17: Found sleep pattern: 'time.sleep(random.uniform(0.0, 0.06))'; Line 24: Found timeout pattern: 'done.wait(timeout=0.03)'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 C3\main\main.c::app_main` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 28: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'; Line 28: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 4 items identified

### Session: `GPIO Toggle ESP32 C6\main\main.c::app_main` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 28: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'; Line 28: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 4 items identified

### Session: `GPIO Toggle ESP32 DEVKIT\main\main.c::app_main` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 28: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'; Line 28: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 4 items identified

### Session: `GPIO Toggle ESP32 H2\main\main.c::app_main` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 18: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 18: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 36: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 6 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setLed` (2026-09-26 07:21:19 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setup` (2026-09-26 07:21:19 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::loop` (2026-09-26 07:21:19 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::set_led` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.55, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 39: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 42: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 55: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 8 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::app_main` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 33: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 36: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 49: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 6 items identified

### Session: `GPIO Toggle ESP32 RGB S2\main\main.c::app_main` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 42: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 42: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 57: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 6 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::moving_average` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.9, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (90%).
- **Evidence Count**: 4 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::adc_init` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.9, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (90%).
- **Evidence Count**: 4 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::read_sensor` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.9, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (90%).
- **Evidence Count**: 4 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::app_main` (2026-09-26 07:21:19 UTC)
- **Verdict**: `TIMING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.4, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (40%).
- **Evidence Count**: 2 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_init` (2026-09-26 07:21:19 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.6, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_init(void)'; Line 14: Found shared_state pattern: 'static void led_on(void)'; Line 19: Found shared_state pattern: 'static void led_off(void)'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_on` (2026-09-26 07:21:19 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_on(void)'; Line 6: Found shared_state pattern: 'static void led_off(void)'; Line 14: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_off` (2026-09-26 07:21:19 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_off(void)'; Line 9: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'; Line 10: Found shared_state pattern: 'static i2c_master_dev_handle_t dev_handle = NULL;'.
- **Evidence Count**: 6 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_master_init` (2026-09-26 07:21:19 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 0.6, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 1: Found hardware_peripheral pattern: 'static bool i2c_master_init(void)'; Line 3: Found hardware_peripheral pattern: 'i2c_master_bus_config_t bus_config = {'; Line 26: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_add_device` (2026-09-26 07:21:19 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.8, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'; Line 13: Found hardware_peripheral pattern: 'esp_err_t ret = i2c_master_bus_add_device(bus_handle, &dev_config, &dev_handle);'; Line 31: Found hardware_peripheral pattern: 'i2c_master_dev_handle_t scan_handle = NULL;'.
- **Evidence Count**: 10 items identified

### Session: `MPU6050_CLEAN\main\mpu6050.h::mpu6050` (2026-09-26 07:21:19 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 6: Found hardware_peripheral pattern: '// MPU6050 I2C Address (AD0 = GND)'; Line 7: Found hardware_peripheral pattern: '#define MPU6050_ADDR            0x68'; Line 9: Found hardware_peripheral pattern: '// MPU6050 Register Map'.
- **Evidence Count**: 28 items identified

### Session: `TestTimingIssues::test_worker_thread_race` (2026-09-26 07:23:06 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 0.6}`
- **Reasoning**: High probability of timing flakiness (100%): Line 7: Found sleep pattern: 'time.sleep(random.uniform(0.0, 0.06))'; Line 14: Found timeout pattern: 'done.wait(timeout=0.03)'.
- **Evidence Count**: 4 items identified

### Session: `TestEnvironmentIssues::test_region_dependent_totals` (2026-09-26 07:23:06 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.8}`
- **Reasoning**: Environment/network dependency detected (80%): Line 3: Found env_variable pattern: 'region = os.environ.get("SALES_REGION", "US")'.
- **Evidence Count**: 3 items identified

### Session: `test_completely_opaque` (2026-09-26 07:23:07 UTC)
- **Verdict**: `UNKNOWN` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Classified as unknown based on parallel subagent pattern analysis.
- **Evidence Count**: 0 items identified

### Session: `TestTimingIssues::test_worker_thread_race` (2026-09-26 07:23:07 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 0.6}`
- **Reasoning**: High probability of timing flakiness (100%): Line 7: Found sleep pattern: 'time.sleep(random.uniform(0.0, 0.06))'; Line 14: Found timeout pattern: 'done.wait(timeout=0.03)'.
- **Evidence Count**: 4 items identified

### Session: `TestEnvironmentIssues::test_region_dependent_totals` (2026-09-26 07:23:07 UTC)
- **Verdict**: `ENVIRONMENT` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.55}`
- **Reasoning**: Environment/network dependency detected (55%): Line 3: Found env_variable pattern: 'region = os.environ.get("SALES_REGION", "US")'.
- **Evidence Count**: 2 items identified

### Session: `TestSample::test_example` (2026-09-26 07:23:07 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 0.6}`
- **Reasoning**: High probability of timing flakiness (75%): Line 17: Found sleep pattern: 'time.sleep(random.uniform(0.0, 0.06))'; Line 24: Found timeout pattern: 'done.wait(timeout=0.03)'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 C3\main\main.c::app_main` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 28: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'; Line 28: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 4 items identified

### Session: `GPIO Toggle ESP32 C6\main\main.c::app_main` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 28: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'; Line 28: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 4 items identified

### Session: `GPIO Toggle ESP32 DEVKIT\main\main.c::app_main` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 28: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'; Line 28: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 4 items identified

### Session: `GPIO Toggle ESP32 H2\main\main.c::app_main` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 18: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 18: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 36: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 6 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setLed` (2026-09-26 07:24:47 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setup` (2026-09-26 07:24:47 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::loop` (2026-09-26 07:24:47 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::set_led` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.55, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 39: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 42: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 55: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 8 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::app_main` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 33: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 36: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 49: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 6 items identified

### Session: `GPIO Toggle ESP32 RGB S2\main\main.c::app_main` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 42: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 42: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 57: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 6 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::moving_average` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.9, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (90%).
- **Evidence Count**: 4 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::adc_init` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.9, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (90%).
- **Evidence Count**: 4 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::read_sensor` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.9, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (90%).
- **Evidence Count**: 4 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::app_main` (2026-09-26 07:24:47 UTC)
- **Verdict**: `TIMING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.4, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (40%).
- **Evidence Count**: 2 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_init` (2026-09-26 07:24:47 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.6, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_init(void)'; Line 14: Found shared_state pattern: 'static void led_on(void)'; Line 19: Found shared_state pattern: 'static void led_off(void)'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_on` (2026-09-26 07:24:47 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_on(void)'; Line 6: Found shared_state pattern: 'static void led_off(void)'; Line 14: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_off` (2026-09-26 07:24:47 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_off(void)'; Line 9: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'; Line 10: Found shared_state pattern: 'static i2c_master_dev_handle_t dev_handle = NULL;'.
- **Evidence Count**: 6 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_master_init` (2026-09-26 07:24:47 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 0.6, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 1: Found hardware_peripheral pattern: 'static bool i2c_master_init(void)'; Line 3: Found hardware_peripheral pattern: 'i2c_master_bus_config_t bus_config = {'; Line 26: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_add_device` (2026-09-26 07:24:47 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.8, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'; Line 13: Found hardware_peripheral pattern: 'esp_err_t ret = i2c_master_bus_add_device(bus_handle, &dev_config, &dev_handle);'; Line 31: Found hardware_peripheral pattern: 'i2c_master_dev_handle_t scan_handle = NULL;'.
- **Evidence Count**: 10 items identified

### Session: `MPU6050_CLEAN\main\mpu6050.h::mpu6050` (2026-09-26 07:24:47 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 6: Found hardware_peripheral pattern: '// MPU6050 I2C Address (AD0 = GND)'; Line 7: Found hardware_peripheral pattern: '#define MPU6050_ADDR            0x68'; Line 9: Found hardware_peripheral pattern: '// MPU6050 Register Map'.
- **Evidence Count**: 28 items identified

### Session: `main.c::set_led` (2026-09-26 07:25:13 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.55, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 39: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 42: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 55: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `main.c::app_main` (2026-09-26 07:25:13 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 33: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 36: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 49: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 C3\main\main.c::app_main` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 C6\main\main.c::app_main` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 DEVKIT\main\main.c::app_main` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 H2\main\main.c::app_main` (2026-09-26 07:27:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 18: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 18: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 36: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setLed` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setup` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::loop` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::set_led` (2026-09-26 07:27:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.55, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 39: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 42: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 55: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::app_main` (2026-09-26 07:27:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 33: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 36: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 49: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB S2\main\main.c::app_main` (2026-09-26 07:27:54 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 42: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 42: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 57: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::moving_average` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static int moving_average(int value)'; Line 24: Found shared_state pattern: 'static void adc_init(void)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::adc_init` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static void adc_init(void)'; Line 54: Found shared_state pattern: 'static int read_sensor(void)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::read_sensor` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static int read_sensor(void)'; Line 32: Found shared_state pattern: 'static const char *get_status(float bpm)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::app_main` (2026-09-26 07:27:54 UTC)
- **Verdict**: `TIMING` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: No significant timing or race condition patterns detected in test code or execution logs.
- **Evidence Count**: 1 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_init` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.6, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_init(void)'; Line 14: Found shared_state pattern: 'static void led_on(void)'; Line 19: Found shared_state pattern: 'static void led_off(void)'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_on` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_on(void)'; Line 6: Found shared_state pattern: 'static void led_off(void)'; Line 14: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_off` (2026-09-26 07:27:54 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_off(void)'; Line 9: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'; Line 10: Found shared_state pattern: 'static i2c_master_dev_handle_t dev_handle = NULL;'.
- **Evidence Count**: 6 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_master_init` (2026-09-26 07:27:55 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 0.6, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 1: Found hardware_peripheral pattern: 'static bool i2c_master_init(void)'; Line 3: Found hardware_peripheral pattern: 'i2c_master_bus_config_t bus_config = {'; Line 26: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_add_device` (2026-09-26 07:27:55 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.8, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'; Line 13: Found hardware_peripheral pattern: 'esp_err_t ret = i2c_master_bus_add_device(bus_handle, &dev_config, &dev_handle);'; Line 31: Found hardware_peripheral pattern: 'i2c_master_dev_handle_t scan_handle = NULL;'.
- **Evidence Count**: 10 items identified

### Session: `MPU6050_CLEAN\main\mpu6050.h::mpu6050` (2026-09-26 07:27:55 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 6: Found hardware_peripheral pattern: '// MPU6050 I2C Address (AD0 = GND)'; Line 7: Found hardware_peripheral pattern: '#define MPU6050_ADDR            0x68'; Line 9: Found hardware_peripheral pattern: '// MPU6050 Register Map'.
- **Evidence Count**: 28 items identified

### Session: `GPIO Toggle ESP32 C3\main\main.c::app_main` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 C6\main\main.c::app_main` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 DEVKIT\main\main.c::app_main` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 H2\main\main.c::app_main` (2026-09-26 07:28:16 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 18: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 18: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 36: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setLed` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setup` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::loop` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::set_led` (2026-09-26 07:28:16 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.55, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 39: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 42: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 55: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::app_main` (2026-09-26 07:28:16 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 33: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 36: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 49: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB S2\main\main.c::app_main` (2026-09-26 07:28:16 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 42: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 42: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 57: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::moving_average` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static int moving_average(int value)'; Line 24: Found shared_state pattern: 'static void adc_init(void)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::adc_init` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static void adc_init(void)'; Line 54: Found shared_state pattern: 'static int read_sensor(void)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::read_sensor` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static int read_sensor(void)'; Line 32: Found shared_state pattern: 'static const char *get_status(float bpm)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::app_main` (2026-09-26 07:28:16 UTC)
- **Verdict**: `TIMING` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: No significant timing or race condition patterns detected in test code or execution logs.
- **Evidence Count**: 1 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_init` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.6, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_init(void)'; Line 14: Found shared_state pattern: 'static void led_on(void)'; Line 19: Found shared_state pattern: 'static void led_off(void)'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_on` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_on(void)'; Line 6: Found shared_state pattern: 'static void led_off(void)'; Line 14: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_off` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_off(void)'; Line 9: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'; Line 10: Found shared_state pattern: 'static i2c_master_dev_handle_t dev_handle = NULL;'.
- **Evidence Count**: 6 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_master_init` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 0.6, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 1: Found hardware_peripheral pattern: 'static bool i2c_master_init(void)'; Line 3: Found hardware_peripheral pattern: 'i2c_master_bus_config_t bus_config = {'; Line 26: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_add_device` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.8, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'; Line 13: Found hardware_peripheral pattern: 'esp_err_t ret = i2c_master_bus_add_device(bus_handle, &dev_config, &dev_handle);'; Line 31: Found hardware_peripheral pattern: 'i2c_master_dev_handle_t scan_handle = NULL;'.
- **Evidence Count**: 10 items identified

### Session: `MPU6050_CLEAN\main\mpu6050.h::mpu6050` (2026-09-26 07:28:16 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 6: Found hardware_peripheral pattern: '// MPU6050 I2C Address (AD0 = GND)'; Line 7: Found hardware_peripheral pattern: '#define MPU6050_ADDR            0x68'; Line 9: Found hardware_peripheral pattern: '// MPU6050 Register Map'.
- **Evidence Count**: 28 items identified

### Session: `GPIO Toggle ESP32 C3\main\main.c::app_main` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 C6\main\main.c::app_main` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 DEVKIT\main\main.c::app_main` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 H2\main\main.c::app_main` (2026-09-26 07:28:48 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 18: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 18: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 36: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setLed` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setup` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::loop` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::set_led` (2026-09-26 07:28:48 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.55, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 39: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 42: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 55: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::app_main` (2026-09-26 07:28:48 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 33: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 36: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 49: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB S2\main\main.c::app_main` (2026-09-26 07:28:48 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 42: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 42: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 57: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::moving_average` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static int moving_average(int value)'; Line 24: Found shared_state pattern: 'static void adc_init(void)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::adc_init` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static void adc_init(void)'; Line 54: Found shared_state pattern: 'static int read_sensor(void)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::read_sensor` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static int read_sensor(void)'; Line 32: Found shared_state pattern: 'static const char *get_status(float bpm)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::app_main` (2026-09-26 07:28:48 UTC)
- **Verdict**: `TIMING` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: No significant timing or race condition patterns detected in test code or execution logs.
- **Evidence Count**: 1 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_init` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.6, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_init(void)'; Line 14: Found shared_state pattern: 'static void led_on(void)'; Line 19: Found shared_state pattern: 'static void led_off(void)'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_on` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_on(void)'; Line 6: Found shared_state pattern: 'static void led_off(void)'; Line 14: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_off` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_off(void)'; Line 9: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'; Line 10: Found shared_state pattern: 'static i2c_master_dev_handle_t dev_handle = NULL;'.
- **Evidence Count**: 6 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_master_init` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 0.6, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 1: Found hardware_peripheral pattern: 'static bool i2c_master_init(void)'; Line 3: Found hardware_peripheral pattern: 'i2c_master_bus_config_t bus_config = {'; Line 26: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_add_device` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.8, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'; Line 13: Found hardware_peripheral pattern: 'esp_err_t ret = i2c_master_bus_add_device(bus_handle, &dev_config, &dev_handle);'; Line 31: Found hardware_peripheral pattern: 'i2c_master_dev_handle_t scan_handle = NULL;'.
- **Evidence Count**: 10 items identified

### Session: `MPU6050_CLEAN\main\mpu6050.h::mpu6050` (2026-09-26 07:28:48 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 6: Found hardware_peripheral pattern: '// MPU6050 I2C Address (AD0 = GND)'; Line 7: Found hardware_peripheral pattern: '#define MPU6050_ADDR            0x68'; Line 9: Found hardware_peripheral pattern: '// MPU6050 Register Map'.
- **Evidence Count**: 28 items identified

### Session: `GPIO Toggle ESP32 C3\main\main.c::app_main` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 C6\main\main.c::app_main` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 DEVKIT\main\main.c::app_main` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.75, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 5: Found hardware_peripheral pattern: 'gpio_config_t led_conf = {'; Line 12: Found hardware_peripheral pattern: 'ESP_ERROR_CHECK(gpio_config(&led_conf));'; Line 13: Found hardware_peripheral pattern: 'gpio_set_level(LED_GPIO, 0);'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 H2\main\main.c::app_main` (2026-09-26 07:29:53 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 18: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 18: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(500));'; Line 36: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(1000));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setLed` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::setup` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\ESP32 button toggles onboard LED.c::loop` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.35, 'state_leakage': 0.25, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 28: Found hardware_peripheral pattern: 'pinMode(LED_PIN, OUTPUT);'; Line 29: Found hardware_peripheral pattern: 'pinMode(BUTTON_PIN, INPUT_PULLUP);'; Line 35: Found hardware_peripheral pattern: 'int reading = digitalRead(BUTTON_PIN);'.
- **Evidence Count**: 3 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::set_led` (2026-09-26 07:29:53 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.55, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 39: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 42: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 55: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB C3\main\main.c::app_main` (2026-09-26 07:29:53 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.35, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 33: Found time_measurement pattern: 'last_debounce_time_us = esp_timer_get_time();'; Line 36: Found time_measurement pattern: 'const int64_t elapsed_us = esp_timer_get_time() - last_debounce_time_us;'; Line 49: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `GPIO Toggle ESP32 RGB S2\main\main.c::app_main` (2026-09-26 07:29:53 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: High probability of timing flakiness (100%): Line 42: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 42: Found timeout pattern: 'vTaskDelay(pdMS_TO_TICKS(30));'; Line 57: Found sleep pattern: 'vTaskDelay(pdMS_TO_TICKS(10));'.
- **Evidence Count**: 5 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::moving_average` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static int moving_average(int value)'; Line 24: Found shared_state pattern: 'static void adc_init(void)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::adc_init` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static void adc_init(void)'; Line 54: Found shared_state pattern: 'static int read_sensor(void)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::read_sensor` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.4, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected (40%): Line 1: Found shared_state pattern: 'static int read_sensor(void)'; Line 32: Found shared_state pattern: 'static const char *get_status(float bpm)'.
- **Evidence Count**: 2 items identified

### Session: `HR-TEST\HR-TEST\hr_test\main\main.c::app_main` (2026-09-26 07:29:53 UTC)
- **Verdict**: `TIMING` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: No significant timing or race condition patterns detected in test code or execution logs.
- **Evidence Count**: 1 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_init` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.6, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_init(void)'; Line 14: Found shared_state pattern: 'static void led_on(void)'; Line 19: Found shared_state pattern: 'static void led_off(void)'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_on` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.4, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_on(void)'; Line 6: Found shared_state pattern: 'static void led_off(void)'; Line 14: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::led_off` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 1.0, 'state_leakage': 0.2, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 1: Found shared_state pattern: 'static void led_off(void)'; Line 9: Found shared_state pattern: 'static i2c_master_bus_handle_t bus_handle = NULL;'; Line 10: Found shared_state pattern: 'static i2c_master_dev_handle_t dev_handle = NULL;'.
- **Evidence Count**: 6 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_master_init` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 0.6, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 1: Found hardware_peripheral pattern: 'static bool i2c_master_init(void)'; Line 3: Found hardware_peripheral pattern: 'i2c_master_bus_config_t bus_config = {'; Line 26: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'.
- **Evidence Count**: 7 items identified

### Session: `MPU6050_CLEAN\main\main.c::i2c_add_device` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.8, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 4: Found hardware_peripheral pattern: 'i2c_master_bus_rm_device(dev_handle);'; Line 13: Found hardware_peripheral pattern: 'esp_err_t ret = i2c_master_bus_add_device(bus_handle, &dev_config, &dev_handle);'; Line 31: Found hardware_peripheral pattern: 'i2c_master_dev_handle_t scan_handle = NULL;'.
- **Evidence Count**: 10 items identified

### Session: `MPU6050_CLEAN\main\mpu6050.h::mpu6050` (2026-09-26 07:29:53 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 6: Found hardware_peripheral pattern: '// MPU6050 I2C Address (AD0 = GND)'; Line 7: Found hardware_peripheral pattern: '#define MPU6050_ADDR            0x68'; Line 9: Found hardware_peripheral pattern: '// MPU6050 Register Map'.
- **Evidence Count**: 28 items identified

### Session: `frontend\src\components\Layout.tsx::Layout` (2026-09-26 07:30:55 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 1.0, 'environment': 1.0}`
- **Reasoning**: State leakage detected (100%): Line 61: Found resource_leak pattern: 'onClick={() => setMobileMenuOpen(false)}'; Line 102: Found resource_leak pattern: 'onClick={() => setMobileMenuOpen(false)}'; Line 140: Found resource_leak pattern: 'onClick={() => setMobileMenuOpen(false)}'.
- **Evidence Count**: 5 items identified

### Session: `frontend\src\components\ui\constellation-grid.tsx::constellation-grid` (2026-09-26 07:30:55 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 1.0, 'state_leakage': 1.0, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 30: Found shared_state pattern: 'const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');'; Line 62: Found shared_state pattern: 'const dpr = Math.min(window.devicePixelRatio || 1, 2);'; Line 63: Found shared_state pattern: 'width = window.innerWidth;'.
- **Evidence Count**: 10 items identified

### Session: `frontend\src\components\ui\kinetic-grid.tsx::kinetic-grid` (2026-09-26 07:30:55 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 1.0, 'state_leakage': 1.0, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 178: Found shared_state pattern: '// Static background dot texture'; Line 334: Found shared_state pattern: 'const w = window.innerWidth;'; Line 335: Found shared_state pattern: 'const h = window.innerHeight;'.
- **Evidence Count**: 9 items identified

### Session: `frontend\src\context\ThemeContext.tsx::ThemeContext` (2026-09-26 07:30:55 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 0.0}`
- **Reasoning**: State leakage detected (40%): Line 23: Found state_mutation pattern: 'root.classList.add('light');'; Line 26: Found state_mutation pattern: 'root.classList.add('dark');'.
- **Evidence Count**: 2 items identified

### Session: `frontend\src\lib\db.ts::db` (2026-09-26 07:30:55 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 1.0, 'environment': 0.8}`
- **Reasoning**: State leakage detected (100%): Line 42: Found state_mutation pattern: 'this.set('users', INITIAL_USERS);'; Line 45: Found state_mutation pattern: 'this.set('attendance', []);'; Line 48: Found state_mutation pattern: 'this.set('leaves', []);'.
- **Evidence Count**: 9 items identified

### Session: `frontend\src\lib\payslipExporter.ts::payslipExporter` (2026-09-26 07:30:55 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.6, 'state_leakage': 0.5, 'environment': 0.25}`
- **Reasoning**: High probability of timing flakiness (100%): Line 34: Found sleep pattern: 'setTimeout(() => {'; Line 255: Found sleep pattern: 'setTimeout(() => {'.
- **Evidence Count**: 5 items identified

### Session: `frontend\src\lib\utils.ts::utils` (2026-09-26 07:30:55 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 10: Found random_value pattern: 'return Math.random().toString(36).substring(2, 9);'.
- **Evidence Count**: 2 items identified

### Session: `frontend\src\pages\Attendance.tsx::Attendance` (2026-09-26 07:30:55 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 129: Found network_call pattern: 'return leaveRequests.some(l => {'; Line 158: Found network_call pattern: 'return leaveRequests.some(l => {'; Line 194: Found network_call pattern: 'const activeLeave = leaveRequests.find(l => {'.
- **Evidence Count**: 6 items identified

### Session: `frontend\src\pages\Landing.tsx::Landing` (2026-09-26 07:30:55 UTC)
- **Verdict**: `TIMING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.4, 'ordering': 0.0, 'state_leakage': 0.25, 'environment': 0.0}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (40%).
- **Evidence Count**: 2 items identified

### Session: `frontend\src\pages\Leave.tsx::Leave` (2026-09-26 07:30:55 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 220: Found network_call pattern: '{requests.map(req => ('; Line 254: Found network_call pattern: '{requests.length === 0 && ('; Line 300: Found network_call pattern: 'const pendingCount = requests.filter(r => r.status === 'Pending').length;'.
- **Evidence Count**: 10 items identified

### Session: `frontend\src\components\Layout.tsx::Layout` (2026-09-26 07:31:32 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 1.0, 'environment': 1.0}`
- **Reasoning**: State leakage detected (100%): Line 61: Found resource_leak pattern: 'onClick={() => setMobileMenuOpen(false)}'; Line 102: Found resource_leak pattern: 'onClick={() => setMobileMenuOpen(false)}'; Line 140: Found resource_leak pattern: 'onClick={() => setMobileMenuOpen(false)}'.
- **Evidence Count**: 5 items identified

### Session: `frontend\src\components\ui\constellation-grid.tsx::constellation-grid` (2026-09-26 07:31:32 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 1.0, 'state_leakage': 1.0, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 30: Found shared_state pattern: 'const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');'; Line 62: Found shared_state pattern: 'const dpr = Math.min(window.devicePixelRatio || 1, 2);'; Line 63: Found shared_state pattern: 'width = window.innerWidth;'.
- **Evidence Count**: 10 items identified

### Session: `frontend\src\components\ui\kinetic-grid.tsx::kinetic-grid` (2026-09-26 07:31:32 UTC)
- **Verdict**: `ORDERING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 1.0, 'state_leakage': 1.0, 'environment': 1.0}`
- **Reasoning**: Order dependency detected (100%): Line 178: Found shared_state pattern: '// Static background dot texture'; Line 334: Found shared_state pattern: 'const w = window.innerWidth;'; Line 335: Found shared_state pattern: 'const h = window.innerHeight;'.
- **Evidence Count**: 9 items identified

### Session: `frontend\src\context\ThemeContext.tsx::ThemeContext` (2026-09-26 07:31:32 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 0.0}`
- **Reasoning**: State leakage detected (40%): Line 23: Found state_mutation pattern: 'root.classList.add('light');'; Line 26: Found state_mutation pattern: 'root.classList.add('dark');'.
- **Evidence Count**: 2 items identified

### Session: `frontend\src\lib\db.ts::db` (2026-09-26 07:31:32 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 1.0, 'environment': 0.8}`
- **Reasoning**: State leakage detected (100%): Line 42: Found state_mutation pattern: 'this.set('users', INITIAL_USERS);'; Line 45: Found state_mutation pattern: 'this.set('attendance', []);'; Line 48: Found state_mutation pattern: 'this.set('leaves', []);'.
- **Evidence Count**: 9 items identified

### Session: `frontend\src\lib\payslipExporter.ts::payslipExporter` (2026-09-26 07:31:32 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.6, 'state_leakage': 0.5, 'environment': 0.25}`
- **Reasoning**: High probability of timing flakiness (100%): Line 34: Found sleep pattern: 'setTimeout(() => {'; Line 255: Found sleep pattern: 'setTimeout(() => {'.
- **Evidence Count**: 5 items identified

### Session: `frontend\src\lib\utils.ts::utils` (2026-09-26 07:31:32 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 10: Found random_value pattern: 'return Math.random().toString(36).substring(2, 9);'.
- **Evidence Count**: 2 items identified

### Session: `frontend\src\pages\Attendance.tsx::Attendance` (2026-09-26 07:31:32 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 129: Found network_call pattern: 'return leaveRequests.some(l => {'; Line 158: Found network_call pattern: 'return leaveRequests.some(l => {'; Line 194: Found network_call pattern: 'const activeLeave = leaveRequests.find(l => {'.
- **Evidence Count**: 6 items identified

### Session: `frontend\src\pages\Landing.tsx::Landing` (2026-09-26 07:31:32 UTC)
- **Verdict**: `TIMING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.4, 'ordering': 0.0, 'state_leakage': 0.25, 'environment': 0.0}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (40%).
- **Evidence Count**: 2 items identified

### Session: `frontend\src\pages\Leave.tsx::Leave` (2026-09-26 07:31:32 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 220: Found network_call pattern: '{requests.map(req => ('; Line 254: Found network_call pattern: '{requests.length === 0 && ('; Line 300: Found network_call pattern: 'const pendingCount = requests.filter(r => r.status === 'Pending').length;'.
- **Evidence Count**: 10 items identified

### Session: `backend\src\controllers\auth.controller.js::auth.controller` (2026-09-26 10:15:29 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.4, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 6: Found env_variable pattern: 'if (process.env.NODE_ENV !== "production") {'; Line 12: Found env_variable pattern: 'const apiKey = process.env.FIREBASE_API_KEY?.trim();'; Line 20: Found network_call pattern: 'const response = await fetch('.
- **Evidence Count**: 7 items identified

### Session: `backend\src\controllers\components.controller.js::components.controller` (2026-09-26 10:15:29 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.0}`
- **Reasoning**: State leakage detected (60%): Line 53: Found state_mutation pattern: 'project.componentsMessages.push({'; Line 97: Found state_mutation pattern: 'project.componentsMessages.push({'; Line 110: Found state_mutation pattern: 'project.componentsMessages.push({'.
- **Evidence Count**: 3 items identified

### Session: `backend\src\controllers\design.controller.js::design.controller` (2026-09-26 10:15:29 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.0}`
- **Reasoning**: State leakage detected (60%): Line 54: Found state_mutation pattern: 'project.designMessages.push({'; Line 98: Found state_mutation pattern: 'project.designMessages.push({'; Line 112: Found state_mutation pattern: 'project.designMessages.push({'.
- **Evidence Count**: 3 items identified

### Session: `backend\src\controllers\ideation.controller.js::ideation.controller` (2026-09-26 10:15:29 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.0}`
- **Reasoning**: State leakage detected (60%): Line 65: Found state_mutation pattern: 'project.messages.push({'; Line 107: Found state_mutation pattern: 'project.messages.push({'; Line 122: Found state_mutation pattern: 'project.messages.push({'.
- **Evidence Count**: 3 items identified

### Session: `backend\src\controllers\project.controller.js::project.controller` (2026-09-26 10:15:29 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.0}`
- **Reasoning**: State leakage detected (60%): Line 43: Found state_mutation pattern: 'project.messages.push({'; Line 257: Found state_mutation pattern: 'project.messages.push({'; Line 272: Found state_mutation pattern: 'project.messages.push({'.
- **Evidence Count**: 3 items identified

### Session: `backend\src\controllers\projectAi.controller.js::projectAi.controller` (2026-09-26 10:15:29 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 1.0, 'environment': 0.75}`
- **Reasoning**: State leakage detected (100%): Line 69: Found state_mutation pattern: 'queue.push(fullPath);'; Line 72: Found state_mutation pattern: 'output.push(fullPath);'; Line 121: Found state_mutation pattern: 'snippets.push({'.
- **Evidence Count**: 6 items identified

### Session: `backend\src\controllers\voice.controller.js::voice.controller` (2026-09-26 10:15:29 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.35, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 3: Found random_value pattern: 'const buildRequestId = () => `voice-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;'.
- **Evidence Count**: 2 items identified

### Session: `backend\src\index.js::index` (2026-09-26 10:15:29 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 18: Found file_system pattern: 'const __filename = fileURLToPath(import.meta.url);'; Line 26: Found network_call pattern: 'origin: "http://localhost:5173",'; Line 41: Found env_variable pattern: 'app.listen(process.env.PORT, () => {'.
- **Evidence Count**: 4 items identified

### Session: `backend\src\lib\db.js::db` (2026-09-26 10:15:29 UTC)
- **Verdict**: `TIMING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.4, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.25}`
- **Reasoning**: Timing flakiness detected based on execution logs and test characteristics (40%).
- **Evidence Count**: 2 items identified

### Session: `backend\src\lib\utils.js::utils` (2026-09-26 10:15:29 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.75}`
- **Reasoning**: Environment/network dependency detected (75%): Line 4: Found env_variable pattern: 'const isProduction = process.env.NODE_ENV === "production";'; Line 5: Found env_variable pattern: 'const jwtSecret = process.env.JWT_SECRET?.trim();'.
- **Evidence Count**: 3 items identified

### Session: `backend\src\lib\wokwi-components.js::wokwi-components` (2026-09-26 10:15:29 UTC)
- **Verdict**: `ENVIRONMENT` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.2, 'environment': 0.5}`
- **Reasoning**: Environment/network dependency detected (50%): Line 30: Found hardware_peripheral pattern: '{ label: "MPU6050", partType: "wokwi-mpu6050", aliases: ["mpu6050"] },'; Line 64: Found env_variable pattern: 'const raw = process.env.WOKWI_EXTRA_COMPONENTS;'.
- **Evidence Count**: 2 items identified

### Session: `backend\src\lib\wokwi-context.js::wokwi-context` (2026-09-26 10:15:29 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.65, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 84: Found network_call pattern: 'const diagramResponse = await fetch(`https://wokwi.com/api/projects/${projectId}/diagram.json`);'; Line 95: Found network_call pattern: 'const response = await fetch(`https://wokwi.com/projects/${projectId}`);'.
- **Evidence Count**: 4 items identified

### Session: `backend\src\lib\wokwi.js::wokwi` (2026-09-26 10:15:29 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 6: Found env_variable pattern: 'if (process.env.WOKWI_CLI_PATH?.trim()) {'; Line 7: Found env_variable pattern: 'return process.env.WOKWI_CLI_PATH.trim();'; Line 10: Found env_variable pattern: 'const home = process.env.USERPROFILE || process.env.HOME || "";'.
- **Evidence Count**: 6 items identified

### Session: `backend\src\middleware\auth.middleware.js::auth.middleware` (2026-09-26 10:15:29 UTC)
- **Verdict**: `ENVIRONMENT` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.5}`
- **Reasoning**: Environment/network dependency detected (50%): Line 4: Found env_variable pattern: 'const getJwtSecret = () => process.env.JWT_SECRET?.trim();'; Line 11: Found env_variable pattern: 'secure: process.env.NODE_ENV === "production",'.
- **Evidence Count**: 2 items identified

### Session: `backend\src\services\ai.services.js::ai.services` (2026-09-26 10:15:29 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 1.0, 'environment': 0.5}`
- **Reasoning**: State leakage detected (100%): Line 55: Found state_mutation pattern: 'if (/\bled\b|\bblink\b|\blight\b/.test(text)) inferred.push("LED");'; Line 56: Found state_mutation pattern: 'if (/\bresistor\b|\bled\b/.test(text)) inferred.push("220 ohm resistor");'; Line 57: Found state_mutation pattern: 'if (/\bbuzzer\b|\balarm\b|\balert\b/.test(text)) inferred.push("Piezo buzzer");'.
- **Evidence Count**: 13 items identified

### Session: `backend\src\services\registry-codegen.service.js::setup` (2026-09-26 10:15:29 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.0, 'state_leakage': 1.0, 'environment': 0.5}`
- **Reasoning**: State leakage detected (100%): Line 72: Found state_mutation pattern: 'candidates.push(cleaned);'; Line 76: Found state_mutation pattern: 'candidates.push(jsonBlock[1]);'; Line 81: Found state_mutation pattern: 'candidates.push(balanced);'.
- **Evidence Count**: 6 items identified

### Session: `backend\src\services\registry-codegen.service.js::loop` (2026-09-26 10:15:29 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.55, 'ordering': 0.0, 'state_leakage': 1.0, 'environment': 0.5}`
- **Reasoning**: State leakage detected (100%): Line 72: Found state_mutation pattern: 'candidates.push(cleaned);'; Line 76: Found state_mutation pattern: 'candidates.push(jsonBlock[1]);'; Line 81: Found state_mutation pattern: 'candidates.push(balanced);'.
- **Evidence Count**: 6 items identified

### Session: `TestTimingIssues::test_worker_thread_race` (2026-09-26 10:19:07 UTC)
- **Verdict**: `TIMING` (HIGH confidence)
- **Subagent Scores**: `{'timing': 1.0, 'ordering': 0.0, 'state_leakage': 0.4, 'environment': 0.6}`
- **Reasoning**: High probability of timing flakiness (100%): Line 17: Found sleep pattern: 'time.sleep(random.uniform(0.0, 0.06))'; Line 24: Found timeout pattern: 'done.wait(timeout=0.03)'.
- **Evidence Count**: 4 items identified

### Session: `TestOrderingIssues::test_depends_on_retry_limit` (2026-09-26 10:19:07 UTC)
- **Verdict**: `ORDERING` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.35, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: Order dependency detected from test structure and naming indicators (35%).
- **Evidence Count**: 1 items identified

### Session: `TestStateLeakage::test_expects_clean_inventory` (2026-09-26 10:19:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 1.0, 'environment': 1.0}`
- **Reasoning**: State leakage detected (100%): Line 26: Found resource_leak pattern: 'with open(inv_file, "r", encoding="utf-8") as f:'; Line 30: Found state_mutation pattern: 'rows.append({"sku": "SKU-1", "qty": 1})'; Line 31: Found resource_leak pattern: 'with open(inv_file, "w", encoding="utf-8") as f:'.
- **Evidence Count**: 8 items identified

### Session: `TestEnvironmentIssues::test_region_dependent_totals` (2026-09-26 10:19:07 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.8}`
- **Reasoning**: Environment/network dependency detected (80%): Line 10: Found env_variable pattern: 'region = os.environ.get("SALES_REGION", "US")'.
- **Evidence Count**: 3 items identified

### Session: `backend\app.py::app` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.3, 'environment': 0.25}`
- **Reasoning**: State leakage detected (30%): Line 97: Found global_mutation pattern: 'app = create_app()'.
- **Evidence Count**: 1 items identified

### Session: `backend\config.py::config` (2026-09-26 10:21:07 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.3, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 10: Found file_system pattern: 'BASE_DIR = Path(__file__).resolve().parent'; Line 30: Found network_call pattern: 'return ("http://localhost:5173", "http://127.0.0.1:5173")'; Line 36: Found env_variable pattern: 'key = os.getenv("SECRET_KEY", "").strip()'.
- **Evidence Count**: 13 items identified

### Session: `backend\database.py::database` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.2, 'state_leakage': 0.6, 'environment': 0.0}`
- **Reasoning**: State leakage detected (60%): Line 19: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'; Line 31: Found global_mutation pattern: 'global _connection_pool'.
- **Evidence Count**: 2 items identified

### Session: `backend\models\__init__.py::__init__` (2026-09-26 10:21:07 UTC)
- **Verdict**: `TIMING` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: No significant timing or race condition patterns detected in test code or execution logs.
- **Evidence Count**: 1 items identified

### Session: `backend\models\account.py::account` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.3, 'environment': 0.0}`
- **Reasoning**: State leakage detected (30%): Line 16: Found global_mutation pattern: 'ALLOWED_ACCOUNT_TYPES = {"Savings", "Current", "Salary", "Fixed Deposit"}'.
- **Evidence Count**: 1 items identified

### Session: `backend\routes\account_routes.py::account_routes` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.8, 'environment': 0.25}`
- **Reasoning**: State leakage detected (80%): Line 18: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'; Line 20: Found global_mutation pattern: 'account_bp = Blueprint("accounts", __name__, url_prefix="/api/accounts")'; Line 170: Found state_mutation pattern: 'account = Account.update(parsed_account_id, cleaned_payload)'.
- **Evidence Count**: 3 items identified

### Session: `backend\routes\branch_routes.py::branch_routes` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 16: Found global_mutation pattern: 'branch_bp = Blueprint("branches", __name__, url_prefix="/api/branches")'; Line 17: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\routes\customer_routes.py::customer_routes` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.8, 'environment': 0.25}`
- **Reasoning**: State leakage detected (80%): Line 18: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'; Line 20: Found global_mutation pattern: 'customer_bp = Blueprint("customers", __name__, url_prefix="/api/customers")'; Line 147: Found state_mutation pattern: 'customer = Customer.update(parsed_customer_id, cleaned_payload)'.
- **Evidence Count**: 3 items identified

### Session: `backend\routes\employee_routes.py::employee_routes` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 16: Found global_mutation pattern: 'employee_bp = Blueprint("employees", __name__, url_prefix="/api/employees")'; Line 17: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\routes\loan_routes.py::loan_routes` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 16: Found global_mutation pattern: 'loan_bp = Blueprint("loans", __name__, url_prefix="/api/loans")'; Line 17: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\routes\procedure_routes.py::procedure_routes` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 17: Found global_mutation pattern: 'procedure_bp = Blueprint("procedures", __name__, url_prefix="/api/procedures")'; Line 18: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\routes\transaction_routes.py::transaction_routes` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 16: Found global_mutation pattern: 'transaction_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")'; Line 17: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\routes\trigger_routes.py::trigger_routes` (2026-09-26 10:21:07 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 17: Found global_mutation pattern: 'trigger_bp = Blueprint("triggers", __name__, url_prefix="/api/triggers")'; Line 18: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\app.py::app` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.3, 'environment': 0.25}`
- **Reasoning**: State leakage detected (30%): Line 97: Found global_mutation pattern: 'app = create_app()'.
- **Evidence Count**: 1 items identified

### Session: `backend\config.py::config` (2026-09-26 10:27:39 UTC)
- **Verdict**: `ENVIRONMENT` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.3, 'environment': 1.0}`
- **Reasoning**: Environment/network dependency detected (100%): Line 10: Found file_system pattern: 'BASE_DIR = Path(__file__).resolve().parent'; Line 30: Found network_call pattern: 'return ("http://localhost:5173", "http://127.0.0.1:5173")'; Line 36: Found env_variable pattern: 'key = os.getenv("SECRET_KEY", "").strip()'.
- **Evidence Count**: 13 items identified

### Session: `backend\database.py::database` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.2, 'state_leakage': 0.6, 'environment': 0.0}`
- **Reasoning**: State leakage detected (60%): Line 19: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'; Line 31: Found global_mutation pattern: 'global _connection_pool'.
- **Evidence Count**: 2 items identified

### Session: `backend\models\__init__.py::__init__` (2026-09-26 10:27:39 UTC)
- **Verdict**: `TIMING` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.0, 'environment': 0.0}`
- **Reasoning**: No significant timing or race condition patterns detected in test code or execution logs.
- **Evidence Count**: 1 items identified

### Session: `backend\models\account.py::account` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (LOW confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.3, 'environment': 0.0}`
- **Reasoning**: State leakage detected (30%): Line 16: Found global_mutation pattern: 'ALLOWED_ACCOUNT_TYPES = {"Savings", "Current", "Salary", "Fixed Deposit"}'.
- **Evidence Count**: 1 items identified

### Session: `backend\routes\account_routes.py::account_routes` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.8, 'environment': 0.25}`
- **Reasoning**: State leakage detected (80%): Line 18: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'; Line 20: Found global_mutation pattern: 'account_bp = Blueprint("accounts", __name__, url_prefix="/api/accounts")'; Line 170: Found state_mutation pattern: 'account = Account.update(parsed_account_id, cleaned_payload)'.
- **Evidence Count**: 3 items identified

### Session: `backend\routes\branch_routes.py::branch_routes` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 16: Found global_mutation pattern: 'branch_bp = Blueprint("branches", __name__, url_prefix="/api/branches")'; Line 17: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\routes\customer_routes.py::customer_routes` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (HIGH confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.8, 'environment': 0.25}`
- **Reasoning**: State leakage detected (80%): Line 18: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'; Line 20: Found global_mutation pattern: 'customer_bp = Blueprint("customers", __name__, url_prefix="/api/customers")'; Line 147: Found state_mutation pattern: 'customer = Customer.update(parsed_customer_id, cleaned_payload)'.
- **Evidence Count**: 3 items identified

### Session: `backend\routes\employee_routes.py::employee_routes` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 16: Found global_mutation pattern: 'employee_bp = Blueprint("employees", __name__, url_prefix="/api/employees")'; Line 17: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\routes\loan_routes.py::loan_routes` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 16: Found global_mutation pattern: 'loan_bp = Blueprint("loans", __name__, url_prefix="/api/loans")'; Line 17: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\routes\procedure_routes.py::procedure_routes` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 17: Found global_mutation pattern: 'procedure_bp = Blueprint("procedures", __name__, url_prefix="/api/procedures")'; Line 18: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\routes\transaction_routes.py::transaction_routes` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 16: Found global_mutation pattern: 'transaction_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")'; Line 17: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified

### Session: `backend\routes\trigger_routes.py::trigger_routes` (2026-09-26 10:27:39 UTC)
- **Verdict**: `STATE_LEAKAGE` (MEDIUM confidence)
- **Subagent Scores**: `{'timing': 0.15, 'ordering': 0.0, 'state_leakage': 0.6, 'environment': 0.25}`
- **Reasoning**: State leakage detected (60%): Line 17: Found global_mutation pattern: 'trigger_bp = Blueprint("triggers", __name__, url_prefix="/api/triggers")'; Line 18: Found global_mutation pattern: 'logger = logging.getLogger(__name__)'.
- **Evidence Count**: 2 items identified
