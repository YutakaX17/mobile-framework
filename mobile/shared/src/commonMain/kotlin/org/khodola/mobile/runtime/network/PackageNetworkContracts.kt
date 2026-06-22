package org.khodola.mobile.runtime.network

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.JsonElement
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson
import org.khodola.mobile.runtime.serialization.decodePackageDownloadResponse
import org.khodola.mobile.runtime.serialization.decodePackageManifestResponse

data class PackageManifestRequest(
    val tenantSlug: String,
    val appId: String,
    val channel: String = "dev",
) {
    init {
        require(tenantSlug.isNotBlank()) { "tenantSlug is required" }
        require(appId.isNotBlank()) { "appId is required" }
        require(channel.isNotBlank()) { "channel is required" }
    }

    val path: String = "/api/mobile/packages/manifest/"

    val queryParameters: Map<String, String>
        get() = mapOf(
            "tenant" to tenantSlug,
            "app_id" to appId,
            "channel" to channel,
        )
}

data class PackageDownloadRequest(
    val tenantSlug: String,
    val packageId: String,
) {
    init {
        require(tenantSlug.isNotBlank()) { "tenantSlug is required" }
        require(packageId.isNotBlank()) { "packageId is required" }
    }

    val path: String
        get() = "/api/mobile/packages/$packageId/download/"

    val queryParameters: Map<String, String>
        get() = mapOf("tenant" to tenantSlug)
}

data class PackageManifestMetadata(
    val packageId: String,
    val appId: String,
    val appVersion: String,
    val channel: String,
    val runtimeMinVersion: String,
    val runtimeMaxVersion: String,
    val hash: String,
    val signature: String,
)

data class PackageDownloadResult(
    val manifest: PackageManifestMetadata,
    val payloadJson: String,
    val etag: String?,
)

interface MobileRuntimeNetworkClient {
    suspend fun fetchActivePackageManifest(request: PackageManifestRequest): PackageManifestMetadata

    suspend fun downloadPackage(request: PackageDownloadRequest): PackageDownloadResult
}

data class SyncDeviceRegistrationRequest(
    val tenantSlug: String,
    val deviceId: String,
    val platform: String,
    val appVersion: String,
    val runtimeVersion: String,
) {
    init {
        require(tenantSlug.isNotBlank()) { "tenantSlug is required" }
        require(deviceId.isNotBlank()) { "deviceId is required" }
        require(platform.isNotBlank()) { "platform is required" }
    }

    val path: String = "/api/mobile/sync/devices/"

    val queryParameters: Map<String, String>
        get() = mapOf("tenant" to tenantSlug)
}

data class SyncOutboxSubmission(
    val clientSubmissionId: String,
    val formId: String,
    val answers: Map<String, JsonElement>,
) {
    init {
        require(clientSubmissionId.isNotBlank()) { "clientSubmissionId is required" }
        require(formId.isNotBlank()) { "formId is required" }
    }
}

data class SyncOutboxRequest(
    val tenantSlug: String,
    val deviceId: String,
    val batchId: String,
    val platform: String,
    val appVersion: String,
    val runtimeVersion: String,
    val submissions: List<SyncOutboxSubmission>,
) {
    init {
        require(tenantSlug.isNotBlank()) { "tenantSlug is required" }
        require(deviceId.isNotBlank()) { "deviceId is required" }
        require(batchId.isNotBlank()) { "batchId is required" }
        require(platform.isNotBlank()) { "platform is required" }
        require(submissions.isNotEmpty()) { "submissions are required" }
    }

    val path: String = "/api/mobile/sync/outbox/"

    val queryParameters: Map<String, String>
        get() = mapOf("tenant" to tenantSlug)
}

