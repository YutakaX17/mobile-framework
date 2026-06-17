plugins {
    alias(libs.plugins.compose.compiler)
    alias(libs.plugins.compose.multiplatform)
    alias(libs.plugins.kotlin.jvm)
}

kotlin {
    jvmToolchain(17)
}

dependencies {
    implementation(compose.desktop.currentOs)
    implementation(project(":composeApp"))
}

compose.desktop {
    application {
        mainClass = "org.khodola.mobile.runtime.desktop.MainKt"
    }
}
