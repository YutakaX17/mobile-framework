package org.khodola.mobile.runtime.desktop

import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import org.khodola.mobile.runtime.compose.MobileRuntimeApp

fun main() = application {
    Window(
        onCloseRequest = ::exitApplication,
        title = "Khodola Mobile Runtime",
    ) {
        MobileRuntimeApp()
    }
}
