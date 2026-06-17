package org.khodola.mobile.runtime.serialization

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import org.khodola.mobile.runtime.network.PackageDownloadResult
import org.khodola.mobile.runtime.network.PackageManifestMetadata

val MobileRuntimeJson: Json = Json {
    ignoreUnknownKeys = true
    explicitNulls = false
}

@Serializable
data class PackageManifestResponseDto(
    val manifest: PackageManifestDto,
)

@Serializable
data class PackageDownloadResponseDto(
    val manifest: PackageManifestDto,
    @SerialName("package")
    val packagePayload: JsonElement,
)

@Serializable
data class PackageManifestDto(
    @SerialName("package_id")
    val packageId: String,
    @SerialName("app_id")
    val appId: String,
    @SerialName("app_version")
    val appVersion: String,
    val channel: String,
    @SerialName("runtime_min_version")
    val runtimeMinVersion: String,
    @SerialName("runtime_max_version")
    val runtimeMaxVersion: String,
    val hash: String,
    val signature: String,
) {
    fun toMetadata(): PackageManifestMetadata =
        PackageManifestMetadata(
            packageId = packageId,
            appId = appId,
            appVersion = appVersion,
            channel = channel,
            runtimeMinVersion = runtimeMinVersion,
            runtimeMaxVersion = runtimeMaxVersion,
            hash = hash,
            signature = signature,
        )
}

fun decodePackageManifestResponse(json: String): PackageManifestMetadata =
    MobileRuntimeJson.decodeFromString<PackageManifestResponseDto>(json).manifest.toMetadata()

fun decodePackageDownloadResponse(json: String, etag: String? = null): PackageDownloadResult {
    val response = MobileRuntimeJson.decodeFromString<PackageDownloadResponseDto>(json)
    return PackageDownloadResult(
        manifest = response.manifest.toMetadata(),
        payloadJson = response.packagePayload.toString(),
        etag = etag,
    )
}
