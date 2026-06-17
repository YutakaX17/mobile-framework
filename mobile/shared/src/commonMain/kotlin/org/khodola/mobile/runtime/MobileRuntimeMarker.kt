package org.khodola.mobile.runtime

data class MobileRuntimeMarker(
    val runtimeName: String,
    val runtimeVersion: String,
    val supportedSchemaVersion: String,
) {
    val displayName: String
        get() = "$runtimeName $runtimeVersion"

    companion object {
        fun default(): MobileRuntimeMarker = MobileRuntimeMarker(
            runtimeName = "Khodola Mobile Runtime",
            runtimeVersion = "0.1.0",
            supportedSchemaVersion = "v1",
        )
    }
}
