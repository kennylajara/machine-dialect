//! Integration tests for function calls

use machine_dialect_vm::{VM, Value, BytecodeModule};
use machine_dialect_vm::instructions::Instruction;
use machine_dialect_vm::values::ConstantPool;
use std::collections::HashMap;

fn create_simple_function_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let c5 = constants.add_int(5);
    let c10 = constants.add_int(10);

    // Function table: add_five at instruction 5
    let mut function_table = HashMap::new();
    function_table.insert("add_five".to_string(), 5);

    let instructions = vec![
        // Main: call add_five(10)
        Instruction::LoadConstR { dst: 0, const_idx: c10 },      // r0 = 10
        Instruction::CallR { func: 0, args: vec![0], dst: 1 },   // r1 = add_five(r0)
        Instruction::ReturnR { src: Some(1) },                   // return r1

        // Padding to reach function offset
        Instruction::Halt,
        Instruction::Halt,

        // add_five function at PC=5
        // Parameters in r0
        Instruction::LoadConstR { dst: 1, const_idx: c5 },       // r1 = 5
        Instruction::AddR { dst: 2, left: 0, right: 1 },         // r2 = r0 + r1
        Instruction::ReturnR { src: Some(2) },                   // return r2
    ];

    BytecodeModule {
        name: "simple_function_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table,
        global_names: Vec::new(),
    }
}

fn create_recursive_function_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let c0 = constants.add_int(0);
    let c1 = constants.add_int(1);
    let c5 = constants.add_int(5);

    // Function table: factorial at instruction 3
    let mut function_table = HashMap::new();
    function_table.insert("factorial".to_string(), 3);

    let instructions = vec![
        // Main: call factorial(5)
        Instruction::LoadConstR { dst: 0, const_idx: c5 },       // r0 = 5
        Instruction::CallR { func: 0, args: vec![0], dst: 1 },   // r1 = factorial(r0)
        Instruction::ReturnR { src: Some(1) },                   // return r1

        // factorial function at PC=3
        // Parameter n in r0
        Instruction::LoadConstR { dst: 1, const_idx: c1 },       // r1 = 1
        Instruction::LteR { dst: 2, left: 0, right: 1 },         // r2 = n <= 1
        Instruction::JumpIfNotR { cond: 2, offset: 2 },          // if !(n <= 1) jump +2
        Instruction::ReturnR { src: Some(1) },                   // return 1

        // Recursive case: n * factorial(n-1)
        Instruction::SubR { dst: 3, left: 0, right: 1 },         // r3 = n - 1
        Instruction::CallR { func: 0, args: vec![3], dst: 4 },   // r4 = factorial(n-1)
        Instruction::MulR { dst: 5, left: 0, right: 4 },         // r5 = n * factorial(n-1)
        Instruction::ReturnR { src: Some(5) },                   // return r5
    ];

    BytecodeModule {
        name: "recursive_function_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table,
        global_names: Vec::new(),
    }
}

fn create_multiple_args_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let c2 = constants.add_int(2);
    let c3 = constants.add_int(3);
    let c4 = constants.add_int(4);

    // Function table: compute at instruction 4
    let mut function_table = HashMap::new();
    function_table.insert("compute".to_string(), 4);

    let instructions = vec![
        // Main: call compute(2, 3, 4)
        Instruction::LoadConstR { dst: 0, const_idx: c2 },           // r0 = 2
        Instruction::LoadConstR { dst: 1, const_idx: c3 },           // r1 = 3
        Instruction::LoadConstR { dst: 2, const_idx: c4 },           // r2 = 4
        Instruction::CallR { func: 0, args: vec![0, 1, 2], dst: 3 }, // r3 = compute(r0, r1, r2)
        Instruction::ReturnR { src: Some(3) },                       // return r3

        // compute function at PC=5: (a + b) * c
        // Parameters: a in r0, b in r1, c in r2
        Instruction::AddR { dst: 3, left: 0, right: 1 },             // r3 = a + b
        Instruction::MulR { dst: 4, left: 3, right: 2 },             // r4 = (a + b) * c
        Instruction::ReturnR { src: Some(4) },                       // return r4
    ];

    BytecodeModule {
        name: "multiple_args_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table,
        global_names: Vec::new(),
    }
}

