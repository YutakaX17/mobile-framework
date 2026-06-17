package org.khodola.mobile.runtime.network

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

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
