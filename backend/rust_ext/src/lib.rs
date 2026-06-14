use pyo3::prelude::*;

const EXTENSION_VERSION: &str = env!("CARGO_PKG_VERSION");

#[pyfunction]
fn extension_version() -> &'static str {
    EXTENSION_VERSION
}

#[pyfunction]
fn health_check() -> &'static str {
    "ok"
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
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
}