data class SyncStatusRequest(
    val tenantSlug: String,
    val deviceId: String? = null,
) {
    init {
        require(tenantSlug.isNotBlank()) { "tenantSlug is required" }
        if (deviceId != null) {
            require(deviceId.isNotBlank()) { "deviceId must not be blank" }
        }
    }

    val path: String = "/api/mobile/sync/status/"

    val queryParameters: Map<String, String>
        get() = buildMap {
            put("tenant", tenantSlug)
            if (deviceId != null) {
                put("device_id", deviceId)
            }
        }
}

data class SyncSubmissionReceipt(
    val clientSubmissionId: String,
    val formId: String,
    val message: String,
    val reasonCode: String,
    val status: String,
    val submissionId: Long?,
) {
    val isAccepted: Boolean
        get() = status == "accepted" || status == "duplicate"
}

data class SyncBatchSummary(
    val batchId: String,
    val status: String,
    val sessionId: String,
    val acceptedCount: Int,
    val duplicateCount: Int,
    val rejectedCount: Int,
    val receipts: List<SyncSubmissionReceipt> = emptyList(),
)

data class SyncDeviceSummary(
    val deviceId: String,
    val platform: String,
    val appVersion: String,
    val runtimeVersion: String,
    val status: String,
)

data class SyncOutboxResult(
    val batch: SyncBatchSummary,
    val receipts: List<SyncSubmissionReceipt>,
)

data class SyncStatusResult(
    val devices: List<SyncDeviceSummary>,
    val batches: List<SyncBatchSummary>,
)

interface MobileRuntimeSyncClient {
    suspend fun registerDevice(request: SyncDeviceRegistrationRequest): SyncDeviceSummary

    suspend fun submitOutboxBatch(request: SyncOutboxRequest): SyncOutboxResult

    suspend fun fetchSyncStatus(request: SyncStatusRequest): SyncStatusResult
}

enum class MobileRuntimeHttpMethod {
    Get,
    Post,
}

data class MobileRuntimeHttpRequest(
    val method: MobileRuntimeHttpMethod,
    val path: String,
    val queryParameters: Map<String, String> = emptyMap(),
    val headers: Map<String, String> = emptyMap(),
    val body: String? = null,
) {
    init {
        require(path.startsWith("/")) { "path must start with /" }
    }
}

data class MobileRuntimeHttpResponse(
    val statusCode: Int,
    val body: String,
    val headers: Map<String, String> = emptyMap(),
) {
    val isSuccess: Boolean
        get() = statusCode in 200..299
}

interface MobileRuntimeHttpTransport {
    suspend fun send(request: MobileRuntimeHttpRequest): MobileRuntimeHttpResponse
}

interface MobileRuntimeAuthorizationProvider {
    fun authorizationHeader(tenantSlug: String): String?
}

