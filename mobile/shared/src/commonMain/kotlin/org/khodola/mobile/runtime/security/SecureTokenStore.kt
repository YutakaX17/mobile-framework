package org.khodola.mobile.runtime.security

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

private fun requireTenant(tenantSlug: String): String {
    val normalized = tenantSlug.trim()
    require(normalized.isNotEmpty()) { "tenantSlug is required" }
    return normalized
}
