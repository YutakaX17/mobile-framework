package org.khodola.mobile.runtime.sync

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import org.khodola.mobile.runtime.outbox.OfflineOutboxRecord
import org.khodola.mobile.runtime.outbox.OfflineOutboxStore
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson

data class RuntimeSyncRule(
    val syncRuleId: String,
    val name: String,
    val entityType: String,
    val direction: String,
    val enabled: Boolean,
    val priority: Int,
    val pull: RuntimePullRule?,
    val push: RuntimePushRule?,
    val conflictPolicy: String,
    val conflict: RuntimeConflictRule?,
    val retryPolicy: RuntimeRetryPolicy?,
    val audit: RuntimeSyncAudit?,
)

data class RuntimePullRule(
    val strategy: String,
    val cursorField: String?,
    val includeDeleted: Boolean,
    val pageSize: Int,
    val filters: List<RuntimeSyncFilter>,
)

data class RuntimeSyncFilter(
    val field: String,
    val operator: String,
    val value: JsonElement,
)

data class RuntimePushRule(
    val operations: List<String>,
    val batchSize: Int,
    val idempotencyKeyFields: List<String>,
    val requiresNetwork: Boolean,
)

data class RuntimeConflictRule(
    val detectWith: List<String>,
    val manualReviewQueue: String?,
    val staleAfterSeconds: Int?,
)

data class RuntimeRetryPolicy(
    val maxAttempts: Int,
    val backoffSeconds: Int,
)

data class RuntimeSyncAudit(
    val logSuccess: Boolean,
    val logRejections: Boolean,
    val logConflicts: Boolean,
)

data class RuntimeSyncPlan(
    val rule: RuntimeSyncRule,
    val outboxRecords: List<OfflineOutboxRecord>,
) {
    val canPush: Boolean
        get() = rule.enabled && rule.push != null && outboxRecords.isNotEmpty()
}

interface RuntimeSyncEngine {
    fun planPush(rule: RuntimeSyncRule, outboxStore: OfflineOutboxStore): RuntimeSyncPlan
}

class DefaultRuntimeSyncEngine : RuntimeSyncEngine {
    override fun planPush(rule: RuntimeSyncRule, outboxStore: OfflineOutboxStore): RuntimeSyncPlan {
        val pushRule = rule.push
        if (!rule.enabled || pushRule == null || "submit" !in pushRule.operations) {
            return RuntimeSyncPlan(rule = rule, outboxRecords = emptyList())
        }

        val maxAttempts = rule.retryPolicy?.maxAttempts ?: DEFAULT_MAX_ATTEMPTS
        val records = outboxStore
            .pendingBatch(pushRule.batchSize)
            .filter { record -> record.attemptCount < maxAttempts }

        return RuntimeSyncPlan(rule = rule, outboxRecords = records)
    }
}

fun decodeRuntimeSyncRulesFromPackagePayload(payloadJson: String): List<RuntimeSyncRule> =
    MobileRuntimeJson
        .decodeFromString<PackageSyncRulesEnvelopeDto>(payloadJson)
        .syncRules
        .map { rule -> rule.toRuntimeSyncRule() }
        .sortedWith(compareBy<RuntimeSyncRule> { rule -> rule.priority }.thenBy { rule -> rule.syncRuleId })

private const val DEFAULT_MAX_ATTEMPTS = 5

@Serializable
private data class PackageSyncRulesEnvelopeDto(
    @SerialName("sync_rules")
    val syncRules: List<RuntimeSyncRuleDto> = emptyList(),
)