class DefaultMobileRuntimeHttpClient(
    private val transport: MobileRuntimeHttpTransport,
    private val authorizationProvider: MobileRuntimeAuthorizationProvider? = null,
) : MobileRuntimeNetworkClient, MobileRuntimeSyncClient {
    override suspend fun fetchActivePackageManifest(request: PackageManifestRequest): PackageManifestMetadata {
        val response = transport.send(
            MobileRuntimeHttpRequest(
                method = MobileRuntimeHttpMethod.Get,
                path = request.path,
                queryParameters = request.queryParameters,
                headers = authHeaders(request.tenantSlug),
            ),
        )
        requireSuccess(response, "fetch package manifest")
        return decodePackageManifestResponse(response.body)
    }

    override suspend fun downloadPackage(request: PackageDownloadRequest): PackageDownloadResult {
        val response = transport.send(
            MobileRuntimeHttpRequest(
                method = MobileRuntimeHttpMethod.Get,
                path = request.path,
                queryParameters = request.queryParameters,
                headers = authHeaders(request.tenantSlug),
            ),
        )
        requireSuccess(response, "download package")
        return decodePackageDownloadResponse(response.body, etag = response.headers["ETag"] ?: response.headers["etag"])
    }

    override suspend fun registerDevice(request: SyncDeviceRegistrationRequest): SyncDeviceSummary {
        val response = transport.send(
            MobileRuntimeHttpRequest(
                method = MobileRuntimeHttpMethod.Post,
                path = request.path,
                queryParameters = request.queryParameters,
                headers = JSON_HEADERS + authHeaders(request.tenantSlug),
                body = MobileRuntimeJson.encodeToString(SyncDeviceRegistrationRequestDto.fromRequest(request)),
            ),
        )
        requireSuccess(response, "register sync device")
        return MobileRuntimeJson.decodeFromString<SyncDeviceRegistrationResponseDto>(response.body).device.toSummary()
    }

    override suspend fun submitOutboxBatch(request: SyncOutboxRequest): SyncOutboxResult {
        val response = transport.send(
            MobileRuntimeHttpRequest(
                method = MobileRuntimeHttpMethod.Post,
                path = request.path,
                queryParameters = request.queryParameters,
                headers = JSON_HEADERS + authHeaders(request.tenantSlug),
                body = MobileRuntimeJson.encodeToString(SyncOutboxRequestDto.fromRequest(request)),
            ),
        )
        requireSuccess(response, "submit sync outbox")
        val dto = MobileRuntimeJson.decodeFromString<SyncOutboxResponseDto>(response.body)
        return SyncOutboxResult(
            batch = dto.batch.toSummary(receipts = dto.receipts.map { receipt -> receipt.toReceipt() }),
            receipts = dto.receipts.map { receipt -> receipt.toReceipt() },
        )
    }

    override suspend fun fetchSyncStatus(request: SyncStatusRequest): SyncStatusResult {
        val response = transport.send(
            MobileRuntimeHttpRequest(
                method = MobileRuntimeHttpMethod.Get,
                path = request.path,
                queryParameters = request.queryParameters,
                headers = authHeaders(request.tenantSlug),
            ),
        )
        requireSuccess(response, "fetch sync status")
        val dto = MobileRuntimeJson.decodeFromString<SyncStatusResponseDto>(response.body)
        return SyncStatusResult(
            devices = dto.devices.map { device -> device.toSummary() },
            batches = dto.batches.map { batch -> batch.toSummary(receipts = batch.results.map { result -> result.toReceipt() }) },
        )
    }

    private fun requireSuccess(response: MobileRuntimeHttpResponse, operation: String) {
        require(response.isSuccess) {
            "Failed to $operation: HTTP ${response.statusCode}"
        }
    }

    private fun authHeaders(tenantSlug: String): Map<String, String> =
        authorizationProvider
            ?.authorizationHeader(tenantSlug)
            ?.let { header -> mapOf("Authorization" to header) }
            ?: emptyMap()
}

private val JSON_HEADERS = mapOf("Content-Type" to "application/json")

@Serializable
private data class SyncDeviceRegistrationRequestDto(
    @SerialName("device_id")
    val deviceId: String,
    val platform: String,
    @SerialName("app_version")
    val appVersion: String,
    @SerialName("runtime_version")
    val runtimeVersion: String,
) {
    companion object {
        fun fromRequest(request: SyncDeviceRegistrationRequest): SyncDeviceRegistrationRequestDto =
            SyncDeviceRegistrationRequestDto(
                deviceId = request.deviceId,
                platform = request.platform,
                appVersion = request.appVersion,
                runtimeVersion = request.runtimeVersion,
            )
    }
}

@Serializable
private data class SyncOutboxRequestDto(
    @SerialName("device_id")
    val deviceId: String,
    @SerialName("batch_id")
    val batchId: String,
    val platform: String,
    @SerialName("app_version")
    val appVersion: String,
    @SerialName("runtime_version")
    val runtimeVersion: String,
    val submissions: List<SyncOutboxSubmissionDto>,
) {
    companion object {
        fun fromRequest(request: SyncOutboxRequest): SyncOutboxRequestDto =
            SyncOutboxRequestDto(
                deviceId = request.deviceId,
                batchId = request.batchId,
                platform = request.platform,
                appVersion = request.appVersion,
                runtimeVersion = request.runtimeVersion,
                submissions = request.submissions.map { submission ->
                    SyncOutboxSubmissionDto(
                        clientSubmissionId = submission.clientSubmissionId,
                        formId = submission.formId,
                        answers = submission.answers,
                    )
                },
            )
    }
}

