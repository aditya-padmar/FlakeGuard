"""Remediation strategy mapping for root causes.

Maps the four root cause categories to deterministic remediation strategies.
"""
from typing import Dict, List, Any
from enum import Enum


class RootCause(str, Enum):
    """Root cause categories from F2."""
    TIMING_RACE = "timing_race"
    TIMING = "timing"
    ORDER_DEPENDENCY = "order_dependency"
    ORDERING = "ordering"
    DATA_LEAKAGE = "data_leakage"
    STATE_LEAKAGE = "state_leakage"
    ENVIRONMENT_NETWORK = "environment_network"
    ENVIRONMENT = "environment"
    NETWORK = "network"
    UNKNOWN = "unknown"


class RemediationStrategy(str, Enum):
    """Deterministic remediation strategies."""
    # Timing/Race
    DETERMINISTIC_WAIT = "deterministic_wait"
    REMOVE_SLEEP = "remove_sleep"
    ADD_PROPER_SYNC = "add_proper_sync"
    RELAX_TIMING_ASSERTION = "relax_timing_assertion"
    
    # Order Dependency
    ISOLATE_SHARED_STATE = "isolate_shared_state"
    ADD_FRESH_FIXTURE = "add_fresh_fixture"
    REMOVE_GLOBAL_STATE = "remove_global_state"
    
    # Data Leakage
    ADD_CLEANUP_TEARDOWN = "add_cleanup_teardown"
    USE_FRESH_INSTANCE = "use_fresh_instance"
    ADD_FIXTURE_ISOLATION = "add_fixture_isolation"
    
    # Environment/Network
    MOCK_EXTERNAL_DEPENDENCY = "mock_external_dependency"
    MAKE_DETERMINISTIC = "make_deterministic"
    ADD_RANDOM_SEED = "add_random_seed"
    SKIP_IF_UNAVAILABLE = "skip_if_unavailable"
    
    # Fallback
    QUARANTINE = "quarantine"


