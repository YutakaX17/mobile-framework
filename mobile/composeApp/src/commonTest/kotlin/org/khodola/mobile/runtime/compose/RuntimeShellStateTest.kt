package org.khodola.mobile.runtime.compose

import org.khodola.mobile.runtime.MobileRuntimeMarker
import org.khodola.mobile.runtime.PracticalRuntimeState
import org.khodola.mobile.runtime.PracticalRuntimeStatus
import kotlin.test.Test
import kotlin.test.assertEquals

class RuntimeShellStateTest {
    @Test
    fun stateUsesRuntimeMarkerMetadata() {
        val state = runtimeShellState(
            MobileRuntimeMarker(
                runtimeName = "Runtime",
                runtimeVersion = "1.2.3",
                supportedSchemaVersion = "v7",
            )
        )

        assertEquals("Runtime 1.2.3", state.title)
        assertEquals("Waiting for package", state.statusLabel)
        assertEquals(
            listOf(
                RuntimeShellSection(label = "Schema", value = "v7"),
                RuntimeShellSection(label = "Runtime", value = "1.2.3"),
            ),
            state.sections,
        )
    }

    @Test
    fun stateSummarizesPracticalRuntimePackage() {
        val state = runtimeShellState(
            marker = MobileRuntimeMarker.default(),
            practicalState = PracticalRuntimeState(
                status = PracticalRuntimeStatus.Ready,
                statusMessage = "Package ready.",
                packageId = "pkg_field_ops_001",
            ),
        )

        assertEquals("Package ready.", state.statusLabel)
        assertEquals(
            listOf(
                RuntimeShellSection(label = "Schema", value = "v1"),
                RuntimeShellSection(label = "Runtime", value = "0.1.0"),
                RuntimeShellSection(label = "Package", value = "pkg_field_ops_001"),
            ),
            state.sections,
        )
    }
}