@Serializable
private data class SyncOutboxSubmissionDto(
    @SerialName("client_submission_id")
    val clientSubmissionId: String,
    @SerialName("form_id")
    val formId: String,
    val answers: Map<String, JsonElement>,
)

@Serializable
private data class SyncDeviceRegistrationResponseDto(
    val device: SyncDeviceDto,
)

@Serializable
private data class SyncOutboxResponseDto(
    val batch: SyncBatchDto,
    val receipts: List<SyncSubmissionReceiptDto>,
)

@Serializable
private data class SyncStatusResponseDto(
    val devices: List<SyncDeviceDto> = emptyList(),
    val batches: List<SyncBatchWithResultsDto> = emptyList(),
)

@Serializable
private data class SyncDeviceDto(
    @SerialName("device_id")
    val deviceId: String,
    val platform: String,
    @SerialName("app_version")
    val appVersion: String = "",
    @SerialName("runtime_version")
    val runtimeVersion: String = "",
    val status: String,
) {
    fun toSummary(): SyncDeviceSummary =
        SyncDeviceSummary(
            deviceId = deviceId,
            platform = platform,
            appVersion = appVersion,
            runtimeVersion = runtimeVersion,
            status = status,
        )
}

@Serializable
private data class SyncBatchDto(
    @SerialName("batch_id")
    val batchId: String,
    val status: String,
    @SerialName("session_id")
    val sessionId: String,
    @SerialName("accepted_count")
    val acceptedCount: Int = 0,
    @SerialName("duplicate_count")
    val duplicateCount: Int = 0,
    @SerialName("rejected_count")
    val rejectedCount: Int = 0,
) {
    fun toSummary(receipts: List<SyncSubmissionReceipt> = emptyList()): SyncBatchSummary =
        SyncBatchSummary(
            batchId = batchId,
            status = status,
            sessionId = sessionId,
            acceptedCount = acceptedCount,
            duplicateCount = duplicateCount,
            rejectedCount = rejectedCount,
            receipts = receipts,
        )
}

@Serializable
private data class SyncBatchWithResultsDto(
    @SerialName("batch_id")
    val batchId: String,
    val status: String,
    @SerialName("session_id")
    val sessionId: String,
    @SerialName("accepted_count")
    val acceptedCount: Int = 0,
    @SerialName("duplicate_count")
    val duplicateCount: Int = 0,
    @SerialName("rejected_count")
    val rejectedCount: Int = 0,
    val results: List<SyncSubmissionReceiptDto> = emptyList(),
) {
    fun toSummary(receipts: List<SyncSubmissionReceipt> = emptyList()): SyncBatchSummary =
        SyncBatchSummary(
            batchId = batchId,
            status = status,
            sessionId = sessionId,
            acceptedCount = acceptedCount,
            duplicateCount = duplicateCount,
            rejectedCount = rejectedCount,
            receipts = receipts,
        )
}

@Serializable
private data class SyncSubmissionReceiptDto(
    @SerialName("client_submission_id")
    val clientSubmissionId: String,
    @SerialName("form_id")
    val formId: String = "",
    val message: String = "",
    @SerialName("reason_code")
    val reasonCode: String = "",
    val status: String,
    @SerialName("submission_id")
    val submissionId: Long? = null,
) {
    fun toReceipt(): SyncSubmissionReceipt =
        SyncSubmissionReceipt(
            clientSubmissionId = clientSubmissionId,
            formId = formId,
            message = message,
            reasonCode = reasonCode,
            status = status,
            submissionId = submissionId,
        )
}
