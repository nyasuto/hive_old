"""
Worker type definitions for Issue Solver Agent system.

Extracted from issue_solver_agent.py for better modularity.
"""

from enum import Enum


class WorkerRole(Enum):
    """Workerの役割"""

    DEVELOPER = "developer"
    TESTER = "tester"
    ANALYZER = "analyzer"
    DOCUMENTER = "documenter"
    REVIEWER = "reviewer"
