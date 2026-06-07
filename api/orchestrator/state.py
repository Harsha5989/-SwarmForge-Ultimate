"""SwarmState — LangGraph state schema for the pipeline."""

from typing import Annotated, Optional, TypedDict


class SwarmState(TypedDict):
    """Central state flowing through the LangGraph pipeline."""

    session_id: str
    iteration: int
    status: str  # PLANNING|BUILDING|REVIEWING|TESTING|SECURING|DEPLOYING|DONE|FAILED
    spec: dict
    architecture: dict
    code_files: list[dict]
    test_results: list[dict]
    quality: dict
    build_retries: int
    test_retries: int
    sec_retries: int
    perf_retries: int
    errors: list[dict]
    verdict: str  # GO|NO_GO|ESCALATE|FAILED
    fix_context: Optional[dict]
