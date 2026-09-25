
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
