package org.khodola.mobile.runtime.screen

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class RuntimeScreenRendererTest {
    @Test
    fun mapsScreenMetadataAndDisplayState() {
        val screen = decodeRuntimeScreenFromPackagePayload(packagePayload(), screenId = "intake")

        assertEquals("intake", screen.screenId)
        assertEquals("Patient Intake", screen.name)
        assertEquals("form", screen.screenType)
        assertEquals("/intake", screen.route)
        assertEquals("forms.submit_patient_intake", screen.permission)
        assertEquals("Patient Intake", screen.display?.title)
        assertEquals("screen_and_data", screen.offline?.cacheStrategy)
        assertEquals(true, screen.offline?.syncRequired)
        assertEquals("single_column", screen.layout?.type)
    }

    @Test
    fun mapsComponentsRecursivelyWithBindingsAndProperties() {
        val screen = decodeRuntimeScreenFromPackagePayload(packagePayload(), screenId = "intake")
        val card = screen.components.first()

        assertEquals("summary_card", card.componentId)
        assertEquals("card", card.componentType)
        assertEquals("forms.view_patient_summary", card.permission)
        assertEquals("patient.summary", card.binding?.dataPath)
        assertEquals("open_summary", card.binding?.actionId)
        assertEquals(RuntimePropertyValue.Flag(true), card.properties.getValue("compact"))
        assertEquals(RuntimePropertyValue.Number(1.0), card.properties.getValue("priority"))
        assertEquals(RuntimePropertyValue.Text("primary"), card.properties.getValue("accent"))

        val child = card.children.single()
        assertEquals("summary_title", child.componentId)
        assertEquals("text", child.componentType)
        assertEquals("patient.name", child.binding?.dataPath)
    }

    @Test
    fun mapsScreenActionsAndBindings() {
        val screen = decodeRuntimeScreenFromPackagePayload(packagePayload(), screenId = "intake")
        val action = screen.actions.single()

        assertEquals("submit_intake", action.actionId)
        assertEquals("submit_form", action.actionType)
        assertEquals("patient_intake", action.target)
        assertEquals("component", action.binding?.source)
        assertEquals("submit", action.binding?.event)
        assertEquals("summary_card", action.binding?.componentId)
        assertEquals(RuntimePropertyValue.Text("high"), action.parameters.getValue("priority"))
    }

    @Test
    fun rejectsMissingScreen() {
        assertFailsWith<IllegalArgumentException> {
            decodeRuntimeScreenFromPackagePayload(packagePayload(), screenId = "missing")
        }
    }
}

private fun packagePayload(): String =
    """
    {
      "schema_version": "v1",
      "package_id": "pkg_field_ops_001",
      "app": {
        "schema_version": "v1",
        "app_id": "field_ops_app",
        "name": "Field Operations",
        "version": "0.1.0",
        "navigation": [
          {
            "label": "Intake",
            "screen_id": "intake"
          }
        ],
        "screens": [
          {
            "screen_id": "intake",
            "name": "Patient Intake",
            "screen_type": "form",
            "order": 0,
            "route": "/intake",
            "permission": "forms.submit_patient_intake",
            "display": {
              "title": "Patient Intake",
              "description": "Capture a patient intake form.",
              "icon": "form"
            },
            "offline": {
              "cache_strategy": "screen_and_data",
              "sync_required": true
            },
            "layout": {
              "type": "single_column"
            },
            "components": [
              {
                "component_id": "summary_card",
                "component_type": "card",
                "label": "Summary",
                "permission": "forms.view_patient_summary",
                "binding": {
                  "data_path": "patient.summary",
                  "action_id": "open_summary"
                },
                "properties": {
                  "compact": true,
                  "priority": 1,
                  "accent": "primary"
                },
                "children": [
                  {
                    "component_id": "summary_title",
                    "component_type": "text",
                    "label": "Patient summary",
                    "binding": {
                      "data_path": "patient.name"
                    }
                  }
                ]
              }
            ],
            "actions": [
              {
                "action_id": "submit_intake",
                "action_type": "submit_form",
                "label": "Submit",
                "target": "patient_intake",
                "binding": {
                  "source": "component",
                  "event": "submit",
                  "component_id": "summary_card"
                },
                "parameters": {
                  "priority": "high"
                }
              }
            ]
          }
        ]
      }
    }
    """.trimIndent()
