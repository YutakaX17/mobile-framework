use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use serde_json::Value;

const EXTENSION_VERSION: &str = env!("CARGO_PKG_VERSION");

#[pyfunction]
fn extension_version() -> &'static str {
    EXTENSION_VERSION
}

#[pyfunction]
fn health_check() -> &'static str {
    "ok"
}

#[pyfunction]
fn canonicalize_json(input: &str) -> PyResult<String> {
    canonicalize_json_str(input)
        .map_err(|error| PyValueError::new_err(format!("invalid JSON input: {error}")))
}

fn canonicalize_json_str(input: &str) -> Result<String, serde_json::Error> {
    let value: Value = serde_json::from_str(input)?;
    serde_json::to_string(&value)
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(canonicalize_json, m)?)?;
    m.add_function(wrap_pyfunction!(extension_version, m)?)?;
    m.add_function(wrap_pyfunction!(health_check, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn extension_version_matches_crate_version() {
        assert_eq!(extension_version(), env!("CARGO_PKG_VERSION"));
    }

    #[test]
    fn health_check_reports_ok() {
        assert_eq!(health_check(), "ok");
    }

    #[test]
    fn canonicalize_json_orders_object_keys() {
        let canonical = canonicalize_json_str(r#"{"z":3,"a":1,"m":2}"#).unwrap();
        assert_eq!(canonical, r#"{"a":1,"m":2,"z":3}"#);
    }

    #[test]
    fn canonicalize_json_orders_nested_objects() {
        let canonical =
            canonicalize_json_str(r#"{"outer":{"b":true,"a":null},"items":[{"d":4,"c":3}]}"#)
                .unwrap();
        assert_eq!(
            canonical,
            r#"{"items":[{"c":3,"d":4}],"outer":{"a":null,"b":true}}"#
        );
    }

    #[test]
    fn canonicalize_json_preserves_array_order() {
        let canonical = canonicalize_json_str(r#"[{"b":2,"a":1},3,2,1]"#).unwrap();
        assert_eq!(canonical, r#"[{"a":1,"b":2},3,2,1]"#);
    }

    #[test]
    fn canonicalize_json_rejects_invalid_input() {
        assert!(canonicalize_json_str(r#"{"missing": "brace""#).is_err());
    }
}
