//! Tests for bytecode loading and round-trip

use machine_dialect_vm::{VM, Value};
use machine_dialect_vm::loader::BytecodeLoader;
use std::io::Write;
use tempfile::NamedTempFile;

/// Create a minimal valid bytecode file for testing
fn create_test_bytecode() -> Vec<u8> {
    let mut data = Vec::new();

    // Header (28 bytes)
    data.extend_from_slice(b"MDBC");  // Magic
    data.extend_from_slice(&1u32.to_le_bytes());  // Version
    data.extend_from_slice(&1u32.to_le_bytes());  // Flags (little-endian)
    data.extend_from_slice(&28u32.to_le_bytes());  // Name offset
    data.extend_from_slice(&36u32.to_le_bytes());  // Constant offset
    data.extend_from_slice(&58u32.to_le_bytes());  // Function offset
    data.extend_from_slice(&62u32.to_le_bytes());  // Instruction offset

    // Module name at offset 28
    data.extend_from_slice(&4u32.to_le_bytes());  // Name length
    data.extend_from_slice(b"test");  // Name

    // Constants at offset 36
    data.extend_from_slice(&2u32.to_le_bytes());  // Count = 2
    data.push(0x01);  // Tag: Int
    data.extend_from_slice(&42i64.to_le_bytes());  // Value: 42
    data.push(0x02);  // Tag: Float
    data.extend_from_slice(&3.14f64.to_le_bytes());  // Value: 3.14

    // Functions at offset 58
    data.extend_from_slice(&0u32.to_le_bytes());  // Count = 0

    // Instructions at offset 62
    data.extend_from_slice(&3u32.to_le_bytes());  // Count = 3

    // LoadConstR r0, 0
    data.push(0);  // Opcode
    data.push(0);  // dst = r0
    data.extend_from_slice(&0u16.to_le_bytes());  // const_idx = 0

    // LoadConstR r1, 1
    data.push(0);  // Opcode
    data.push(1);  // dst = r1
    data.extend_from_slice(&1u16.to_le_bytes());  // const_idx = 1

    // ReturnR r0
    data.push(26);  // Opcode
    data.push(1);   // has_value = true
    data.push(0);   // src = r0

    data
}

#[test]
fn test_bytecode_loading() {
    // Create a temporary file with test bytecode
    let mut temp_file = NamedTempFile::new().unwrap();
    let bytecode = create_test_bytecode();
    temp_file.write_all(&bytecode).unwrap();

    // Get the path without extension
    let path = temp_file.path().with_extension("");

    // Rename to .mdbc extension
    let mdbc_path = path.with_extension("mdbc");
    std::fs::rename(temp_file.path(), &mdbc_path).unwrap();

    // Load the bytecode
    let (module, _metadata) = BytecodeLoader::load_module(&path).unwrap();

    // Verify the loaded module
    assert_eq!(module.name, "test");
    assert_eq!(module.version, 1);
    assert_eq!(module.flags, 1);
    assert_eq!(module.constants.len(), 2);
    assert_eq!(module.instructions.len(), 3);

    // Clean up
    std::fs::remove_file(mdbc_path).unwrap();
}

#[test]
fn test_bytecode_execution() {
    // Create bytecode that loads a constant and returns it
    let mut temp_file = NamedTempFile::new().unwrap();
    let bytecode = create_test_bytecode();
    temp_file.write_all(&bytecode).unwrap();

    // Get the path without extension
    let path = temp_file.path().with_extension("");

    // Rename to .mdbc extension
    let mdbc_path = path.with_extension("mdbc");
    std::fs::rename(temp_file.path(), &mdbc_path).unwrap();

    // Create VM and load bytecode
    let mut vm = VM::new();
    let (module, metadata) = BytecodeLoader::load_module(&path).unwrap();
    vm.load_module(module, metadata).unwrap();

    // Execute the bytecode
    let result = vm.run().unwrap();

    // Should return the integer 42 (first constant)
    assert_eq!(result, Some(Value::Int(42)));

    // Clean up
    std::fs::remove_file(mdbc_path).unwrap();
}

#[test]
fn test_invalid_magic() {
    let mut data = Vec::new();
    data.extend_from_slice(b"BADC");  // Invalid magic
    data.extend_from_slice(&[0u8; 20]);  // Rest of header

    let mut temp_file = NamedTempFile::new().unwrap();
    temp_file.write_all(&data).unwrap();

    let path = temp_file.path().with_extension("");
    let mdbc_path = path.with_extension("mdbc");
    std::fs::rename(temp_file.path(), &mdbc_path).unwrap();

    // Should fail with invalid magic
    let result = BytecodeLoader::load_module(&path);
    assert!(result.is_err());

    // Clean up
    std::fs::remove_file(mdbc_path).unwrap();
}
