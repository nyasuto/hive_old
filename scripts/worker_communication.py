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
        """Send task to specific worker via tmux direct communication"""
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

        # Get pane name
        pane_name = self.config["workers"][worker_name]["tmux_pane"]

        # Create message for Claude worker
        message = self._create_worker_message(worker_name, task_with_id)

        try:
            # Send message to Claude worker via tmux with confirmed input pattern
            await self._send_message_with_confirmation(pane_name, message)

            # Wait for response and capture result
            timeout = self.config["workers"][worker_name].get("timeout", 120)
            result = await self._wait_for_claude_response(pane_name, timeout)

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

    async def _send_message_with_confirmation(
        self, pane_name: str, message: str
    ) -> None:
        """Send message to Claude Code with confirmed input pattern

        Uses the pattern: message + Enter + 1 second wait + Enter
        This ensures Claude Code properly processes and confirms the input.
        """
        # Step 1: Send the message with Enter
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_name, message, "Enter"], check=True
        )

        # Step 2: Wait 1 second for message processing
        await asyncio.sleep(1)

        # Step 3: Send additional Enter for confirmation
        subprocess.run(["tmux", "send-keys", "-t", pane_name, "Enter"], check=True)

    def _create_worker_message(self, worker_name: str, task: dict[str, Any]) -> str:
        """Create message to send to Claude worker"""
        issue_number = task.get("issue_number", "N/A")
        instruction = task.get("instruction", "")
        task_type = task.get("task_type", "general_task")

        # Create role-specific message
        role_context = {
            "documenter": f"あなたはDocumenterとして、Issue #{issue_number}について説明してください。",
            "developer": f"あなたはDeveloperとして、Issue #{issue_number}の実装を行ってください。",
            "tester": f"あなたはTesterとして、Issue #{issue_number}のテストを作成してください。",
            "analyzer": f"あなたはAnalyzerとして、Issue #{issue_number}を分析してください。",
            "reviewer": f"あなたはReviewerとして、Issue #{issue_number}をレビューしてください。",
        }

        role_message = role_context.get(worker_name, f"Task: {task_type}")

        task_id = task.get("task_id", "unknown")

        # Format message with clear instruction structure (like start-cozy-hive pattern)
        return f"""以下があなたのタスクです。理解して実行してください：

{role_message}

{instruction}

回答が完了したら、以下のコマンドを実行してQueenに結果を送信してください：
tmux send-keys -t cozy-hive:queen 'WORKER_RESULT:{worker_name}:{task_id}:[あなたの回答をここに]' Enter

その後、[TASK_COMPLETED]と出力してください。

上記のタスクを理解しました。実行を開始します。"""

    async def _wait_for_claude_response(
        self, pane_name: str, timeout: int
    ) -> dict[str, Any]:
        """Wait for Claude response via tmux capture-pane"""
        start_time = time.time()
        last_content = ""

        while time.time() - start_time < timeout:
            try:
                # Capture pane content
                result = subprocess.run(
                    ["tmux", "capture-pane", "-t", pane_name, "-p"],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                current_content = result.stdout

                # Check if Claude has completed the task
                if "[TASK_COMPLETED]" in current_content:
                    # Extract the response (everything after the last message until [TASK_COMPLETED])
                    response_text = self._extract_claude_response(current_content)

                    return {
                        "output": response_text,
                        "status": "completed",
                        "content": response_text,
                        "processing_time": time.time() - start_time,
                        "timestamp": datetime.now().isoformat(),
                    }

                # Check if content has changed (Claude is still working)
                if current_content != last_content:
                    last_content = current_content
                    # Reset timeout if Claude is actively responding
                    start_time = time.time()

                await asyncio.sleep(2)  # Check every 2 seconds

            except subprocess.SubprocessError as e:
                raise WorkerCommunicationError(
                    f"Failed to capture pane {pane_name}: {e}"
                ) from e

        raise TimeoutError(f"Claude response not received within {timeout} seconds")

    def _extract_claude_response(self, content: str) -> str:
        """Extract Claude response from tmux pane content"""
        lines = content.split("\n")
        response_lines = []
        collecting = False

        for line in lines:
            # Skip empty lines and tmux formatting
            if not line.strip() or line.startswith("∙"):
                continue

            # Look for the start of Claude's response (after our message)
            if not collecting and ("あなたは" in line or "Issue #" in line):
                collecting = True
                continue

            # Stop collecting when we hit [TASK_COMPLETED]
            if "[TASK_COMPLETED]" in line:
                break

            # Collect response lines
            if collecting:
                response_lines.append(line.strip())

        # Clean up the response
        response = "\n".join(response_lines)

        # Remove any remaining tmux artifacts
        response = response.replace("∙", "").strip()

        return response if response else "Task completed successfully"

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
