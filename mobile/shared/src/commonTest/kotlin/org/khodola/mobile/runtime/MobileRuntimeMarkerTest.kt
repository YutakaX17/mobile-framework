package org.khodola.mobile.runtime

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.coroutines.startCoroutine
import kotlinx.serialization.json.JsonPrimitive
import org.khodola.mobile.runtime.downloader.MobilePackageDownloader
import org.khodola.mobile.runtime.downloader.PackageDownloaderResult
import org.khodola.mobile.runtime.downloader.PackageDownloaderSource
import org.khodola.mobile.runtime.network.MobileRuntimeSyncClient
import org.khodola.mobile.runtime.network.PackageManifestMetadata
import org.khodola.mobile.runtime.network.SyncBatchSummary
import org.khodola.mobile.runtime.network.SyncDeviceRegistrationRequest
import org.khodola.mobile.runtime.network.SyncDeviceSummary
import org.khodola.mobile.runtime.network.SyncOutboxRequest
import org.khodola.mobile.runtime.network.SyncOutboxResult
import org.khodola.mobile.runtime.network.SyncStatusRequest
import org.khodola.mobile.runtime.network.SyncStatusResult
import org.khodola.mobile.runtime.network.SyncSubmissionReceipt
import org.khodola.mobile.runtime.outbox.InMemoryOfflineOutboxStore
import org.khodola.mobile.runtime.outbox.OutboxRecordState
import org.khodola.mobile.runtime.storage.LocalPackageRecord

class MobileRuntimeMarkerTest {
    @Test
    fun defaultMarkerDeclaresRuntimeIdentity() {
        val marker = MobileRuntimeMarker.default()

        assertEquals("Khodola Mobile Runtime", marker.runtimeName)
        assertEquals("0.1.0", marker.runtimeVersion)
        assertEquals("v1", marker.supportedSchemaVersion)
        assertEquals("Khodola Mobile Runtime 0.1.0", marker.displayName)
    }

    @Test
    fun practicalSessionLoadsPackageRenderModelAndQueuesSubmission() = runSuspendTest {
        val outbox = InMemoryOfflineOutboxStore()
        val session = PracticalMobileRuntimeSession(
            marker = MobileRuntimeMarker.default(),
            downloader = FakeDownloader(packagePayload()),
            outboxStore = outbox,
            syncClient = FakeSyncClient(),
        )

        val state = session.loadActivePackage(settings(), nowEpochMillis = 100)
        val queued = session.queueFormSubmission(
            state = state,
            settings = settings(),
            localId = "local-0001",
            answers = mapOf("full_name" to JsonPrimitive("Ada Lovelace")),
            submittedAt = "2026-06-21T12:00:00Z",
            queuedAtEpochMillis = 200,
        )

        assertEquals(PracticalRuntimeStatus.Ready, state.status)
        assertEquals("pkg_field_ops_001", state.packageId)
        assertEquals("Field Operations", state.navigation?.appName)
        assertEquals("Patient Intake", state.screen?.name)
        assertEquals("Patient Intake", state.form?.name)
        assertEquals("field_ops", state.theme?.themeId)
        assertEquals("local-0001", queued.localId)
        assertEquals(OutboxRecordState.Pending, outbox.getRecord("local-0001")?.state)
    }

    @Test
    fun practicalSessionSyncsQueuedSubmission() = runSuspendTest {
        val outbox = InMemoryOfflineOutboxStore()
        val syncClient = FakeSyncClient()
        val session = PracticalMobileRuntimeSession(
            marker = MobileRuntimeMarker.default(),
            downloader = FakeDownloader(packagePayload()),
            outboxStore = outbox,
            syncClient = syncClient,
        )
        val state = session.loadActivePackage(settings(), nowEpochMillis = 100)
        session.queueFormSubmission(
            state = state,
            settings = settings(),
            localId = "local-0001",
            answers = mapOf("full_name" to JsonPrimitive("Ada Lovelace")),
            submittedAt = "2026-06-21T12:00:00Z",
            queuedAtEpochMillis = 200,
        )

        val result = session.syncPending(state, settings(), nowEpochMillis = 300)

        assertEquals(listOf("local-0001"), result.syncedLocalIds)
        assertEquals(OutboxRecordState.Synced, outbox.getRecord("local-0001")?.state)
        assertEquals("local-0001", syncClient.lastRequest?.submissions?.single()?.clientSubmissionId)
    }

