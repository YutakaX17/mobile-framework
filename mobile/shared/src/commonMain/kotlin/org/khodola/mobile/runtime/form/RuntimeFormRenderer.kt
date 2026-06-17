package org.khodola.mobile.runtime.form

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import org.khodola.mobile.runtime.serialization.MobileRuntimeJson

data class RuntimeForm(
    val formId: String,
    val name: String,
    val description: String?,
    val version: String,
    val mode: String,
    val status: String,
    val entityType: String?,
    val layout: RuntimeFormLayout?,
    val fields: List<RuntimeFormField>,
    val submitAction: RuntimeFormSubmitAction?,
    val offline: RuntimeFormOffline?,
)

data class RuntimeFormLayout(
    val type: String?,
    val sections: List<RuntimeFormSection>,
)

data class RuntimeFormSection(
    val sectionId: String,
    val label: String,
    val fieldIds: List<String>,
)

data class RuntimeFormField(
    val fieldId: String,
    val fieldType: String,
    val label: String,
    val helpText: String?,
    val required: Boolean,
    val readOnly: Boolean,
    val hidden: Boolean,
    val binding: RuntimeFieldBinding,
    val validation: RuntimeFieldValidation?,
    val visibility: RuntimeFieldRule?,
    val calculation: RuntimeFieldRule?,
    val options: List<RuntimeFieldOption>,
    val customControl: RuntimeCustomControl?,
)

data class RuntimeFieldBinding(
    val dataPath: String,
    val entityType: String?,
)

data class RuntimeFieldValidation(
    val minLength: Int?,
    val maxLength: Int?,
    val minimum: Double?,
    val maximum: Double?,
    val pattern: String?,
    val message: String?,
)

data class RuntimeFieldRule(
    val ruleType: String,
    val expression: String,
)

data class RuntimeFieldOption(
    val value: String,
    val label: String,
    val disabled: Boolean,
)

data class RuntimeCustomControl(
    val controlId: String,
    val runtimeWidget: String,
)

data class RuntimeFormSubmitAction(
    val actionType: String,
    val target: String?,
)

data class RuntimeFormOffline(
    val enabled: Boolean,
    val queueSubmissions: Boolean,
    val conflictPolicy: String?,
)

fun decodeRuntimeFormFromPackagePayload(
    payloadJson: String,
    formId: String,
): RuntimeForm =
    MobileRuntimeJson
        .decodeFromString<PackageFormsEnvelopeDto>(payloadJson)
        .forms
        .firstOrNull { form -> form.formId == formId }
        ?.toRuntimeForm()
        ?: throw IllegalArgumentException("Form $formId is not available in package payload")

@Serializable
private data class PackageFormsEnvelopeDto(
    val forms: List<RuntimeFormDto>,
)

@Serializable
private data class RuntimeFormDto(
    @SerialName("form_id")
    val formId: String,
    val name: String,
    val description: String? = null,
    val version: String,
    val mode: String,
    val status: String = "draft",
    @SerialName("entity_type")
    val entityType: String? = null,
    val layout: RuntimeFormLayoutDto? = null,
    val fields: List<RuntimeFormFieldDto>,
    @SerialName("submit_action")
    val submitAction: RuntimeFormSubmitActionDto? = null,
    val offline: RuntimeFormOfflineDto? = null,
) {
    fun toRuntimeForm(): RuntimeForm =
        RuntimeForm(
            formId = formId,
            name = name,
            description = description,
            version = version,
            mode = mode,
            status = status,
            entityType = entityType,
            layout = layout?.toRuntimeLayout(),
            fields = fields.map { field -> field.toRuntimeField() },
            submitAction = submitAction?.toRuntimeSubmitAction(),
            offline = offline?.toRuntimeOffline(),
        )
}

@Serializable
private data class RuntimeFormLayoutDto(
    val type: String? = null,
    val sections: List<RuntimeFormSectionDto> = emptyList(),
) {
    fun toRuntimeLayout(): RuntimeFormLayout =
        RuntimeFormLayout(
            type = type,
            sections = sections.map { section -> section.toRuntimeSection() },
        )
}

