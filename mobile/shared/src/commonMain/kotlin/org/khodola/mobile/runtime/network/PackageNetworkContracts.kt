package org.khodola.mobile.runtime.network

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
