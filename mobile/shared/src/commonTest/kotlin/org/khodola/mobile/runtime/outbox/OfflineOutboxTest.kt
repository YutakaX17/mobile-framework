package org.khodola.mobile.runtime.outbox

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlinx.serialization.json.JsonPrimitive

class OfflineOutboxTest {
    @Test
    fun queuesFormSubmissionAsPendingRecord() {
        val store = InMemoryOfflineOutboxStore()
        val submission = submission("local-0001")

        val record = store.enqueueSubmission(submission, queuedAtEpochMillis = 100)

        assertEquals("local-0001", record.localId)
        assertEquals(OutboxRecordState.Pending, record.state)
        assertEquals(100, record.queuedAtEpochMillis)
        assertEquals("Ada Lovelace", record.submission.answers.getValue("full_name").toString().trim('"'))
        assertEquals(record, store.getRecord("local-0001"))
    }

    @Test
    fun rejectsDuplicateLocalIds() {
        val store = InMemoryOfflineOutboxStore()
        store.enqueueSubmission(submission("local-0001"), 100)

        assertFailsWith<IllegalArgumentException> {
            store.enqueueSubmission(submission("local-0001"), 200)
        }
    }

    @Test
    fun returnsPendingBatchInQueuedOrder() {
        val store = InMemoryOfflineOutboxStore()
        store.enqueueSubmission(submission("local-0002"), 200)
        store.enqueueSubmission(submission("local-0001"), 100)
        store.enqueueSubmission(submission("local-0003"), 300)

        val batch = store.pendingBatch(limit = 2)

        assertEquals(listOf("local-0001", "local-0002"), batch.map { record -> record.localId })
    }

    @Test
    fun tracksInFlightSyncedAndFailedStates() {
        val store = InMemoryOfflineOutboxStore()
        store.enqueueSubmission(submission("local-0001"), 100)
        store.enqueueSubmission(submission("local-0002"), 200)

        val inFlight = store.markInFlight(listOf("local-0001", "local-0002"), updatedAtEpochMillis = 300)
        assertEquals(listOf(OutboxRecordState.InFlight, OutboxRecordState.InFlight), inFlight.map { it.state })

        val failed = store.markFailed("local-0001", error = "network unavailable", updatedAtEpochMillis = 400)
        assertEquals(OutboxRecordState.Failed, failed.state)
        assertEquals(1, failed.attemptCount)
        assertEquals("network unavailable", failed.lastError)

        val synced = store.markSynced("local-0002", updatedAtEpochMillis = 500)
        assertEquals(OutboxRecordState.Synced, synced.state)
        assertEquals(null, synced.lastError)
        assertEquals(listOf("local-0001"), store.pendingBatch(limit = 10).map { record -> record.localId })
    }

    @Test
    fun rejectsMissingRecordTransitions() {
        val store = InMemoryOfflineOutboxStore()

        assertFailsWith<IllegalArgumentException> {
            store.markSynced("missing", 100)
        }
        assertFailsWith<IllegalArgumentException> {
            store.markInFlight(listOf("missing"), 100)
        }
    }

    private fun submission(localId: String): MobileFormSubmission =
        MobileFormSubmission(
            localId = localId,
            deviceId = "device-alpha-01",
            formId = "patient_intake",
            revision = 3,
            submittedAt = "2026-06-16T11:00:00Z",
            answers = mapOf(
                "full_name" to JsonPrimitive("Ada Lovelace"),
                "age" to JsonPrimitive(36),
                "consent" to JsonPrimitive(true),
            ),
            metadata = MobileFormSubmissionMetadata(
                appId = "field_ops",
                packageVersion = "0.1.0",
                screenId = "patient_intake_screen",
            ),
        )
}
