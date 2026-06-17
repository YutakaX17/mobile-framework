package org.khodola.mobile.runtime.theme

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson

data class RuntimeTheme(
    val themeId: String,
    val name: String,
    val version: String,
    val modeId: String,
    val colors: RuntimeThemeColors,
    val typography: RuntimeTypography,
    val spacing: Map<String, Double>,
    val radius: Map<String, Double>,
    val elevation: Map<String, RuntimeElevation>,
    val components: Map<String, RuntimeComponentStyle>,
    val assets: RuntimeThemeAssets?,
    val accessibility: RuntimeThemeAccessibility?,
)

data class RuntimeThemeColors(
    val primary: RuntimeColorScale,
    val secondary: RuntimeColorScale,
    val background: String,
    val surface: String,
    val text: String,
    val success: String,
    val warning: String,
    val danger: String,
) {
    fun withOverrides(overrides: Map<String, String>): RuntimeThemeColors =
        copy(
            background = overrides["background"] ?: background,
            surface = overrides["surface"] ?: surface,
            text = overrides["text"] ?: text,
            success = overrides["success"] ?: success,
            warning = overrides["warning"] ?: warning,
            danger = overrides["danger"] ?: danger,
        )
}

data class RuntimeColorScale(
    val light: String?,
    val main: String,
    val dark: String?,
    val contrast: String,
)

data class RuntimeTypography(
    val fontFamily: String,
    val fallbackFamily: String?,
    val scale: Map<String, RuntimeTypeStyle>,
)

data class RuntimeTypeStyle(
    val fontSize: Double,
    val lineHeight: Double,
    val fontWeight: Int,
    val letterSpacing: Double?,
)

data class RuntimeElevation(
    val level: Int,
    val shadow: String?,
)

data class RuntimeComponentStyle(
    val background: String?,
    val text: String?,
    val border: String?,
    val radius: Double?,
    val padding: Double?,
    val elevation: Int?,
)

data class RuntimeThemeAssets(
    val logoAssetId: String?,
    val iconAssetId: String?,
)

data class RuntimeThemeAccessibility(
    val contrastStandard: String,
    val validated: Boolean,
    val overrideRecorded: Boolean,
)

fun decodeRuntimeThemeFromPackagePayload(
    payloadJson: String,
    modeId: String = "light",
): RuntimeTheme =
    MobileRuntimeJson
        .decodeFromString<PackageThemeEnvelopeDto>(payloadJson)
        .theme
        .toRuntimeTheme(modeId)

@Serializable
private data class PackageThemeEnvelopeDto(
    val theme: RuntimeThemeDto,
)

@Serializable
private data class RuntimeThemeDto(
    @SerialName("theme_id")
    val themeId: String,
    val name: String,
    val version: String,
    val tokens: RuntimeThemeTokensDto,
    val modes: List<RuntimeThemeModeDto>,
    val assets: RuntimeThemeAssetsDto? = null,
    val accessibility: RuntimeThemeAccessibilityDto? = null,
) {
    fun toRuntimeTheme(modeId: String): RuntimeTheme {
        val mode = modes.firstOrNull { candidate -> candidate.modeId == modeId }
            ?: throw IllegalArgumentException("Theme mode $modeId is not available for theme $themeId")

        return RuntimeTheme(
            themeId = themeId,
            name = name,
            version = version,
            modeId = mode.modeId,
            colors = tokens.colors.toRuntimeColors().withOverrides(mode.colorOverrides),
            typography = tokens.typography.toRuntimeTypography(),
            spacing = tokens.spacing,
            radius = tokens.radius,
            elevation = tokens.elevation.mapValues { (_, value) -> value.toRuntimeElevation() },
            components = tokens.components.mapValues { (_, value) -> value.toRuntimeComponentStyle() },
            assets = assets?.toRuntimeAssets(),
            accessibility = accessibility?.toRuntimeAccessibility(),
        )
    }
}

