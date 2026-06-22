package org.khodola.mobile.runtime.sync

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import kotlin.coroutines.startCoroutine
import kotlinx.serialization.json.JsonPrimitive
import org.khodola.mobile.runtime.network.MobileRuntimeSyncClient
import org.khodola.mobile.runtime.network.SyncBatchSummary
import org.khodola.mobile.runtime.network.SyncDeviceRegistrationRequest
import org.khodola.mobile.runtime.network.SyncDeviceSummary
import org.khodola.mobile.runtime.network.SyncOutboxRequest
import org.khodola.mobile.runtime.network.SyncOutboxResult
import org.khodola.mobile.runtime.network.SyncStatusRequest
import org.khodola.mobile.runtime.network.SyncStatusResult
import org.khodola.mobile.runtime.network.SyncSubmissionReceipt
import org.khodola.mobile.runtime.outbox.InMemoryOfflineOutboxStore
import org.khodola.mobile.runtime.outbox.MobileFormSubmission
import org.khodola.mobile.runtime.outbox.OutboxRecordState

class RuntimeSyncEngineTest {
    @Test
    fun decodesRuntimeSyncRulesFromPackagePayload() {
        val rule = decodeRuntimeSyncRulesFromPackagePayload(packagePayload()).single()

        assertEquals("patient_submissions", rule.syncRuleId)
        assertEquals("patient", rule.entityType)
        assertEquals("bidirectional", rule.direction)
        assertEquals(true, rule.enabled)
        assertEquals("incremental_cursor", rule.pull?.strategy)
        assertEquals("changed_at", rule.pull?.cursorField)
        assertEquals(listOf("submit", "update"), rule.push?.operations)
        assertEquals(2, rule.push?.batchSize)
        assertEquals(listOf("device_id", "local_id"), rule.push?.idempotencyKeyFields)
        assertEquals("manual_review", rule.conflictPolicy)
        assertEquals("sync_conflicts", rule.conflict?.manualReviewQueue)
        assertEquals(5, rule.retryPolicy?.maxAttempts)
        assertEquals(true, rule.audit?.logConflicts)
    }

    @Test
    fun plansPushBatchWithinRuleLimit() {
        val rule = decodeRuntimeSyncRulesFromPackagePayload(packagePayload()).single()
        val outbox = InMemoryOfflineOutboxStore()
        outbox.enqueueSubmission(submission("local-0001"), 100)
        outbox.enqueueSubmission(submission("local-0002"), 200)
        outbox.enqueueSubmission(submission("local-0003"), 300)

        val plan = DefaultRuntimeSyncEngine().planPush(rule, outbox)

        assertTrue(plan.canPush)
        assertEquals(listOf("local-0001", "local-0002"), plan.outboxRecords.map { record -> record.localId })
    }

    @Test
    fun disabledRulesProduceNoPushPlan() {
        val rule = decodeRuntimeSyncRulesFromPackagePayload(
            packagePayload().replace("\"enabled\": true", "\"enabled\": false"),
        ).single()
        val outbox = InMemoryOfflineOutboxStore()
        outbox.enqueueSubmission(submission("local-0001"), 100)

        val plan = DefaultRuntimeSyncEngine().planPush(rule, outbox)

        assertFalse(plan.canPush)
        assertEquals(emptyList(), plan.outboxRecords)
    }

    @Test
    fun filtersRecordsThatExceededRetryLimit() {
        val rule = decodeRuntimeSyncRulesFromPackagePayload(packagePayload()).single()
        val outbox = InMemoryOfflineOutboxStore()
        outbox.enqueueSubmission(submission("local-0001"), 100)
        repeat(5) { attempt ->
            outbox.markFailed("local-0001", error = "attempt-$attempt", updatedAtEpochMillis = 200L + attempt)
        }

        val plan = DefaultRuntimeSyncEngine().planPush(rule, outbox)

        assertFalse(plan.canPush)
        assertEquals(emptyList(), plan.outboxRecords)
    }

