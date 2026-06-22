package org.khodola.mobile.runtime.compose

import org.khodola.mobile.runtime.MobileRuntimeMarker
import org.khodola.mobile.runtime.PracticalRuntimeState

data class RuntimeShellSection(
    val label: String,
    val value: String,
)

data class RuntimeShellState(
    val title: String,
    val statusLabel: String,
    val sections: List<RuntimeShellSection>,
)

fun runtimeShellState(marker: MobileRuntimeMarker = MobileRuntimeMarker.default()): RuntimeShellState =
    RuntimeShellState(
        title = marker.displayName,
        statusLabel = "Waiting for package",
        sections = listOf(
            RuntimeShellSection(label = "Schema", value = marker.supportedSchemaVersion),
            RuntimeShellSection(label = "Runtime", value = marker.runtimeVersion),
        ),
    )

fun runtimeShellState(
    marker: MobileRuntimeMarker = MobileRuntimeMarker.default(),
    practicalState: PracticalRuntimeState,
): RuntimeShellState {
    val baseSections = mutableListOf(
        RuntimeShellSection(label = "Schema", value = marker.supportedSchemaVersion),
        RuntimeShellSection(label = "Runtime", value = marker.runtimeVersion),
    )
    practicalState.packageId?.let { packageId ->
        baseSections += RuntimeShellSection(label = "Package", value = packageId)
    }
    practicalState.navigation?.let { navigation ->
        baseSections += RuntimeShellSection(label = "App", value = navigation.appName)
        baseSections += RuntimeShellSection(label = "Screen", value = navigation.defaultItem.target.name)
    }
    practicalState.form?.let { form ->
        baseSections += RuntimeShellSection(label = "Form", value = form.name)
    }
    if (practicalState.unsupportedPluginApiVersions.isNotEmpty()) {
        baseSections += RuntimeShellSection(
            label = "Unsupported plugins",
            value = practicalState.unsupportedPluginApiVersions.entries.joinToString { (moduleId, version) ->
                "$moduleId:$version"
            },
        )
    }
    if (practicalState.unsupportedWidgets.isNotEmpty()) {
        baseSections += RuntimeShellSection(
            label = "Unsupported widgets",
            value = practicalState.unsupportedWidgets.joinToString(),
        )
    }
    if (practicalState.unsupportedActions.isNotEmpty()) {
        baseSections += RuntimeShellSection(
            label = "Unsupported actions",
            value = practicalState.unsupportedActions.joinToString(),
        )
    }
    return RuntimeShellState(
        title = marker.displayName,
        statusLabel = practicalState.statusMessage,
        sections = baseSections,
    )
}
