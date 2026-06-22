package org.khodola.mobile.runtime.storage

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson
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

interface RuntimeKeyValueStore {
    fun putString(key: String, value: String)

    fun getString(key: String): String?

    fun remove(key: String): Boolean
}

class InMemoryRuntimeKeyValueStore : RuntimeKeyValueStore {
    private val values = mutableMapOf<String, String>()

    override fun putString(key: String, value: String) {
        require(key.isNotBlank()) { "key is required" }
        values[key] = value
    }

    override fun getString(key: String): String? =
        values[key]

    override fun remove(key: String): Boolean =
        values.remove(key) != null
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

class KeyValuePackageLocalStore(
    private val keyValueStore: RuntimeKeyValueStore,
    private val namespace: String = "runtime:packages",
) : MobilePackageLocalStore {
    override fun savePackage(
        tenantSlug: String,
        download: PackageDownloadResult,
        cachedAtEpochMillis: Long,
    ): LocalPackageRecord {
        val normalizedTenant = requireTenant(tenantSlug)
        val records = readRecords().toMutableMap()
        val key = PackageStoreKey(normalizedTenant, download.manifest.packageId)
        val existing = records[key]
        val record = LocalPackageRecord(
            tenantSlug = normalizedTenant,
            manifest = download.manifest,
            payloadJson = download.payloadJson,
            etag = download.etag,
            cachedAtEpochMillis = cachedAtEpochMillis,
            activeAtEpochMillis = existing?.activeAtEpochMillis,
        )
        records[key] = record
        writeRecords(records)
        return record
    }

    override fun getPackage(tenantSlug: String, packageId: String): LocalPackageRecord? =
        readRecords()[PackageStoreKey(requireTenant(tenantSlug), requireId(packageId, "packageId"))]

    override fun getActivePackage(
        tenantSlug: String,
        appId: String,
        channel: String,
    ): LocalPackageRecord? {
        val normalizedTenant = requireTenant(tenantSlug)
        val normalizedAppId = requireId(appId, "appId")
        val normalizedChannel = requireId(channel, "channel")
        return readRecords().values.firstOrNull { record ->
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
        val records = readRecords().toMutableMap()
        val target = records[key]
            ?: throw IllegalArgumentException("Package $normalizedPackageId is not cached for tenant $normalizedTenant")

        records.keys.toList().forEach { packageKey ->
            val record = records.getValue(packageKey)
            if (
                record.tenantSlug == normalizedTenant &&
                record.appId == target.appId &&
                record.channel == target.channel
            ) {
                records[packageKey] = record.copy(activeAtEpochMillis = null)
            }
        }

        val activated = target.copy(activeAtEpochMillis = activatedAtEpochMillis)
        records[key] = activated
        writeRecords(records)
        return activated
    }

    override fun removePackage(tenantSlug: String, packageId: String): Boolean {
        val records = readRecords().toMutableMap()
        val removed = records.remove(PackageStoreKey(requireTenant(tenantSlug), requireId(packageId, "packageId"))) != null
        if (removed) {
            writeRecords(records)
        }
        return removed
    }

    override fun clearTenantPackages(tenantSlug: String): Int {
        val normalizedTenant = requireTenant(tenantSlug)
        val records = readRecords().toMutableMap()
        val keys = records.keys.filter { key -> key.tenantSlug == normalizedTenant }
        keys.forEach { key -> records.remove(key) }
        if (keys.isNotEmpty()) {
            writeRecords(records)
        }
        return keys.size
    }

    private fun readRecords(): Map<PackageStoreKey, LocalPackageRecord> =
        keyValueStore.getString(namespace)
            ?.let { encoded -> MobileRuntimeJson.decodeFromString(PackageStoreEnvelopeDto.serializer(), encoded) }
            ?.records
            ?.associate { dto -> PackageStoreKey(dto.tenantSlug, dto.manifest.packageId) to dto.toRecord() }
            ?: emptyMap()

    private fun writeRecords(records: Map<PackageStoreKey, LocalPackageRecord>) {
        keyValueStore.putString(
            namespace,
            MobileRuntimeJson.encodeToString(
                PackageStoreEnvelopeDto(
                    records = records.values
                        .sortedWith(compareBy<LocalPackageRecord> { record -> record.tenantSlug }.thenBy { record -> record.packageId })
                        .map { record -> PackageRecordDto.fromRecord(record) },
                ),
            ),
        )
    }
}

private data class PackageStoreKey(
    val tenantSlug: String,
    val packageId: String,
)

@Serializable
private data class PackageStoreEnvelopeDto(
    val records: List<PackageRecordDto> = emptyList(),
)

@Serializable
private data class PackageRecordDto(
    @SerialName("tenant_slug")
    val tenantSlug: String,
    val manifest: PackageManifestMetadataDto,
    @SerialName("payload_json")
    val payloadJson: String,
    val etag: String? = null,
    @SerialName("cached_at_epoch_millis")
    val cachedAtEpochMillis: Long,
    @SerialName("active_at_epoch_millis")
    val activeAtEpochMillis: Long? = null,
) {
    fun toRecord(): LocalPackageRecord =
        LocalPackageRecord(
            tenantSlug = tenantSlug,
            manifest = manifest.toMetadata(),
            payloadJson = payloadJson,
            etag = etag,
            cachedAtEpochMillis = cachedAtEpochMillis,
            activeAtEpochMillis = activeAtEpochMillis,
        )

    companion object {
        fun fromRecord(record: LocalPackageRecord): PackageRecordDto =
            PackageRecordDto(
                tenantSlug = record.tenantSlug,
                manifest = PackageManifestMetadataDto.fromMetadata(record.manifest),
                payloadJson = record.payloadJson,
                etag = record.etag,
                cachedAtEpochMillis = record.cachedAtEpochMillis,
                activeAtEpochMillis = record.activeAtEpochMillis,
            )
    }
}

@Serializable
data class PackageManifestMetadataDto(
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

    companion object {
        fun fromMetadata(metadata: PackageManifestMetadata): PackageManifestMetadataDto =
            PackageManifestMetadataDto(
                packageId = metadata.packageId,
                appId = metadata.appId,
                appVersion = metadata.appVersion,
                channel = metadata.channel,
                runtimeMinVersion = metadata.runtimeMinVersion,
                runtimeMaxVersion = metadata.runtimeMaxVersion,
                hash = metadata.hash,
                signature = metadata.signature,
            )
    }
}

private fun requireTenant(tenantSlug: String): String =
    requireId(tenantSlug, "tenantSlug")

private fun requireId(value: String, name: String): String {
    val normalized = value.trim()
    require(normalized.isNotEmpty()) { "$name is required" }
    return normalized
}
