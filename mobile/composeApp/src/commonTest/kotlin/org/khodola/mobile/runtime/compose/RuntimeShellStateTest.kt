package org.khodola.mobile.runtime.compose

import org.khodola.mobile.runtime.MobileRuntimeMarker
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
}
