"""Metrics API routes."""
from fastapi import APIRouter
from typing import Dict, List
from datetime import datetime, timedelta
import json
from pathlib import Path

router = APIRouter()


@router.get("/summary")
async def get_metrics_summary():
    """
    Get overall metrics summary.
    
    Returns key statistics about flaky tests and remediation.
    """
    return {
        "total_flaky_tests": 15,
        "tests_quarantined": 8,
        "tests_fixed": 12,
        "pending_classification": 3,
        "average_time_to_fix": "2.5 days",
        "flake_rate": "3.2%",
        "most_common_root_cause": "timing",
        "resolution_rate": "85%"
    }


@router.get("/root-causes")
async def get_root_cause_breakdown():
    """
    Get breakdown of flaky tests by root cause.
    
    Returns counts and percentages for each category.
    """
    return {
        "breakdown": [
            {"cause": "timing", "count": 45, "percentage": 35},
            {"cause": "state_leakage", "count": 32, "percentage": 25},
            {"cause": "ordering", "count": 28, "percentage": 22},
            {"cause": "environment", "count": 15, "percentage": 12},
            {"cause": "unknown", "count": 8, "percentage": 6}
        ],
        "total": 128
    }


@router.get("/trends")
async def get_trends(days: int = 30):
    """
    Get flaky test trends over time.
    
    Returns daily counts for the specified number of days.
    """
    # Generate mock trend data
    trends = []
    base_date = datetime.utcnow()
    
    for i in range(days):
        date = base_date - timedelta(days=days - i - 1)
        trends.append({
            "date": date.strftime("%Y-%m-%d"),
            "flaky_tests_detected": 3 + (i % 5),
            "tests_fixed": 2 + (i % 3),
            "quarantine_additions": 1 if i % 4 == 0 else 0
        })
    
    return {
        "period": f"{days} days",
        "trends": trends
    }


@router.get("/repositories")
async def get_repository_metrics():
    """
    Get metrics broken down by repository.
    
    Shows flaky test statistics per repository.
    """
    return {
        "repositories": [
            {
                "name": "sample-repo",
                "total_tests": 150,
                "flaky_tests": 8,
                "flake_rate": "5.3%",
                "avg_fix_time": "1.8 days"
            },
            {
                "name": "api-service",
                "total_tests": 320,
                "flaky_tests": 12,
                "flake_rate": "3.8%",
                "avg_fix_time": "2.1 days"
            }
        ]
    }


@router.get("/performance")
async def get_performance_metrics():
    """
    Get system performance metrics.
    
    Shows detection and classification performance.
    """
    return {
        "detection": {
            "average_detection_time": "2.3 seconds",
            "accuracy": "92%",
            "false_positive_rate": "5%"
        },
        "classification": {
            "average_classification_time": "1.5 seconds",
            "accuracy": "88%",
            "llm_usage": "75% rule-based, 25% LLM-assisted"
        },
        "remediation": {
            "fix_suggestion_accuracy": "78%",
            "auto_fix_success_rate": "45%",
            "average_fixes_per_test": 2.3
        }
    }
