package org.khodola.mobile.runtime.storage

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue
import org.khodola.mobile.runtime.network.PackageDownloadResult
import org.khodola.mobile.runtime.network.PackageManifestMetadata

class PackageLocalStoreTest {
    @Test
    fun savesAndReadsCachedPackage() {
        val store = InMemoryPackageLocalStore()
        val download = packageDownload(packageId = "pkg_field_ops_001")

        val record = store.savePackage(
            tenantSlug = "acme",
            download = download,
            cachedAtEpochMillis = 1_720_000_000_000,
        )

        assertEquals("pkg_field_ops_001", record.packageId)
        assertEquals("field-ops", record.appId)
        assertEquals("{\"screens\":[]}", record.payloadJson)
        assertFalse(record.isActive)
        assertEquals(record, store.getPackage("acme", "pkg_field_ops_001"))
    }

    @Test
    fun activatesOnePackagePerTenantAppAndChannel() {
        val store = InMemoryPackageLocalStore()
        store.savePackage("acme", packageDownload("pkg_v1", appVersion = "1.0.0"), 100)
        store.savePackage("acme", packageDownload("pkg_v2", appVersion = "1.1.0"), 200)

        val active = store.activatePackage(
            tenantSlug = "acme",
            packageId = "pkg_v2",
            activatedAtEpochMillis = 300,
        )

        assertEquals("pkg_v2", active.packageId)
        assertEquals(300, active.activeAtEpochMillis)
        assertEquals("pkg_v2", store.getActivePackage("acme", "field-ops", "dev")?.packageId)
        assertNull(store.getPackage("acme", "pkg_v1")?.activeAtEpochMillis)
    }

    @Test
    fun isolatesActivePackagesByTenant() {
        val store = InMemoryPackageLocalStore()
        store.savePackage("acme", packageDownload("pkg_acme"), 100)
        store.savePackage("northwind", packageDownload("pkg_northwind"), 100)

        store.activatePackage("acme", "pkg_acme", 200)
        store.activatePackage("northwind", "pkg_northwind", 300)

        assertEquals("pkg_acme", store.getActivePackage("acme", "field-ops", "dev")?.packageId)
        assertEquals("pkg_northwind", store.getActivePackage("northwind", "field-ops", "dev")?.packageId)
    }

    @Test
    fun removesAndClearsCachedPackages() {
        val store = InMemoryPackageLocalStore()
        store.savePackage("acme", packageDownload("pkg_v1"), 100)
        store.savePackage("acme", packageDownload("pkg_v2"), 200)
        store.savePackage("northwind", packageDownload("pkg_v3"), 300)

        assertTrue(store.removePackage("acme", "pkg_v1"))
        assertFalse(store.removePackage("acme", "missing"))
        assertNull(store.getPackage("acme", "pkg_v1"))

        assertEquals(1, store.clearTenantPackages("acme"))
        assertNull(store.getPackage("acme", "pkg_v2"))
        assertEquals("pkg_v3", store.getPackage("northwind", "pkg_v3")?.packageId)
    }

    @Test
    fun keyValueStorePersistsPackagesAcrossInstances() {
        val keyValueStore = InMemoryRuntimeKeyValueStore()
        val firstStore = KeyValuePackageLocalStore(keyValueStore)
        firstStore.savePackage("acme", packageDownload("pkg_v1"), 100)
        firstStore.activatePackage("acme", "pkg_v1", 200)

        val secondStore = KeyValuePackageLocalStore(keyValueStore)

        assertEquals("pkg_v1", secondStore.getPackage("acme", "pkg_v1")?.packageId)
        assertEquals("pkg_v1", secondStore.getActivePackage("acme", "field-ops", "dev")?.packageId)
        assertEquals(200, secondStore.getActivePackage("acme", "field-ops", "dev")?.activeAtEpochMillis)
    }

    @Test
    fun rejectsActivatingMissingPackage() {
        val store = InMemoryPackageLocalStore()

        assertFailsWith<IllegalArgumentException> {
            store.activatePackage("acme", "missing", 100)
        }
    }

    private fun packageDownload(
        packageId: String,
        appVersion: String = "1.0.0",
    ): PackageDownloadResult =
        PackageDownloadResult(
            manifest = PackageManifestMetadata(
                packageId = packageId,
                appId = "field-ops",
                appVersion = appVersion,
                channel = "dev",
                runtimeMinVersion = "0.1.0",
                runtimeMaxVersion = "0.9.0",
                hash = "sha256:$packageId",
                signature = "sig:$packageId",
            ),
            payloadJson = "{\"screens\":[]}",
            etag = "etag-$packageId",
        )
}
