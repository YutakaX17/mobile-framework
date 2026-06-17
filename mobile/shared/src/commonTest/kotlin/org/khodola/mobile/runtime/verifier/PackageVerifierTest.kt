package org.khodola.mobile.runtime.verifier

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import org.khodola.mobile.runtime.network.PackageDownloadResult
import org.khodola.mobile.runtime.network.PackageManifestMetadata

class PackageVerifierTest {
    @Test
    fun acceptsPackageWhenHashAndSignatureMatch() {
        val payload = packagePayload()
        val verifier = verifierFor(payloadHash = VALID_HASH, signatureAccepted = true)
        val result = verifier.verifyPackage(packageRequest(payload))

        assertTrue(result.isValid)
        assertEquals(emptySet(), result.failures)
        assertEquals(VALID_HASH, result.expectedHash)
        assertEquals(VALID_HASH, result.actualHash)
    }

    @Test
    fun rejectsHashMismatch() {
        val payload = packagePayload()
        val verifier = verifierFor(payloadHash = DIFFERENT_HASH, signatureAccepted = true)
        val result = verifier.verifyPackage(packageRequest(payload))

        assertFalse(result.isValid)
        assertTrue(PackageVerificationFailure.HashMismatch in result.failures)
        assertEquals(VALID_HASH, result.expectedHash)
        assertEquals(DIFFERENT_HASH, result.actualHash)
    }

    @Test
    fun rejectsInvalidHashAndSignatureFormats() {
        val payload = packagePayload()
        val verifier = verifierFor(payloadHash = VALID_HASH, signatureAccepted = true)
        val result = verifier.verifyPackage(
            packageRequest(
                payloadJson = payload,
                manifest = packageManifest(
                    hash = "sha256:not-valid",
                    signature = "sig:not-valid",
                ),
            ),
        )

        assertFalse(result.isValid)
        assertTrue(PackageVerificationFailure.InvalidHashFormat in result.failures)
        assertTrue(PackageVerificationFailure.InvalidSignatureFormat in result.failures)
    }

    @Test
    fun rejectsSignatureFailure() {
        val payload = packagePayload()
        val verifier = verifierFor(payloadHash = VALID_HASH, signatureAccepted = false)
        val result = verifier.verifyPackage(packageRequest(payload))

        assertFalse(result.isValid)
        assertTrue(PackageVerificationFailure.SignatureRejected in result.failures)
    }

    @Test
    fun rejectsPayloadMetadataMismatch() {
        val payload = packagePayload(packageId = "pkg_other", appId = "other-app", channel = "staging")
        val verifier = verifierFor(payloadHash = VALID_HASH, signatureAccepted = true)
        val result = verifier.verifyPackage(packageRequest(payload))

        assertFalse(result.isValid)
        assertTrue(PackageVerificationFailure.PackageIdMismatch in result.failures)
        assertTrue(PackageVerificationFailure.AppIdMismatch in result.failures)
        assertTrue(PackageVerificationFailure.ChannelMismatch in result.failures)
    }

    @Test
    fun convertsDownloadResultToVerificationRequest() {
        val download = PackageDownloadResult(
            manifest = packageManifest(),
            payloadJson = packagePayload(),
            etag = "\"$VALID_HASH\"",
        )

        val request = download.toVerificationRequest()

        assertEquals(download.manifest, request.manifest)
        assertEquals(download.payloadJson, request.payloadJson)
    }

    private fun verifierFor(
        payloadHash: String,
        signatureAccepted: Boolean,
    ): DefaultMobilePackageVerifier =
        DefaultMobilePackageVerifier(
            payloadHasher = object : PackagePayloadHasher {
                override fun calculateHash(payloadJson: String): String = payloadHash
            },
            signatureVerifier = object : PackageSignatureVerifier {
                override fun verifySignature(packageHash: String, signature: String): Boolean =
                    signatureAccepted
            },
        )
}

private const val VALID_HASH =
    "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
private const val DIFFERENT_HASH =
    "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
private const val VALID_SIGNATURE =
    "hmac-sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"

private fun packageRequest(
    payloadJson: String,
    manifest: PackageManifestMetadata = packageManifest(),
): PackageVerificationRequest =
    PackageVerificationRequest(
        manifest = manifest,
        payloadJson = payloadJson,
    )

private fun packageManifest(
    hash: String = VALID_HASH,
    signature: String = VALID_SIGNATURE,
): PackageManifestMetadata =
    PackageManifestMetadata(
        packageId = "pkg_field_ops_001",
        appId = "field-ops",
        appVersion = "1.0.0",
        channel = "dev",
        runtimeMinVersion = "0.1.0",
        runtimeMaxVersion = "0.9.0",
        hash = hash,
        signature = signature,
    )

private fun packagePayload(
    packageId: String = "pkg_field_ops_001",
    appId: String = "field-ops",
    channel: String = "dev",
): String =
    """{"package_id":"$packageId","app_id":"$appId","channel":"$channel","screens":[]}"""
