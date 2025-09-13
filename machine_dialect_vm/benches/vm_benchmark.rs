//! Performance benchmarks for the Machine Dialect™ VM

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use machine_dialect_vm::{VM, BytecodeModule};
use machine_dialect_vm::instructions::Instruction;
use machine_dialect_vm::values::ConstantPool;
use std::collections::HashMap;

fn create_fibonacci_module(n: i64) -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let c0 = constants.add_float(0.0);
    let c1 = constants.add_float(1.0);
    let c2 = constants.add_float(2.0);
    let cn = constants.add_float(n as f64);
    let c_one = constants.add_float(1.0);

    let instructions = vec![
        // Initialize: r0 = 0 (prev), r1 = 1 (curr), r2 = 2 (i), r3 = n, r6 = 1 (increment)
        Instruction::LoadConstR { dst: 0, const_idx: c0 },
        Instruction::LoadConstR { dst: 1, const_idx: c1 },
        Instruction::LoadConstR { dst: 2, const_idx: c2 },
        Instruction::LoadConstR { dst: 3, const_idx: cn },
        Instruction::LoadConstR { dst: 6, const_idx: c_one },

        // Loop: while i <= n
        Instruction::GtR { dst: 4, left: 2, right: 3 },      // r4 = i > n
        Instruction::JumpIfR { cond: 4, offset: 5 },          // if r4, exit loop

        // Fibonacci step: next = prev + curr
        Instruction::AddR { dst: 5, left: 0, right: 1 },     // r5 = prev + curr
        Instruction::MoveR { dst: 0, src: 1 },                // prev = curr
        Instruction::MoveR { dst: 1, src: 5 },                // curr = next
        Instruction::AddR { dst: 2, left: 2, right: 6 },     // i = i + 1
        Instruction::JumpR { offset: -6 },                    // loop back

        Instruction::ReturnR { src: Some(1) },
    ];

    BytecodeModule {
        name: "fibonacci".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

fn create_arithmetic_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let mut instructions = Vec::new();

    // Perform many arithmetic operations
    for i in 0..100 {
        let c = constants.add_int(i);
        instructions.push(Instruction::LoadConstR { dst: (i % 16) as u8, const_idx: c });

        if i > 0 {
            let op = match i % 4 {
                0 => Instruction::AddR { dst: 16, left: (i % 16) as u8, right: ((i-1) % 16) as u8 },
                1 => Instruction::SubR { dst: 16, left: (i % 16) as u8, right: ((i-1) % 16) as u8 },
                2 => Instruction::MulR { dst: 16, left: (i % 16) as u8, right: ((i-1) % 16) as u8 },
                _ => Instruction::DivR { dst: 16, left: (i % 16) as u8, right: ((i-1) % 16) as u8 },
            };
            instructions.push(op);
        }
    }

    instructions.push(Instruction::ReturnR { src: Some(16) });

    BytecodeModule {
        name: "arithmetic_bench".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

fn benchmark_fibonacci(c: &mut Criterion) {
    let module = create_fibonacci_module(10);

    c.bench_function("fibonacci_10", |b| {
        b.iter(|| {
            let mut vm = VM::new();
            vm.load_module(module.clone(), None).unwrap();
            let result = vm.run().unwrap();
            black_box(result);
        });
    });
}

fn benchmark_arithmetic(c: &mut Criterion) {
    let module = create_arithmetic_module();

    c.bench_function("arithmetic_100_ops", |b| {
        b.iter(|| {
            let mut vm = VM::new();
            vm.load_module(module.clone(), None).unwrap();
            let result = vm.run().unwrap();
            black_box(result);
        });
    });
}

fn benchmark_instruction_dispatch(c: &mut Criterion) {
    let mut constants = ConstantPool::new();
    let c1 = constants.add_int(1);

    // Create a module with many simple instructions
    let mut instructions = Vec::new();
    for _ in 0..1000 {
        instructions.push(Instruction::LoadConstR { dst: 0, const_idx: c1 });
        instructions.push(Instruction::MoveR { dst: 1, src: 0 });
    }
    instructions.push(Instruction::ReturnR { src: Some(0) });

    let module = BytecodeModule {
        name: "dispatch_bench".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    };

    c.bench_function("instruction_dispatch_2000", |b| {
        b.iter(|| {
            let mut vm = VM::new();
            vm.load_module(module.clone(), None).unwrap();
            let result = vm.run().unwrap();
            black_box(result);
        });
    });
}

criterion_group!(benches, benchmark_fibonacci, benchmark_arithmetic, benchmark_instruction_dispatch);
criterion_main!(benches);
