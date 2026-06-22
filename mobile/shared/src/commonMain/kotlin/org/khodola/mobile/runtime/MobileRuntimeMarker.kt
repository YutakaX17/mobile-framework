package org.khodola.mobile.runtime

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import org.khodola.mobile.runtime.downloader.MobilePackageDownloader
import org.khodola.mobile.runtime.form.RuntimeForm
import org.khodola.mobile.runtime.form.decodeRuntimeFormFromPackagePayload
import org.khodola.mobile.runtime.navigation.RuntimeNavigationGraph
import org.khodola.mobile.runtime.navigation.decodeRuntimeNavigationGraphFromPackagePayload
import org.khodola.mobile.runtime.network.MobileRuntimeSyncClient
import org.khodola.mobile.runtime.outbox.MobileFormSubmission
import org.khodola.mobile.runtime.outbox.MobileFormSubmissionMetadata
import org.khodola.mobile.runtime.outbox.OfflineOutboxRecord
import org.khodola.mobile.runtime.outbox.OfflineOutboxStore
import org.khodola.mobile.runtime.screen.RuntimeScreen
import org.khodola.mobile.runtime.screen.decodeRuntimeScreenFromPackagePayload
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson
import org.khodola.mobile.runtime.sync.DefaultRuntimeSyncEngine
import org.khodola.mobile.runtime.sync.MobileOutboxSyncResult
import org.khodola.mobile.runtime.sync.MobileOutboxSynchronizer
import org.khodola.mobile.runtime.sync.MobileSyncContext
import org.khodola.mobile.runtime.sync.RuntimeSyncRule
import org.khodola.mobile.runtime.sync.decodeRuntimeSyncRulesFromPackagePayload
import org.khodola.mobile.runtime.theme.RuntimeTheme
import org.khodola.mobile.runtime.theme.decodeRuntimeThemeFromPackagePayload
import org.khodola.mobile.runtime.widget.DefaultRuntimeWidgetRegistry
import org.khodola.mobile.runtime.widget.RuntimeWidgetRegistry

data class MobileRuntimeMarker(
    val runtimeName: String,
    val runtimeVersion: String,
    val supportedSchemaVersion: String,
    val supportedPluginApiVersion: Int = 0,
) {
    val displayName: String
        get() = "$runtimeName $runtimeVersion"

    companion object {
        fun default(): MobileRuntimeMarker = MobileRuntimeMarker(
            runtimeName = "Khodola Mobile Runtime",
            runtimeVersion = "0.1.0",
            supportedSchemaVersion = "v1",
            supportedPluginApiVersion = 0,
        )
    }
}

data class MobileRuntimeConnectionSettings(
    val backendBaseUrl: String,
    val tenantSlug: String,
    val appId: String,
    val channel: String = "dev",
    val deviceId: String,
    val platform: String,
) {
    init {
        require(backendBaseUrl.isNotBlank()) { "backendBaseUrl is required" }
        require(tenantSlug.isNotBlank()) { "tenantSlug is required" }
        require(appId.isNotBlank()) { "appId is required" }
        require(channel.isNotBlank()) { "channel is required" }
        require(deviceId.isNotBlank()) { "deviceId is required" }
        require(platform.isNotBlank()) { "platform is required" }
    }
}

enum class PracticalRuntimeStatus {
    WaitingForConfiguration,
    Ready,
    VerificationFailed,
    UnsupportedPluginApi,
    UnsupportedWidget,
    UnsupportedAction,
}

data class PracticalRuntimeState(
    val status: PracticalRuntimeStatus,
    val statusMessage: String,
    val packageId: String? = null,
    val appVersion: String? = null,
    val navigation: RuntimeNavigationGraph? = null,
    val screen: RuntimeScreen? = null,
    val form: RuntimeForm? = null,
    val theme: RuntimeTheme? = null,
    val syncRules: List<RuntimeSyncRule> = emptyList(),
    val unsupportedPluginApiVersions: Map<String, Int> = emptyMap(),
    val unsupportedWidgets: Set<String> = emptySet(),
    val unsupportedActions: Set<String> = emptySet(),
) {
    val isReady: Boolean
        get() = status == PracticalRuntimeStatus.Ready
}

