from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "backend/apps/workflow_builder/apps.py",
    "backend/apps/workflow_builder/models.py",
    "backend/apps/workflow_builder/services.py",
    "backend/apps/workflow_builder/tests.py",
    "backend/apps/workflow_builder/migrations/0001_initial.py",
    "backend/apps/workflow_builder/migrations/0002_workflowtask.py",
    "backend/apps/workflow_builder/migrations/0003_workflowtaskassignment.py",
    "backend/apps/workflow_builder/migrations/0004_workflowtrigger.py",
    "backend/apps/workflow_builder/migrations/0005_workflowexecutionlog.py",
    "frontend-admin/src/app/views/WorkflowEditorView.tsx",
    "frontend-admin/src/builders/workflowEditorModel.ts",
    "frontend-admin/src/builders/workflowEditorModel.test.ts",
    "frontend-admin/src/tests/smoke/adminShell.smoke.spec.ts",
]

REQUIRED_SNIPPETS = {
    "backend/apps/workflow_builder/models.py": [
        "class WorkflowDefinition",
        "class WorkflowRevision",
        "class WorkflowTask",
        "class WorkflowTaskAssignment",
        "class WorkflowTrigger",
        "class WorkflowExecutionLog",
    ],
    "backend/apps/workflow_builder/services.py": [
        "validate_workflow_payload",
        "validate_workflow_state_machine",
    ],
    "backend/apps/workflow_builder/tests.py": [
        "WorkflowDefinitionTests",
        "test_workflow_execution_log_can_be_recorded_for_revision",
        "test_workflow_task_can_be_assigned_to_role",
        "test_workflow_trigger_can_be_created_from_revision_payload",
    ],
    "frontend-admin/src/app/views/WorkflowEditorView.tsx": [
        "WorkflowEditorView",
        "SimulationPanel",
        "TaskInboxPanel",
    ],
    "frontend-admin/src/builders/workflowEditorModel.test.ts": [
        "workflow editor model",
        "simulates the default workflow path",
        "summarizes workflow inbox tasks",
    ],
    "frontend-admin/src/tests/smoke/adminShell.smoke.spec.ts": [
        "Workflow canvas",
        "Workflow simulator",
        "Task inbox",
    ],
}


def require_file(relative_path: str) -> None:
    path = ROOT / relative_path
    if not path.is_file():
        raise AssertionError(f"Missing workflow builder coverage file: {relative_path}")
    if path.stat().st_size == 0:
        raise AssertionError(f"Workflow builder coverage file is empty: {relative_path}")


def require_snippets(relative_path: str, snippets: list[str]) -> None:
    content = (ROOT / relative_path).read_text(encoding="utf-8-sig")
    for snippet in snippets:
        if snippet not in content:
            raise AssertionError(f"{relative_path} is missing `{snippet}`")


def main() -> int:
    for relative_path in REQUIRED_FILES:
        require_file(relative_path)

    for relative_path, snippets in REQUIRED_SNIPPETS.items():
        require_snippets(relative_path, snippets)

    print("Workflow builder validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
