"""Integration tests for Phase 1 Temporal advanced features.

Tests:
1. Interceptors (LoggingInterceptor, MetricsInterceptor)
2. Local Activities (4 functions)
3. Search Attributes (configuration and workflow integration)
"""

import pytest


class TestInterceptors:
    """Test interceptor implementation and integration."""

    def test_interceptors_can_be_imported(self):
        """Test that interceptors can be imported without errors."""
        from app.core.interceptors import LoggingInterceptor, MetricsInterceptor

        assert LoggingInterceptor is not None
        assert MetricsInterceptor is not None

    def test_interceptors_can_be_instantiated(self):
        """Test that interceptors can be instantiated."""
        from app.core.interceptors import LoggingInterceptor, MetricsInterceptor

        li = LoggingInterceptor()
        mi = MetricsInterceptor()

        assert li is not None
        assert mi is not None
        assert type(li).__name__ == "LoggingInterceptor"
        assert type(mi).__name__ == "MetricsInterceptor"

    def test_interceptors_have_required_methods(self):
        """Test that interceptors have required Temporal methods."""
        from app.core.interceptors import LoggingInterceptor, MetricsInterceptor

        li = LoggingInterceptor()
        mi = MetricsInterceptor()

        # Check required methods
        assert hasattr(li, "intercept_activity")
        assert hasattr(li, "workflow_interceptor_class")
        assert hasattr(mi, "intercept_activity")
        assert hasattr(mi, "workflow_interceptor_class")

        # Check methods are callable
        assert callable(li.intercept_activity)
        assert callable(li.workflow_interceptor_class)
        assert callable(mi.intercept_activity)
        assert callable(mi.workflow_interceptor_class)

    def test_inbound_interceptors_exist(self):
        """Test that inbound interceptor classes exist."""
        from app.core.interceptors import (
            LoggingActivityInboundInterceptor,
            LoggingWorkflowInboundInterceptor,
            MetricsActivityInboundInterceptor,
            MetricsWorkflowInboundInterceptor,
        )

        assert LoggingActivityInboundInterceptor is not None
        assert LoggingWorkflowInboundInterceptor is not None
        assert MetricsActivityInboundInterceptor is not None
        assert MetricsWorkflowInboundInterceptor is not None


class TestLocalActivities:
    """Test local activities implementation."""

    def test_local_activities_can_be_imported(self):
        """Test that all local activities can be imported."""
        from app.activities.local import (
            check_user_exists_local,
            get_user_email_local,
            get_user_reputation_local,
            get_user_verification_score_local,
        )

        assert get_user_reputation_local is not None
        assert get_user_verification_score_local is not None
        assert check_user_exists_local is not None
        assert get_user_email_local is not None

    def test_local_activities_are_temporal_activities(self):
        """Test that local activities have Temporal activity decorator."""
        from app.activities.local import (
            check_user_exists_local,
            get_user_email_local,
            get_user_reputation_local,
            get_user_verification_score_local,
        )

        activities = [
            get_user_reputation_local,
            get_user_verification_score_local,
            check_user_exists_local,
            get_user_email_local,
        ]

        for activity in activities:
            assert hasattr(
                activity, "__temporal_activity_definition"
            ), f"{activity.__name__} is not a Temporal activity"

    def test_local_activities_have_correct_signatures(self):
        """Test that local activities have expected function signatures."""
        import inspect

        from app.activities.local import (
            check_user_exists_local,
            get_user_email_local,
            get_user_reputation_local,
            get_user_verification_score_local,
        )

        # get_user_reputation_local(user_id: int) -> float
        sig = inspect.signature(get_user_reputation_local)
        assert "user_id" in sig.parameters
        assert sig.return_annotation == float

        # get_user_verification_score_local(user_id: int) -> float
        sig = inspect.signature(get_user_verification_score_local)
        assert "user_id" in sig.parameters
        assert sig.return_annotation == float

        # check_user_exists_local(user_id: int) -> bool
        sig = inspect.signature(check_user_exists_local)
        assert "user_id" in sig.parameters
        assert sig.return_annotation == bool

        # get_user_email_local(user_id: int) -> str | None
        sig = inspect.signature(get_user_email_local)
        assert "user_id" in sig.parameters
        # Return annotation is str | None (union type)


