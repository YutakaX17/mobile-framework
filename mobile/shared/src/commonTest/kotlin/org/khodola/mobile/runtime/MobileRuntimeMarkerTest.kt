package org.khodola.mobile.runtime

import kotlin.test.Test
import kotlin.test.assertEquals

class MobileRuntimeMarkerTest {
    @Test
    fun defaultMarkerDeclaresRuntimeIdentity() {
        val marker = MobileRuntimeMarker.default()

        assertEquals("Khodola Mobile Runtime", marker.runtimeName)
        assertEquals("0.1.0", marker.runtimeVersion)
        assertEquals("v1", marker.supportedSchemaVersion)
        assertEquals("Khodola Mobile Runtime 0.1.0", marker.displayName)
    }
}
