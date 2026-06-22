package org.khodola.mobile.runtime.downloader

import org.khodola.mobile.runtime.network.MobileRuntimeNetworkClient
import org.khodola.mobile.runtime.network.PackageDownloadRequest
import org.khodola.mobile.runtime.network.PackageDownloadResult
import org.khodola.mobile.runtime.network.PackageManifestMetadata
import org.khodola.mobile.runtime.network.PackageManifestRequest
import org.khodola.mobile.runtime.storage.LocalPackageRecord
import org.khodola.mobile.runtime.storage.MobilePackageLocalStore
import org.khodola.mobile.runtime.verifier.MobilePackageVerifier
import org.khodola.mobile.runtime.verifier.PackageVerificationRequest

enum class PackageDownloaderSource {
    ActiveCache,
    CachedPackage,
    Network,
}

data class PackageDownloaderResult(
    val manifest: PackageManifestMetadata,
    val packageRecord: LocalPackageRecord,
    val source: PackageDownloaderSource,
)

interface MobilePackageDownloader {
    suspend fun ensureActivePackage(
        tenantSlug: String,
        appId: String,
        channel: String = "dev",
        nowEpochMillis: Long,
    ): PackageDownloaderResult
}

class DefaultMobilePackageDownloader(
    private val networkClient: MobileRuntimeNetworkClient,
    private val localStore: MobilePackageLocalStore,
    private val packageVerifier: MobilePackageVerifier? = null,
) : MobilePackageDownloader {
    override suspend fun ensureActivePackage(
        tenantSlug: String,
        appId: String,
        channel: String,
        nowEpochMillis: Long,
    ): PackageDownloaderResult {
        val manifest = networkClient.fetchActivePackageManifest(
            PackageManifestRequest(
                tenantSlug = tenantSlug,
                appId = appId,
                channel = channel,
            ),
        )

        val activeRecord = localStore.getActivePackage(
            tenantSlug = tenantSlug,
            appId = appId,
            channel = channel,
        )
        if (activeRecord?.packageId == manifest.packageId) {
            return PackageDownloaderResult(
                manifest = manifest,
                packageRecord = activeRecord,
                source = PackageDownloaderSource.ActiveCache,
            )
        }

        val cachedRecord = localStore.getPackage(tenantSlug, manifest.packageId)
        if (cachedRecord != null) {
            val activated = localStore.activatePackage(
                tenantSlug = tenantSlug,
                packageId = manifest.packageId,
                activatedAtEpochMillis = nowEpochMillis,
            )
            return PackageDownloaderResult(
                manifest = manifest,
                packageRecord = activated,
                source = PackageDownloaderSource.CachedPackage,
            )
        }

        val download = networkClient.downloadPackage(
            PackageDownloadRequest(
                tenantSlug = tenantSlug,
                packageId = manifest.packageId,
            ),
        )
        requireMatchingDownload(manifest, download)
        verifyDownload(download)

        localStore.savePackage(
            tenantSlug = tenantSlug,
            download = download,
            cachedAtEpochMillis = nowEpochMillis,
        )
        val activated = localStore.activatePackage(
            tenantSlug = tenantSlug,
            packageId = manifest.packageId,
            activatedAtEpochMillis = nowEpochMillis,
        )
        return PackageDownloaderResult(
            manifest = manifest,
            packageRecord = activated,
            source = PackageDownloaderSource.Network,
        )
    }

    private fun verifyDownload(download: PackageDownloadResult) {
        val verifier = packageVerifier ?: return
        val verification = verifier.verifyPackage(
            PackageVerificationRequest(
                manifest = download.manifest,
                payloadJson = download.payloadJson,
            ),
        )
        require(verification.isValid) {
            "Downloaded package ${download.manifest.packageId} failed verification: ${verification.failures}"
        }
    }
}

private fun requireMatchingDownload(
    manifest: PackageManifestMetadata,
    download: PackageDownloadResult,
) {
    require(download.manifest.packageId == manifest.packageId) {
        "Downloaded package ${download.manifest.packageId} does not match manifest ${manifest.packageId}"
    }
    require(download.manifest.appId == manifest.appId) {
        "Downloaded package app ${download.manifest.appId} does not match manifest app ${manifest.appId}"
    }
    require(download.manifest.channel == manifest.channel) {
        "Downloaded package channel ${download.manifest.channel} does not match manifest channel ${manifest.channel}"
    }
}
