package org.khodola.mobile.runtime.security

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import org.khodola.mobile.runtime.network.MobileRuntimeAuthorizationProvider
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson
import org.khodola.mobile.runtime.storage.RuntimeKeyValueStore

data class MobileAuthTokens(
    val accessToken: String,
    val refreshToken: String?,
    val tokenType: String = "Bearer",
    val expiresAtEpochMillis: Long? = null,
) {
    init {
        require(accessToken.isNotBlank()) { "accessToken is required" }
        require(tokenType.isNotBlank()) { "tokenType is required" }
    }

    val authorizationHeader: String
        get() = "${tokenType.trim()} ${accessToken.trim()}"

    fun isExpired(nowEpochMillis: Long): Boolean =
        expiresAtEpochMillis?.let { expiresAt -> nowEpochMillis >= expiresAt } ?: false
}

interface MobileSecureTokenStore {
    fun saveTokens(tenantSlug: String, tokens: MobileAuthTokens): MobileAuthTokens

    fun getTokens(tenantSlug: String): MobileAuthTokens?

    fun clearTokens(tenantSlug: String): Boolean

    fun clearAllTokens(): Int
}

class InMemorySecureTokenStore : MobileSecureTokenStore {
    private val tokensByTenant = mutableMapOf<String, MobileAuthTokens>()

    override fun saveTokens(tenantSlug: String, tokens: MobileAuthTokens): MobileAuthTokens {
        tokensByTenant[requireTenant(tenantSlug)] = tokens
        return tokens
    }

    override fun getTokens(tenantSlug: String): MobileAuthTokens? =
        tokensByTenant[requireTenant(tenantSlug)]

    override fun clearTokens(tenantSlug: String): Boolean =
        tokensByTenant.remove(requireTenant(tenantSlug)) != null

    override fun clearAllTokens(): Int {
        val removed = tokensByTenant.size
        tokensByTenant.clear()
        return removed
    }
}

class KeyValueSecureTokenStore(
    private val keyValueStore: RuntimeKeyValueStore,
    private val namespace: String = "runtime:tokens",
) : MobileSecureTokenStore {
    override fun saveTokens(tenantSlug: String, tokens: MobileAuthTokens): MobileAuthTokens {
        val normalizedTenant = requireTenant(tenantSlug)
        val tokensByTenant = readTokens().toMutableMap()
        tokensByTenant[normalizedTenant] = tokens
        writeTokens(tokensByTenant)
        return tokens
    }

    override fun getTokens(tenantSlug: String): MobileAuthTokens? =
        readTokens()[requireTenant(tenantSlug)]

    override fun clearTokens(tenantSlug: String): Boolean {
        val tokensByTenant = readTokens().toMutableMap()
        val removed = tokensByTenant.remove(requireTenant(tenantSlug)) != null
        if (removed) {
            writeTokens(tokensByTenant)
        }
        return removed
    }

    override fun clearAllTokens(): Int {
        val removed = readTokens().size
        keyValueStore.remove(namespace)
        return removed
    }

    private fun readTokens(): Map<String, MobileAuthTokens> =
        keyValueStore.getString(namespace)
            ?.let { encoded -> MobileRuntimeJson.decodeFromString(TokenStoreEnvelopeDto.serializer(), encoded) }
            ?.tokens
            ?.associate { dto -> dto.tenantSlug to dto.toTokens() }
            ?: emptyMap()

    private fun writeTokens(tokensByTenant: Map<String, MobileAuthTokens>) {
        keyValueStore.putString(
            namespace,
            MobileRuntimeJson.encodeToString(
                TokenStoreEnvelopeDto(
                    tokens = tokensByTenant.entries
                        .sortedBy { (tenantSlug, _) -> tenantSlug }
                        .map { (tenantSlug, tokens) -> MobileAuthTokensDto.fromTokens(tenantSlug, tokens) },
                ),
            ),
        )
    }
}

class TokenStoreAuthorizationProvider(
    private val tokenStore: MobileSecureTokenStore,
    private val nowEpochMillis: Long,
) : MobileRuntimeAuthorizationProvider {
    override fun authorizationHeader(tenantSlug: String): String? =
        tokenStore
            .getTokens(tenantSlug)
            ?.takeUnless { tokens -> tokens.isExpired(nowEpochMillis) }
            ?.authorizationHeader
}

@Serializable
private data class TokenStoreEnvelopeDto(
    val tokens: List<MobileAuthTokensDto> = emptyList(),
)

@Serializable
private data class MobileAuthTokensDto(
    @SerialName("tenant_slug")
    val tenantSlug: String,
    @SerialName("access_token")
    val accessToken: String,
    @SerialName("refresh_token")
    val refreshToken: String? = null,
    @SerialName("token_type")
    val tokenType: String = "Bearer",
    @SerialName("expires_at_epoch_millis")
    val expiresAtEpochMillis: Long? = null,
) {
    fun toTokens(): MobileAuthTokens =
        MobileAuthTokens(
            accessToken = accessToken,
            refreshToken = refreshToken,
            tokenType = tokenType,
            expiresAtEpochMillis = expiresAtEpochMillis,
        )

    companion object {
        fun fromTokens(tenantSlug: String, tokens: MobileAuthTokens): MobileAuthTokensDto =
            MobileAuthTokensDto(
                tenantSlug = tenantSlug,
                accessToken = tokens.accessToken,
                refreshToken = tokens.refreshToken,
                tokenType = tokens.tokenType,
                expiresAtEpochMillis = tokens.expiresAtEpochMillis,
            )
    }
}

private fun requireTenant(tenantSlug: String): String {
    val normalized = tenantSlug.trim()
    require(normalized.isNotEmpty()) { "tenantSlug is required" }
    return normalized
}
