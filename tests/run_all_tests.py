import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import unittest
from tests.test_database import test_database_crud
from tests.test_ml_pipeline import (
    test_feature_engineering,
    test_model_training_and_metrics,
    test_predictor_forecast
)
from tests.test_agents import (
    test_agent_workflow_execution,
    test_human_approval_lifecycle
)


def run_all_tests():
    print("=" * 65)
    print("  HEALTH SUPPLY AI: COMPREHENSIVE AUTOMATED VERIFICATION SUITE")
    print("=" * 65)

    tests = [
        ("Database Models & CRUD Operations", test_database_crud),
        ("Feature Engineering & Leakage Check", test_feature_engineering),
        ("Random Forest Training & MAE/RMSE", test_model_training_and_metrics),
        ("Multi-Horizon Demand Predictor", test_predictor_forecast),
        ("4-Agent Sequential Workflow Execution", test_agent_workflow_execution),
        ("Human-in-the-Loop Approval & Stock Update", test_human_approval_lifecycle),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"\n[RUNNING] {name}...")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAILED] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 65)
    print(f"  TEST RESULTS: {passed} PASSED, {failed} FAILED (TOTAL: {len(tests)})")
    print("=" * 65)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