fn create_nested_calls_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let c2 = constants.add_int(2);
    let c3 = constants.add_int(3);

    // Function table
    let mut function_table = HashMap::new();
    function_table.insert("double".to_string(), 5);
    function_table.insert("add_one".to_string(), 8);
    function_table.insert("process".to_string(), 11);

    let instructions = vec![
        // Main: call process(3)
        Instruction::LoadConstR { dst: 0, const_idx: c3 },       // r0 = 3
        Instruction::CallR { func: 2, args: vec![0], dst: 1 },   // r1 = process(r0)
        Instruction::ReturnR { src: Some(1) },                   // return r1

        // Padding
        Instruction::Halt,
        Instruction::Halt,

        // double function at PC=5
        Instruction::LoadConstR { dst: 1, const_idx: c2 },       // r1 = 2
        Instruction::MulR { dst: 2, left: 0, right: 1 },         // r2 = x * 2
        Instruction::ReturnR { src: Some(2) },                   // return r2

        // add_one function at PC=8
        Instruction::LoadConstR { dst: 1, const_idx: constants.add_int(1) }, // r1 = 1
        Instruction::AddR { dst: 2, left: 0, right: 1 },         // r2 = x + 1
        Instruction::ReturnR { src: Some(2) },                   // return r2

        // process function at PC=11: double(add_one(x))
        Instruction::CallR { func: 1, args: vec![0], dst: 1 },   // r1 = add_one(x)
        Instruction::CallR { func: 0, args: vec![1], dst: 2 },   // r2 = double(r1)
        Instruction::ReturnR { src: Some(2) },                   // return r2
    ];

    BytecodeModule {
        name: "nested_calls_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table,
        global_names: Vec::new(),
    }
}

#[test]
fn test_simple_function_call() {
    let mut vm = VM::new();
    let module = create_simple_function_module();
    vm.load_module(module, None).unwrap();

    // Execute main
    let result = vm.run().unwrap();

    // add_five(10) = 15
    assert_eq!(result, Some(Value::Int(15)));
}

#[test]
fn test_recursive_function() {
    let mut vm = VM::new();
    let module = create_recursive_function_module();
    vm.load_module(module, None).unwrap();

    // Execute main
    let result = vm.run().unwrap();

    // factorial(5) = 120
    assert_eq!(result, Some(Value::Int(120)));
}

#[test]
fn test_multiple_arguments() {
    let mut vm = VM::new();
    let module = create_multiple_args_module();
    vm.load_module(module, None).unwrap();

    // Execute main
    let result = vm.run().unwrap();

    // compute(2, 3, 4) = (2 + 3) * 4 = 20
    assert_eq!(result, Some(Value::Int(20)));
}

#[test]
fn test_nested_function_calls() {
    let mut vm = VM::new();
    let module = create_nested_calls_module();
    vm.load_module(module, None).unwrap();

    // Execute main
    let result = vm.run().unwrap();

    // process(3) = double(add_one(3)) = double(4) = 8
    assert_eq!(result, Some(Value::Int(8)));
}

#[test]
fn test_call_stack_depth() {
    let mut constants = ConstantPool::new();
    let c1 = constants.add_int(1);
    let c10 = constants.add_int(10);

    // Function that calls itself 10 times
    let mut function_table = HashMap::new();
    function_table.insert("countdown".to_string(), 3);

    let instructions = vec![
        // Main
        Instruction::LoadConstR { dst: 0, const_idx: c10 },      // r0 = 10
        Instruction::CallR { func: 0, args: vec![0], dst: 1 },   // r1 = countdown(10)
        Instruction::ReturnR { src: Some(1) },                   // return r1

        // countdown function at PC=3
        Instruction::LoadConstR { dst: 1, const_idx: c1 },       // r1 = 1
        Instruction::LteR { dst: 2, left: 0, right: 1 },         // r2 = n <= 1
        Instruction::JumpIfNotR { cond: 2, offset: 2 },          // if !(n <= 1) jump +2
        Instruction::ReturnR { src: Some(0) },                   // return n

        // Recursive case
        Instruction::SubR { dst: 3, left: 0, right: 1 },         // r3 = n - 1
        Instruction::CallR { func: 0, args: vec![3], dst: 4 },   // r4 = countdown(n-1)
        Instruction::ReturnR { src: Some(4) },                   // return r4
    ];

    let module = BytecodeModule {
        name: "call_stack_test".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table,
        global_names: Vec::new(),
    };

    let mut vm = VM::new();
    vm.load_module(module, None).unwrap();

    // Run and check stack depth during execution
    let mut max_depth = 0;
    while !vm.halted {
        let depth = vm.call_stack.len();
        if depth > max_depth {
            max_depth = depth;
        }
        if vm.step().unwrap().is_some() {
            break;
        }
    }

    // Should have reached at least 10 frames deep
    assert!(max_depth >= 10);

    // Final result should be 1
    assert_eq!(vm.registers.get(1), &Value::Int(1));
}
