package org.khodola.mobile.runtime.outbox

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.JsonElement
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson
import org.khodola.mobile.runtime.storage.RuntimeKeyValueStore

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

class KeyValueOfflineOutboxStore(
    private val keyValueStore: RuntimeKeyValueStore,
    private val namespace: String = "runtime:outbox",
) : OfflineOutboxStore {
    override fun enqueueSubmission(
        submission: MobileFormSubmission,
        queuedAtEpochMillis: Long,
    ): OfflineOutboxRecord {
        val records = readRecords().toMutableMap()
        require(submission.localId !in records) {
            "Outbox submission ${submission.localId} is already queued"
        }
        val record = OfflineOutboxRecord(
            submission = submission,
            state = OutboxRecordState.Pending,
            queuedAtEpochMillis = queuedAtEpochMillis,
            updatedAtEpochMillis = queuedAtEpochMillis,
        )
        records[submission.localId] = record
        writeRecords(records)
        return record
    }

    override fun getRecord(localId: String): OfflineOutboxRecord? =
        readRecords()[localId]

    override fun pendingBatch(limit: Int): List<OfflineOutboxRecord> {
        require(limit > 0) { "limit must be positive" }
        return readRecords().values
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
        val records = readRecords().toMutableMap()
        val current = records[localId]
            ?: throw IllegalArgumentException("Outbox submission $localId does not exist")
        val updated = update(current)
        records[localId] = updated
        writeRecords(records)
        return updated
    }

    private fun readRecords(): Map<String, OfflineOutboxRecord> =
        keyValueStore.getString(namespace)
            ?.let { encoded -> MobileRuntimeJson.decodeFromString(OutboxStoreEnvelopeDto.serializer(), encoded) }
            ?.records
            ?.associate { dto -> dto.submission.localId to dto.toRecord() }
            ?: emptyMap()

    private fun writeRecords(records: Map<String, OfflineOutboxRecord>) {
        keyValueStore.putString(
            namespace,
            MobileRuntimeJson.encodeToString(
                OutboxStoreEnvelopeDto(
                    records = records.values
                        .sortedBy { record -> record.queuedAtEpochMillis }
                        .map { record -> OfflineOutboxRecordDto.fromRecord(record) },
                ),
            ),
        )
    }
}

@Serializable
private data class OutboxStoreEnvelopeDto(
    val records: List<OfflineOutboxRecordDto> = emptyList(),
)

@Serializable
private data class OfflineOutboxRecordDto(
    val submission: MobileFormSubmissionDto,
    val state: String,
    @SerialName("queued_at_epoch_millis")
    val queuedAtEpochMillis: Long,
    @SerialName("updated_at_epoch_millis")
    val updatedAtEpochMillis: Long,
    @SerialName("attempt_count")
    val attemptCount: Int = 0,
    @SerialName("last_error")
    val lastError: String? = null,
) {
    fun toRecord(): OfflineOutboxRecord =
        OfflineOutboxRecord(
            submission = submission.toSubmission(),
            state = OutboxRecordState.valueOf(state),
            queuedAtEpochMillis = queuedAtEpochMillis,
            updatedAtEpochMillis = updatedAtEpochMillis,
            attemptCount = attemptCount,
            lastError = lastError,
        )

    companion object {
        fun fromRecord(record: OfflineOutboxRecord): OfflineOutboxRecordDto =
            OfflineOutboxRecordDto(
                submission = MobileFormSubmissionDto.fromSubmission(record.submission),
                state = record.state.name,
                queuedAtEpochMillis = record.queuedAtEpochMillis,
                updatedAtEpochMillis = record.updatedAtEpochMillis,
                attemptCount = record.attemptCount,
                lastError = record.lastError,
            )
    }
}

@Serializable
private data class MobileFormSubmissionDto(
    @SerialName("local_id")
    val localId: String,
    @SerialName("device_id")
    val deviceId: String,
    @SerialName("form_id")
    val formId: String,
    val revision: Int,
    @SerialName("submitted_at")
    val submittedAt: String,
    val answers: Map<String, JsonElement>,
    val metadata: MobileFormSubmissionMetadataDto? = null,
) {
    fun toSubmission(): MobileFormSubmission =
        MobileFormSubmission(
            localId = localId,
            deviceId = deviceId,
            formId = formId,
            revision = revision,
            submittedAt = submittedAt,
            answers = answers,
            metadata = metadata?.toMetadata(),
        )

    companion object {
        fun fromSubmission(submission: MobileFormSubmission): MobileFormSubmissionDto =
            MobileFormSubmissionDto(
                localId = submission.localId,
                deviceId = submission.deviceId,
                formId = submission.formId,
                revision = submission.revision,
                submittedAt = submission.submittedAt,
                answers = submission.answers,
                metadata = submission.metadata?.let { metadata -> MobileFormSubmissionMetadataDto.fromMetadata(metadata) },
            )
    }
}

@Serializable
private data class MobileFormSubmissionMetadataDto(
    @SerialName("app_id")
    val appId: String? = null,
    @SerialName("package_version")
    val packageVersion: String? = null,
    @SerialName("screen_id")
    val screenId: String? = null,
) {
    fun toMetadata(): MobileFormSubmissionMetadata =
        MobileFormSubmissionMetadata(
            appId = appId,
            packageVersion = packageVersion,
            screenId = screenId,
        )

    companion object {
        fun fromMetadata(metadata: MobileFormSubmissionMetadata): MobileFormSubmissionMetadataDto =
            MobileFormSubmissionMetadataDto(
                appId = metadata.appId,
                packageVersion = metadata.packageVersion,
                screenId = metadata.screenId,
            )
    }
}
