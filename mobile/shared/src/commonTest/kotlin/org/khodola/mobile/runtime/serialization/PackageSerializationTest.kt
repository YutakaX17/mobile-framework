package org.khodola.mobile.runtime.serialization

import kotlin.test.Test
import kotlin.test.assertEquals

class PackageSerializationTest {
    @Test
    fun decodesPackageManifestResponse() {
        val manifest = decodePackageManifestResponse(
            """
            {
              "manifest": {
                "package_id": "pkg_field_ops_001",
                "app_id": "field_ops_app",
                "app_version": "0.1.0",
                "channel": "dev",
                "runtime_min_version": "0.1.0",
                "runtime_max_version": "0.1.0",
                "hash": "sha256:abc",
                "signature": "hmac-sha256:def",
                "status": "active"
              }
            }
            """.trimIndent()
        )

        assertEquals("pkg_field_ops_001", manifest.packageId)
        assertEquals("field_ops_app", manifest.appId)
        assertEquals("0.1.0", manifest.appVersion)
        assertEquals("dev", manifest.channel)
        assertEquals("sha256:abc", manifest.hash)
        assertEquals("hmac-sha256:def", manifest.signature)
    }

    @Test
    fun decodesPackageDownloadResponse() {
        val result = decodePackageDownloadResponse(
            """
            {
              "manifest": {
                "package_id": "pkg_field_ops_001",
                "app_id": "field_ops_app",
                "app_version": "0.1.0",
                "channel": "dev",
                "runtime_min_version": "0.1.0",
                "runtime_max_version": "0.1.0",
                "hash": "sha256:abc",
                "signature": "hmac-sha256:def"
              },
              "package": {
                "schema_version": "v1",
                "package_id": "pkg_field_ops_001"
              }
            }
            """.trimIndent(),
            etag = "\"sha256:abc\"",
        )

        assertEquals("pkg_field_ops_001", result.manifest.packageId)
        assertEquals("sha256:abc", result.manifest.hash)
        assertEquals("\"sha256:abc\"", result.etag)
        assertEquals("""{"schema_version":"v1","package_id":"pkg_field_ops_001"}""", result.payloadJson)
    }
}
