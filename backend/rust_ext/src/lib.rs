use std::collections::BTreeSet;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use serde_json::{json, Value};
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
fn diff_app_json(old_input: &str, new_input: &str) -> PyResult<String> {
    diff_app_json_str(old_input, new_input)
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

fn diff_app_json_str(old_input: &str, new_input: &str) -> Result<String, serde_json::Error> {
    let old_value: Value = serde_json::from_str(old_input)?;
    let new_value: Value = serde_json::from_str(new_input)?;
    let mut changes = Vec::new();
    diff_values("$", &old_value, &new_value, &mut changes);
    serde_json::to_string(&changes)
}

fn diff_values(path: &str, old_value: &Value, new_value: &Value, changes: &mut Vec<Value>) {
    if old_value == new_value {
        return;
    }

    match (old_value, new_value) {
        (Value::Object(old_map), Value::Object(new_map)) => {
            let keys: BTreeSet<_> = old_map.keys().chain(new_map.keys()).collect();
            for key in keys {
                let child_path = object_path(path, key);
                match (old_map.get(key), new_map.get(key)) {
                    (Some(old_child), Some(new_child)) => {
                        diff_values(&child_path, old_child, new_child, changes);
                    }
                    (Some(old_child), None) => {
                        changes.push(json!({
                            "change_type": "removed",
                            "path": child_path,
                            "old": old_child
                        }));
                    }
                    (None, Some(new_child)) => {
                        changes.push(json!({
                            "change_type": "added",
                            "path": child_path,
                            "new": new_child
                        }));
                    }
                    (None, None) => {}
                }
            }
        }
        (Value::Array(old_items), Value::Array(new_items)) => {
            let shared_len = old_items.len().min(new_items.len());
            for index in 0..shared_len {
                let child_path = array_path(path, index);
                diff_values(&child_path, &old_items[index], &new_items[index], changes);
            }
            for (index, old_child) in old_items.iter().enumerate().skip(shared_len) {
                changes.push(json!({
                    "change_type": "removed",
                    "path": array_path(path, index),
                    "old": old_child
                }));
            }
            for (index, new_child) in new_items.iter().enumerate().skip(shared_len) {
                changes.push(json!({
                    "change_type": "added",
                    "path": array_path(path, index),
                    "new": new_child
                }));
            }
        }
        _ => {
            changes.push(json!({
                "change_type": "changed",
                "path": path,
                "old": old_value,
                "new": new_value
            }));
        }
    }
}

fn object_path(parent: &str, key: &str) -> String {
    format!("{parent}.{key}")
}

fn array_path(parent: &str, index: usize) -> String {
    format!("{parent}[{index}]")
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
    m.add_function(wrap_pyfunction!(diff_app_json, m)?)?;
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
    fn diff_app_json_returns_empty_array_for_unchanged_input() {
        let diff =
            diff_app_json_str(r#"{"app_id":"field_ops"}"#, r#"{"app_id":"field_ops"}"#).unwrap();
        assert_eq!(serde_json::from_str::<Value>(&diff).unwrap(), json!([]));
    }

    #[test]
    fn diff_app_json_reports_added_removed_and_changed_paths() {
        let diff = diff_app_json_str(
            r#"{"app_id":"field_ops","name":"Old","theme_id":"legacy"}"#,
            r#"{"app_id":"field_ops","name":"New","version":"1.0.0"}"#,
        )
        .unwrap();
        assert_eq!(
            serde_json::from_str::<Value>(&diff).unwrap(),
            json!([
                {
                    "change_type": "changed",
                    "path": "$.name",
                    "old": "Old",
                    "new": "New"
                },
                {
                    "change_type": "removed",
                    "path": "$.theme_id",
                    "old": "legacy"
                },
                {
                    "change_type": "added",
                    "path": "$.version",
                    "new": "1.0.0"
                }
            ])
        );
    }

    #[test]
    fn diff_app_json_reports_nested_array_paths() {
        let diff = diff_app_json_str(
            r#"{"screens":[{"screen_id":"home","name":"Home"}]}"#,
            r#"{"screens":[{"screen_id":"home","name":"Start"},{"screen_id":"settings"}]}"#,
        )
        .unwrap();
        assert_eq!(
            serde_json::from_str::<Value>(&diff).unwrap(),
            json!([
                {
                    "change_type": "changed",
                    "path": "$.screens[0].name",
                    "old": "Home",
                    "new": "Start"
                },
                {
                    "change_type": "added",
                    "path": "$.screens[1]",
                    "new": {"screen_id": "settings"}
                }
            ])
        );
    }

    #[test]
    fn diff_app_json_rejects_invalid_input() {
        assert!(diff_app_json_str(r#"{"missing": "brace""#, r#"{"ok":true}"#).is_err());
        assert!(diff_app_json_str(r#"{"ok":true}"#, r#"{"missing": "brace""#).is_err());
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
