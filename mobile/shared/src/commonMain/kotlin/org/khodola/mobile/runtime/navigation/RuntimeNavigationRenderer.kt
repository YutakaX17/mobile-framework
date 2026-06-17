package org.khodola.mobile.runtime.navigation

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson

data class RuntimeNavigationGraph(
    val appId: String,
    val appName: String,
    val items: List<RuntimeNavigationItem>,
) {
    init {
        require(items.isNotEmpty()) { "navigation graph requires at least one item" }
    }

    val defaultItem: RuntimeNavigationItem =
        items.firstOrNull { item -> item.isDefault } ?: items.first()
}

data class RuntimeNavigationItem(
    val label: String,
    val order: Int,
    val group: String,
    val presentation: String,
    val isDefault: Boolean,
    val icon: String?,
    val permission: String?,
    val target: RuntimeNavigationTarget,
)

data class RuntimeNavigationTarget(
    val screenId: String,
    val name: String,
    val screenType: String,
    val route: String?,
)

fun decodeRuntimeNavigationGraphFromPackagePayload(payloadJson: String): RuntimeNavigationGraph =
    MobileRuntimeJson
        .decodeFromString<PackageAppEnvelopeDto>(payloadJson)
        .app
        .toRuntimeNavigationGraph()

@Serializable
private data class PackageAppEnvelopeDto(
    val app: RuntimeAppDto,
)

@Serializable
private data class RuntimeAppDto(
    @SerialName("app_id")
    val appId: String,
    val name: String,
    val navigation: List<RuntimeNavigationItemDto>,
    val screens: List<RuntimeScreenTargetDto>,
) {
    fun toRuntimeNavigationGraph(): RuntimeNavigationGraph {
        val screensById = screens.associateBy { screen -> screen.screenId }
        val items = navigation
            .map { item -> item.toRuntimeNavigationItem(screensById) }
            .sortedWith(compareBy<RuntimeNavigationItem> { item -> item.order }.thenBy { item -> item.label })

        return RuntimeNavigationGraph(
            appId = appId,
            appName = name,
            items = items,
        )
    }
}

@Serializable
private data class RuntimeNavigationItemDto(
    val label: String,
    val order: Int = 0,
    val group: String = "primary",
    val presentation: String = "drawer",
    @SerialName("is_default")
    val isDefault: Boolean = false,
    @SerialName("screen_id")
    val screenId: String,
    val icon: String? = null,
    val permission: String? = null,
) {
    fun toRuntimeNavigationItem(screensById: Map<String, RuntimeScreenTargetDto>): RuntimeNavigationItem {
        val target = screensById[screenId]
            ?: throw IllegalArgumentException("Navigation item $label references missing screen $screenId")

        return RuntimeNavigationItem(
            label = label,
            order = order,
            group = group,
            presentation = presentation,
            isDefault = isDefault,
            icon = icon,
            permission = permission,
            target = target.toRuntimeNavigationTarget(),
        )
    }
}

@Serializable
private data class RuntimeScreenTargetDto(
    @SerialName("screen_id")
    val screenId: String,
    val name: String,
    @SerialName("screen_type")
    val screenType: String,
    val route: String? = null,
) {
    fun toRuntimeNavigationTarget(): RuntimeNavigationTarget =
        RuntimeNavigationTarget(
            screenId = screenId,
            name = name,
            screenType = screenType,
            route = route,
        )
}
