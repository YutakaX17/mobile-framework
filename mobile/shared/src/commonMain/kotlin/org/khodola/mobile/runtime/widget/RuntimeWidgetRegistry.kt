package org.khodola.mobile.runtime.widget

import org.khodola.mobile.runtime.screen.RuntimeScreenComponent

data class RuntimeWidgetDescriptor(
    val componentType: String,
    val supportsChildren: Boolean,
    val requiredBindingKeys: Set<String> = emptySet(),
)

data class RuntimeWidgetValidationResult(
    val isValid: Boolean,
    val unsupportedComponentTypes: Set<String> = emptySet(),
    val missingBindings: Set<String> = emptySet(),
) {
    init {
        require(isValid || unsupportedComponentTypes.isNotEmpty() || missingBindings.isNotEmpty()) {
            "invalid widget validation results must include failures"
        }
    }
}

interface RuntimeWidgetRegistry {
    fun getDescriptor(componentType: String): RuntimeWidgetDescriptor?

    fun validateComponents(components: List<RuntimeScreenComponent>): RuntimeWidgetValidationResult
}

class DefaultRuntimeWidgetRegistry(
    descriptors: List<RuntimeWidgetDescriptor> = DEFAULT_WIDGET_DESCRIPTORS,
) : RuntimeWidgetRegistry {
    private val descriptorsByType = descriptors.associateBy { descriptor -> descriptor.componentType }

    override fun getDescriptor(componentType: String): RuntimeWidgetDescriptor? =
        descriptorsByType[componentType]

    override fun validateComponents(components: List<RuntimeScreenComponent>): RuntimeWidgetValidationResult {
        val unsupported = mutableSetOf<String>()
        val missingBindings = mutableSetOf<String>()

        components.forEach { component ->
            validateComponent(component, unsupported, missingBindings)
        }

        return RuntimeWidgetValidationResult(
            isValid = unsupported.isEmpty() && missingBindings.isEmpty(),
            unsupportedComponentTypes = unsupported,
            missingBindings = missingBindings,
        )
    }

    private fun validateComponent(
        component: RuntimeScreenComponent,
        unsupported: MutableSet<String>,
        missingBindings: MutableSet<String>,
    ) {
        val descriptor = getDescriptor(component.componentType)
        if (descriptor == null) {
            unsupported += component.componentType
        } else {
            descriptor.requiredBindingKeys.forEach { bindingKey ->
                if (!component.hasBinding(bindingKey)) {
                    missingBindings += "${component.componentId}:$bindingKey"
                }
            }
        }

        component.children.forEach { child ->
            validateComponent(child, unsupported, missingBindings)
        }
    }
}

val DEFAULT_WIDGET_DESCRIPTORS: List<RuntimeWidgetDescriptor> = listOf(
    RuntimeWidgetDescriptor(componentType = "text", supportsChildren = false),
    RuntimeWidgetDescriptor(componentType = "button", supportsChildren = false, requiredBindingKeys = setOf("action_id")),
    RuntimeWidgetDescriptor(componentType = "form", supportsChildren = false, requiredBindingKeys = setOf("form_id")),
    RuntimeWidgetDescriptor(componentType = "list", supportsChildren = true),
    RuntimeWidgetDescriptor(componentType = "card", supportsChildren = true),
    RuntimeWidgetDescriptor(componentType = "image", supportsChildren = false, requiredBindingKeys = setOf("data_path")),
    RuntimeWidgetDescriptor(componentType = "spacer", supportsChildren = false),
    RuntimeWidgetDescriptor(componentType = "custom", supportsChildren = true),
)

private fun RuntimeScreenComponent.hasBinding(bindingKey: String): Boolean =
    when (bindingKey) {
        "data_path" -> binding?.dataPath?.isNotBlank() == true
        "form_id" -> binding?.formId?.isNotBlank() == true
        "action_id" -> binding?.actionId?.isNotBlank() == true
        else -> false
    }
