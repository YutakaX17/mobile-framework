use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use serde_json::Value;
use sha2::{Digest, Sha256};

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

#[pyfunction]
fn hash_config_json(input: &str) -> PyResult<String> {
    hash_config_json_str(input)
        .map_err(|error| PyValueError::new_err(format!("invalid JSON input: {error}")))
}

#[pyfunction]
fn hash_package_json(input: &str) -> PyResult<String> {
    hash_package_json_str(input)
        .map_err(|error| PyValueError::new_err(format!("invalid JSON input: {error}")))
}

fn canonicalize_json_str(input: &str) -> Result<String, serde_json::Error> {
    let value: Value = serde_json::from_str(input)?;
    serde_json::to_string(&value)
}

fn hash_config_json_str(input: &str) -> Result<String, serde_json::Error> {
    canonical_json_sha256(input)
}

fn hash_package_json_str(input: &str) -> Result<String, serde_json::Error> {
    canonical_json_sha256(input)
}

fn canonical_json_sha256(input: &str) -> Result<String, serde_json::Error> {
    let canonical = canonicalize_json_str(input)?;
    let digest = Sha256::digest(canonical.as_bytes());
    Ok(format!("sha256:{}", to_lower_hex(&digest)))
}

fn to_lower_hex(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        output.push(HEX[(byte >> 4) as usize] as char);
        output.push(HEX[(byte & 0x0f) as usize] as char);
    }
    output
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(canonicalize_json, m)?)?;
    m.add_function(wrap_pyfunction!(extension_version, m)?)?;
    m.add_function(wrap_pyfunction!(hash_config_json, m)?)?;
    m.add_function(wrap_pyfunction!(hash_package_json, m)?)?;
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

    #[test]
    fn hash_config_json_is_stable_for_equivalent_object_ordering() {
        let first = hash_config_json_str(r#"{"z":3,"a":{"b":2,"a":1}}"#).unwrap();
        let second = hash_config_json_str(r#"{"a":{"a":1,"b":2},"z":3}"#).unwrap();
        assert_eq!(first, second);
    }

    #[test]
    fn hash_config_json_is_sensitive_to_array_order() {
        let first = hash_config_json_str(r#"{"items":[1,2,3]}"#).unwrap();
        let second = hash_config_json_str(r#"{"items":[3,2,1]}"#).unwrap();
        assert_ne!(first, second);
    }

    #[test]
    fn hash_config_json_returns_sha256_digest() {
        let digest = hash_config_json_str(r#"{"a":1}"#).unwrap();
        assert_eq!(
            digest,
            "sha256:015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862"
        );
    }

    #[test]
    fn hash_config_json_rejects_invalid_input() {
        assert!(hash_config_json_str(r#"{"missing": "brace""#).is_err());
    }

    #[test]
    fn hash_package_json_is_stable_for_equivalent_object_ordering() {
        let first = hash_package_json_str(
            r#"{"signature":"placeholder","hash":"sha256:abc","app":{"version":"1.0.0","app_id":"field_ops"}}"#,
        )
        .unwrap();
        let second = hash_package_json_str(
            r#"{"app":{"app_id":"field_ops","version":"1.0.0"},"hash":"sha256:abc","signature":"placeholder"}"#,
        )
        .unwrap();
        assert_eq!(first, second);
    }

    #[test]
    fn hash_package_json_is_sensitive_to_array_order() {
        let first = hash_package_json_str(r#"{"modules":["core","forms"]}"#).unwrap();
        let second = hash_package_json_str(r#"{"modules":["forms","core"]}"#).unwrap();
        assert_ne!(first, second);
    }

    #[test]
    fn hash_package_json_rejects_invalid_input() {
        assert!(hash_package_json_str(r#"{"missing": "brace""#).is_err());
    }
}