@Serializable
private data class RuntimeThemeTokensDto(
    val colors: RuntimeThemeColorsDto,
    val typography: RuntimeTypographyDto,
    val spacing: Map<String, Double>,
    val radius: Map<String, Double>,
    val elevation: Map<String, RuntimeElevationDto>,
    val components: Map<String, RuntimeComponentStyleDto> = emptyMap(),
)

@Serializable
private data class RuntimeThemeColorsDto(
    val primary: RuntimeColorScaleDto,
    val secondary: RuntimeColorScaleDto,
    val background: String,
    val surface: String,
    val text: String,
    val success: String,
    val warning: String,
    val danger: String,
) {
    fun toRuntimeColors(): RuntimeThemeColors =
        RuntimeThemeColors(
            primary = primary.toRuntimeColorScale(),
            secondary = secondary.toRuntimeColorScale(),
            background = background,
            surface = surface,
            text = text,
            success = success,
            warning = warning,
            danger = danger,
        )
}

@Serializable
private data class RuntimeColorScaleDto(
    val light: String? = null,
    val main: String,
    val dark: String? = null,
    val contrast: String,
) {
    fun toRuntimeColorScale(): RuntimeColorScale =
        RuntimeColorScale(
            light = light,
            main = main,
            dark = dark,
            contrast = contrast,
        )
}

@Serializable
private data class RuntimeTypographyDto(
    @SerialName("font_family")
    val fontFamily: String,
    @SerialName("fallback_family")
    val fallbackFamily: String? = null,
    val scale: Map<String, RuntimeTypeStyleDto>,
) {
    fun toRuntimeTypography(): RuntimeTypography =
        RuntimeTypography(
            fontFamily = fontFamily,
            fallbackFamily = fallbackFamily,
            scale = scale.mapValues { (_, value) -> value.toRuntimeTypeStyle() },
        )
}

@Serializable
private data class RuntimeTypeStyleDto(
    @SerialName("font_size")
    val fontSize: Double,
    @SerialName("line_height")
    val lineHeight: Double,
    @SerialName("font_weight")
    val fontWeight: Int,
    @SerialName("letter_spacing")
    val letterSpacing: Double? = null,
) {
    fun toRuntimeTypeStyle(): RuntimeTypeStyle =
        RuntimeTypeStyle(
            fontSize = fontSize,
            lineHeight = lineHeight,
            fontWeight = fontWeight,
            letterSpacing = letterSpacing,
        )
}

@Serializable
private data class RuntimeElevationDto(
    val level: Int,
    val shadow: String? = null,
) {
    fun toRuntimeElevation(): RuntimeElevation =
        RuntimeElevation(level = level, shadow = shadow)
}

@Serializable
private data class RuntimeComponentStyleDto(
    val background: String? = null,
    val text: String? = null,
    val border: String? = null,
    val radius: Double? = null,
    val padding: Double? = null,
    val elevation: Int? = null,
) {
    fun toRuntimeComponentStyle(): RuntimeComponentStyle =
        RuntimeComponentStyle(
            background = background,
            text = text,
            border = border,
            radius = radius,
            padding = padding,
            elevation = elevation,
        )
}

@Serializable
private data class RuntimeThemeModeDto(
    @SerialName("mode_id")
    val modeId: String,
    val label: String,
    @SerialName("color_overrides")
    val colorOverrides: Map<String, String>,
)

@Serializable
private data class RuntimeThemeAssetsDto(
    @SerialName("logo_asset_id")
    val logoAssetId: String? = null,
    @SerialName("icon_asset_id")
    val iconAssetId: String? = null,
) {
    fun toRuntimeAssets(): RuntimeThemeAssets =
        RuntimeThemeAssets(
            logoAssetId = logoAssetId,
            iconAssetId = iconAssetId,
        )
}

@Serializable
private data class RuntimeThemeAccessibilityDto(
    @SerialName("contrast_standard")
    val contrastStandard: String,
    val validated: Boolean,
    @SerialName("override_recorded")
    val overrideRecorded: Boolean = false,
) {
    fun toRuntimeAccessibility(): RuntimeThemeAccessibility =
        RuntimeThemeAccessibility(
            contrastStandard = contrastStandard,
            validated = validated,
            overrideRecorded = overrideRecorded,
        )
}
