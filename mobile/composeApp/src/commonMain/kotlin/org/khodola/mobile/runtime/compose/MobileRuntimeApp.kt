package org.khodola.mobile.runtime.compose

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import org.khodola.mobile.runtime.MobileRuntimeMarker

@Composable
fun MobileRuntimeApp(
    marker: MobileRuntimeMarker = MobileRuntimeMarker.default(),
    state: RuntimeShellState = runtimeShellState(marker),
) {
    MaterialTheme {
        Surface {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(text = state.title, style = MaterialTheme.typography.titleLarge)
                Text(text = state.statusLabel, style = MaterialTheme.typography.bodyMedium)
                Spacer(modifier = Modifier.height(12.dp))
                state.sections.forEach { section ->
                    Text(
                        text = "${section.label}: ${section.value}",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }
    }
}
