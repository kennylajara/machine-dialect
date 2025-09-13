//! Machine Dialect™ VM CLI
//!
//! Command-line interface for running Machine Dialect™ bytecode files.

use std::path::PathBuf;
use std::process;

use anyhow::Result;
use machine_dialect_vm::{VM, BytecodeLoader};

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: {} <bytecode_file.mdbc>", args[0]);
        process::exit(1);
    }

    let bytecode_path = PathBuf::from(&args[1]);

    // Load bytecode
    let (module, metadata) = BytecodeLoader::load_module(&bytecode_path)?;

    // Create and initialize VM
    let mut vm = VM::new();
    vm.load_module(module, metadata)?;

    // Execute
    match vm.run() {
        Ok(Some(value)) => {
            println!("Result: {:?}", value);
            Ok(())
        }
        Ok(None) => Ok(()),
        Err(e) => {
            eprintln!("Runtime error: {}", e);
            process::exit(1);
        }
    }
}