@Serializable
private data class RuntimeFormSectionDto(
    @SerialName("section_id")
    val sectionId: String,
    val label: String,
    @SerialName("field_ids")
    val fieldIds: List<String>,
) {
    fun toRuntimeSection(): RuntimeFormSection =
        RuntimeFormSection(sectionId = sectionId, label = label, fieldIds = fieldIds)
}

@Serializable
private data class RuntimeFormFieldDto(
    @SerialName("field_id")
    val fieldId: String,
    @SerialName("field_type")
    val fieldType: String,
    val label: String,
    @SerialName("help_text")
    val helpText: String? = null,
    val required: Boolean = false,
    @SerialName("read_only")
    val readOnly: Boolean = false,
    val hidden: Boolean = false,
    val binding: RuntimeFieldBindingDto,
    val validation: RuntimeFieldValidationDto? = null,
    val visibility: RuntimeFieldRuleDto? = null,
    val calculation: RuntimeFieldRuleDto? = null,
    val options: List<RuntimeFieldOptionDto> = emptyList(),
    @SerialName("custom_control")
    val customControl: RuntimeCustomControlDto? = null,
) {
    fun toRuntimeField(): RuntimeFormField =
        RuntimeFormField(
            fieldId = fieldId,
            fieldType = fieldType,
            label = label,
            helpText = helpText,
            required = required,
            readOnly = readOnly,
            hidden = hidden,
            binding = binding.toRuntimeBinding(),
            validation = validation?.toRuntimeValidation(),
            visibility = visibility?.toRuntimeRule(),
            calculation = calculation?.toRuntimeRule(),
            options = options.map { option -> option.toRuntimeOption() },
            customControl = customControl?.toRuntimeCustomControl(),
        )
}

@Serializable
private data class RuntimeFieldBindingDto(
    @SerialName("data_path")
    val dataPath: String,
    @SerialName("entity_type")
    val entityType: String? = null,
) {
    fun toRuntimeBinding(): RuntimeFieldBinding =
        RuntimeFieldBinding(dataPath = dataPath, entityType = entityType)
}

@Serializable
private data class RuntimeFieldValidationDto(
    @SerialName("min_length")
    val minLength: Int? = null,
    @SerialName("max_length")
    val maxLength: Int? = null,
    val minimum: Double? = null,
    val maximum: Double? = null,
    val pattern: String? = null,
    val message: String? = null,
) {
    fun toRuntimeValidation(): RuntimeFieldValidation =
        RuntimeFieldValidation(
            minLength = minLength,
            maxLength = maxLength,
            minimum = minimum,
            maximum = maximum,
            pattern = pattern,
            message = message,
        )
}

@Serializable
private data class RuntimeFieldRuleDto(
    @SerialName("rule_type")
    val ruleType: String,
    val expression: String,
) {
    fun toRuntimeRule(): RuntimeFieldRule =
        RuntimeFieldRule(ruleType = ruleType, expression = expression)
}

@Serializable
private data class RuntimeFieldOptionDto(
    val value: String,
    val label: String,
    val disabled: Boolean = false,
) {
    fun toRuntimeOption(): RuntimeFieldOption =
        RuntimeFieldOption(value = value, label = label, disabled = disabled)
}

@Serializable
private data class RuntimeCustomControlDto(
    @SerialName("control_id")
    val controlId: String,
    @SerialName("runtime_widget")
    val runtimeWidget: String,
) {
    fun toRuntimeCustomControl(): RuntimeCustomControl =
        RuntimeCustomControl(controlId = controlId, runtimeWidget = runtimeWidget)
}

@Serializable
private data class RuntimeFormSubmitActionDto(
    @SerialName("action_type")
    val actionType: String,
    val target: String? = null,
) {
    fun toRuntimeSubmitAction(): RuntimeFormSubmitAction =
        RuntimeFormSubmitAction(actionType = actionType, target = target)
}

@Serializable
private data class RuntimeFormOfflineDto(
    val enabled: Boolean,
    @SerialName("queue_submissions")
    val queueSubmissions: Boolean,
    @SerialName("conflict_policy")
    val conflictPolicy: String? = null,
) {
    fun toRuntimeOffline(): RuntimeFormOffline =
        RuntimeFormOffline(
            enabled = enabled,
            queueSubmissions = queueSubmissions,
            conflictPolicy = conflictPolicy,
        )
}