class PracticalMobileRuntimeSession(
    private val marker: MobileRuntimeMarker,
    private val downloader: MobilePackageDownloader,
    private val outboxStore: OfflineOutboxStore,
    private val syncClient: MobileRuntimeSyncClient,
    private val widgetRegistry: RuntimeWidgetRegistry = DefaultRuntimeWidgetRegistry(),
    private val supportedActions: Set<String> = DEFAULT_SUPPORTED_ACTIONS,
) {
    suspend fun loadActivePackage(
        settings: MobileRuntimeConnectionSettings,
        nowEpochMillis: Long,
        themeModeId: String = "light",
    ): PracticalRuntimeState {
        val packageResult = try {
            downloader.ensureActivePackage(
                tenantSlug = settings.tenantSlug,
                appId = settings.appId,
                channel = settings.channel,
                nowEpochMillis = nowEpochMillis,
            )
        } catch (exc: IllegalArgumentException) {
            return PracticalRuntimeState(
                status = PracticalRuntimeStatus.VerificationFailed,
                statusMessage = exc.message ?: "Package could not be loaded.",
            )
        }

        val payloadJson = packageResult.packageRecord.payloadJson
        val compatibility = decodePackageCompatibility(payloadJson)
        val unsupportedPluginApis = compatibility.unsupportedPluginApiVersions(marker.supportedPluginApiVersion)
        if (unsupportedPluginApis.isNotEmpty()) {
            return PracticalRuntimeState(
                status = PracticalRuntimeStatus.UnsupportedPluginApi,
                statusMessage = "Package requires unsupported plugin API versions.",
                packageId = packageResult.packageRecord.packageId,
                appVersion = packageResult.manifest.appVersion,
                unsupportedPluginApiVersions = unsupportedPluginApis,
            )
        }

        val navigation = decodeRuntimeNavigationGraphFromPackagePayload(payloadJson)
        val screen = decodeRuntimeScreenFromPackagePayload(payloadJson, navigation.defaultItem.target.screenId)
        val widgetValidation = widgetRegistry.validateComponents(screen.components)
        if (!widgetValidation.isValid) {
            return PracticalRuntimeState(
                status = PracticalRuntimeStatus.UnsupportedWidget,
                statusMessage = "Screen contains unsupported widgets.",
                packageId = packageResult.packageRecord.packageId,
                appVersion = packageResult.manifest.appVersion,
                navigation = navigation,
                screen = screen,
                unsupportedWidgets = widgetValidation.unsupportedComponentTypes,
            )
        }

        val unsupportedActionTypes = screen.actions.map { action -> action.actionType }
            .filterNot { actionType -> actionType in supportedActions }
            .toSet()
        if (unsupportedActionTypes.isNotEmpty()) {
            return PracticalRuntimeState(
                status = PracticalRuntimeStatus.UnsupportedAction,
                statusMessage = "Screen contains unsupported actions.",
                packageId = packageResult.packageRecord.packageId,
                appVersion = packageResult.manifest.appVersion,
                navigation = navigation,
                screen = screen,
                unsupportedActions = unsupportedActionTypes,
            )
        }

        val formId = screen.components.firstNotNullOfOrNull { component -> component.binding?.formId }
        val form = formId?.let { id -> decodeRuntimeFormFromPackagePayload(payloadJson, id) }
        return PracticalRuntimeState(
            status = PracticalRuntimeStatus.Ready,
            statusMessage = "Package ready.",
            packageId = packageResult.packageRecord.packageId,
            appVersion = packageResult.manifest.appVersion,
            navigation = navigation,
            screen = screen,
            form = form,
            theme = decodeRuntimeThemeFromPackagePayload(payloadJson, modeId = themeModeId),
            syncRules = decodeRuntimeSyncRulesFromPackagePayload(payloadJson),
        )
    }

    fun queueFormSubmission(
        state: PracticalRuntimeState,
        settings: MobileRuntimeConnectionSettings,
        localId: String,
        answers: Map<String, JsonElement>,
        submittedAt: String,
        queuedAtEpochMillis: Long,
    ): OfflineOutboxRecord {
        require(state.isReady) { "Runtime state is not ready." }
        val form = state.form ?: throw IllegalArgumentException("No form is active in the current runtime state.")
        return outboxStore.enqueueSubmission(
            MobileFormSubmission(
                localId = localId,
                deviceId = settings.deviceId,
                formId = form.formId,
                revision = 1,
                submittedAt = submittedAt,
                answers = answers,
                metadata = MobileFormSubmissionMetadata(
                    appId = settings.appId,
                    packageVersion = state.appVersion,
                    screenId = state.screen?.screenId,
                ),
            ),
            queuedAtEpochMillis = queuedAtEpochMillis,
        )
    }

    suspend fun syncPending(
        state: PracticalRuntimeState,
        settings: MobileRuntimeConnectionSettings,
        nowEpochMillis: Long,
    ): MobileOutboxSyncResult {
        require(state.isReady) { "Runtime state is not ready." }
        val rule = state.syncRules.firstOrNull()
            ?: defaultFormSubmissionRule()
        val synchronizer = MobileOutboxSynchronizer(
            syncEngine = DefaultRuntimeSyncEngine(),
            outboxStore = outboxStore,
            syncClient = syncClient,
        )
        return synchronizer.pushPending(
            rule,
            MobileSyncContext(
                tenantSlug = settings.tenantSlug,
                deviceId = settings.deviceId,
                platform = settings.platform,
                appVersion = state.appVersion ?: marker.runtimeVersion,
                runtimeVersion = marker.runtimeVersion,
                nowEpochMillis = nowEpochMillis,
            ),
        )
    }
}

