package org.khodola.mobile.runtime.screen

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.isString
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson

data class RuntimeScreen(
    val screenId: String,
    val name: String,
    val screenType: String,
    val order: Int,
    val route: String?,
    val permission: String?,
    val display: RuntimeScreenDisplay?,
    val offline: RuntimeScreenOffline?,
    val layout: RuntimeScreenLayout?,
    val components: List<RuntimeScreenComponent>,
    val actions: List<RuntimeScreenAction>,
)

data class RuntimeScreenDisplay(
    val title: String?,
    val description: String?,
    val icon: String?,
)

data class RuntimeScreenOffline(
    val cacheStrategy: String,
    val syncRequired: Boolean,
)

data class RuntimeScreenLayout(
    val type: String?,
)

data class RuntimeScreenComponent(
    val componentId: String,
    val componentType: String,
    val label: String?,
    val permission: String?,
    val binding: RuntimeComponentBinding?,
    val properties: Map<String, RuntimePropertyValue>,
    val children: List<RuntimeScreenComponent>,
)

data class RuntimeComponentBinding(
    val dataPath: String?,
    val formId: String?,
    val actionId: String?,
)

data class RuntimeScreenAction(
    val actionId: String,
    val actionType: String,
    val label: String?,
    val target: String?,
    val permission: String?,
    val binding: RuntimeActionBinding?,
    val parameters: Map<String, RuntimePropertyValue>,
)

data class RuntimeActionBinding(
    val source: String,
    val event: String,
    val componentId: String?,
    val payloadPath: String?,
    val resultPath: String?,
)

sealed class RuntimePropertyValue {
    data class Text(val value: String) : RuntimePropertyValue()
    data class Number(val value: Double) : RuntimePropertyValue()
    data class Flag(val value: Boolean) : RuntimePropertyValue()
    data object NullValue : RuntimePropertyValue()
}

fun decodeRuntimeScreenFromPackagePayload(
    payloadJson: String,
    screenId: String,
): RuntimeScreen =
    MobileRuntimeJson
        .decodeFromString<PackageScreenEnvelopeDto>(payloadJson)
        .app
        .screens
        .firstOrNull { screen -> screen.screenId == screenId }
        ?.toRuntimeScreen()
        ?: throw IllegalArgumentException("Screen $screenId is not available in package payload")

@Serializable
private data class PackageScreenEnvelopeDto(
    val app: RuntimeScreenAppDto,
)

@Serializable
private data class RuntimeScreenAppDto(
    val screens: List<RuntimeScreenDto>,
)

@Serializable
private data class RuntimeScreenDto(
    @SerialName("screen_id")
    val screenId: String,
    val name: String,
    @SerialName("screen_type")
    val screenType: String,
    val order: Int = 0,
    val route: String? = null,
    val permission: String? = null,
    val display: RuntimeScreenDisplayDto? = null,
    val offline: RuntimeScreenOfflineDto? = null,
    val layout: RuntimeScreenLayoutDto? = null,
    val components: List<RuntimeScreenComponentDto>,
    val actions: List<RuntimeScreenActionDto> = emptyList(),
) {
    fun toRuntimeScreen(): RuntimeScreen =
        RuntimeScreen(
            screenId = screenId,
            name = name,
            screenType = screenType,
            order = order,
            route = route,
            permission = permission,
            display = display?.toRuntimeDisplay(),
            offline = offline?.toRuntimeOffline(),
            layout = layout?.toRuntimeLayout(),
            components = components.map { component -> component.toRuntimeComponent() },
            actions = actions.map { action -> action.toRuntimeAction() },
        )
}

@Serializable
private data class RuntimeScreenDisplayDto(
    val title: String? = null,
    val description: String? = null,
    val icon: String? = null,
) {
    fun toRuntimeDisplay(): RuntimeScreenDisplay =
        RuntimeScreenDisplay(title = title, description = description, icon = icon)
}

@Serializable
private data class RuntimeScreenOfflineDto(
    @SerialName("cache_strategy")
    val cacheStrategy: String = "none",
    @SerialName("sync_required")
    val syncRequired: Boolean = false,
) {
    fun toRuntimeOffline(): RuntimeScreenOffline =
        RuntimeScreenOffline(cacheStrategy = cacheStrategy, syncRequired = syncRequired)
}

@Serializable
private data class RuntimeScreenLayoutDto(
    val type: String? = null,
) {
    fun toRuntimeLayout(): RuntimeScreenLayout =
        RuntimeScreenLayout(type = type)
}

@Serializable
private data class RuntimeScreenComponentDto(
    @SerialName("component_id")
    val componentId: String,
    @SerialName("component_type")
    val componentType: String,
    val label: String? = null,
    val permission: String? = null,
    val binding: RuntimeComponentBindingDto? = null,
    val properties: Map<String, JsonPrimitive> = emptyMap(),
    val children: List<RuntimeScreenComponentDto> = emptyList(),
) {
    fun toRuntimeComponent(): RuntimeScreenComponent =
        RuntimeScreenComponent(
            componentId = componentId,
            componentType = componentType,
            label = label,
            permission = permission,
            binding = binding?.toRuntimeBinding(),
            properties = properties.mapValues { (_, value) -> value.toRuntimePropertyValue() },
            children = children.map { child -> child.toRuntimeComponent() },
        )
}

@Serializable
private data class RuntimeComponentBindingDto(
    @SerialName("data_path")
    val dataPath: String? = null,
    @SerialName("form_id")
    val formId: String? = null,
    @SerialName("action_id")
    val actionId: String? = null,
) {
    fun toRuntimeBinding(): RuntimeComponentBinding =
        RuntimeComponentBinding(dataPath = dataPath, formId = formId, actionId = actionId)
}

@Serializable
private data class RuntimeScreenActionDto(
    @SerialName("action_id")
    val actionId: String,
    @SerialName("action_type")
    val actionType: String,
    val label: String? = null,
    val target: String? = null,
    val permission: String? = null,
    val binding: RuntimeActionBindingDto? = null,
    val parameters: Map<String, JsonPrimitive> = emptyMap(),
) {
    fun toRuntimeAction(): RuntimeScreenAction =
        RuntimeScreenAction(
            actionId = actionId,
            actionType = actionType,
            label = label,
            target = target,
            permission = permission,
            binding = binding?.toRuntimeBinding(),
            parameters = parameters.mapValues { (_, value) -> value.toRuntimePropertyValue() },
        )
}

@Serializable
private data class RuntimeActionBindingDto(
    val source: String,
    val event: String,
    @SerialName("component_id")
    val componentId: String? = null,
    @SerialName("payload_path")
    val payloadPath: String? = null,
    @SerialName("result_path")
    val resultPath: String? = null,
) {
    fun toRuntimeBinding(): RuntimeActionBinding =
        RuntimeActionBinding(
            source = source,
            event = event,
            componentId = componentId,
            payloadPath = payloadPath,
            resultPath = resultPath,
        )
}

private fun JsonPrimitive.toRuntimePropertyValue(): RuntimePropertyValue =
    if (isString) {
        RuntimePropertyValue.Text(content)
    } else {
        booleanOrNull?.let { RuntimePropertyValue.Flag(it) }
        ?: doubleOrNull?.let { RuntimePropertyValue.Number(it) }
        ?: contentOrNull?.let { RuntimePropertyValue.Text(it) }
        ?: RuntimePropertyValue.NullValue
    }