    @Test
    fun synchronizerMarksAcceptedAndDuplicateReceiptsAsSynced() = runSuspendTest {
        val rule = decodeRuntimeSyncRulesFromPackagePayload(packagePayload()).single()
        val outbox = InMemoryOfflineOutboxStore()
        outbox.enqueueSubmission(submission("local-0001"), 100)
        outbox.enqueueSubmission(submission("local-0002"), 200)
        val syncClient = FakeSyncClient(
            receipts = listOf(
                receipt("local-0001", status = "accepted"),
                receipt("local-0002", status = "duplicate"),
            ),
        )

        val result = MobileOutboxSynchronizer(DefaultRuntimeSyncEngine(), outbox, syncClient)
            .pushPending(rule, syncContext(now = 500))

        assertEquals(listOf("local-0001", "local-0002"), result.syncedLocalIds)
        assertEquals(emptyList(), result.failedLocalIds)
        assertEquals(OutboxRecordState.Synced, outbox.getRecord("local-0001")?.state)
        assertEquals(OutboxRecordState.Synced, outbox.getRecord("local-0002")?.state)
        assertEquals(listOf("local-0001", "local-0002"), syncClient.lastRequest?.submissions?.map { it.clientSubmissionId })
    }

    @Test
    fun synchronizerMarksRejectedReceiptsAsFailedForRetry() = runSuspendTest {
        val rule = decodeRuntimeSyncRulesFromPackagePayload(packagePayload()).single()
        val outbox = InMemoryOfflineOutboxStore()
        outbox.enqueueSubmission(submission("local-0001"), 100)
        val syncClient = FakeSyncClient(
            receipts = listOf(receipt("local-0001", status = "rejected", message = "unknown form")),
        )

        val result = MobileOutboxSynchronizer(DefaultRuntimeSyncEngine(), outbox, syncClient)
            .pushPending(rule, syncContext(now = 500))

        assertEquals(emptyList(), result.syncedLocalIds)
        assertEquals(listOf("local-0001"), result.failedLocalIds)
        assertEquals(OutboxRecordState.Failed, outbox.getRecord("local-0001")?.state)
        assertEquals("unknown form", outbox.getRecord("local-0001")?.lastError)
    }

    private fun submission(localId: String): MobileFormSubmission =
        MobileFormSubmission(
            localId = localId,
            deviceId = "device-alpha-01",
            formId = "patient_intake",
            revision = 3,
            submittedAt = "2026-06-16T11:00:00Z",
            answers = mapOf("full_name" to JsonPrimitive("Ada Lovelace")),
        )

    private fun syncContext(now: Long): MobileSyncContext =
        MobileSyncContext(
            tenantSlug = "demo",
            deviceId = "device-alpha-01",
            platform = "android",
            appVersion = "0.1.0",
            runtimeVersion = "0.1.0",
            nowEpochMillis = now,
        )
}

private class FakeSyncClient(
    private val receipts: List<SyncSubmissionReceipt>,
) : MobileRuntimeSyncClient {
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
                acceptedCount = receipts.count { receipt -> receipt.status == "accepted" },
                duplicateCount = receipts.count { receipt -> receipt.status == "duplicate" },
                rejectedCount = receipts.count { receipt -> receipt.status == "rejected" },
            ),
            receipts = receipts,
        )
    }

    override suspend fun fetchSyncStatus(request: SyncStatusRequest): SyncStatusResult =
        SyncStatusResult(devices = emptyList(), batches = emptyList())
}

private fun receipt(
    localId: String,
    status: String,
    message: String = "ok",
): SyncSubmissionReceipt =
    SyncSubmissionReceipt(
        clientSubmissionId = localId,
        formId = "patient_intake",
        message = message,
        reasonCode = status,
        status = status,
        submissionId = 1,
    )

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

private fun packagePayload(): String =
    """
    {
      "sync_rules": [
        {
          "schema_version": "v1",
          "sync_rule_id": "patient_submissions",
          "name": "Patient submissions",
          "entity_type": "patient",
          "direction": "bidirectional",
          "enabled": true,
          "priority": 100,
          "pull": {
            "strategy": "incremental_cursor",
            "cursor_field": "changed_at",
            "include_deleted": true,
            "page_size": 100,
            "filters": [
              {
                "field": "status",
                "operator": "in",
                "value": ["active", "pending_review"]
              }
            ]
          },
          "push": {
            "operations": ["submit", "update"],
            "batch_size": 2,
            "idempotency_key_fields": ["device_id", "local_id"],
            "requires_network": true
          },
          "conflict_policy": "manual_review",
          "conflict": {
            "detect_with": ["version", "changed_at"],
            "manual_review_queue": "sync_conflicts",
            "stale_after_seconds": 86400
          },
          "retry_policy": {
            "max_attempts": 5,
            "backoff_seconds": 30
          },
          "audit": {
            "log_success": false,
            "log_rejections": true,
            "log_conflicts": true
          }
        }
      ]
    }
    """.trimIndent()