private val DEFAULT_SUPPORTED_ACTIONS = setOf("navigate", "submit_form")

private data class PackageCompatibility(
    val modules: List<PackageModuleCompatibility>,
) {
    fun unsupportedPluginApiVersions(maxSupported: Int): Map<String, Int> =
        modules
            .filter { module -> module.pluginApiVersion > maxSupported }
            .associate { module -> module.moduleId to module.pluginApiVersion }
}

private data class PackageModuleCompatibility(
    val moduleId: String,
    val pluginApiVersion: Int,
)

private fun decodePackageCompatibility(payloadJson: String): PackageCompatibility =
    MobileRuntimeJson
        .decodeFromString<PackageCompatibilityEnvelopeDto>(payloadJson)
        .toCompatibility()

@Serializable
private data class PackageCompatibilityEnvelopeDto(
    val modules: List<PackageModuleCompatibilityDto> = emptyList(),
) {
    fun toCompatibility(): PackageCompatibility =
        PackageCompatibility(
            modules = modules.map { module -> module.toCompatibility() },
        )
}

@Serializable
private data class PackageModuleCompatibilityDto(
    @SerialName("module_id")
    val moduleId: String,
    @SerialName("plugin_api_version")
    val pluginApiVersion: Int = 0,
) {
    fun toCompatibility(): PackageModuleCompatibility =
        PackageModuleCompatibility(
            moduleId = moduleId,
            pluginApiVersion = pluginApiVersion,
        )
}

private fun defaultFormSubmissionRule(): RuntimeSyncRule =
    RuntimeSyncRule(
        syncRuleId = "default_form_submission_push",
        name = "Default form submission push",
        entityType = "form_submission",
        direction = "push",
        enabled = true,
        priority = 100,
        pull = null,
        push = org.khodola.mobile.runtime.sync.RuntimePushRule(
            operations = listOf("submit"),
            batchSize = 50,
            idempotencyKeyFields = listOf("device_id", "local_id"),
            requiresNetwork = true,
        ),
        conflictPolicy = "server_rejects",
        conflict = null,
        retryPolicy = org.khodola.mobile.runtime.sync.RuntimeRetryPolicy(
            maxAttempts = 5,
            backoffSeconds = 30,
        ),
        audit = null,
    )
