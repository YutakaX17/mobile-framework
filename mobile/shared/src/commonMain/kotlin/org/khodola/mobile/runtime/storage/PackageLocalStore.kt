package org.khodola.mobile.runtime.storage

import org.khodola.mobile.runtime.network.PackageDownloadResult
import org.khodola.mobile.runtime.network.PackageManifestMetadata

data class LocalPackageRecord(
    val tenantSlug: String,
    val manifest: PackageManifestMetadata,
    val payloadJson: String,
    val etag: String?,
    val cachedAtEpochMillis: Long,
    val activeAtEpochMillis: Long? = null,
) {
    init {
        require(tenantSlug.isNotBlank()) { "tenantSlug is required" }
        require(payloadJson.isNotBlank()) { "payloadJson is required" }
    }

    val packageId: String
        get() = manifest.packageId

    val appId: String
        get() = manifest.appId

    val channel: String
        get() = manifest.channel

    val isActive: Boolean
        get() = activeAtEpochMillis != null
}

interface MobilePackageLocalStore {
    fun savePackage(
        tenantSlug: String,
        download: PackageDownloadResult,
        cachedAtEpochMillis: Long,
    ): LocalPackageRecord

    fun getPackage(tenantSlug: String, packageId: String): LocalPackageRecord?

    fun getActivePackage(
        tenantSlug: String,
        appId: String,
        channel: String,
    ): LocalPackageRecord?

    fun activatePackage(
        tenantSlug: String,
        packageId: String,
        activatedAtEpochMillis: Long,
    ): LocalPackageRecord

    fun removePackage(tenantSlug: String, packageId: String): Boolean

    fun clearTenantPackages(tenantSlug: String): Int
}

class InMemoryPackageLocalStore : MobilePackageLocalStore {
    private val packages = mutableMapOf<PackageStoreKey, LocalPackageRecord>()

    override fun savePackage(
        tenantSlug: String,
        download: PackageDownloadResult,
        cachedAtEpochMillis: Long,
    ): LocalPackageRecord {
        val normalizedTenant = requireTenant(tenantSlug)
        val key = PackageStoreKey(normalizedTenant, download.manifest.packageId)
        val existing = packages[key]
        val record = LocalPackageRecord(
            tenantSlug = normalizedTenant,
            manifest = download.manifest,
            payloadJson = download.payloadJson,
            etag = download.etag,
            cachedAtEpochMillis = cachedAtEpochMillis,
            activeAtEpochMillis = existing?.activeAtEpochMillis,
        )
        packages[key] = record
        return record
    }

    override fun getPackage(tenantSlug: String, packageId: String): LocalPackageRecord? =
        packages[PackageStoreKey(requireTenant(tenantSlug), requireId(packageId, "packageId"))]

    override fun getActivePackage(
        tenantSlug: String,
        appId: String,
        channel: String,
    ): LocalPackageRecord? {
        val normalizedTenant = requireTenant(tenantSlug)
        val normalizedAppId = requireId(appId, "appId")
        val normalizedChannel = requireId(channel, "channel")
        return packages.values.firstOrNull { record ->
            record.tenantSlug == normalizedTenant &&
                record.appId == normalizedAppId &&
                record.channel == normalizedChannel &&
                record.isActive
        }
    }

    override fun activatePackage(
        tenantSlug: String,
        packageId: String,
        activatedAtEpochMillis: Long,
    ): LocalPackageRecord {
        val normalizedTenant = requireTenant(tenantSlug)
        val normalizedPackageId = requireId(packageId, "packageId")
        val key = PackageStoreKey(normalizedTenant, normalizedPackageId)
        val target = packages[key]
            ?: throw IllegalArgumentException("Package $normalizedPackageId is not cached for tenant $normalizedTenant")

        val packageKeys = packages.keys.toList()
        packageKeys.forEach { packageKey ->
            val record = packages.getValue(packageKey)
            if (
                record.tenantSlug == normalizedTenant &&
                record.appId == target.appId &&
                record.channel == target.channel
            ) {
                packages[packageKey] = record.copy(activeAtEpochMillis = null)
            }
        }

        val activated = target.copy(activeAtEpochMillis = activatedAtEpochMillis)
        packages[key] = activated
        return activated
    }

    override fun removePackage(tenantSlug: String, packageId: String): Boolean =
        packages.remove(PackageStoreKey(requireTenant(tenantSlug), requireId(packageId, "packageId"))) != null

    override fun clearTenantPackages(tenantSlug: String): Int {
        val normalizedTenant = requireTenant(tenantSlug)
        val keys = packages.keys.filter { key -> key.tenantSlug == normalizedTenant }
        keys.forEach { key -> packages.remove(key) }
        return keys.size
    }
}

private data class PackageStoreKey(
    val tenantSlug: String,
    val packageId: String,
)

private fun requireTenant(tenantSlug: String): String =
    requireId(tenantSlug, "tenantSlug")

private fun requireId(value: String, name: String): String {
    val normalized = value.trim()
    require(normalized.isNotEmpty()) { "$name is required" }
    return normalized
}
