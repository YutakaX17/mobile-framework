package org.khodola.mobile.runtime.compose

import org.khodola.mobile.runtime.MobileRuntimeMarker

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
