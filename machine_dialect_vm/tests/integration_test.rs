//! Integration tests for the VM

use machine_dialect_vm::{VM, Value};

// Include dictionary tests
mod integration {
    mod test_dict;
}

#[test]
fn test_basic_arithmetic() {
    let vm = VM::new();

    // Test that VM can be created and initialized
    assert_eq!(vm.instruction_count, 0);
    assert!(!vm.debug_mode);
}

#[test]
fn test_value_system() {
    // Test value creation and comparison
    let v1 = Value::Int(42);
    let v2 = Value::Float(3.14);
    let v3 = Value::String(std::sync::Arc::new("test".to_string()));

    assert_eq!(v1, Value::Int(42));
    assert_ne!(v1, Value::Int(43));
    assert!(v2.is_truthy());
    assert!(v3.is_truthy());
    assert!(!Value::Empty.is_truthy());
}

#[test]
fn test_register_operations() {
    use machine_dialect_vm::vm::RegisterFile;

    let mut regs = RegisterFile::new();

    // Test register set and get
    regs.set(0, Value::Int(100));
    assert_eq!(regs.get(0), &Value::Int(100));

    regs.set(1, Value::String(std::sync::Arc::new("hello".to_string())));
    assert!(matches!(regs.get(1), Value::String(_)));
}