class StrategySelector:
    """Selects appropriate remediation strategy based on root cause."""
    
    # Mapping of root causes to strategies (in priority order)
    STRATEGY_MAP: Dict[RootCause, List[RemediationStrategy]] = {
        RootCause.TIMING_RACE: [
            RemediationStrategy.DETERMINISTIC_WAIT,
            RemediationStrategy.REMOVE_SLEEP,
            RemediationStrategy.ADD_PROPER_SYNC,
            RemediationStrategy.RELAX_TIMING_ASSERTION,
        ],
        RootCause.TIMING: [
            RemediationStrategy.DETERMINISTIC_WAIT,
            RemediationStrategy.REMOVE_SLEEP,
            RemediationStrategy.RELAX_TIMING_ASSERTION,
        ],
        RootCause.ORDER_DEPENDENCY: [
            RemediationStrategy.ADD_FRESH_FIXTURE,
            RemediationStrategy.ISOLATE_SHARED_STATE,
            RemediationStrategy.REMOVE_GLOBAL_STATE,
        ],
        RootCause.ORDERING: [
            RemediationStrategy.ADD_FRESH_FIXTURE,
            RemediationStrategy.ISOLATE_SHARED_STATE,
        ],
        RootCause.DATA_LEAKAGE: [
            RemediationStrategy.USE_FRESH_INSTANCE,
            RemediationStrategy.ADD_CLEANUP_TEARDOWN,
            RemediationStrategy.ADD_FIXTURE_ISOLATION,
        ],
        RootCause.STATE_LEAKAGE: [
            RemediationStrategy.USE_FRESH_INSTANCE,
            RemediationStrategy.ADD_CLEANUP_TEARDOWN,
        ],
        RootCause.ENVIRONMENT_NETWORK: [
            RemediationStrategy.MOCK_EXTERNAL_DEPENDENCY,
            RemediationStrategy.MAKE_DETERMINISTIC,
            RemediationStrategy.ADD_RANDOM_SEED,
            RemediationStrategy.SKIP_IF_UNAVAILABLE,
        ],
        RootCause.ENVIRONMENT: [
            RemediationStrategy.MAKE_DETERMINISTIC,
            RemediationStrategy.MOCK_EXTERNAL_DEPENDENCY,
            RemediationStrategy.ADD_RANDOM_SEED,
        ],
        RootCause.NETWORK: [
            RemediationStrategy.MOCK_EXTERNAL_DEPENDENCY,
            RemediationStrategy.SKIP_IF_UNAVAILABLE,
        ],
        RootCause.UNKNOWN: [
            RemediationStrategy.QUARANTINE,
        ],
    }
    
    @classmethod
    def select_strategies(
        cls, 
        root_cause: str,
        evidence: List[Dict[str, Any]] = None
    ) -> List[RemediationStrategy]:
        """
        Select remediation strategies for a root cause.
        
        Args:
            root_cause: Root cause from F2 diagnosis
            evidence: Optional evidence to refine strategy selection
            
        Returns:
            List of strategies in priority order
        """
        # Normalize root cause
        try:
            cause = RootCause(root_cause.lower())
        except ValueError:
            # Unknown root cause
            return [RemediationStrategy.QUARANTINE]
        
        strategies = cls.STRATEGY_MAP.get(cause, [RemediationStrategy.QUARANTINE])
        
        # Evidence-based refinement
        if evidence:
            strategies = cls._refine_with_evidence(cause, strategies, evidence)
        
        return strategies
    
    @classmethod
    def _refine_with_evidence(
        cls,
        root_cause: RootCause,
        strategies: List[RemediationStrategy],
        evidence: List[Dict[str, Any]]
    ) -> List[RemediationStrategy]:
        """
        Refine strategy selection based on evidence.
        
        Args:
            root_cause: Root cause category
            strategies: Initial strategies
            evidence: Evidence from F2
            
        Returns:
            Refined strategy list
        """
        refined = strategies.copy()
        
        # Extract evidence reasons
        reasons = [e.get("reason", "").lower() for e in evidence]
        evidence_text = " ".join(reasons)
        
        # Timing refinements
        if root_cause in [RootCause.TIMING_RACE, RootCause.TIMING]:
            if "sleep" in evidence_text:
                # Prioritize sleep removal
                if RemediationStrategy.REMOVE_SLEEP in refined:
                    refined.remove(RemediationStrategy.REMOVE_SLEEP)
                    refined.insert(0, RemediationStrategy.REMOVE_SLEEP)
            
            if "assertion" in evidence_text and "elapsed" in evidence_text:
                # Prioritize relaxing timing assertions
                if RemediationStrategy.RELAX_TIMING_ASSERTION in refined:
                    refined.remove(RemediationStrategy.RELAX_TIMING_ASSERTION)
                    refined.insert(0, RemediationStrategy.RELAX_TIMING_ASSERTION)
        
        # Order/State refinements
        if root_cause in [RootCause.ORDER_DEPENDENCY, RootCause.ORDERING]:
            if "shared" in evidence_text or "global" in evidence_text:
                if RemediationStrategy.ISOLATE_SHARED_STATE in refined:
                    refined.remove(RemediationStrategy.ISOLATE_SHARED_STATE)
                    refined.insert(0, RemediationStrategy.ISOLATE_SHARED_STATE)
        
        # Leakage refinements
        if root_cause in [RootCause.DATA_LEAKAGE, RootCause.STATE_LEAKAGE]:
            if "cleanup" in evidence_text or "teardown" in evidence_text:
                if RemediationStrategy.ADD_CLEANUP_TEARDOWN in refined:
                    refined.remove(RemediationStrategy.ADD_CLEANUP_TEARDOWN)
                    refined.insert(0, RemediationStrategy.ADD_CLEANUP_TEARDOWN)
        
        # Environment refinements
        if root_cause in [RootCause.ENVIRONMENT_NETWORK, RootCause.ENVIRONMENT]:
            if "random" in evidence_text:
                if RemediationStrategy.ADD_RANDOM_SEED in refined:
                    refined.remove(RemediationStrategy.ADD_RANDOM_SEED)
                    refined.insert(0, RemediationStrategy.ADD_RANDOM_SEED)
            
            if "network" in evidence_text or "api" in evidence_text:
                if RemediationStrategy.MOCK_EXTERNAL_DEPENDENCY in refined:
                    refined.remove(RemediationStrategy.MOCK_EXTERNAL_DEPENDENCY)
                    refined.insert(0, RemediationStrategy.MOCK_EXTERNAL_DEPENDENCY)
        
        return refined
    
    @classmethod
    def get_strategy_description(cls, strategy: RemediationStrategy) -> str:
        """
        Get human-readable description of a strategy.
        
        Args:
            strategy: Remediation strategy
            
        Returns:
            Description string
        """
        descriptions = {
            RemediationStrategy.DETERMINISTIC_WAIT: "Replace arbitrary sleep with deterministic wait condition",
            RemediationStrategy.REMOVE_SLEEP: "Remove hard-coded sleep and use proper synchronization",
            RemediationStrategy.ADD_PROPER_SYNC: "Add proper synchronization mechanism (locks, events)",
            RemediationStrategy.RELAX_TIMING_ASSERTION: "Relax or remove timing-based assertion",
            
            RemediationStrategy.ISOLATE_SHARED_STATE: "Isolate shared/global state between tests",
            RemediationStrategy.ADD_FRESH_FIXTURE: "Add fresh fixture to provide test isolation",
            RemediationStrategy.REMOVE_GLOBAL_STATE: "Remove or reset global state dependencies",
            
            RemediationStrategy.ADD_CLEANUP_TEARDOWN: "Add cleanup/teardown to reset state",
            RemediationStrategy.USE_FRESH_INSTANCE: "Use fresh instance instead of shared object",
            RemediationStrategy.ADD_FIXTURE_ISOLATION: "Add fixture with proper isolation (yield pattern)",
            
            RemediationStrategy.MOCK_EXTERNAL_DEPENDENCY: "Mock external dependency (network, filesystem)",
            RemediationStrategy.MAKE_DETERMINISTIC: "Make test deterministic (fixed seed, etc.)",
            RemediationStrategy.ADD_RANDOM_SEED: "Add fixed random seed for deterministic behavior",
            RemediationStrategy.SKIP_IF_UNAVAILABLE: "Skip test if external resource unavailable",
            
            RemediationStrategy.QUARANTINE: "Quarantine test pending investigation",
        }
        
        return descriptions.get(strategy, "Unknown strategy")
