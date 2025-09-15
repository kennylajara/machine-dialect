//! Integration tests for dictionary operations

use machine_dialect_vm::{VM, Value, BytecodeModule};
use machine_dialect_vm::instructions::Instruction;
use machine_dialect_vm::values::ConstantPool;
use std::collections::HashMap;
use std::sync::Arc;

/// Test basic dictionary creation and operations
#[test]
fn test_dict_basic_operations() {
    let mut vm = VM::new();

    // Create constants pool
    let mut constants = ConstantPool::new();
    let name_idx = constants.add_string("name".to_string());
    let alice_idx = constants.add_string("Alice".to_string());

    // Create instructions for dict operations
    let instructions = vec![
        Instruction::DictNewR { dst: 0 }, // Create dict in r0

        // Load string constants
        Instruction::LoadConstR { dst: 1, const_idx: name_idx },   // r1 = "name"
        Instruction::LoadConstR { dst: 2, const_idx: alice_idx },  // r2 = "Alice"

        // Set dict["name"] = "Alice"
        Instruction::DictSetR { dict: 0, key: 1, value: 2 },

        // Get dict["name"] into r3
        Instruction::DictGetR { dst: 3, dict: 0, key: 1 },

        // Check if "name" is in dict, result in r4
        Instruction::DictContainsR { dst: 4, dict: 0, key: 1 },

        // Get dict length into r5
        Instruction::DictLenR { dst: 5, dict: 0 },

        Instruction::Halt,
    ];

    // Create bytecode module
    let module = BytecodeModule {
        name: "dict_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    };

    // Load and run the module
    vm.load_module(module, None).expect("Failed to load module");
    vm.run().expect("Failed to run VM");

    // Check the results
    // r0 should be a dict
    let dict = vm.registers.get(0);
    assert!(matches!(dict, Value::Dict(_)));

    // r3 should be "Alice" (value retrieved from dict)
    let retrieved = vm.registers.get(3);
    assert_eq!(retrieved, &Value::String(Arc::new("Alice".to_string())));

    // r4 should be true (key exists)
    let contains = vm.registers.get(4);
    assert_eq!(contains, &Value::Bool(true));

    // r5 should be 1 (dict has one entry)
    let length = vm.registers.get(5);
    assert_eq!(length, &Value::Int(1));
}

/// Test dictionary keys and values extraction
#[test]
fn test_dict_keys_values() {
    let mut vm = VM::new();

    // Create constants pool
    let mut constants = ConstantPool::new();
    let key1_idx = constants.add_string("key1".to_string());
    let value1_idx = constants.add_string("value1".to_string());
    let key2_idx = constants.add_string("key2".to_string());
    let value2_idx = constants.add_string("value2".to_string());

    let instructions = vec![
        // Create dict in r0
        Instruction::DictNewR { dst: 0 },

        // Load constants
        Instruction::LoadConstR { dst: 1, const_idx: key1_idx },     // r1 = "key1"
        Instruction::LoadConstR { dst: 2, const_idx: value1_idx },   // r2 = "value1"
        Instruction::LoadConstR { dst: 3, const_idx: key2_idx },     // r3 = "key2"
        Instruction::LoadConstR { dst: 4, const_idx: value2_idx },   // r4 = "value2"

        // Set dict["key1"] = "value1"
        Instruction::DictSetR { dict: 0, key: 1, value: 2 },

        // Set dict["key2"] = "value2"
        Instruction::DictSetR { dict: 0, key: 3, value: 4 },

        // Get keys into r5
        Instruction::DictKeysR { dst: 5, dict: 0 },

        // Get values into r6
        Instruction::DictValuesR { dst: 6, dict: 0 },

        Instruction::Halt,
    ];

    let module = BytecodeModule {
        name: "dict_keys_values_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    };

    vm.load_module(module, None).expect("Failed to load module");
    vm.run().expect("Failed to run VM");

    // r5 should be an array of keys
    let keys = vm.registers.get(5);
    if let Value::Array(arr) = keys {
        assert_eq!(arr.len(), 2);
        // Keys might be in any order
        let keys_set: std::collections::HashSet<_> = arr.iter()
            .filter_map(|v| if let Value::String(s) = v { Some(s.as_ref().clone()) } else { None })
            .collect();
        assert!(keys_set.contains("key1"));
        assert!(keys_set.contains("key2"));
    } else {
        panic!("Expected array of keys");
    }

    // r6 should be an array of values
    let values = vm.registers.get(6);
    if let Value::Array(arr) = values {
        assert_eq!(arr.len(), 2);
        // Values might be in any order
        let values_set: std::collections::HashSet<_> = arr.iter()
            .filter_map(|v| if let Value::String(s) = v { Some(s.as_ref().clone()) } else { None })
            .collect();
        assert!(values_set.contains("value1"));
        assert!(values_set.contains("value2"));
    } else {
        panic!("Expected array of values");
    }
}

/// Test dictionary remove and clear operations
#[test]
fn test_dict_remove_clear() {
    let mut vm = VM::new();

    // Create constants pool
    let mut constants = ConstantPool::new();
    let key1_idx = constants.add_string("key1".to_string());
    let value1_idx = constants.add_string("value1".to_string());

    let instructions = vec![
        // Create dict in r0
        Instruction::DictNewR { dst: 0 },

        // Load constants
        Instruction::LoadConstR { dst: 1, const_idx: key1_idx },     // r1 = "key1"
        Instruction::LoadConstR { dst: 2, const_idx: value1_idx },   // r2 = "value1"

        // Set dict["key1"] = "value1"
        Instruction::DictSetR { dict: 0, key: 1, value: 2 },

        // Get length before remove (should be 1)
        Instruction::DictLenR { dst: 3, dict: 0 },

        // Remove "key1"
        Instruction::DictRemoveR { dict: 0, key: 1 },

        // Get length after remove (should be 0)
        Instruction::DictLenR { dst: 4, dict: 0 },

        // Add it back
        Instruction::DictSetR { dict: 0, key: 1, value: 2 },

        // Clear the dict
        Instruction::DictClearR { dict: 0 },

        // Get length after clear (should be 0)
        Instruction::DictLenR { dst: 5, dict: 0 },

        Instruction::Halt,
    ];

    let module = BytecodeModule {
        name: "dict_remove_clear_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    };

    vm.load_module(module, None).expect("Failed to load module");
    vm.run().expect("Failed to run VM");

    // r3 should be 1 (before remove)
    assert_eq!(vm.registers.get(3), &Value::Int(1));

    // r4 should be 0 (after remove)
    assert_eq!(vm.registers.get(4), &Value::Int(0));

    // r5 should be 0 (after clear)
    assert_eq!(vm.registers.get(5), &Value::Int(0));
}
