package org.khodola.mobile.runtime.verifier

import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.khodola.mobile.runtime.network.PackageDownloadResult
import org.khodola.mobile.runtime.network.PackageManifestMetadata
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson

data class PackageVerificationRequest(
    val manifest: PackageManifestMetadata,
    val payloadJson: String,
)

enum class PackageVerificationFailure {
    InvalidPayloadJson,
    PackageIdMismatch,
    AppIdMismatch,
    ChannelMismatch,
    InvalidHashFormat,
    HashMismatch,
    InvalidSignatureFormat,
    SignatureRejected,
}

data class PackageVerificationResult(
    val isValid: Boolean,
    val failures: Set<PackageVerificationFailure> = emptySet(),
    val expectedHash: String? = null,
    val actualHash: String? = null,
) {
    init {
        require(isValid || failures.isNotEmpty()) { "invalid verification results must include failures" }
    }
}

interface MobilePackageVerifier {
    fun verifyPackage(request: PackageVerificationRequest): PackageVerificationResult
}

interface PackagePayloadHasher {
    fun calculateHash(payloadJson: String): String
}

interface PackageSignatureVerifier {
    fun verifySignature(packageHash: String, signature: String): Boolean
}

class DefaultMobilePackageVerifier(
    private val payloadHasher: PackagePayloadHasher,
    private val signatureVerifier: PackageSignatureVerifier,
) : MobilePackageVerifier {
    override fun verifyPackage(request: PackageVerificationRequest): PackageVerificationResult {
        val manifest = request.manifest
        val actualHash = payloadHasher.calculateHash(request.payloadJson)
        val failures = mutableSetOf<PackageVerificationFailure>()
        val payloadMetadata = request.payloadJson.readPackageMetadata()

        if (payloadMetadata == null) {
            failures += PackageVerificationFailure.InvalidPayloadJson
        } else {
            if (payloadMetadata.packageId != manifest.packageId) {
                failures += PackageVerificationFailure.PackageIdMismatch
            }
            if (payloadMetadata.appId != manifest.appId) {
                failures += PackageVerificationFailure.AppIdMismatch
            }
            if (payloadMetadata.channel != manifest.channel) {
                failures += PackageVerificationFailure.ChannelMismatch
            }
        }
        if (!manifest.hash.isSha256Hash()) {
            failures += PackageVerificationFailure.InvalidHashFormat
        }
        if (manifest.hash != actualHash) {
            failures += PackageVerificationFailure.HashMismatch
        }
        if (!manifest.signature.isHmacSha256Signature()) {
            failures += PackageVerificationFailure.InvalidSignatureFormat
        } else if (!signatureVerifier.verifySignature(manifest.hash, manifest.signature)) {
            failures += PackageVerificationFailure.SignatureRejected
        }

        return PackageVerificationResult(
            isValid = failures.isEmpty(),
            failures = failures,
            expectedHash = manifest.hash,
            actualHash = actualHash,
        )
    }
}

fun PackageDownloadResult.toVerificationRequest(): PackageVerificationRequest =
    PackageVerificationRequest(
        manifest = manifest,
        payloadJson = payloadJson,
    )

private fun String.isSha256Hash(): Boolean =
    matches(Regex("^sha256:[a-f0-9]{64}$"))

private fun String.isHmacSha256Signature(): Boolean =
    matches(Regex("^hmac-sha256:[a-f0-9]{64}$"))

private data class PackagePayloadMetadata(
    val packageId: String?,
    val appId: String?,
    val channel: String?,
)

private fun String.readPackageMetadata(): PackagePayloadMetadata? =
    try {
        val payload = MobileRuntimeJson.parseToJsonElement(this).jsonObject
        PackagePayloadMetadata(
            packageId = payload["package_id"]?.jsonPrimitive?.contentOrNull,
            appId = payload["app_id"]?.jsonPrimitive?.contentOrNull,
            channel = payload["channel"]?.jsonPrimitive?.contentOrNull,
        )
    } catch (_: Exception) {
        null
    }
