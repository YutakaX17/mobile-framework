package org.khodola.mobile.runtime.outbox

import kotlinx.serialization.json.JsonElement

data class MobileFormSubmission(
    val localId: String,
    val deviceId: String,
    val formId: String,
    val revision: Int,
    val submittedAt: String,
    val answers: Map<String, JsonElement>,
    val metadata: MobileFormSubmissionMetadata? = null,
) {
    init {
        require(localId.isNotBlank()) { "localId is required" }
        require(deviceId.isNotBlank()) { "deviceId is required" }
        require(formId.isNotBlank()) { "formId is required" }
        require(revision >= 1) { "revision must be at least 1" }
        require(submittedAt.isNotBlank()) { "submittedAt is required" }
    }
}

data class MobileFormSubmissionMetadata(
    val appId: String?,
    val packageVersion: String?,
    val screenId: String?,
)

enum class OutboxRecordState {
    Pending,
    InFlight,
    Synced,
    Failed,
}

data class OfflineOutboxRecord(
    val submission: MobileFormSubmission,
    val state: OutboxRecordState,
    val queuedAtEpochMillis: Long,
    val updatedAtEpochMillis: Long,
    val attemptCount: Int = 0,
    val lastError: String? = null,
) {
    val localId: String
        get() = submission.localId
}

interface OfflineOutboxStore {
    fun enqueueSubmission(
        submission: MobileFormSubmission,
        queuedAtEpochMillis: Long,
    ): OfflineOutboxRecord

    fun getRecord(localId: String): OfflineOutboxRecord?

    fun pendingBatch(limit: Int): List<OfflineOutboxRecord>

    fun markInFlight(localIds: List<String>, updatedAtEpochMillis: Long): List<OfflineOutboxRecord>

    fun markSynced(localId: String, updatedAtEpochMillis: Long): OfflineOutboxRecord

    fun markFailed(localId: String, error: String, updatedAtEpochMillis: Long): OfflineOutboxRecord
}

class InMemoryOfflineOutboxStore : OfflineOutboxStore {
    private val recordsByLocalId = linkedMapOf<String, OfflineOutboxRecord>()

    override fun enqueueSubmission(
        submission: MobileFormSubmission,
        queuedAtEpochMillis: Long,
    ): OfflineOutboxRecord {
        require(submission.localId !in recordsByLocalId) {
            "Outbox submission ${submission.localId} is already queued"
        }
        val record = OfflineOutboxRecord(
            submission = submission,
            state = OutboxRecordState.Pending,
            queuedAtEpochMillis = queuedAtEpochMillis,
            updatedAtEpochMillis = queuedAtEpochMillis,
        )
        recordsByLocalId[submission.localId] = record
        return record
    }

    override fun getRecord(localId: String): OfflineOutboxRecord? =
        recordsByLocalId[localId]

    override fun pendingBatch(limit: Int): List<OfflineOutboxRecord> {
        require(limit > 0) { "limit must be positive" }
        return recordsByLocalId.values
            .filter { record -> record.state == OutboxRecordState.Pending || record.state == OutboxRecordState.Failed }
            .sortedBy { record -> record.queuedAtEpochMillis }
            .take(limit)
    }

    override fun markInFlight(localIds: List<String>, updatedAtEpochMillis: Long): List<OfflineOutboxRecord> =
        localIds.map { localId ->
            updateRecord(localId) { record ->
                record.copy(
                    state = OutboxRecordState.InFlight,
                    updatedAtEpochMillis = updatedAtEpochMillis,
                    lastError = null,
                )
            }
        }

    override fun markSynced(localId: String, updatedAtEpochMillis: Long): OfflineOutboxRecord =
        updateRecord(localId) { record ->
            record.copy(
                state = OutboxRecordState.Synced,
                updatedAtEpochMillis = updatedAtEpochMillis,
                lastError = null,
            )
        }

    override fun markFailed(localId: String, error: String, updatedAtEpochMillis: Long): OfflineOutboxRecord {
        require(error.isNotBlank()) { "error is required" }
        return updateRecord(localId) { record ->
            record.copy(
                state = OutboxRecordState.Failed,
                updatedAtEpochMillis = updatedAtEpochMillis,
                attemptCount = record.attemptCount + 1,
                lastError = error,
            )
        }
    }

    private fun updateRecord(
        localId: String,
        update: (OfflineOutboxRecord) -> OfflineOutboxRecord,
    ): OfflineOutboxRecord {
        val current = recordsByLocalId[localId]
            ?: throw IllegalArgumentException("Outbox submission $localId does not exist")
        val updated = update(current)
        recordsByLocalId[localId] = updated
        return updated
    }
}
