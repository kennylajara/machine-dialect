//! Integration tests for string operations

use machine_dialect_vm::{VM, Value, BytecodeModule};
use machine_dialect_vm::instructions::Instruction;
use machine_dialect_vm::values::ConstantPool;
use std::collections::HashMap;

fn create_string_concat_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let s1 = constants.add_string("Hello, ".to_string());
    let s2 = constants.add_string("World!".to_string());
    let s3 = constants.add_string(" How are you?".to_string());

    let instructions = vec![
        // Load strings
        Instruction::LoadConstR { dst: 0, const_idx: s1 },    // r0 = "Hello, "
        Instruction::LoadConstR { dst: 1, const_idx: s2 },    // r1 = "World!"
        Instruction::LoadConstR { dst: 2, const_idx: s3 },    // r2 = " How are you?"

        // Concatenate first two
        Instruction::ConcatR { dst: 3, left: 0, right: 1 },   // r3 = "Hello, " + "World!"

        // Concatenate result with third
        Instruction::ConcatR { dst: 4, left: 3, right: 2 },   // r4 = r3 + " How are you?"

        Instruction::ReturnR { src: Some(4) },
    ];

    BytecodeModule {
        name: "string_concat_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

fn create_string_comparison_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let s1 = constants.add_string("apple".to_string());
    let s2 = constants.add_string("banana".to_string());
    let s3 = constants.add_string("apple".to_string());
    let s4 = constants.add_string("APPLE".to_string());

    let instructions = vec![
        // Load strings
        Instruction::LoadConstR { dst: 0, const_idx: s1 },    // r0 = "apple"
        Instruction::LoadConstR { dst: 1, const_idx: s2 },    // r1 = "banana"
        Instruction::LoadConstR { dst: 2, const_idx: s3 },    // r2 = "apple"
        Instruction::LoadConstR { dst: 3, const_idx: s4 },    // r3 = "APPLE"

        // Test equality
        Instruction::EqR { dst: 4, left: 0, right: 2 },       // r4 = "apple" == "apple" (true)
        Instruction::EqR { dst: 5, left: 0, right: 1 },       // r5 = "apple" == "banana" (false)
        Instruction::EqR { dst: 6, left: 0, right: 3 },       // r6 = "apple" == "APPLE" (false)

        // Test inequality
        Instruction::NeqR { dst: 7, left: 0, right: 1 },      // r7 = "apple" != "banana" (true)

        // Test ordering
        Instruction::LtR { dst: 8, left: 0, right: 1 },       // r8 = "apple" < "banana" (true)
        Instruction::GtR { dst: 9, left: 1, right: 0 },       // r9 = "banana" > "apple" (true)

        // Return first equality result
        Instruction::ReturnR { src: Some(4) },
    ];

    BytecodeModule {
        name: "string_comparison_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

fn create_string_length_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let s1 = constants.add_string("Hello".to_string());
    let s2 = constants.add_string("".to_string());
    let s3 = constants.add_string("A longer string with spaces".to_string());

    let instructions = vec![
        // Load strings
        Instruction::LoadConstR { dst: 0, const_idx: s1 },    // r0 = "Hello"
        Instruction::LoadConstR { dst: 1, const_idx: s2 },    // r1 = ""
        Instruction::LoadConstR { dst: 2, const_idx: s3 },    // r2 = "A longer string with spaces"

        // Get lengths
        Instruction::LenR { dst: 3, src: 0 },                 // r3 = len("Hello") = 5
        Instruction::LenR { dst: 4, src: 1 },                 // r4 = len("") = 0
        Instruction::LenR { dst: 5, src: 2 },                 // r5 = len("A longer...") = 27

        // Sum the lengths
        Instruction::AddR { dst: 6, left: 3, right: 4 },      // r6 = 5 + 0
        Instruction::AddR { dst: 7, left: 6, right: 5 },      // r7 = 5 + 27 = 32

        Instruction::ReturnR { src: Some(7) },
    ];

    BytecodeModule {
        name: "string_length_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

fn create_string_slice_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let s = constants.add_string("Hello, World!".to_string());
    let i0 = constants.add_int(0);
    let i5 = constants.add_int(5);
    let i7 = constants.add_int(7);
    let i12 = constants.add_int(12);

    let instructions = vec![
        // Load string and indices
        Instruction::LoadConstR { dst: 0, const_idx: s },     // r0 = "Hello, World!"
        Instruction::LoadConstR { dst: 1, const_idx: i0 },    // r1 = 0
        Instruction::LoadConstR { dst: 2, const_idx: i5 },    // r2 = 5
        Instruction::LoadConstR { dst: 3, const_idx: i7 },    // r3 = 7
        Instruction::LoadConstR { dst: 4, const_idx: i12 },   // r4 = 12

        // Extract substrings
        Instruction::SliceR { dst: 5, src: 0, start: 1, end: 2 },  // r5 = s[0:5] = "Hello"
        Instruction::SliceR { dst: 6, src: 0, start: 3, end: 4 },  // r6 = s[7:12] = "World"

        // Concatenate with exclamation
        Instruction::LoadConstR { dst: 7, const_idx: constants.add_string("!".to_string()) },
        Instruction::ConcatR { dst: 8, left: 5, right: 7 },   // r8 = "Hello" + "!" = "Hello!"

        Instruction::ReturnR { src: Some(8) },
    ];

    BytecodeModule {
        name: "string_slice_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

fn create_mixed_type_operations_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let s1 = constants.add_string("The answer is: ".to_string());
    let i42 = constants.add_int(42);
    let s2 = constants.add_string("42".to_string());

    let instructions = vec![
        // Load values
        Instruction::LoadConstR { dst: 0, const_idx: s1 },    // r0 = "The answer is: "
        Instruction::LoadConstR { dst: 1, const_idx: i42 },   // r1 = 42
        Instruction::LoadConstR { dst: 2, const_idx: s2 },    // r2 = "42"

        // Convert int to string
        Instruction::ToStringR { dst: 3, src: 1 },            // r3 = str(42) = "42"

        // Concatenate
        Instruction::ConcatR { dst: 4, left: 0, right: 3 },   // r4 = "The answer is: " + "42"

        // Compare string representations
        Instruction::EqR { dst: 5, left: 3, right: 2 },       // r5 = "42" == "42" (true)

        Instruction::ReturnR { src: Some(4) },
    ];

    BytecodeModule {
        name: "mixed_type_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

#[test]
fn test_string_concatenation() {
    let mut vm = VM::new();
    let module = create_string_concat_module();
    vm.load_module(module, None).unwrap();

    let result = vm.run().unwrap();

    assert_eq!(
        result,
        Some(Value::String("Hello, World! How are you?".to_string()))
    );
}

#[test]
fn test_string_comparison() {
    let mut vm = VM::new();
    let module = create_string_comparison_module();
    vm.load_module(module, None).unwrap();

    // Execute comparisons
    for _ in 0..10 {
        vm.step().unwrap();
    }

    // Check comparison results
    assert_eq!(vm.registers.get(4), &Value::Bool(true));   // "apple" == "apple"
    assert_eq!(vm.registers.get(5), &Value::Bool(false));  // "apple" == "banana"
    assert_eq!(vm.registers.get(6), &Value::Bool(false));  // "apple" == "APPLE"
    assert_eq!(vm.registers.get(7), &Value::Bool(true));   // "apple" != "banana"
    assert_eq!(vm.registers.get(8), &Value::Bool(true));   // "apple" < "banana"
    assert_eq!(vm.registers.get(9), &Value::Bool(true));   // "banana" > "apple"

    // Execute return
    let result = vm.step().unwrap();
    assert_eq!(result, Some(Value::Bool(true)));
}

#[test]
fn test_string_length() {
    let mut vm = VM::new();
    let module = create_string_length_module();
    vm.load_module(module, None).unwrap();

    // Step through to check individual lengths
    for _ in 0..6 {
        vm.step().unwrap();
    }

    assert_eq!(vm.registers.get(3), &Value::Int(5));   // len("Hello")
    assert_eq!(vm.registers.get(4), &Value::Int(0));   // len("")
    assert_eq!(vm.registers.get(5), &Value::Int(27));  // len("A longer string with spaces")

    // Run to completion
    let result = vm.run().unwrap();
    assert_eq!(result, Some(Value::Int(32)));  // Sum of lengths
}

#[test]
fn test_string_slicing() {
    let mut vm = VM::new();
    let module = create_string_slice_module();
    vm.load_module(module, None).unwrap();

    // Execute slicing operations
    for _ in 0..7 {
        vm.step().unwrap();
    }

    // Check sliced strings
    assert_eq!(vm.registers.get(5), &Value::String("Hello".to_string()));
    assert_eq!(vm.registers.get(6), &Value::String("World".to_string()));

    // Run to completion
    let result = vm.run().unwrap();
    assert_eq!(result, Some(Value::String("Hello!".to_string())));
}

#[test]
fn test_mixed_type_operations() {
    let mut vm = VM::new();
    let module = create_mixed_type_operations_module();
    vm.load_module(module, None).unwrap();

    // Execute through conversion
    for _ in 0..4 {
        vm.step().unwrap();
    }

    // Check int to string conversion
    assert_eq!(vm.registers.get(3), &Value::String("42".to_string()));

    // Run to completion
    let result = vm.run().unwrap();
    assert_eq!(result, Some(Value::String("The answer is: 42".to_string())));
}

#[test]
fn test_empty_string_operations() {
    let mut constants = ConstantPool::new();
    let empty = constants.add_string("".to_string());
    let hello = constants.add_string("Hello".to_string());

    let instructions = vec![
        Instruction::LoadConstR { dst: 0, const_idx: empty },
        Instruction::LoadConstR { dst: 1, const_idx: hello },

        // Empty + Hello = Hello
        Instruction::ConcatR { dst: 2, left: 0, right: 1 },

        // Hello + Empty = Hello
        Instruction::ConcatR { dst: 3, left: 1, right: 0 },

        // Empty + Empty = Empty
        Instruction::ConcatR { dst: 4, left: 0, right: 0 },

        // Length of empty
        Instruction::LenR { dst: 5, src: 0 },

        // Empty == Empty
        Instruction::EqR { dst: 6, left: 0, right: 0 },

        Instruction::ReturnR { src: Some(6) },
    ];

    let module = BytecodeModule {
        name: "empty_string_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    };

    let mut vm = VM::new();
    vm.load_module(module, None).unwrap();

    // Run all operations
    for _ in 0..7 {
        vm.step().unwrap();
    }

    assert_eq!(vm.registers.get(2), &Value::String("Hello".to_string()));
    assert_eq!(vm.registers.get(3), &Value::String("Hello".to_string()));
    assert_eq!(vm.registers.get(4), &Value::String("".to_string()));
    assert_eq!(vm.registers.get(5), &Value::Int(0));
    assert_eq!(vm.registers.get(6), &Value::Bool(true));

    let result = vm.step().unwrap();
    assert_eq!(result, Some(Value::Bool(true)));
}
