//! Integration tests for arithmetic operations

use machine_dialect_vm::{VM, Value, BytecodeModule, BytecodeLoader};
use machine_dialect_vm::loader::BytecodeModule as Module;
use std::collections::HashMap;

fn create_arithmetic_module() -> BytecodeModule {
    use machine_dialect_vm::instructions::Instruction;
    use machine_dialect_vm::values::ConstantPool;

    let mut constants = ConstantPool::new();
    let c1 = constants.add_int(10);
    let c2 = constants.add_int(20);
    let c3 = constants.add_float(3.14);
    let c4 = constants.add_float(2.0);

    let instructions = vec![
        // Load constants
        Instruction::LoadConstR { dst: 0, const_idx: c1 },  // r0 = 10
        Instruction::LoadConstR { dst: 1, const_idx: c2 },  // r1 = 20
        Instruction::LoadConstR { dst: 2, const_idx: c3 },  // r2 = 3.14
        Instruction::LoadConstR { dst: 3, const_idx: c4 },  // r3 = 2.0

        // Integer arithmetic
        Instruction::AddR { dst: 4, left: 0, right: 1 },    // r4 = r0 + r1 = 30
        Instruction::SubR { dst: 5, left: 1, right: 0 },    // r5 = r1 - r0 = 10
        Instruction::MulR { dst: 6, left: 0, right: 1 },    // r6 = r0 * r1 = 200
        Instruction::DivR { dst: 7, left: 1, right: 0 },    // r7 = r1 / r0 = 2
        Instruction::ModR { dst: 8, left: 1, right: 0 },    // r8 = r1 % r0 = 0

        // Float arithmetic
        Instruction::AddR { dst: 9, left: 2, right: 3 },    // r9 = r2 + r3 = 5.14
        Instruction::MulR { dst: 10, left: 2, right: 3 },   // r10 = r2 * r3 = 6.28

        // Return the sum
        Instruction::ReturnR { src: Some(4) },
    ];

    BytecodeModule {
        name: "arithmetic_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

#[test]
fn test_integer_arithmetic() {
    let mut vm = VM::new();
    let module = create_arithmetic_module();
    vm.load_module(module, None).unwrap();

    let result = vm.run().unwrap();
    assert_eq!(result, Some(Value::Int(30)));
}

#[test]
fn test_arithmetic_operations() {
    let mut vm = VM::new();
    let module = create_arithmetic_module();
    vm.load_module(module.clone(), None).unwrap();

    // Execute step by step and check intermediate results
    for _ in 0..5 {
        vm.step().unwrap();
    }

    // Check addition result
    assert_eq!(vm.registers.get(4), &Value::Int(30));

    vm.step().unwrap();
    // Check subtraction result
    assert_eq!(vm.registers.get(5), &Value::Int(10));

    vm.step().unwrap();
    // Check multiplication result
    assert_eq!(vm.registers.get(6), &Value::Int(200));

    vm.step().unwrap();
    // Check division result
    assert_eq!(vm.registers.get(7), &Value::Int(2));

    vm.step().unwrap();
    // Check modulo result
    assert_eq!(vm.registers.get(8), &Value::Int(0));
}

#[test]
fn test_float_arithmetic() {
    let mut vm = VM::new();
    let module = create_arithmetic_module();
    vm.load_module(module, None).unwrap();

    // Execute until float operations
    for _ in 0..10 {
        vm.step().unwrap();
    }

    // Check float addition
    if let Value::Float(f) = vm.registers.get(9) {
        assert!((f - 5.14).abs() < 0.001);
    } else {
        panic!("Expected float value");
    }

    vm.step().unwrap();

    // Check float multiplication
    if let Value::Float(f) = vm.registers.get(10) {
        assert!((f - 6.28).abs() < 0.001);
    } else {
        panic!("Expected float value");
    }
}

#[test]
fn test_negation() {
    use machine_dialect_vm::instructions::Instruction;
    use machine_dialect_vm::values::ConstantPool;

    let mut constants = ConstantPool::new();
    let c1 = constants.add_int(42);
    let c2 = constants.add_float(-3.14);

    let instructions = vec![
        Instruction::LoadConstR { dst: 0, const_idx: c1 },
        Instruction::LoadConstR { dst: 1, const_idx: c2 },
        Instruction::NegR { dst: 2, src: 0 },  // r2 = -42
        Instruction::NegR { dst: 3, src: 1 },  // r3 = 3.14
        Instruction::ReturnR { src: Some(2) },
    ];

    let module = BytecodeModule {
        name: "negation_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    };

    let mut vm = VM::new();
    vm.load_module(module, None).unwrap();

    vm.step().unwrap();
    vm.step().unwrap();
    vm.step().unwrap();

    assert_eq!(vm.registers.get(2), &Value::Int(-42));

    vm.step().unwrap();

    if let Value::Float(f) = vm.registers.get(3) {
        assert!((f - 3.14).abs() < 0.001);
    }
}
