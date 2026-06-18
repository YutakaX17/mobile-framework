# Mobile Runtime Testing

Mobile runtime coverage currently uses Kotlin Multiplatform common tests plus lightweight repository validation.

## Coverage Baseline

The shared runtime requires common test coverage for every Kotlin source under:

```text
mobile/shared/src/commonMain/kotlin/org/khodola/mobile/runtime
```

The shared Compose shell requires common test coverage for state logic under:

```text
mobile/composeApp/src/commonMain/kotlin/org/khodola/mobile/runtime/compose
```

`tools/validate_mobile_tests.py` enforces this baseline by checking that each tracked source file has a matching test file and that every matching test file declares at least one `@Test`.

## Local Validation

Run mobile validation from the repository root:

```powershell
python tools/validate_mobile.py
python tools/validate_mobile_tests.py
```

Full Gradle build and test execution is intentionally deferred to the mobile Gradle test workflow task.
