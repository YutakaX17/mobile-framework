package org.khodola.mobile.runtime.navigation

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class RuntimeNavigationRendererTest {
    @Test
    fun mapsOrderedNavigationItemsAndTargets() {
        val graph = decodeRuntimeNavigationGraphFromPackagePayload(packagePayload())

        assertEquals("field_ops_app", graph.appId)
        assertEquals("Field Operations", graph.appName)
        assertEquals(listOf("Intake", "Settings"), graph.items.map { item -> item.label })

        val intake = graph.items.first()
        assertEquals("tab", intake.presentation)
        assertEquals("primary", intake.group)
        assertEquals("form", intake.icon)
        assertEquals("forms.submit_patient_intake", intake.permission)
        assertEquals("intake", intake.target.screenId)
        assertEquals("Patient Intake", intake.target.name)
        assertEquals("form", intake.target.screenType)
        assertEquals("/intake", intake.target.route)
    }

    @Test
    fun exposesDefaultNavigationItem() {
        val graph = decodeRuntimeNavigationGraphFromPackagePayload(packagePayload())

        assertEquals("intake", graph.defaultItem.target.screenId)
        assertEquals(true, graph.defaultItem.isDefault)
    }

    @Test
    fun fallsBackToFirstItemWhenNoDefaultIsMarked() {
        val graph = decodeRuntimeNavigationGraphFromPackagePayload(
            packagePayload().replace("\"is_default\": true", "\"is_default\": false"),
        )

        assertEquals("intake", graph.defaultItem.target.screenId)
    }

    @Test
    fun rejectsNavigationItemWithMissingScreenTarget() {
        val payload = packagePayload().replaceFirst("\"screen_id\": \"settings\"", "\"screen_id\": \"missing\"")

        assertFailsWith<IllegalArgumentException> {
            decodeRuntimeNavigationGraphFromPackagePayload(payload)
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
            "label": "Settings",
            "order": 2,
            "group": "overflow",
            "presentation": "drawer",
            "screen_id": "settings",
            "icon": "settings"
          },
          {
            "label": "Intake",
            "order": 1,
            "group": "primary",
            "presentation": "tab",
            "is_default": true,
            "screen_id": "intake",
            "icon": "form",
            "permission": "forms.submit_patient_intake"
          }
        ],
        "screens": [
          {
            "screen_id": "intake",
            "name": "Patient Intake",
            "screen_type": "form",
            "route": "/intake",
            "components": [
              {
                "component_id": "intake_form",
                "component_type": "form",
                "label": "Patient Intake"
              }
            ]
          },
          {
            "screen_id": "settings",
            "name": "Settings",
            "screen_type": "settings",
            "route": "/settings",
            "components": [
              {
                "component_id": "settings_text",
                "component_type": "text",
                "label": "Settings"
              }
            ]
          }
        ]
      }
    }
    """.trimIndent()