@Serializable
private data class RuntimeSyncRuleDto(
    @SerialName("sync_rule_id")
    val syncRuleId: String,
    val name: String,
    @SerialName("entity_type")
    val entityType: String,
    val direction: String,
    val enabled: Boolean = true,
    val priority: Int = 100,
    val pull: RuntimePullRuleDto? = null,
    val push: RuntimePushRuleDto? = null,
    @SerialName("conflict_policy")
    val conflictPolicy: String,
    val conflict: RuntimeConflictRuleDto? = null,
    @SerialName("retry_policy")
    val retryPolicy: RuntimeRetryPolicyDto? = null,
    val audit: RuntimeSyncAuditDto? = null,
) {
    fun toRuntimeSyncRule(): RuntimeSyncRule =
        RuntimeSyncRule(
            syncRuleId = syncRuleId,
            name = name,
            entityType = entityType,
            direction = direction,
            enabled = enabled,
            priority = priority,
            pull = pull?.toRuntimePullRule(),
            push = push?.toRuntimePushRule(),
            conflictPolicy = conflictPolicy,
            conflict = conflict?.toRuntimeConflictRule(),
            retryPolicy = retryPolicy?.toRuntimeRetryPolicy(),
            audit = audit?.toRuntimeSyncAudit(),
        )
}

@Serializable
private data class RuntimePullRuleDto(
    val strategy: String,
    @SerialName("cursor_field")
    val cursorField: String? = null,
    @SerialName("include_deleted")
    val includeDeleted: Boolean = true,
    @SerialName("page_size")
    val pageSize: Int = 100,
    val filters: List<RuntimeSyncFilterDto> = emptyList(),
) {
    fun toRuntimePullRule(): RuntimePullRule =
        RuntimePullRule(
            strategy = strategy,
            cursorField = cursorField,
            includeDeleted = includeDeleted,
            pageSize = pageSize,
            filters = filters.map { filter -> filter.toRuntimeFilter() },
        )
}

@Serializable
private data class RuntimeSyncFilterDto(
    val field: String,
    val operator: String,
    val value: JsonElement,
) {
    fun toRuntimeFilter(): RuntimeSyncFilter =
        RuntimeSyncFilter(field = field, operator = operator, value = value)
}

@Serializable
private data class RuntimePushRuleDto(
    val operations: List<String>,
    @SerialName("batch_size")
    val batchSize: Int = 50,
    @SerialName("idempotency_key_fields")
    val idempotencyKeyFields: List<String> = emptyList(),
    @SerialName("requires_network")
    val requiresNetwork: Boolean = true,
) {
    fun toRuntimePushRule(): RuntimePushRule =
        RuntimePushRule(
            operations = operations,
            batchSize = batchSize,
            idempotencyKeyFields = idempotencyKeyFields,
            requiresNetwork = requiresNetwork,
        )
}

@Serializable
private data class RuntimeConflictRuleDto(
    @SerialName("detect_with")
    val detectWith: List<String> = emptyList(),
    @SerialName("manual_review_queue")
    val manualReviewQueue: String? = null,
    @SerialName("stale_after_seconds")
    val staleAfterSeconds: Int? = null,
) {
    fun toRuntimeConflictRule(): RuntimeConflictRule =
        RuntimeConflictRule(
            detectWith = detectWith,
            manualReviewQueue = manualReviewQueue,
            staleAfterSeconds = staleAfterSeconds,
        )
}

@Serializable
private data class RuntimeRetryPolicyDto(
    @SerialName("max_attempts")
    val maxAttempts: Int = DEFAULT_MAX_ATTEMPTS,
    @SerialName("backoff_seconds")
    val backoffSeconds: Int = 30,
) {
    fun toRuntimeRetryPolicy(): RuntimeRetryPolicy =
        RuntimeRetryPolicy(maxAttempts = maxAttempts, backoffSeconds = backoffSeconds)
}

@Serializable
private data class RuntimeSyncAuditDto(
    @SerialName("log_success")
    val logSuccess: Boolean = false,
    @SerialName("log_rejections")
    val logRejections: Boolean = true,
    @SerialName("log_conflicts")
    val logConflicts: Boolean = true,
) {
    fun toRuntimeSyncAudit(): RuntimeSyncAudit =
        RuntimeSyncAudit(
            logSuccess = logSuccess,
            logRejections = logRejections,
            logConflicts = logConflicts,
        )
}
