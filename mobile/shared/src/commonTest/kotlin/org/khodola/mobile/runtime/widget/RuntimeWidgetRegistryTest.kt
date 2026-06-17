package org.khodola.mobile.runtime.widget

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue
import org.khodola.mobile.runtime.screen.RuntimeComponentBinding
import org.khodola.mobile.runtime.screen.RuntimeScreenComponent

class RuntimeWidgetRegistryTest {
    @Test
    fun exposesDefaultWidgetDescriptors() {
        val registry = DefaultRuntimeWidgetRegistry()

        assertEquals("form", registry.getDescriptor("form")?.componentType)
        assertEquals(setOf("form_id"), registry.getDescriptor("form")?.requiredBindingKeys)
        assertEquals(true, registry.getDescriptor("card")?.supportsChildren)
        assertNull(registry.getDescriptor("unknown"))
    }

    @Test
    fun validatesRecursiveSupportedComponents() {
        val registry = DefaultRuntimeWidgetRegistry()
        val result = registry.validateComponents(
            listOf(
                component(
                    componentId = "card",
                    componentType = "card",
                    children = listOf(
                        component("title", "text"),
                        component("form", "form", binding = RuntimeComponentBinding(null, "patient_intake", null)),
                    ),
                ),
            ),
        )

        assertTrue(result.isValid)
        assertEquals(emptySet(), result.unsupportedComponentTypes)
        assertEquals(emptySet(), result.missingBindings)
    }

    @Test
    fun rejectsUnsupportedComponentTypesRecursively() {
        val registry = DefaultRuntimeWidgetRegistry()
        val result = registry.validateComponents(
            listOf(
                component(
                    componentId = "card",
                    componentType = "card",
                    children = listOf(component("mystery", "unsupported")),
                ),
            ),
        )

        assertFalse(result.isValid)
        assertEquals(setOf("unsupported"), result.unsupportedComponentTypes)
    }

    @Test
    fun rejectsMissingRequiredBindings() {
        val registry = DefaultRuntimeWidgetRegistry()
        val result = registry.validateComponents(
            listOf(
                component("submit", "button"),
                component("photo", "image"),
            ),
        )

        assertFalse(result.isValid)
        assertEquals(setOf("submit:action_id", "photo:data_path"), result.missingBindings)
    }

    private fun component(
        componentId: String,
        componentType: String,
        binding: RuntimeComponentBinding? = null,
        children: List<RuntimeScreenComponent> = emptyList(),
    ): RuntimeScreenComponent =
        RuntimeScreenComponent(
            componentId = componentId,
            componentType = componentType,
            label = null,
            permission = null,
            binding = binding,
            properties = emptyMap(),
            children = children,
        )
}