    @Test
    fun practicalSessionFailsSafelyForUnsupportedPluginApi() = runSuspendTest {
        val state = PracticalMobileRuntimeSession(
            marker = MobileRuntimeMarker.default(),
            downloader = FakeDownloader(packagePayload(pluginApiVersion = 99)),
            outboxStore = InMemoryOfflineOutboxStore(),
            syncClient = FakeSyncClient(),
        ).loadActivePackage(settings(), nowEpochMillis = 100)

        assertEquals(PracticalRuntimeStatus.UnsupportedPluginApi, state.status)
        assertEquals(mapOf("field_ops" to 99), state.unsupportedPluginApiVersions)
    }

    @Test
    fun practicalSessionFailsSafelyForUnsupportedWidgetAndAction() = runSuspendTest {
        val unsupportedWidget = PracticalMobileRuntimeSession(
            marker = MobileRuntimeMarker.default(),
            downloader = FakeDownloader(packagePayload(componentType = "map")),
            outboxStore = InMemoryOfflineOutboxStore(),
            syncClient = FakeSyncClient(),
        ).loadActivePackage(settings(), nowEpochMillis = 100)

        val unsupportedAction = PracticalMobileRuntimeSession(
            marker = MobileRuntimeMarker.default(),
            downloader = FakeDownloader(packagePayload(actionType = "print_label")),
            outboxStore = InMemoryOfflineOutboxStore(),
            syncClient = FakeSyncClient(),
        ).loadActivePackage(settings(), nowEpochMillis = 100)

        assertEquals(PracticalRuntimeStatus.UnsupportedWidget, unsupportedWidget.status)
        assertEquals(setOf("map"), unsupportedWidget.unsupportedWidgets)
        assertEquals(PracticalRuntimeStatus.UnsupportedAction, unsupportedAction.status)
        assertEquals(setOf("print_label"), unsupportedAction.unsupportedActions)
    }
}

