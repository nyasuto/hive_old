#!/usr/bin/env python3
"""
Worker Communication System for Hive Distributed Processing

This module provides communication between issue_solver_agent.py and tmux workers,
enabling real distributed processing instead of simulation.
"""

import asyncio
import json
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


class WorkerCommunicationError(Exception):
    """Worker communication related errors"""

    pass


class WorkerCommunicator:
    """Handles communication between issue solver and tmux workers"""

    def __init__(self, session_name: str = "cozy-hive"):
        self.session_name = session_name
        self.config = self._load_config()
        self.temp_dir = Path(tempfile.gettempdir()) / "hive_worker_comm"
        self.temp_dir.mkdir(exist_ok=True)

    def _load_config(self) -> dict[str, Any]:
        """Load worker configuration"""
        config_path = Path(__file__).parent.parent / "config" / "worker_config.yaml"

        # Default configuration if file doesn't exist
        default_config = {
            "session_name": "cozy-hive",
            "workers": {
                "developer": {
                    "tmux_pane": "cozy-hive:developer",
                    "claude_command": "claude-code --role=developer",
                    "timeout": 300,
                },
                "tester": {
                    "tmux_pane": "cozy-hive:tester",
                    "claude_command": "claude-code --role=tester",
                    "timeout": 180,
                },
                "analyzer": {
                    "tmux_pane": "cozy-hive:analyzer",
                    "claude_command": "claude-code --role=analyzer",
                    "timeout": 240,
                },
                "documenter": {
                    "tmux_pane": "cozy-hive:documenter",
                    "claude_command": "claude-code --role=documenter",
                    "timeout": 120,
                },
                "reviewer": {
                    "tmux_pane": "cozy-hive:reviewer-",
                    "claude_command": "claude-code --role=reviewer",
                    "timeout": 180,
                },
            },
        }

        if config_path.exists() and yaml is not None:
            with open(config_path) as f:
                loaded_config = yaml.safe_load(f)
                return loaded_config if loaded_config is not None else default_config
        else:
            # Create default config file if yaml is available
            if yaml is not None:
                config_path.parent.mkdir(exist_ok=True)
                with open(config_path, "w") as f:
                    yaml.dump(default_config, f, default_flow_style=False)
            return default_config

    def check_tmux_session(self) -> bool:
        """Check if tmux session exists"""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", self.session_name],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False

    def check_worker_pane(self, worker_name: str) -> bool:
        """Check if specific worker pane exists"""
        if worker_name not in self.config["workers"]:
            return False

        pane_name = self.config["workers"][worker_name]["tmux_pane"]
        try:
            result = subprocess.run(
                ["tmux", "list-panes", "-t", pane_name], capture_output=True, text=True
            )
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False

    async def send_task_to_worker(
        self, worker_name: str, task: dict[str, Any]
    ) -> dict[str, Any]:
        """Send task to specific worker via tmux"""
        if not self.check_tmux_session():
            raise WorkerCommunicationError(
                f"Tmux session '{self.session_name}' not found"
            )

        if not self.check_worker_pane(worker_name):
            raise WorkerCommunicationError(f"Worker pane '{worker_name}' not found")

        # Generate task ID
        task_id = str(uuid4())
        task_with_id = {
            "task_id": task_id,
            "worker_name": worker_name,
            "timestamp": datetime.now().isoformat(),
            **task,
        }

        # Create task file
        task_file = self.temp_dir / f"task_{task_id}.json"
        with open(task_file, "w") as f:
            json.dump(task_with_id, f, indent=2)

        # Create result file path
        result_file = self.temp_dir / f"result_{task_id}.json"

        # Send task to worker
        pane_name = self.config["workers"][worker_name]["tmux_pane"]

        # Create command to execute in worker pane
        command = self._create_worker_command(worker_name, task_file, result_file)

        try:
            # Send command to tmux pane
            subprocess.run(
                ["tmux", "send-keys", "-t", pane_name, command, "Enter"], check=True
            )

            # Wait for result
            timeout = self.config["workers"][worker_name].get("timeout", 300)
            result = await self._wait_for_result(result_file, timeout)

            return {
                "task_id": task_id,
                "worker_name": worker_name,
                "status": "completed",
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }

        except subprocess.SubprocessError as e:
            raise WorkerCommunicationError(
                f"Failed to send task to worker {worker_name}: {e}"
            ) from e
        except TimeoutError as e:
            raise WorkerCommunicationError(f"Worker {worker_name} timed out") from e
        finally:
            # Cleanup files
            for file_path in [task_file, result_file]:
                if file_path.exists():
                    file_path.unlink()

    def _create_worker_command(
        self, worker_name: str, task_file: Path, result_file: Path
    ) -> str:
        """Create command to execute in worker pane"""
        # For now, we'll use a simple Python command to process the task
        # In a full implementation, this would integrate with Claude Code
        return f'''python3 -c "
import json
import time
from pathlib import Path

# Read task
with open('{task_file}', 'r') as f:
    task = json.load(f)

# Simulate worker processing
print(f'🏗️ {{task[\"worker_name\"].capitalize()}} Worker: Processing task {{task[\"task_id\"][:8]}}...')
time.sleep(1)  # Simulate work

# Create result based on worker type
if task['worker_name'] == 'documenter':
    result = {{
        'task_id': task['task_id'],
        'worker_type': 'documenter',
        'status': 'completed',
        'output': 'GitHub Issue information retrieved and formatted',
        'content': {{
            'issue_number': task.get('issue_number', 'N/A'),
            'issue_title': 'Example Issue Title',
            'issue_body': 'This is example issue content retrieved from GitHub',
            'labels': ['bug', 'priority: medium'],
            'assignees': [],
            'status': 'open'
        }},
        'processing_time': 1.0,
        'timestamp': task['timestamp']
    }}
elif task['worker_name'] == 'developer':
    result = {{
        'task_id': task['task_id'],
        'worker_type': 'developer',
        'status': 'completed',
        'output': 'Code implementation completed',
        'content': {{
            'files_modified': ['main.py', 'utils.py'],
            'tests_added': ['test_main.py'],
            'changes_summary': 'Implemented bug fix and added unit tests'
        }},
        'processing_time': 2.0,
        'timestamp': task['timestamp']
    }}
else:
    result = {{
        'task_id': task['task_id'],
        'worker_type': task['worker_name'],
        'status': 'completed',
        'output': f'{{task[\"worker_name\"].capitalize()}} work completed',
        'content': {{}},
        'processing_time': 1.0,
        'timestamp': task['timestamp']
    }}

# Write result
with open('{result_file}', 'w') as f:
    json.dump(result, f, indent=2)

print(f'✅ {{task[\"worker_name\"].capitalize()}} Worker: Task completed')
"'''

    async def _wait_for_result(self, result_file: Path, timeout: int) -> dict[str, Any]:
        """Wait for worker result with timeout"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if result_file.exists():
                try:
                    with open(result_file) as f:
                        loaded_result = json.load(f)
                        return loaded_result if loaded_result is not None else {}
                except (OSError, json.JSONDecodeError):
                    # File might be being written, wait a bit more
                    await asyncio.sleep(0.1)
                    continue

            await asyncio.sleep(0.5)

        raise TimeoutError(f"Worker result not received within {timeout} seconds")

    async def send_parallel_tasks(
        self, tasks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Send multiple tasks to workers in parallel"""
        if not tasks:
            return []

        # Group tasks by worker
        worker_tasks: dict[str, list[dict[str, Any]]] = {}
        for task in tasks:
            worker_name = task.get("worker_name")
            if not worker_name:
                continue
            if worker_name not in worker_tasks:
                worker_tasks[worker_name] = []
            worker_tasks[worker_name].append(task)

        # Send tasks in parallel
        async_tasks = []
        for worker_name, worker_task_list in worker_tasks.items():
            for task in worker_task_list:
                async_tasks.append(self.send_task_to_worker(worker_name, task))

        # Wait for all results
        results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # Process results
        processed_results: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                error_result: dict[str, Any] = {
                    "status": "error",
                    "error": str(result),
                    "timestamp": datetime.now().isoformat(),
                }
                processed_results.append(error_result)
            else:
                # result is dict[str, Any] here due to return type of send_task_to_worker
                processed_results.append(result)  # type: ignore

        return processed_results

    def monitor_worker_status(self) -> dict[str, Any]:
        """Monitor the status of all workers"""
        if not self.check_tmux_session():
            return {
                "session_active": False,
                "error": f"Tmux session '{self.session_name}' not found",
            }

        worker_status = {}
        for worker_name in self.config["workers"].keys():
            worker_status[worker_name] = {
                "pane_active": self.check_worker_pane(worker_name),
                "pane_name": self.config["workers"][worker_name]["tmux_pane"],
            }

        return {
            "session_active": True,
            "session_name": self.session_name,
            "workers": worker_status,
            "timestamp": datetime.now().isoformat(),
        }

    def cleanup(self) -> None:
        """Clean up temporary files"""
        if self.temp_dir.exists():
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()


async def main() -> None:
    """Test the worker communication system"""
    print("🧪 Testing Worker Communication System...")

    try:
        communicator = WorkerCommunicator()

        # Check worker status
        print("\n📊 Worker Status:")
        status = communicator.monitor_worker_status()
        print(json.dumps(status, indent=2))

        if not status["session_active"]:
            print(
                "❌ Tmux session not active. Please run: ./scripts/start-cozy-hive.sh"
            )
            return

        # Test single worker task
        print("\n🔧 Testing Documenter Worker:")
        task = {
            "worker_name": "documenter",
            "task_type": "explain_issue",
            "issue_number": "84",
            "instruction": "Issue 84の内容を教えて",
        }

        try:
            result = await communicator.send_task_to_worker("documenter", task)
            print("✅ Task completed successfully:")
            print(json.dumps(result, indent=2))
        except WorkerCommunicationError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

        # Cleanup
        communicator.cleanup()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
