import json
from copy import deepcopy
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.tenants.models import Tenant
from apps.workflow_builder.models import (
    WorkflowDefinition,
    WorkflowRevision,
    WorkflowRevisionStatus,
    WorkflowTask,
    WorkflowTaskAssignment,
    WorkflowTaskAssignmentType,
    WorkflowTaskStatus,
)


ROOT = Path(__file__).resolve().parents[3]
VALID_WORKFLOW = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "workflow-patient-intake-approval.json"


def load_valid_workflow() -> dict:
    with VALID_WORKFLOW.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class WorkflowDefinitionTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        self.payload = load_valid_workflow()
        self.workflow = WorkflowDefinition.from_payload(self.tenant, self.payload)
        self.workflow.save()

    def test_workflow_can_be_created_from_valid_payload(self):
        self.assertEqual(self.workflow.workflow_id, "patient_intake_approval")
        self.assertEqual(self.workflow.name, "Patient intake approval")
        self.assertEqual(
            self.workflow.description,
            "Routes submitted patient intake forms to the triage role for review.",
        )
        self.assertEqual(str(self.workflow), "demo:patient_intake_approval")

    def test_valid_workflow_revision_is_created(self):
        revision = WorkflowRevision.create_next(
            self.workflow,
            deepcopy(self.payload),
            status=WorkflowRevisionStatus.REVIEWED,
        )

        self.assertEqual(revision.revision, 1)
        self.assertEqual(revision.version, "1.0.0")
        self.assertEqual(revision.schema_version, "v1")
        self.assertEqual(revision.status, WorkflowRevisionStatus.REVIEWED)
        self.assertEqual(str(revision), "demo:patient_intake_approval#1")

    def test_invalid_workflow_payload_is_rejected(self):
        payload = deepcopy(self.payload)
        payload.pop("states")

        with self.assertRaises(ValidationError):
            WorkflowRevision.create_next(self.workflow, payload)

    def test_initial_state_must_reference_defined_state(self):
        payload = deepcopy(self.payload)
        payload["initial_state"] = "missing_state"

        with self.assertRaises(ValidationError):
            WorkflowRevision.create_next(self.workflow, payload)

    def test_initial_state_must_be_start_state(self):
        payload = deepcopy(self.payload)
        payload["initial_state"] = "triage_review"

        with self.assertRaises(ValidationError):
            WorkflowRevision.create_next(self.workflow, payload)

    def test_workflow_allows_only_one_start_state(self):
        payload = deepcopy(self.payload)
        payload["states"][1]["state_type"] = "start"

        with self.assertRaises(ValidationError):
            WorkflowRevision.create_next(self.workflow, payload)

    def test_duplicate_state_ids_are_rejected(self):
        payload = deepcopy(self.payload)
        payload["states"][1]["state_id"] = "submitted"

        with self.assertRaises(ValidationError):
            WorkflowRevision.create_next(self.workflow, payload)

    def test_transition_from_state_must_exist(self):
        payload = deepcopy(self.payload)
        payload["transitions"][0]["from_state"] = "missing_state"

        with self.assertRaises(ValidationError):
            WorkflowRevision.create_next(self.workflow, payload)

    def test_transition_to_state_must_exist(self):
        payload = deepcopy(self.payload)
        payload["transitions"][0]["to_state"] = "missing_state"

        with self.assertRaises(ValidationError):
            WorkflowRevision.create_next(self.workflow, payload)

    def test_transition_trigger_must_exist(self):
        payload = deepcopy(self.payload)
        payload["transitions"][0]["trigger"] = "missing_trigger"

        with self.assertRaises(ValidationError):
            WorkflowRevision.create_next(self.workflow, payload)

    def test_unreachable_state_is_rejected(self):
        payload = deepcopy(self.payload)
        payload["transitions"] = []

        with self.assertRaises(ValidationError):
            WorkflowRevision.create_next(self.workflow, payload)

    def test_workflow_id_is_unique_per_tenant(self):
        with self.assertRaises(ValidationError):
            WorkflowDefinition.from_payload(self.tenant, self.payload).save()

        other_tenant_workflow = WorkflowDefinition.from_payload(self.other_tenant, self.payload)
        other_tenant_workflow.save()

        self.assertEqual(other_tenant_workflow.workflow_id, "patient_intake_approval")

    def test_revision_numbering_increments_per_workflow(self):
        first = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        second = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))

        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)

    def test_revision_fields_must_match_payload(self):
        payload = deepcopy(self.payload)
        payload["workflow_id"] = "other_workflow"

        with self.assertRaises(ValidationError):
            WorkflowRevision.create_next(self.workflow, payload)

    def test_current_revision_must_belong_to_workflow(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        other_payload = deepcopy(self.payload)
        other_payload["workflow_id"] = "other_workflow"
        other_payload["name"] = "Other workflow"
        other_workflow = WorkflowDefinition.from_payload(self.tenant, other_payload)
        other_workflow.save()

        other_workflow.current_revision = revision

        with self.assertRaises(ValidationError):
            other_workflow.full_clean()

    def test_revision_tenant_must_match_workflow_tenant(self):
        revision = WorkflowRevision(
            tenant=self.other_tenant,
            workflow=self.workflow,
            revision=1,
            version=self.payload["version"],
            payload=deepcopy(self.payload),
        )

        with self.assertRaises(ValidationError):
            revision.full_clean()

    def test_workflow_task_can_be_created_for_revision(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))

        task = WorkflowTask.create_for_revision(
            revision,
            task_key="patient_123_triage",
            subject="Review patient intake",
            context={"patient_id": "patient_123"},
        )

        self.assertEqual(task.workflow, self.workflow)
        self.assertEqual(task.revision, revision)
        self.assertEqual(task.current_state, "submitted")
        self.assertEqual(task.status, WorkflowTaskStatus.OPEN)
        self.assertEqual(task.context_size, 1)
        self.assertEqual(str(task), "demo:patient_intake_approval:patient_123_triage")

    def test_workflow_task_key_is_unique_per_tenant(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        WorkflowTask.create_for_revision(
            revision,
            task_key="patient_123_triage",
            subject="Review patient intake",
        )

        with self.assertRaises(ValidationError):
            WorkflowTask.create_for_revision(
                revision,
                task_key="patient_123_triage",
                subject="Duplicate",
            )

        other_tenant_workflow = WorkflowDefinition.from_payload(self.other_tenant, self.payload)
        other_tenant_workflow.save()
        other_revision = WorkflowRevision.create_next(other_tenant_workflow, deepcopy(self.payload))
        task = WorkflowTask.create_for_revision(
            other_revision,
            task_key="patient_123_triage",
            subject="Other tenant review",
        )

        self.assertEqual(task.tenant, self.other_tenant)

    def test_workflow_task_state_must_exist_in_revision_payload(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))

        with self.assertRaises(ValidationError):
            WorkflowTask.create_for_revision(
                revision,
                task_key="bad_state",
                subject="Bad state",
                current_state="missing_state",
            )

    def test_workflow_task_revision_must_belong_to_workflow(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        other_payload = deepcopy(self.payload)
        other_payload["workflow_id"] = "other_workflow"
        other_payload["name"] = "Other workflow"
        other_workflow = WorkflowDefinition.from_payload(self.tenant, other_payload)
        other_workflow.save()

        task = WorkflowTask(
            tenant=self.tenant,
            workflow=other_workflow,
            revision=revision,
            task_key="wrong_revision",
            subject="Wrong revision",
            current_state="submitted",
        )

        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_workflow_task_tenant_must_match_revision(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        task = WorkflowTask(
            tenant=self.other_tenant,
            workflow=self.workflow,
            revision=revision,
            task_key="wrong_tenant",
            subject="Wrong tenant",
            current_state="submitted",
        )

        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_workflow_task_context_must_be_json_object(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))

        with self.assertRaises(ValidationError):
            WorkflowTask.create_for_revision(
                revision,
                task_key="bad_context",
                subject="Bad context",
                context=["not", "an", "object"],
            )

    def test_workflow_task_can_be_assigned_to_role(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        task = WorkflowTask.create_for_revision(
            revision,
            task_key="role_assignment",
            subject="Role assignment",
        )

        assignment = WorkflowTaskAssignment.assign_role(task, "clinical.triage")

        self.assertEqual(assignment.assignment_type, WorkflowTaskAssignmentType.ROLE)
        self.assertEqual(assignment.role, "clinical.triage")
        self.assertEqual(assignment.target, "clinical.triage")
        self.assertTrue(assignment.is_active)
        self.assertEqual(str(assignment), "demo:patient_intake_approval:role_assignment:role:clinical.triage")

    def test_workflow_task_can_be_assigned_to_user(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        task = WorkflowTask.create_for_revision(
            revision,
            task_key="user_assignment",
            subject="User assignment",
        )

        assignment = WorkflowTaskAssignment.assign_user(task, "user_123")

        self.assertEqual(assignment.assignment_type, WorkflowTaskAssignmentType.USER)
        self.assertEqual(assignment.user_id, "user_123")
        self.assertEqual(assignment.target, "user_123")

    def test_workflow_task_can_be_assigned_by_expression(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        task = WorkflowTask.create_for_revision(
            revision,
            task_key="expression_assignment",
            subject="Expression assignment",
        )

        assignment = WorkflowTaskAssignment.assign_expression(task, "patient.region.owner")

        self.assertEqual(assignment.assignment_type, WorkflowTaskAssignmentType.EXPRESSION)
        self.assertEqual(assignment.expression, "patient.region.owner")
        self.assertEqual(assignment.target, "patient.region.owner")

    def test_assignment_requires_target_for_type(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        task = WorkflowTask.create_for_revision(
            revision,
            task_key="missing_target",
            subject="Missing target",
        )

        assignment = WorkflowTaskAssignment(
            tenant=self.tenant,
            task=task,
            assignment_type=WorkflowTaskAssignmentType.ROLE,
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_assignment_rejects_inactive_target_fields(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        task = WorkflowTask.create_for_revision(
            revision,
            task_key="mixed_target",
            subject="Mixed target",
        )

        assignment = WorkflowTaskAssignment(
            tenant=self.tenant,
            task=task,
            assignment_type=WorkflowTaskAssignmentType.USER,
            role="clinical.triage",
            user_id="user_123",
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_assignment_tenant_must_match_task(self):
        revision = WorkflowRevision.create_next(self.workflow, deepcopy(self.payload))
        task = WorkflowTask.create_for_revision(
            revision,
            task_key="wrong_assignment_tenant",
            subject="Wrong assignment tenant",
        )

        assignment = WorkflowTaskAssignment(
            tenant=self.other_tenant,
            task=task,
            assignment_type=WorkflowTaskAssignmentType.ROLE,
            role="clinical.triage",
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()
