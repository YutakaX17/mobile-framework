package org.khodola.mobile.runtime.downloader

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.fail
import kotlin.coroutines.startCoroutine
import org.khodola.mobile.runtime.network.MobileRuntimeNetworkClient
import org.khodola.mobile.runtime.network.PackageDownloadRequest
import org.khodola.mobile.runtime.network.PackageDownloadResult
import org.khodola.mobile.runtime.network.PackageManifestMetadata
import org.khodola.mobile.runtime.network.PackageManifestRequest
import org.khodola.mobile.runtime.storage.InMemoryPackageLocalStore

class PackageDownloaderTest {
    @Test
    fun downloadsCachesAndActivatesPackage() = runSuspendTest {
        val manifest = packageManifest("pkg_v1")
        val network = FakeNetworkClient(manifest)
        val store = InMemoryPackageLocalStore()
        val downloader = DefaultMobilePackageDownloader(network, store)

        val result = downloader.ensureActivePackage(
            tenantSlug = "acme",
            appId = "field-ops",
            channel = "dev",
            nowEpochMillis = 100,
        )

        assertEquals(PackageDownloaderSource.Network, result.source)
        assertEquals("pkg_v1", result.packageRecord.packageId)
        assertEquals(100, result.packageRecord.cachedAtEpochMillis)
        assertEquals(100, result.packageRecord.activeAtEpochMillis)
        assertEquals(1, network.manifestFetches)
        assertEquals(1, network.packageDownloads)
        assertEquals("pkg_v1", store.getActivePackage("acme", "field-ops", "dev")?.packageId)
    }

    @Test
    fun reusesActiveCachedPackage() = runSuspendTest {
        val manifest = packageManifest("pkg_v1")
        val network = FakeNetworkClient(manifest)
        val store = InMemoryPackageLocalStore()
        store.savePackage("acme", packageDownload(manifest), 100)
        store.activatePackage("acme", "pkg_v1", 200)
        val downloader = DefaultMobilePackageDownloader(network, store)

        val result = downloader.ensureActivePackage("acme", "field-ops", "dev", nowEpochMillis = 300)

        assertEquals(PackageDownloaderSource.ActiveCache, result.source)
        assertEquals(200, result.packageRecord.activeAtEpochMillis)
        assertEquals(1, network.manifestFetches)
        assertEquals(0, network.packageDownloads)
    }

    @Test
    fun activatesCachedPackageWhenManifestChangesBackToCachedVersion() = runSuspendTest {
        val manifest = packageManifest("pkg_v2", appVersion = "1.1.0")
        val network = FakeNetworkClient(manifest)
        val store = InMemoryPackageLocalStore()
        store.savePackage("acme", packageDownload(packageManifest("pkg_v1")), 100)
        store.savePackage("acme", packageDownload(manifest), 200)
        store.activatePackage("acme", "pkg_v1", 250)
        val downloader = DefaultMobilePackageDownloader(network, store)

        val result = downloader.ensureActivePackage("acme", "field-ops", "dev", nowEpochMillis = 300)

        assertEquals(PackageDownloaderSource.CachedPackage, result.source)
        assertEquals("pkg_v2", result.packageRecord.packageId)
        assertEquals(300, result.packageRecord.activeAtEpochMillis)
        assertEquals(0, network.packageDownloads)
    }

    @Test
    fun rejectsMismatchedDownloadManifest() = runSuspendTest {
        val manifest = packageManifest("pkg_v1")
        val network = FakeNetworkClient(
            manifest = manifest,
            download = packageDownload(packageManifest("pkg_other")),
        )
        val downloader = DefaultMobilePackageDownloader(network, InMemoryPackageLocalStore())

        try {
            downloader.ensureActivePackage("acme", "field-ops", "dev", nowEpochMillis = 100)
            fail("Expected mismatched download manifest to be rejected")
        } catch (_: IllegalArgumentException) {
        }
    }

    private class FakeNetworkClient(
        private val manifest: PackageManifestMetadata,
        private val download: PackageDownloadResult = packageDownload(manifest),
    ) : MobileRuntimeNetworkClient {
        var manifestFetches = 0
            private set
        var packageDownloads = 0
            private set

        override suspend fun fetchActivePackageManifest(request: PackageManifestRequest): PackageManifestMetadata {
            manifestFetches += 1
            assertEquals("acme", request.tenantSlug)
            assertEquals("field-ops", request.appId)
            assertEquals("dev", request.channel)
            return manifest
        }

        override suspend fun downloadPackage(request: PackageDownloadRequest): PackageDownloadResult {
            packageDownloads += 1
            assertEquals("acme", request.tenantSlug)
            assertEquals(manifest.packageId, request.packageId)
            return download
        }
    }
}

private fun packageManifest(
    packageId: String,
    appVersion: String = "1.0.0",
): PackageManifestMetadata =
    PackageManifestMetadata(
        packageId = packageId,
        appId = "field-ops",
        appVersion = appVersion,
        channel = "dev",
        runtimeMinVersion = "0.1.0",
        runtimeMaxVersion = "0.9.0",
        hash = "sha256:$packageId",
        signature = "sig:$packageId",
    )

private fun packageDownload(manifest: PackageManifestMetadata): PackageDownloadResult =
    PackageDownloadResult(
        manifest = manifest,
        payloadJson = "{\"screens\":[]}",
        etag = "etag-${manifest.packageId}",
    )

private fun runSuspendTest(block: suspend () -> Unit) {
    block.startCoroutineOrThrow()
}

private fun (suspend () -> Unit).startCoroutineOrThrow() {
    var failure: Throwable? = null
    startCoroutine(
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
