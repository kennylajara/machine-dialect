//! PyO3 VM bindings
//!
//! This module provides the Python interface to the Rust VM.

use std::path::PathBuf;

use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;

use crate::vm::VM;
use crate::loader::BytecodeLoader;

/// Rust VM exposed to Python
#[pyclass]
pub struct RustVM {
    vm: VM,
}

#[pymethods]
impl RustVM {
    /// Create a new VM instance
    #[new]
    pub fn new() -> PyResult<Self> {
        Ok(Self {
            vm: VM::new(),
        })
    }

    /// Load bytecode from file
    pub fn load_bytecode(&mut self, path: String) -> PyResult<()> {
        let path = PathBuf::from(path);
        let (module, metadata) = BytecodeLoader::load_module(&path)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to load bytecode: {}", e)))?;

        self.vm.load_module(module, metadata)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to load module: {}", e)))?;

        Ok(())
    }

    /// Execute the loaded bytecode
    pub fn execute(&mut self) -> PyResult<Option<PyObject>> {
        match self.vm.run() {
            Ok(Some(value)) => {
                Python::with_gil(|py| {
                    Ok(Some(self.value_to_python(py, &value)))
                })
            }
            Ok(None) => Ok(None),
            Err(e) => Err(PyRuntimeError::new_err(format!("Runtime error: {}", e))),
        }
    }

    /// Set debug mode
    pub fn set_debug(&mut self, debug: bool) {
        self.vm.debug_mode = debug;
    }

    /// Get instruction count
    pub fn instruction_count(&self) -> usize {
        self.vm.instruction_count
    }
}

// Helper methods implementation (not exposed to Python)
impl RustVM {
    /// Convert a Rust value to Python
    fn value_to_python(&self, py: Python<'_>, value: &crate::values::Value) -> PyObject {
        use crate::values::Value;

        match value {
            Value::Empty => py.None(),
            Value::Bool(b) => b.into_py(py),
            Value::Int(i) => i.into_py(py),
            Value::Float(f) => f.into_py(py),
            Value::String(s) => s.as_ref().into_py(py),
            Value::URL(u) => u.as_ref().into_py(py),
            Value::Function(f) => format!("function<{}>", f.name).into_py(py),
        }
    }
}

/// Python module for the VM
#[pymodule]
fn machine_dialect_vm(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RustVM>()?;
    m.add("__version__", crate::VM_VERSION)?;
    Ok(())
}