private class FakeDownloader(
    private val payloadJson: String,
) : MobilePackageDownloader {
    private val manifest = PackageManifestMetadata(
        packageId = "pkg_field_ops_001",
        appId = "field_ops_app",
        appVersion = "0.1.0",
        channel = "dev",
        runtimeMinVersion = "0.1.0",
        runtimeMaxVersion = "0.1.0",
        hash = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        signature = "hmac-sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    )

    override suspend fun ensureActivePackage(
        tenantSlug: String,
        appId: String,
        channel: String,
        nowEpochMillis: Long,
    ): PackageDownloaderResult =
        PackageDownloaderResult(
            manifest = manifest,
            packageRecord = LocalPackageRecord(
                tenantSlug = tenantSlug,
                manifest = manifest,
                payloadJson = payloadJson,
                etag = "etag-1",
                cachedAtEpochMillis = nowEpochMillis,
                activeAtEpochMillis = nowEpochMillis,
            ),
            source = PackageDownloaderSource.Network,
        )
}

private class FakeSyncClient : MobileRuntimeSyncClient {
    var lastRequest: SyncOutboxRequest? = null
        private set

    override suspend fun registerDevice(request: SyncDeviceRegistrationRequest): SyncDeviceSummary =
        SyncDeviceSummary(
            deviceId = request.deviceId,
            platform = request.platform,
            appVersion = request.appVersion,
            runtimeVersion = request.runtimeVersion,
            status = "active",
        )

    override suspend fun submitOutboxBatch(request: SyncOutboxRequest): SyncOutboxResult {
        lastRequest = request
        return SyncOutboxResult(
            batch = SyncBatchSummary(
                batchId = request.batchId,
                status = "accepted",
                sessionId = "session-1",
                acceptedCount = request.submissions.size,
                duplicateCount = 0,
                rejectedCount = 0,
            ),
            receipts = request.submissions.map { submission ->
                SyncSubmissionReceipt(
                    clientSubmissionId = submission.clientSubmissionId,
                    formId = submission.formId,
                    message = "Submission accepted.",
                    reasonCode = "accepted",
                    status = "accepted",
                    submissionId = 1,
                )
            },
        )
    }

    override suspend fun fetchSyncStatus(request: SyncStatusRequest): SyncStatusResult =
        SyncStatusResult(devices = emptyList(), batches = emptyList())
}

private fun settings(): MobileRuntimeConnectionSettings =
    MobileRuntimeConnectionSettings(
        backendBaseUrl = "http://localhost:8000",
        tenantSlug = "demo",
        appId = "field_ops_app",
        channel = "dev",
        deviceId = "tablet-1",
        platform = "android",
    )

private fun packagePayload(
    pluginApiVersion: Int = 0,
    componentType: String = "form",
    actionType: String = "submit_form",
): String =
    """
    {
      "package_id": "pkg_field_ops_001",
      "app_id": "field_ops_app",
      "channel": "dev",
      "modules": [
        {
          "module_id": "field_ops",
          "plugin_api_version": $pluginApiVersion
        }
      ],
      "theme": {
        "theme_id": "field_ops",
        "name": "Field Operations",
        "version": "0.1.0",
        "tokens": {
          "colors": {
            "primary": {"main": "#0B5FFF", "contrast": "#FFFFFF"},
            "secondary": {"main": "#168A55", "contrast": "#FFFFFF"},
            "background": "#F6F8FB",
            "surface": "#FFFFFF",
            "text": "#172033",
            "success": "#168A55",
            "warning": "#B26A00",
            "danger": "#B42318"
          },
          "typography": {
            "font_family": "Atkinson Hyperlegible",
            "scale": {
              "body": {"font_size": 16, "line_height": 24, "font_weight": 400}
            }
          },
          "spacing": {"md": 16},
          "radius": {"md": 8},
          "elevation": {"none": {"level": 0}},
          "components": {}
        },
        "modes": [
          {
            "mode_id": "light",
            "label": "Light",
            "color_overrides": {}
          }
        ]
      },
      "app": {
        "app_id": "field_ops_app",
        "name": "Field Operations",
        "navigation": [
          {
            "label": "Intake",
            "order": 0,
            "is_default": true,
            "screen_id": "intake"
          }
        ],
        "screens": [
          {
            "screen_id": "intake",
            "name": "Patient Intake",
            "screen_type": "form",
            "components": [
              {
                "component_id": "intake_form",
                "component_type": "$componentType",
                "binding": {"form_id": "patient_intake"}
              }
            ],
            "actions": [
              {
                "action_id": "submit_intake",
                "action_type": "$actionType",
                "target": "patient_intake"
              }
            ]
          }
        ]
      },
      "forms": [
        {
          "form_id": "patient_intake",
          "name": "Patient Intake",
          "version": "0.1.0",
          "mode": "standalone",
          "fields": [
            {
              "field_id": "full_name",
              "field_type": "text",
              "label": "Full name",
              "binding": {"data_path": "patient.full_name"}
            }
          ],
          "offline": {
            "enabled": true,
            "queue_submissions": true,
            "conflict_policy": "manual_review"
          }
        }
      ],
      "sync_rules": []
    }
    """.trimIndent()

private fun runSuspendTest(block: suspend () -> Unit) {
    var failure: Throwable? = null
    block.startCoroutine(
        object : kotlin.coroutines.Continuation<Unit> {
            override val context: kotlin.coroutines.CoroutineContext =
                kotlin.coroutines.EmptyCoroutineContext

            override fun resumeWith(result: Result<Unit>) {
                failure = result.exceptionOrNull()
            }
        },
    )
    failure?.let { throw it }
}
