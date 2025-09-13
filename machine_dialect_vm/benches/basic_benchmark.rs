//! Basic performance benchmarks for the Machine Dialect™ VM

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use machine_dialect_vm::{VM, BytecodeModule};
use machine_dialect_vm::instructions::Instruction;
use machine_dialect_vm::values::ConstantPool;
use std::collections::HashMap;

fn create_simple_add_module() -> BytecodeModule {
    let mut constants = ConstantPool::new();
    let c1 = constants.add_int(100);
    let c2 = constants.add_int(200);

    let instructions = vec![
        Instruction::LoadConstR { dst: 0, const_idx: c1 },
        Instruction::LoadConstR { dst: 1, const_idx: c2 },
        Instruction::AddR { dst: 2, left: 0, right: 1 },
        Instruction::ReturnR { src: Some(2) },
    ];

    BytecodeModule {
        name: "simple_add".to_string(),
        version: 1,
        flags: 0,
        constants,
        instructions,
        function_table: HashMap::new(),
        global_names: Vec::new(),
    }
}

fn benchmark_simple_addition(c: &mut Criterion) {
    let module = create_simple_add_module();

    c.bench_function("simple_addition", |b| {
        b.iter(|| {
            let mut vm = VM::new();
            vm.load_module(module.clone(), None).unwrap();
            let result = vm.run().unwrap();
            black_box(result);
        });
    });
}

fn benchmark_vm_creation(c: &mut Criterion) {
    c.bench_function("vm_creation", |b| {
        b.iter(|| {
            let vm = VM::new();
            black_box(vm);
        });
    });
}

criterion_group!(benches,
    benchmark_simple_addition,
    benchmark_vm_creation
);
criterion_main!(benches);
