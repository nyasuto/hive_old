"""
System Integration Tests for Hive

Tests the complete workflow from Worker startup to Honey collection
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from comb.api import CombAPI
from comb.message_router import MessagePriority, MessageType
from queen.honey_collector import HoneyCollector
from queen.task_distributor import Priority, TaskDistributor


class TestSystemIntegration:
    """Complete system integration tests"""

    def setup_method(self) -> None:
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        import os

        # Change to temp directory for isolated testing
        try:
            self.original_cwd = os.getcwd()
        except FileNotFoundError:
            # If current directory doesn't exist, use the temp directory
            self.original_cwd = str(self.temp_dir)
        os.chdir(self.temp_dir)

        # Initialize core components
        self.queen_api = CombAPI("queen")
        self.developer_api = CombAPI("developer")
        self.task_distributor = TaskDistributor()
        self.honey_collector = HoneyCollector()

    def teardown_method(self) -> None:
        """Clean up test environment"""
        import os
        import shutil

        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_complete_hive_workflow(self) -> None:
        """Test complete workflow: Task creation → Worker communication → Completion → Honey collection"""

        # Phase 1: Project initialization
        project_task_id = self.queen_api.start_task(
            "Web Application Development",
            task_type="feature",
            description="Build a complete web application with authentication",
            issue_number=100,
            workers=["queen", "developer"],
        )

        assert project_task_id is not None
        assert len(project_task_id) == 8  # 8-character UUID

        # Phase 2: Task decomposition and distribution
        nectar = self.task_distributor.create_nectar(
            title="Implement User Authentication",
            description="Create JWT-based authentication system",
            assigned_to="developer",
            priority=Priority.HIGH,
            expected_honey=["auth_module.py", "auth_tests.py", "auth_docs.md"],
        )
        nectar_id = nectar.nectar_id

        assert nectar_id is not None
        assert nectar_id.startswith("nectar-")

        # Phase 3: Worker communication - Queen sends task details
        communication_success = self.queen_api.send_message(
            to_worker="developer",
            content={
                "nectar_id": nectar_id,
                "task_type": "authentication_implementation",
                "requirements": [
                    "JWT token generation and validation",
                    "Password hashing with bcrypt",
                    "Login/logout endpoints",
                    "Unit tests with >90% coverage",
                ],
                "technical_specs": {
                    "framework": "FastAPI",
                    "auth_library": "PyJWT",
                    "password_hashing": "bcrypt",
                    "database": "PostgreSQL",
                },
                "deadline": "2024-01-20T18:00:00Z",
            },
            message_type=MessageType.REQUEST,
            priority=MessagePriority.HIGH,
        )

        assert communication_success is True

        # Phase 4: Developer receives and acknowledges task
        developer_messages = self.developer_api.receive_messages()
        assert len(developer_messages) == 1

        task_message = developer_messages[0]
        assert task_message.from_worker == "queen"
        assert task_message.to_worker == "developer"
        assert task_message.message_type == MessageType.REQUEST
        assert "nectar_id" in task_message.content

        # Developer acknowledges task
        acknowledgment_success = self.developer_api.send_response(
            original_message=task_message,
            response_content={
                "status": "acknowledged",
                "estimated_completion": "2024-01-19T16:00:00Z",
                "questions": [
                    "Should we implement OAuth2 integration as well?",
                    "What should be the JWT token expiration time?",
                ],
                "proposed_approach": "Start with core JWT implementation, then add OAuth2",
            },
            priority=MessagePriority.MEDIUM,
        )

        assert acknowledgment_success is True

        # Phase 5: Implementation simulation - Create actual files
        auth_module_content = '''"""
User Authentication Module

JWT-based authentication system with bcrypt password hashing
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

class AuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def generate_token(self, user_id: int, expires_in: int = 3600) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
'''

        auth_test_content = '''"""
Authentication Module Tests

Comprehensive tests for JWT authentication system
"""

import pytest
from auth_module import AuthManager

