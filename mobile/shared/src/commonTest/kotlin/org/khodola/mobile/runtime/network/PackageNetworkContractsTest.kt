package org.khodola.mobile.runtime.network

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.coroutines.startCoroutine

class PackageNetworkContractsTest {
    @Test
    fun manifestRequestBuildsBackendPathAndQuery() {
        val request = PackageManifestRequest(
            tenantSlug = "tenant_demo",
            appId = "field_ops_app",
            channel = "staging",
        )

        assertEquals("/api/mobile/packages/manifest/", request.path)
        assertEquals(
            mapOf(
                "tenant" to "tenant_demo",
                "app_id" to "field_ops_app",
                "channel" to "staging",
            ),
            request.queryParameters,
        )
    }

    @Test
    fun manifestRequestDefaultsToDevChannel() {
        val request = PackageManifestRequest(
            tenantSlug = "tenant_demo",
            appId = "field_ops_app",
        )

        assertEquals("dev", request.channel)
        assertEquals("dev", request.queryParameters["channel"])
    }

    @Test
    fun packageDownloadRequestBuildsBackendPathAndQuery() {
        val request = PackageDownloadRequest(
            tenantSlug = "tenant_demo",
            packageId = "pkg_field_ops_001",
        )

        assertEquals("/api/mobile/packages/pkg_field_ops_001/download/", request.path)
        assertEquals(mapOf("tenant" to "tenant_demo"), request.queryParameters)
    }

    @Test
    fun syncRequestsBuildBackendPathsAndQueries() {
        val outbox = SyncOutboxRequest(
            tenantSlug = "demo",
            deviceId = "tablet-1",
            batchId = "batch-1",
            platform = "android",
            appVersion = "0.1.0",
            runtimeVersion = "0.1.0",
            submissions = listOf(
                SyncOutboxSubmission(
                    clientSubmissionId = "local-1",
                    formId = "patient_intake",
                    answers = emptyMap(),
                ),
            ),
        )
        val status = SyncStatusRequest(tenantSlug = "demo", deviceId = "tablet-1")

        assertEquals("/api/mobile/sync/outbox/", outbox.path)
        assertEquals(mapOf("tenant" to "demo"), outbox.queryParameters)
        assertEquals("/api/mobile/sync/status/", status.path)
        assertEquals(mapOf("tenant" to "demo", "device_id" to "tablet-1"), status.queryParameters)
    }

    @Test
    fun defaultHttpClientFetchesPackageAndSyncResponses() = runSuspendTest {
        val transport = RecordingTransport()
        val client = DefaultMobileRuntimeHttpClient(
            transport = transport,
            authorizationProvider = object : MobileRuntimeAuthorizationProvider {
                override fun authorizationHeader(tenantSlug: String): String = "Bearer token-for-$tenantSlug"
            },
        )

        val manifest = client.fetchActivePackageManifest(PackageManifestRequest("demo", "field_ops_app"))
        val download = client.downloadPackage(PackageDownloadRequest("demo", manifest.packageId))
        val sync = client.submitOutboxBatch(
            SyncOutboxRequest(
                tenantSlug = "demo",
                deviceId = "tablet-1",
                batchId = "batch-1",
                platform = "android",
                appVersion = "0.1.0",
                runtimeVersion = "0.1.0",
                submissions = listOf(
                    SyncOutboxSubmission(
                        clientSubmissionId = "local-1",
                        formId = "patient_intake",
                        answers = emptyMap(),
                    ),
                ),
            ),
        )

        assertEquals("pkg_field_ops_001", manifest.packageId)
        assertEquals("etag-1", download.etag)
        assertEquals("batch-1", sync.batch.batchId)
        assertEquals("accepted", sync.receipts.single().status)
        assertEquals("Bearer token-for-demo", transport.requests.first().headers["Authorization"])
        assertEquals(
            listOf(
                "/api/mobile/packages/manifest/",
                "/api/mobile/packages/pkg_field_ops_001/download/",
                "/api/mobile/sync/outbox/",
            ),
            transport.requests.map { request -> request.path },
        )
    }

    @Test
    fun requestsRejectBlankRequiredValues() {
        assertFailsWith<IllegalArgumentException> {
            PackageManifestRequest(tenantSlug = "", appId = "field_ops_app")
        }
        assertFailsWith<IllegalArgumentException> {
            PackageDownloadRequest(tenantSlug = "tenant_demo", packageId = "")
        }
    }

    @Test
    fun packageDownloadResultCarriesVerificationMetadata() {
        val manifest = PackageManifestMetadata(
            packageId = "pkg_field_ops_001",
            appId = "field_ops_app",
            appVersion = "0.1.0",
            channel = "dev",
            runtimeMinVersion = "0.1.0",
            runtimeMaxVersion = "0.1.0",
            hash = "sha256:abc",
            signature = "hmac-sha256:def",
        )

        val result = PackageDownloadResult(
            manifest = manifest,
            payloadJson = """{"package_id":"pkg_field_ops_001"}""",
            etag = "\"sha256:abc\"",
        )

        assertEquals("pkg_field_ops_001", result.manifest.packageId)
        assertEquals("sha256:abc", result.manifest.hash)
        assertEquals("hmac-sha256:def", result.manifest.signature)
        assertEquals("\"sha256:abc\"", result.etag)
    }
}

private class RecordingTransport : MobileRuntimeHttpTransport {
    val requests = mutableListOf<MobileRuntimeHttpRequest>()

    override suspend fun send(request: MobileRuntimeHttpRequest): MobileRuntimeHttpResponse {
        requests += request
        return when (request.path) {
            "/api/mobile/packages/manifest/" -> MobileRuntimeHttpResponse(200, manifestResponse())
            "/api/mobile/packages/pkg_field_ops_001/download/" -> MobileRuntimeHttpResponse(
                200,
                downloadResponse(),
                headers = mapOf("ETag" to "etag-1"),
            )
            "/api/mobile/sync/outbox/" -> MobileRuntimeHttpResponse(202, syncResponse())
            else -> MobileRuntimeHttpResponse(404, "{}")
        }
    }
}

private fun manifestResponse(): String =
    """
    {
      "manifest": {
        "package_id": "pkg_field_ops_001",
        "app_id": "field_ops_app",
        "app_version": "0.1.0",
        "channel": "dev",
        "runtime_min_version": "0.1.0",
        "runtime_max_version": "0.1.0",
        "hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "signature": "hmac-sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
      }
    }
    """.trimIndent()

private fun downloadResponse(): String =
    """
    {
      "manifest": {
        "package_id": "pkg_field_ops_001",
        "app_id": "field_ops_app",
        "app_version": "0.1.0",
        "channel": "dev",
        "runtime_min_version": "0.1.0",
        "runtime_max_version": "0.1.0",
        "hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "signature": "hmac-sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
      },
      "package": {"package_id": "pkg_field_ops_001"}
    }
    """.trimIndent()

private fun syncResponse(): String =
    """
    {
      "batch": {
        "batch_id": "batch-1",
        "status": "accepted",
        "session_id": "session-1",
        "accepted_count": 1,
        "duplicate_count": 0,
        "rejected_count": 0
      },
      "receipts": [
        {
          "client_submission_id": "local-1",
          "form_id": "patient_intake",
          "message": "Submission accepted.",
          "reason_code": "accepted",
          "status": "accepted",
          "submission_id": 1
        }
      ]
    }
    """.trimIndent()

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
