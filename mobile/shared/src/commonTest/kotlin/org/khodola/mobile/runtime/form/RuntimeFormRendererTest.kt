package org.khodola.mobile.runtime.form

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class RuntimeFormRendererTest {
    @Test
    fun mapsFormMetadataLayoutAndOfflineSettings() {
        val form = decodeRuntimeFormFromPackagePayload(packagePayload(), formId = "patient_intake")

        assertEquals("patient_intake", form.formId)
        assertEquals("Patient Intake", form.name)
        assertEquals("standalone", form.mode)
        assertEquals("patient", form.entityType)
        assertEquals("sectioned", form.layout?.type)
        assertEquals("identity", form.layout?.sections?.single()?.sectionId)
        assertEquals(listOf("full_name", "age", "gender"), form.layout?.sections?.single()?.fieldIds)
        assertEquals("create_submission", form.submitAction?.actionType)
        assertEquals("patient_intake_submission", form.submitAction?.target)
        assertEquals(true, form.offline?.enabled)
        assertEquals("manual_review", form.offline?.conflictPolicy)
    }

    @Test
    fun mapsFieldBindingsValidationAndOptions() {
        val form = decodeRuntimeFormFromPackagePayload(packagePayload(), formId = "patient_intake")
        val fullName = form.fields.first { field -> field.fieldId == "full_name" }
        val gender = form.fields.first { field -> field.fieldId == "gender" }

        assertEquals("text", fullName.fieldType)
        assertEquals(true, fullName.required)
        assertEquals("patient.full_name", fullName.binding.dataPath)
        assertEquals("patient", fullName.binding.entityType)
        assertEquals(2, fullName.validation?.minLength)
        assertEquals(120, fullName.validation?.maxLength)
        assertEquals("Enter the patient's full name.", fullName.validation?.message)

        assertEquals("select", gender.fieldType)
        assertEquals(listOf("female", "male", "other"), gender.options.map { option -> option.value })
        assertEquals(false, gender.options.first().disabled)
    }

    @Test
    fun mapsRulesAndCustomControls() {
        val form = decodeRuntimeFormFromPackagePayload(packagePayload(), formId = "patient_intake")
        val calculated = form.fields.first { field -> field.fieldId == "risk_score" }

        assertEquals("calculated", calculated.fieldType)
        assertEquals(true, calculated.readOnly)
        assertEquals("supported_expression", calculated.calculation?.ruleType)
        assertEquals("patient.age > 65", calculated.visibility?.expression)
        assertEquals("risk_widget", calculated.customControl?.runtimeWidget)
    }

    @Test
    fun rejectsMissingForm() {
        assertFailsWith<IllegalArgumentException> {
            decodeRuntimeFormFromPackagePayload(packagePayload(), formId = "missing")
        }
    }
}

private fun packagePayload(): String =
    """
    {
      "schema_version": "v1",
      "package_id": "pkg_field_ops_001",
      "forms": [
        {
          "schema_version": "v1",
          "form_id": "patient_intake",
          "name": "Patient Intake",
          "description": "Basic offline-capable intake form.",
          "version": "0.1.0",
          "mode": "standalone",
          "status": "draft",
          "entity_type": "patient",
          "layout": {
            "type": "sectioned",
            "sections": [
              {
                "section_id": "identity",
                "label": "Identity",
                "field_ids": ["full_name", "age", "gender"]
              }
            ]
          },
          "fields": [
            {
              "field_id": "full_name",
              "field_type": "text",
              "label": "Full name",
              "required": true,
              "binding": {
                "data_path": "patient.full_name",
                "entity_type": "patient"
              },
              "validation": {
                "min_length": 2,
                "max_length": 120,
                "message": "Enter the patient's full name."
              }
            },
            {
              "field_id": "age",
              "field_type": "number",
              "label": "Age",
              "binding": {
                "data_path": "patient.age",
                "entity_type": "patient"
              },
              "validation": {
                "minimum": 0,
                "maximum": 130
              }
            },
            {
              "field_id": "gender",
              "field_type": "select",
              "label": "Gender",
              "binding": {
                "data_path": "patient.gender",
                "entity_type": "patient"
              },
              "options": [
                { "value": "female", "label": "Female" },
                { "value": "male", "label": "Male" },
                { "value": "other", "label": "Other" }
              ]
            },
            {
              "field_id": "risk_score",
              "field_type": "calculated",
              "label": "Risk score",
              "read_only": true,
              "binding": {
                "data_path": "patient.risk_score",
                "entity_type": "patient"
              },
              "visibility": {
                "rule_type": "supported_expression",
                "expression": "patient.age > 65"
              },
              "calculation": {
                "rule_type": "supported_expression",
                "expression": "patient.age * 2"
              },
              "custom_control": {
                "control_id": "risk_score_control",
                "runtime_widget": "risk_widget"
              }
            }
          ],
          "submit_action": {
            "action_type": "create_submission",
            "target": "patient_intake_submission"
          },
          "offline": {
            "enabled": true,
            "queue_submissions": true,
            "conflict_policy": "manual_review"
          }
        }
      ]
    }
    """.trimIndent()