class TestAuthManager:
    def setup_method(self):
        self.auth = AuthManager("test_secret_key")

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "secure_password_123"
        hashed = self.auth.hash_password(password)

        assert hashed != password
        assert self.auth.verify_password(password, hashed)
        assert not self.auth.verify_password("wrong_password", hashed)

    def test_token_generation(self):
        """Test JWT token generation and verification"""
        user_id = 12345
        token = self.auth.generate_token(user_id)

        assert token is not None
        assert isinstance(token, str)

        payload = self.auth.verify_token(token)
        assert payload is not None
        assert payload['user_id'] == user_id

    def test_token_expiration(self):
        """Test token expiration handling"""
        user_id = 12345
        # Create token with 1 second expiration
        token = self.auth.generate_token(user_id, expires_in=1)

        # Token should be valid immediately
        payload = self.auth.verify_token(token)
        assert payload is not None
'''

        auth_docs_content = """# Authentication System Documentation

## Overview

This module provides JWT-based authentication with bcrypt password hashing for secure user management.

## Features

- **Password Hashing**: Secure bcrypt hashing with salt
- **JWT Tokens**: Stateless authentication tokens
- **Token Validation**: Automatic expiration and signature verification
- **Security**: Industry-standard cryptographic practices

## Usage

```python
from auth_module import AuthManager

# Initialize
auth = AuthManager("your_secret_key")

# Hash password
hashed_password = auth.hash_password("user_password")

# Generate token
token = auth.generate_token(user_id=123)

# Verify token
payload = auth.verify_token(token)
```

## API Reference

### AuthManager Class

#### `__init__(secret_key: str)`
Initialize authentication manager with secret key.

#### `hash_password(password: str) -> str`
Hash password using bcrypt with automatic salt generation.

#### `verify_password(password: str, hashed: str) -> bool`
Verify plain password against bcrypt hash.

#### `generate_token(user_id: int, expires_in: int = 3600) -> str`
Generate JWT token with user ID and expiration.

#### `verify_token(token: str) -> Optional[dict]`
Verify and decode JWT token, returning payload or None.

## Security Considerations

- Use strong secret keys (minimum 32 characters)
- Implement token refresh mechanisms
- Consider token blacklisting for logout
- Use HTTPS in production

## Test Coverage

Current test coverage: 95%
- Password hashing: 100%
- Token generation: 100%
- Token validation: 90%
"""

        # Create implementation files
        auth_module_file = self.temp_dir / "auth_module.py"
        auth_test_file = self.temp_dir / "auth_tests.py"
        auth_docs_file = self.temp_dir / "auth_docs.md"

        auth_module_file.write_text(auth_module_content)
        auth_test_file.write_text(auth_test_content)
        auth_docs_file.write_text(auth_docs_content)

        # Phase 6: Progress reporting during implementation
        # Developer starts working on the authentication task
        dev_task_id = self.developer_api.start_task(
            "Implement User Authentication",
            task_type="implementation",
            description="JWT authentication with bcrypt password hashing"
        )
        assert dev_task_id is not None

        progress_reports = [
            (
                "Authentication framework setup completed",
                "Created base AuthManager class",
            ),
            (
                "Password hashing implementation completed",
                "bcrypt integration with salt",
            ),
            ("JWT token generation implemented", "HS256 algorithm with expiration"),
            ("Token validation completed", "Error handling for expired/invalid tokens"),
            ("Unit tests created", "95% test coverage achieved"),
            ("Documentation completed", "API reference and usage examples"),
        ]

        for description, details in progress_reports:
            progress_success = self.developer_api.add_progress(description, details)
            assert progress_success is True

            # Send progress notification to Queen
            notification_success = self.developer_api.send_notification(
                to_worker="queen",
                content={
                    "type": "progress_update",
                    "nectar_id": nectar_id,
                    "progress_description": description,
                    "completion_percentage": (
                        progress_reports.index((description, details)) + 1
                    )
                    / len(progress_reports)
                    * 100,
                },
                priority=MessagePriority.MEDIUM,
            )
            assert notification_success is True

        # Phase 7: Technical decisions recording
        technical_decisions = [
            (
                "JWT vs Session-based authentication",
                "Stateless JWT tokens better for microservices architecture",
                ["Session cookies", "OAuth2 only", "API keys"],
            ),
            (
                "bcrypt vs other hashing algorithms",
                "bcrypt provides adaptive hashing with built-in salt",
                ["PBKDF2", "scrypt", "Argon2"],
            ),
        ]

        for decision, reasoning, alternatives in technical_decisions:
            decision_success = self.developer_api.add_technical_decision(
                decision, reasoning, alternatives
            )
            assert decision_success is True

        # Phase 8: Challenge and solution recording
        challenges = [
            (
                "JWT secret key management",
                "Use environment variables with fallback to secure key derivation",
            ),
            (
                "Token refresh strategy",
                "Implement sliding window refresh with blacklist for security",
            ),
        ]

        for challenge, solution in challenges:
            challenge_success = self.developer_api.add_challenge(challenge, solution)
            assert challenge_success is True

        # Phase 9: Metrics recording
        implementation_metrics = {
            "implementation_time_hours": 6.5,
            "lines_of_code": 145,
            "test_coverage_percentage": 95,
            "performance_metrics": {
                "password_hash_time_ms": 125,
                "token_generation_time_ms": 8,
                "token_validation_time_ms": 12,
            },
            "code_quality": {"pylint_score": 9.1, "complexity_score": "low"},
        }

        metrics_success = self.developer_api.add_metrics(implementation_metrics)
        assert metrics_success is True

        # Phase 10: Task completion
        completion_result = {
            "status": "completed_successfully",
            "files_created": ["auth_module.py", "auth_tests.py", "auth_docs.md"],
            "test_results": {
                "tests_run": 8,
                "tests_passed": 8,
                "tests_failed": 0,
                "coverage_percentage": 95,
            },
            "performance_benchmarks": {
                "authentication_speed": "12ms average",
                "memory_usage": "2.1MB baseline",
            },
            "documentation_status": "complete",
            "ready_for_review": True,
        }

        task_completion_success = self.developer_api.complete_task("completed")
        assert task_completion_success is True

        # Notify Queen of completion
        completion_notification = self.developer_api.send_notification(
            to_worker="queen",
            content={
                "type": "task_completed",
                "nectar_id": nectar_id,
                "completion_result": completion_result,
                "next_steps_suggested": [
                    "Code review",
                    "Integration testing",
                    "Documentation review",
                ],
            },
            priority=MessagePriority.HIGH,
        )
        assert completion_notification is True

        # Phase 11: Queen processes completion
        queen_messages = self.queen_api.receive_messages()
        completion_messages = [
            msg for msg in queen_messages if msg.content.get("type") == "task_completed"
        ]
        assert len(completion_messages) >= 1

        completion_msg = completion_messages[0]
        assert completion_msg.content["nectar_id"] == nectar_id
        assert (
            completion_msg.content["completion_result"]["status"]
            == "completed_successfully"
        )

        # Phase 12: Honey collection (artifact collection)
        honey_artifacts = self.honey_collector.collect_manual_artifacts(
            [str(auth_module_file), str(auth_test_file), str(auth_docs_file)], nectar_id
        )

        assert len(honey_artifacts) == 3

        # Verify artifact details
        code_artifacts = [a for a in honey_artifacts if a.original_path.endswith(".py")]
        doc_artifacts = [a for a in honey_artifacts if a.original_path.endswith(".md")]

        assert len(code_artifacts) == 2  # auth_module.py and auth_tests.py
        assert len(doc_artifacts) == 1  # auth_docs.md

        # Check quality scores
        for artifact in honey_artifacts:
            assert artifact.quality_score > 0
            assert artifact.nectar_id == nectar_id
            assert Path(artifact.collected_path).exists()

        # Phase 13: Quality reporting
        quality_report = self.honey_collector.generate_quality_report()

        assert quality_report.total_artifacts == 3
        assert quality_report.average_quality > 50  # Should be good quality
        assert len(quality_report.type_distribution) >= 2  # code and docs
        assert quality_report.generated_at is not None

        # Phase 14: Final system verification
        system_status = {
            "queen_status": self.queen_api.get_status(),
            "developer_status": self.developer_api.get_status(),
            "task_distributor_stats": self.task_distributor.get_worker_workload("queen"),
            "honey_collection_stats": self.honey_collector.get_collection_stats(),
        }

        # Verify all components are functioning
        assert system_status["queen_status"]["worker_id"] == "queen"
        assert system_status["developer_status"]["worker_id"] == "developer"
        assert system_status["honey_collection_stats"]["total_artifacts"] == 3

        # Phase 15: Generate comprehensive reports
        daily_summary_success = self.queen_api.generate_daily_summary()
        assert daily_summary_success is True

        # Verify workflow completeness
        current_task = self.queen_api.get_current_task()
        if current_task:
            assert current_task["id"] == project_task_id
            assert current_task["status"] in ["completed", "in_progress"]

    def test_multi_worker_coordination(self) -> None:
        """Test coordination between multiple workers"""

        # Initialize additional workers
        architect_api = CombAPI("architect")
        tester_api = CombAPI("tester")

        # Multi-worker project
        self.queen_api.start_task(
            "Microservices Architecture Implementation",
            task_type="architecture",
            workers=["queen", "architect", "developer", "tester"],
        )

        # Phase 1: Architecture planning
        self.task_distributor.create_nectar(
            title="Design microservices architecture",
            description="Create comprehensive microservices architecture design",
            assigned_to="architect",
            expected_honey=["architecture_diagram.md", "service_specs.json"],
        )

        # Phase 2: Architect → Developer communication
        arch_to_dev_success = architect_api.send_message(
            to_worker="developer",
            content={
                "architecture_decision": "Event-driven microservices",
                "services_to_implement": [
                    "user-service",
                    "auth-service",
                    "notification-service",
                ],
                "communication_pattern": "async_messaging",
                "technology_stack": {
                    "messaging": "RabbitMQ",
                    "database": "PostgreSQL + Redis",
                    "api_gateway": "Kong",
                },
            },
            message_type=MessageType.REQUEST,
        )
        assert arch_to_dev_success is True

        # Phase 3: Developer → Tester communication
        dev_to_tester_success = self.developer_api.send_message(
            to_worker="tester",
            content={
                "services_ready": ["user-service"],
                "test_endpoints": [
                    "POST /users",
                    "GET /users/{id}",
                    "PUT /users/{id}",
                    "DELETE /users/{id}",
                ],
                "test_data_location": "test_fixtures/users.json",
            },
            message_type=MessageType.NOTIFICATION,
        )
        assert dev_to_tester_success is True

        # Phase 4: Cross-worker status updates
        status_updates = [
            (architect_api, "Architecture design 80% complete"),
            (self.developer_api, "User service implementation started"),
            (tester_api, "Test plan created, waiting for endpoints"),
        ]

        for worker_api, status in status_updates:
            notification_success = worker_api.send_notification(
                to_worker="queen",
                content={"status_update": status, "worker": worker_api.worker_id},
                priority=MessagePriority.MEDIUM,
            )
            assert notification_success is True

        # Phase 5: Verify cross-communication
        all_workers = [self.queen_api, architect_api, self.developer_api, tester_api]

        for worker_api in all_workers:
            messages = worker_api.receive_messages()
            # Each worker should have received relevant messages
            if worker_api.worker_id == "queen":
                status_messages = [
                    msg for msg in messages if "status_update" in msg.content
                ]
                assert len(status_messages) >= 2  # At least 2 status updates

    def test_error_handling_and_recovery(self) -> None:
        """Test system behavior under error conditions"""

        # Phase 1: Simulate communication errors
        with patch.object(
            self.developer_api.message_router, "send_message", return_value=False
        ):
            # This should fail
            failed_send = self.developer_api.send_message(
                to_worker="queen",
                content={"test": "should_fail"},
                message_type=MessageType.REQUEST,
            )
            assert failed_send is False

        # Phase 2: Test with invalid message content
        try:
            # This should handle gracefully
            self.queen_api.send_message(
                to_worker="nonexistent_worker",
                content={"invalid": None},  # None values might cause issues
                message_type=MessageType.REQUEST,
            )
        except Exception:
            pytest.fail("Should handle invalid content gracefully")

        # Phase 3: Test resource lock conflicts
        resource_name = "shared_database"

        # Queen acquires lock
        queen_lock = self.queen_api.acquire_lock(resource_name, timeout=1.0)
        assert queen_lock is True

        # Developer tries to acquire same lock (should fail)
        dev_lock = self.developer_api.acquire_lock(resource_name, timeout=1.0)
        assert dev_lock is False

        # Queen releases lock
        queen_release = self.queen_api.release_lock(resource_name)
        assert queen_release is True

        # Developer can now acquire lock
        dev_lock_retry = self.developer_api.acquire_lock(resource_name, timeout=1.0)
        assert dev_lock_retry is True

        # Clean up
        self.developer_api.release_lock(resource_name)

        # Phase 4: Test invalid nectar handling
        invalid_nectar = self.task_distributor.create_nectar(
            title="Test Task",  # Valid title
            description="Test task for invalid handling",  # Valid description
            assigned_to="test_worker",  # Valid worker
            expected_honey=[],  # No expected outputs
        )
        # Should still create nectar but with defaults
        assert invalid_nectar is not None

    def test_performance_under_load(self) -> None:
        """Test system performance with multiple concurrent operations"""

        # Phase 1: Bulk message sending
        start_time = time.time()
        message_count = 50

        for i in range(message_count):
            success = self.queen_api.send_message(
                to_worker="developer",
                content={"bulk_message": i, "data": f"message_{i}"},
                message_type=MessageType.NOTIFICATION,
            )
            assert success is True

        send_time = time.time() - start_time
        print(f"Sent {message_count} messages in {send_time:.2f} seconds")

        # Should complete within reasonable time
        assert send_time < 10.0  # 10 seconds for 50 messages

        # Phase 2: Bulk message receiving
        start_time = time.time()
        received_messages = self.developer_api.receive_messages()
        receive_time = time.time() - start_time

        print(
            f"Received {len(received_messages)} messages in {receive_time:.2f} seconds"
        )
        assert len(received_messages) == message_count
        assert receive_time < 5.0  # Should be fast to receive

        # Phase 3: Concurrent lock operations
        locks_acquired = 0
        lock_attempts = 20

        for i in range(lock_attempts):
            resource_name = f"resource_{i}"
            if self.queen_api.acquire_lock(resource_name, timeout=0.1):
                locks_acquired += 1
                self.queen_api.release_lock(resource_name)

        assert locks_acquired == lock_attempts  # All should succeed

        # Phase 4: Task and honey collection performance
        start_time = time.time()

        # Create multiple tasks
        task_count = 10
        for i in range(task_count):
            task_id = self.queen_api.start_task(
                f"Performance Test Task {i}",
                task_type="performance_test",
            )
            assert task_id is not None

        task_creation_time = time.time() - start_time
        print(f"Created {task_count} tasks in {task_creation_time:.2f} seconds")
        assert task_creation_time < 5.0

        # Test file collection performance
        test_files = []
        for i in range(10):
            test_file = self.temp_dir / f"perf_test_{i}.py"
            test_file.write_text(f"# Performance test file {i}\nprint('test {i}')")
            test_files.append(str(test_file))

        start_time = time.time()
        honey_artifacts = self.honey_collector.collect_manual_artifacts(
            test_files, "performance_test"
        )
        collection_time = time.time() - start_time

        print(
            f"Collected {len(honey_artifacts)} artifacts in {collection_time:.2f} seconds"
        )
        assert len(honey_artifacts) == 10
        assert collection_time < 3.0

    def test_data_persistence_and_recovery(self) -> None:
        """Test data persistence across API restarts"""

        # Phase 1: Create initial data
        original_task_id = self.queen_api.start_task(
            "Persistence Test", task_type="test"
        )
        original_message_success = self.queen_api.send_message(
            to_worker="developer",
            content={"persistence_test": True},
            message_type=MessageType.REQUEST,
        )

        assert original_task_id is not None
        assert original_message_success is True

        # Create test file for honey collection
        test_file = self.temp_dir / "persistence_test.py"
        test_file.write_text("# Persistence test file\nprint('persistence test')")

        original_artifacts = self.honey_collector.collect_manual_artifacts(
            [str(test_file)], "persistence_nectar"
        )
        assert len(original_artifacts) == 1

        # Phase 2: Simulate system restart by creating new API instances
        new_queen_api = CombAPI("queen")
        new_developer_api = CombAPI("developer")
        new_honey_collector = HoneyCollector()

        # Phase 3: Verify data persistence
        # Messages should be available to new API instance
        persisted_messages = new_developer_api.receive_messages()
        assert len(persisted_messages) >= 1

        persistence_message = None
        for msg in persisted_messages:
            if msg.content.get("persistence_test"):
                persistence_message = msg
                break

        assert persistence_message is not None
        assert persistence_message.from_worker == "queen"

        # Honey collection should persist
        collection_stats = new_honey_collector.get_collection_stats()
        assert collection_stats["total_artifacts"] >= 1

        # Work logs should persist
        # Current task might be None if completed, but at least the system should work
        new_task_id = new_queen_api.start_task(
            "Post-restart task", task_type="recovery_test"
        )
        assert new_task_id is not None


class TestHiveScenarios:
    """Real-world scenario tests"""

    def setup_method(self) -> None:
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        import os

        try:
            self.original_cwd = os.getcwd()
        except FileNotFoundError:
            # If current directory doesn't exist, use the temp directory
            self.original_cwd = str(self.temp_dir)
        os.chdir(self.temp_dir)

    def teardown_method(self) -> None:
        """Clean up test environment"""
        import os
        import shutil

        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_web_development_scenario(self) -> None:
        """Test complete web development project scenario"""

        # Initialize team
        queen = CombAPI("queen")
        frontend = CombAPI("frontend")
        backend = CombAPI("backend")
        task_distributor = TaskDistributor()

        # Project start
        queen.start_task(
            "E-commerce Platform Development",
            task_type="web_development",
            description="Build complete e-commerce platform",
            workers=["queen", "frontend", "backend"],
        )

        # Backend task
        task_distributor.create_nectar(
            title="API Development",
            description="Develop backend API with database models and tests",
            assigned_to="backend",
            expected_honey=["api_server.py", "database_models.py", "api_tests.py"],
        )

        # Frontend task
        task_distributor.create_nectar(
            title="User Interface Development",
            description="Create user interface with HTML, CSS, and JavaScript",
            assigned_to="frontend",
            expected_honey=["index.html", "styles.css", "app.js"],
        )

        # Coordinate between frontend and backend
        api_spec_sharing = backend.send_message(
            to_worker="frontend",
            content={
                "api_specification": {
                    "base_url": "http://localhost:8000/api",
                    "endpoints": {
                        "products": {"GET": "/products", "POST": "/products"},
                        "users": {"GET": "/users", "POST": "/users"},
                        "orders": {"GET": "/orders", "POST": "/orders"},
                    },
                    "authentication": "Bearer token",
                }
            },
            message_type=MessageType.NOTIFICATION,
        )

        assert api_spec_sharing is True

        # Frontend acknowledges API spec
        frontend_messages = frontend.receive_messages()
        api_msg = next(
            msg for msg in frontend_messages if "api_specification" in msg.content
        )

        frontend_response = frontend.send_response(
            api_msg,
            {
                "status": "api_spec_received",
                "integration_plan": "Will implement API client with axios",
                "expected_completion": "2 days",
            },
        )

        assert frontend_response is True

        # Verify coordination success
        backend_messages = backend.receive_messages()
        response_msgs = [
            msg for msg in backend_messages if msg.message_type == MessageType.RESPONSE
        ]
        assert len(response_msgs) >= 1

    def test_bug_fix_scenario(self) -> None:
        """Test bug fix workflow scenario"""

        queen = CombAPI("queen")
        developer = CombAPI("developer")
        tester = CombAPI("tester")

        # Bug report
        queen.start_task(
            "Fix Authentication Bug",
            task_type="bug_fix",
            description="Users cannot log in with special characters in password",
            issue_number=404,
        )

        # Bug analysis - need to start a task first for progress tracking
        developer.start_task("Bug Analysis", task_type="bug_analysis")
        analysis_progress = developer.add_progress(
            "Bug analysis completed",
            "Issue traced to password encoding in JWT generation",
        )
        assert analysis_progress is True

        # Technical decision
        fix_decision = developer.add_technical_decision(
            "UTF-8 encoding for password handling",
            "Ensures proper handling of special characters",
            ["Base64 encoding", "ASCII restriction", "Character escaping"],
        )
        assert fix_decision is True

        # Fix implementation
        bug_challenge = developer.add_challenge(
            "Backward compatibility with existing hashed passwords",
            "Implement migration script for password re-hashing",
        )
        assert bug_challenge is True

        # Testing coordination
        test_request = developer.send_message(
            to_worker="tester",
            content={
                "bug_fix_ready": True,
                "test_scenarios": [
                    "Login with special characters: !@#$%^&*()",
                    "Login with unicode characters: café, naïve",
                    "Login with existing user passwords",
                ],
                "expected_behavior": "All logins should succeed",
            },
            message_type=MessageType.REQUEST,
        )
        assert test_request is True

        # Tester confirms
        tester_messages = tester.receive_messages()
        test_msg = next(
            msg for msg in tester_messages if "bug_fix_ready" in msg.content
        )

        test_confirmation = tester.send_response(
            test_msg,
            {
                "testing_status": "in_progress",
                "test_cases_created": 15,
                "estimated_completion": "4 hours",
            },
        )
        assert test_confirmation is True

        # Complete bug fix
        completion_success = developer.complete_task("bug_fixed")
        assert completion_success is True
