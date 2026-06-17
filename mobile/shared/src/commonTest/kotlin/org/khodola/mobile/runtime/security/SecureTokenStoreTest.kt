package org.khodola.mobile.runtime.security

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class SecureTokenStoreTest {
    @Test
    fun storesAndReadsTokensByTenant() {
        val store = InMemorySecureTokenStore()
        val tokens = MobileAuthTokens(
            accessToken = "access-token",
            refreshToken = "refresh-token",
            expiresAtEpochMillis = 1_720_000_000_000,
        )

        val saved = store.saveTokens("acme", tokens)

        assertEquals(tokens, saved)
        assertEquals(tokens, store.getTokens("acme"))
        assertNull(store.getTokens("northwind"))
    }

    @Test
    fun replacesExistingTenantTokens() {
        val store = InMemorySecureTokenStore()
        store.saveTokens("acme", MobileAuthTokens(accessToken = "old", refreshToken = "old-refresh"))

        val replacement = MobileAuthTokens(accessToken = "new", refreshToken = null)
        store.saveTokens("acme", replacement)

        assertEquals(replacement, store.getTokens("acme"))
    }

    @Test
    fun clearsTenantAndAllTokens() {
        val store = InMemorySecureTokenStore()
        store.saveTokens("acme", MobileAuthTokens(accessToken = "acme-token", refreshToken = null))
        store.saveTokens("northwind", MobileAuthTokens(accessToken = "northwind-token", refreshToken = null))

        assertTrue(store.clearTokens("acme"))
        assertFalse(store.clearTokens("acme"))
        assertNull(store.getTokens("acme"))
        assertEquals("northwind-token", store.getTokens("northwind")?.accessToken)

        assertEquals(1, store.clearAllTokens())
        assertNull(store.getTokens("northwind"))
    }

    @Test
    fun formatsAuthorizationHeaderAndDetectsExpiry() {
        val tokens = MobileAuthTokens(
            accessToken = "access-token",
            refreshToken = null,
            tokenType = "Bearer",
            expiresAtEpochMillis = 200,
        )

        assertEquals("Bearer access-token", tokens.authorizationHeader)
        assertFalse(tokens.isExpired(nowEpochMillis = 199))
        assertTrue(tokens.isExpired(nowEpochMillis = 200))
    }

    @Test
    fun rejectsBlankRequiredValues() {
        assertFailsWith<IllegalArgumentException> {
            MobileAuthTokens(accessToken = " ", refreshToken = null)
        }
        assertFailsWith<IllegalArgumentException> {
            InMemorySecureTokenStore().saveTokens(" ", MobileAuthTokens("token", null))
        }
    }
}
