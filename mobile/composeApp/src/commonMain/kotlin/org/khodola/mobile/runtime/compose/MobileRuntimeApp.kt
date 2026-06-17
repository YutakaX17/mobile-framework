package org.khodola.mobile.runtime.compose

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import org.khodola.mobile.runtime.MobileRuntimeMarker

@Composable
fun MobileRuntimeApp(marker: MobileRuntimeMarker = MobileRuntimeMarker.default()) {
    MaterialTheme {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = marker.displayName)
            Text(text = "Schema ${marker.supportedSchemaVersion}")
        }
    }
}