class TestSearchAttributes:
    """Test search attributes configuration."""

    def test_docker_compose_yaml_is_valid(self):
        """Test that docker-compose.yaml is valid YAML."""
        import yaml

        with open("docker-compose.yaml", "r") as f:
            data = yaml.safe_load(f)

        assert data is not None
        assert "services" in data
        assert "temporal" in data["services"]

    def test_search_attributes_configured_in_docker_compose(self):
        """Test that all search attributes are configured in docker-compose.yaml."""
        import yaml

        with open("docker-compose.yaml", "r") as f:
            data = yaml.safe_load(f)

        temporal = data["services"]["temporal"]
        cmd = temporal.get("command", [])
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)

        # Check all 5 search attributes
        assert "user_id" in cmd_str
        assert "verification_status" in cmd_str
        assert "target_score" in cmd_str
        assert "created_at" in cmd_str
        assert "verification_methods_count" in cmd_str

    def test_verification_workflow_uses_search_attributes(self):
        """Test that VerificationWorkflow sets search attributes."""
        with open("app/workflows/verification.py", "r") as f:
            content = f.read()

        # Check for upsert_search_attributes calls
        assert "workflow.upsert_search_attributes" in content

        # Check that all attributes are set
        assert "user_id" in content
        assert "verification_status" in content
        assert "target_score" in content
        assert "created_at" in content
        assert "verification_methods_count" in content

    def test_search_attributes_example_file_exists(self):
        """Test that search attributes example file exists and is valid."""
        import ast

        with open("app/examples/search_attributes.py", "r") as f:
            content = f.read()

        # Parse to verify syntax
        ast.parse(content)

        # Check for expected query patterns
        assert "list_workflows" in content
        assert "user_id" in content
        assert "verification_status" in content


class TestWorkerIntegration:
    """Test worker integration of Phase 1 components."""

    def test_worker_module_can_be_imported(self):
        """Test that worker module can be imported."""
        from app.worker import main

        assert main is not None
        assert callable(main)

    def test_worker_imports_interceptors(self):
        """Test that worker imports interceptors."""
        with open("app/worker.py", "r") as f:
            content = f.read()

        assert "from app.core.interceptors import" in content
        assert "LoggingInterceptor" in content
        assert "MetricsInterceptor" in content

    def test_worker_imports_local_activities(self):
        """Test that worker imports local activities."""
        with open("app/worker.py", "r") as f:
            content = f.read()

        assert "from app.activities.local import" in content
        assert "get_user_reputation_local" in content
        assert "get_user_verification_score_local" in content
        assert "check_user_exists_local" in content
        assert "get_user_email_local" in content

    def test_worker_registers_interceptors(self):
        """Test that worker registers interceptors in Worker."""
        with open("app/worker.py", "r") as f:
            content = f.read()

        assert "interceptors=[LoggingInterceptor(), MetricsInterceptor()]" in content

    def test_worker_registers_local_activities(self):
        """Test that worker registers local activities in Worker."""
        with open("app/worker.py", "r") as f:
            content = f.read()

        # Check activities list includes local activities
        assert "get_user_reputation_local," in content
        assert "get_user_verification_score_local," in content
        assert "check_user_exists_local," in content
        assert "get_user_email_local," in content

    def test_worker_has_concurrency_settings(self):
        """Test that worker has proper concurrency settings."""
        with open("app/worker.py", "r") as f:
            content = f.read()

        assert "max_concurrent_activities=100" in content
        assert "max_concurrent_workflow_tasks=50" in content


class TestPhase1Documentation:
    """Test Phase 1 documentation completeness."""

    def test_temporal_advanced_features_doc_exists(self):
        """Test that TEMPORAL_ADVANCED_FEATURES.md exists."""
        import os

        assert os.path.exists("TEMPORAL_ADVANCED_FEATURES.md")

    def test_temporal_doc_mentions_phase1_features(self):
        """Test that documentation mentions all Phase 1 features."""
        with open("TEMPORAL_ADVANCED_FEATURES.md", "r") as f:
            content = f.read()

        # Check Phase 1 features are documented
        assert "Interceptors" in content
        assert "Local Activities" in content
        assert "Search Attributes" in content
        assert "Phase 1" in content

    def test_changelog_documents_phase1(self):
        """Test that CHANGELOG.md documents Phase 1 completion."""
        with open("CHANGELOG.md", "r") as f:
            content = f.read()

        # Check Phase 1 is documented
        assert "Phase 1" in content or "interceptors" in content.lower()
        assert "LoggingInterceptor" in content or "MetricsInterceptor" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
