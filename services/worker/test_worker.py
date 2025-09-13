"""
Basic test script to verify Celery worker setup.
Run this to ensure the worker configuration is correct.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported correctly."""
    try:
        from services.worker.celery_app import celery_app
        from services.worker.config import get_worker_settings
        from services.worker.database import get_database_session
        from services.worker.tasks.email_tasks import send_verification_email
        from services.worker.tasks.data_tasks import process_artifact_analytics
        from services.worker.tasks.maintenance_tasks import cleanup_expired_tokens
        
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_configuration():
    """Test that configuration loads correctly."""
    try:
        from services.worker.config import get_worker_settings
        
        settings = get_worker_settings()
        
        # Check required settings
        assert settings.redis_url is not None, "Redis URL not configured"
        assert settings.database_url is not None, "Database URL not configured"
        assert settings.celery_broker_url is not None, "Celery broker URL not configured"
        
        print("✓ Configuration loaded successfully")
        print(f"  - Environment: {settings.environment}")
        print(f"  - Redis URL: {settings.redis_url}")
        print(f"  - Broker URL: {settings.celery_broker_url}")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def test_celery_app():
    """Test that Celery app is configured correctly."""
    try:
        from services.worker.celery_app import celery_app
        
        # Check basic configuration
        assert celery_app.conf.broker_url is not None, "Broker URL not set"
        assert celery_app.conf.result_backend is not None, "Result backend not set"
        
        # Check task routing
        assert "task_routes" in celery_app.conf, "Task routes not configured"
        
        print("✓ Celery app configured successfully")
        print(f"  - Broker: {celery_app.conf.broker_url}")
        print(f"  - Backend: {celery_app.conf.result_backend}")
        print(f"  - Task routes: {len(celery_app.conf.task_routes)} configured")
        return True
    except Exception as e:
        print(f"✗ Celery app error: {e}")
        return False


def test_tasks():
    """Test that tasks are registered correctly."""
    try:
        from services.worker.celery_app import celery_app
        
        # Get registered tasks
        registered_tasks = list(celery_app.tasks.keys())
        
        # Check for expected tasks
        expected_tasks = [
            "health_check",
            "send_verification_email",
            "send_password_reset_email",
            "send_workspace_invitation",
            "process_artifact_analytics",
            "generate_usage_report",
            "bulk_artifact_update",
            "cleanup_expired_tokens",
            "database_health_check",
            "cleanup_old_logs",
            "system_metrics_collection",
        ]
        
        missing_tasks = []
        for task in expected_tasks:
            if task not in registered_tasks:
                missing_tasks.append(task)
        
        if missing_tasks:
            print(f"✗ Missing tasks: {missing_tasks}")
            return False
        
        print("✓ All expected tasks registered")
        print(f"  - Total tasks: {len(registered_tasks)}")
        print(f"  - Expected tasks: {len(expected_tasks)}")
        return True
    except Exception as e:
        print(f"✗ Task registration error: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Ghostworks Worker Setup")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_configuration,
        test_celery_app,
        test_tasks,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\nRunning {test.__name__}...")
        if test():
            passed += 1
        else:
            print("Test failed!")
    
    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Worker setup is correct.")
        return 0
    else:
        print("❌ Some tests failed. Check configuration and dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())