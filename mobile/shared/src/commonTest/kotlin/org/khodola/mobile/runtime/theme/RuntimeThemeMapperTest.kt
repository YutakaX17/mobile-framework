package org.khodola.mobile.runtime.theme

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class RuntimeThemeMapperTest {
    @Test
    fun mapsBaseThemeTokensFromPackagePayload() {
        val theme = decodeRuntimeThemeFromPackagePayload(packagePayload())

        assertEquals("field_ops", theme.themeId)
        assertEquals("Field Operations", theme.name)
        assertEquals("0.1.0", theme.version)
        assertEquals("light", theme.modeId)
        assertEquals("#0B5FFF", theme.colors.primary.main)
        assertEquals("#FFFFFF", theme.colors.primary.contrast)
        assertEquals("#F6F8FB", theme.colors.background)
        assertEquals("Atkinson Hyperlegible", theme.typography.fontFamily)
        assertEquals(24.0, theme.typography.scale.getValue("heading").fontSize)
        assertEquals(16.0, theme.spacing.getValue("md"))
        assertEquals(10.0, theme.radius.getValue("md"))
        assertEquals(2, theme.elevation.getValue("card").level)
        assertEquals("#0B5FFF", theme.components.getValue("button_primary").background)
        assertEquals("field_ops_logo", theme.assets?.logoAssetId)
        assertEquals(true, theme.accessibility?.validated)
    }

    @Test
    fun appliesRequestedModeColorOverrides() {
        val theme = decodeRuntimeThemeFromPackagePayload(packagePayload(), modeId = "dark")

        assertEquals("dark", theme.modeId)
        assertEquals("#111827", theme.colors.background)
        assertEquals("#1F2937", theme.colors.surface)
        assertEquals("#F9FAFB", theme.colors.text)
        assertEquals("#0B5FFF", theme.colors.primary.main)
    }

    @Test
    fun rejectsUnavailableThemeMode() {
        assertFailsWith<IllegalArgumentException> {
            decodeRuntimeThemeFromPackagePayload(packagePayload(), modeId = "high_contrast")
        }
    }
}

private fun packagePayload(): String =
    """
    {
      "schema_version": "v1",
      "package_id": "pkg_field_ops_001",
      "theme": {
        "schema_version": "v1",
        "theme_id": "field_ops",
        "name": "Field Operations",
        "version": "0.1.0",
        "tokens": {
          "colors": {
            "primary": {
              "light": "#6EA8FF",
              "main": "#0B5FFF",
              "dark": "#003EA8",
              "contrast": "#FFFFFF"
            },
            "secondary": {
              "light": "#9BE7C2",
              "main": "#168A55",
              "dark": "#0B5C38",
              "contrast": "#FFFFFF"
            },
            "background": "#F6F8FB",
            "surface": "#FFFFFF",
            "text": "#172033",
            "success": "#168A55",
            "warning": "#B26A00",
            "danger": "#B42318"
          },
          "typography": {
            "font_family": "Atkinson Hyperlegible",
            "fallback_family": "sans-serif",
            "scale": {
              "body": {
                "font_size": 16,
                "line_height": 24,
                "font_weight": 400
              },
              "heading": {
                "font_size": 24,
                "line_height": 32,
                "font_weight": 700,
                "letter_spacing": -0.2
              }
            }
          },
          "spacing": {
            "sm": 8,
            "md": 16
          },
          "radius": {
            "sm": 4,
            "md": 10
          },
          "elevation": {
            "none": {
              "level": 0
            },
            "card": {
              "level": 2,
              "shadow": "0 8px 24px rgba(23, 32, 51, 0.12)"
            }
          },
          "components": {
            "button_primary": {
              "background": "#0B5FFF",
              "text": "#FFFFFF",
              "radius": 10,
              "padding": 12,
              "elevation": 1
            }
          }
        },
        "modes": [
          {
            "mode_id": "light",
            "label": "Light",
            "color_overrides": {
              "background": "#F6F8FB",
              "surface": "#FFFFFF",
              "text": "#172033"
            }
          },
          {
            "mode_id": "dark",
            "label": "Dark",
            "color_overrides": {
              "background": "#111827",
              "surface": "#1F2937",
              "text": "#F9FAFB"
            }
          }
        ],
        "assets": {
          "logo_asset_id": "field_ops_logo",
          "icon_asset_id": "field_ops_icon"
        },
        "accessibility": {
          "contrast_standard": "wcag_2_2_aa",
          "validated": true,
          "override_recorded": false
        }
      }
    }
    """.trimIndent()
