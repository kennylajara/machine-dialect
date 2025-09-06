//! Integration tests for control flow operations

use machine_dialect_vm::{VM, Value, BytecodeModule};
use machine_dialect_vm::instructions::Instruction;
use machine_dialect_vm::values::ConstantPool;
use std::collections::HashMap;

fn create_if_else_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let c_true = constants.add_bool(true);
    let c_false = constants.add_bool(false);
    let c10 = constants.add_int(10);
    let c20 = constants.add_int(20);
    let c30 = constants.add_int(30);

    let instructions = vec![
        // Test if-else with true condition
        Instruction::LoadConstR { dst: 0, const_idx: c_true },    // r0 = true
        Instruction::JumpIfNotR { cond: 0, offset: 2 },           // if !r0 jump +2
        Instruction::LoadConstR { dst: 1, const_idx: c10 },       // r1 = 10 (then branch)
        Instruction::JumpR { offset: 1 },                         // jump over else
        Instruction::LoadConstR { dst: 1, const_idx: c20 },       // r1 = 20 (else branch)

        // Test if-else with false condition
        Instruction::LoadConstR { dst: 2, const_idx: c_false },   // r2 = false
        Instruction::JumpIfNotR { cond: 2, offset: 2 },           // if !r2 jump +2
        Instruction::LoadConstR { dst: 3, const_idx: c30 },       // r3 = 30 (then - skipped)
        Instruction::JumpR { offset: 1 },                         // jump over else
        Instruction::LoadConstR { dst: 3, const_idx: c10 },       // r3 = 10 (else - executed)

        Instruction::ReturnR { src: Some(1) },
    ];

    BytecodeModule {
        name: "if_else_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

fn create_loop_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let c0 = constants.add_int(0);
    let c1 = constants.add_int(1);
    let c5 = constants.add_int(5);

    let instructions = vec![
        // Simple counter loop: count from 0 to 4
        Instruction::LoadConstR { dst: 0, const_idx: c0 },    // r0 = 0 (counter)
        Instruction::LoadConstR { dst: 1, const_idx: c5 },    // r1 = 5 (limit)
        Instruction::LoadConstR { dst: 2, const_idx: c0 },    // r2 = 0 (sum)
        Instruction::LoadConstR { dst: 3, const_idx: c1 },    // r3 = 1 (increment)

        // Loop start (PC = 4)
        Instruction::GteR { dst: 4, left: 0, right: 1 },      // r4 = r0 >= r1
        Instruction::JumpIfR { cond: 4, offset: 4 },          // if r4 jump +4 (exit loop)
        Instruction::AddR { dst: 2, left: 2, right: 0 },      // r2 = r2 + r0 (add to sum)
        Instruction::AddR { dst: 0, left: 0, right: 3 },      // r0 = r0 + 1 (increment)
        Instruction::JumpR { offset: -4 },                    // jump back to loop start

        // Loop exit - sum should be 0+1+2+3+4 = 10
        Instruction::ReturnR { src: Some(2) },
    ];

    BytecodeModule {
        name: "loop_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

fn create_nested_conditions_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let c5 = constants.add_int(5);
    let c10 = constants.add_int(10);
    let c15 = constants.add_int(15);
    let c100 = constants.add_int(100);
    let c200 = constants.add_int(200);
    let c300 = constants.add_int(300);

    let instructions = vec![
        // Setup: x = 10, y = 5
        Instruction::LoadConstR { dst: 0, const_idx: c10 },   // r0 = 10 (x)
        Instruction::LoadConstR { dst: 1, const_idx: c5 },    // r1 = 5 (y)

        // if (x > y)
        Instruction::GtR { dst: 2, left: 0, right: 1 },       // r2 = x > y
        Instruction::JumpIfNotR { cond: 2, offset: 9 },       // if !r2 jump to else

        // then: if (x > 15)
        Instruction::LoadConstR { dst: 3, const_idx: c15 },   // r3 = 15
        Instruction::GtR { dst: 4, left: 0, right: 3 },       // r4 = x > 15
        Instruction::JumpIfNotR { cond: 4, offset: 2 },       // if !r4 jump to inner else
        Instruction::LoadConstR { dst: 5, const_idx: c300 },  // r5 = 300
        Instruction::JumpR { offset: 1 },                     // jump over inner else
        Instruction::LoadConstR { dst: 5, const_idx: c200 },  // r5 = 200
        Instruction::JumpR { offset: 1 },                     // jump to end

        // else:
        Instruction::LoadConstR { dst: 5, const_idx: c100 },  // r5 = 100

        // Result should be 200 (x > y is true, x > 15 is false)
        Instruction::ReturnR { src: Some(5) },
    ];

    BytecodeModule {
        name: "nested_conditions_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

#[test]
fn test_if_else() {
    let mut vm = VM::new();
    let module = create_if_else_module();
    vm.load_module(module, None).unwrap();

    // Execute all instructions
    for _ in 0..5 {
        vm.step().unwrap();
    }

    // Check that true branch was taken (r1 = 10)
    assert_eq!(vm.registers.get(1), &Value::Int(10));

    // Continue execution
    for _ in 0..5 {
        vm.step().unwrap();
    }

    // Check that else branch was taken for false condition (r3 = 10)
    assert_eq!(vm.registers.get(3), &Value::Int(10));

    // Execute return
    let result = vm.step().unwrap();
    assert_eq!(result, Some(Value::Int(10)));
}

#[test]
fn test_loop() {
    let mut vm = VM::new();
    let module = create_loop_module();
    vm.load_module(module, None).unwrap();

    // Run the entire loop
    let result = vm.run().unwrap();

    // Sum of 0+1+2+3+4 = 10
    assert_eq!(result, Some(Value::Int(10)));
}

#[test]
fn test_loop_iterations() {
    let mut vm = VM::new();
    let module = create_loop_module();
    vm.load_module(module, None).unwrap();

    // Setup phase
    for _ in 0..4 {
        vm.step().unwrap();
    }

    // Track sum through iterations
    let mut iteration = 0;
    let expected_sums = [0, 0, 1, 3, 6, 10];

    while vm.pc < vm.instructions.len() - 1 {
        if vm.pc == 6 {  // After sum update
            assert_eq!(vm.registers.get(2), &Value::Int(expected_sums[iteration]));
            iteration += 1;
        }
        vm.step().unwrap();
    }

    // Final return
    let result = vm.step().unwrap();
    assert_eq!(result, Some(Value::Int(10)));
}

#[test]
fn test_nested_conditions() {
    let mut vm = VM::new();
    let module = create_nested_conditions_module();
    vm.load_module(module, None).unwrap();

    let result = vm.run().unwrap();

    // With x=10, y=5: x > y is true, x > 15 is false, so result = 200
    assert_eq!(result, Some(Value::Int(200)));
}

#[test]
fn test_jump_forward_backward() {
    let mut constants = ConstantPool::new();
    let c1 = constants.add_int(1);
    let c2 = constants.add_int(2);
    let c3 = constants.add_int(3);

    let instructions = vec![
        Instruction::LoadConstR { dst: 0, const_idx: c1 },  // r0 = 1
        Instruction::JumpR { offset: 2 },                   // jump forward +2
        Instruction::LoadConstR { dst: 0, const_idx: c2 },  // r0 = 2 (skipped)
        Instruction::LoadConstR { dst: 0, const_idx: c3 },  // r0 = 3 (skipped)
        Instruction::LoadConstR { dst: 1, const_idx: c2 },  // r1 = 2
        Instruction::JumpR { offset: -2 },                  // jump backward -2
        Instruction::ReturnR { src: Some(0) },              // (skipped initially)
    ];

    let module = BytecodeModule {
        name: "jump_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    };

    let mut vm = VM::new();
    vm.load_module(module, None).unwrap();

    // Execute: Load 1, Jump +2 to PC=3
    vm.step().unwrap();
    vm.step().unwrap();
    assert_eq!(vm.pc, 3);

    // Execute: Load r1 = 2
    vm.step().unwrap();
    assert_eq!(vm.registers.get(1), &Value::Int(2));

    // Execute: Jump -2 to PC=3 (LoadConstR r0 = 3)
    vm.step().unwrap();
    assert_eq!(vm.pc, 3);

    // Execute: Load r0 = 3
    vm.step().unwrap();
    assert_eq!(vm.registers.get(0), &Value::Int(3));

    // Final result
    let result = vm.run().unwrap();
    assert_eq!(result, Some(Value::Int(3)));
}
