//! VM execution engine
//!
//! This module implements the main VM execution engine.

use std::sync::Arc;

use crate::values::{Value, Type, ConstantPool};
use crate::vm::{RegisterFile, VMState};
use crate::instructions::{Instruction, AssertType};
use crate::runtime::{ArithmeticOps, LogicOps, StringOps};
use crate::errors::{RuntimeError, Result, StackFrame};
use crate::loader::{BytecodeModule, MetadataFile};

/// Virtual Machine
pub struct VM {
    /// Register file
    pub registers: RegisterFile,
    /// VM state
    pub state: VMState,
    /// Loaded module
    pub module: Option<BytecodeModule>,
    /// Instructions
    pub instructions: Vec<Instruction>,
    /// Constants
    pub constants: ConstantPool,
    /// Metadata
    pub metadata: Option<MetadataFile>,
    /// Debug mode
    pub debug_mode: bool,
    /// Instruction count (for profiling)
    pub instruction_count: usize,
}

impl VM {
    /// Create a new VM
    pub fn new() -> Self {
        Self {
            registers: RegisterFile::new(),
            state: VMState::new(),
            module: None,
            instructions: Vec::new(),
            constants: ConstantPool::new(),
            metadata: None,
            debug_mode: false,
            instruction_count: 0,
        }
    }

    /// Load a module and metadata
    pub fn load_module(&mut self, module: BytecodeModule, metadata: Option<MetadataFile>) -> Result<()> {
        self.instructions = module.instructions.clone();
        self.constants = module.constants.clone();
        self.module = Some(module);
        self.metadata = metadata;
        self.state.reset();
        self.registers.clear();
        Ok(())
    }

    /// Run the VM until completion
    pub fn run(&mut self) -> Result<Option<Value>> {
        if self.module.is_none() {
            return Err(RuntimeError::ModuleNotLoaded);
        }

        // Check if there's a main function and start there
        if let Some(module) = &self.module {
            if let Some(&main_offset) = module.function_table.get("main") {
                // Jump to main function
                self.state.pc = main_offset;
            }
            // Otherwise, start at PC = 0 (for modules without explicit main)
        }

        let mut last_value = None;

        while self.state.is_running() && self.state.pc < self.instructions.len() {
            let result = self.step()?;
            if let Some(value) = result {
                last_value = Some(value);
            }
        }

        Ok(last_value)
    }

    /// Execute a single instruction
    pub fn step(&mut self) -> Result<Option<Value>> {
        if self.state.pc >= self.instructions.len() {
            self.state.halt();
            return Ok(None);
        }

        let inst = self.instructions[self.state.pc].clone();
        self.state.pc += 1;
        self.instruction_count += 1;

        if self.debug_mode {
            println!("PC: {}, Instruction: {:?}", self.state.pc - 1, inst);
        }

        self.execute_instruction(inst)
    }

    /// Execute an instruction
    fn execute_instruction(&mut self, inst: Instruction) -> Result<Option<Value>> {
        match inst {
            // Basic Operations
            Instruction::LoadConstR { dst, const_idx } => {
                let value = self.constants.get(const_idx)
                    .ok_or(RuntimeError::InvalidConstant(const_idx))?
                    .to_value();

                if self.debug_mode {
                    println!("  LoadConstR: r{} = constants[{}] = {:?}", dst, const_idx, value);
                }

                self.registers.set(dst, value);
            }

            Instruction::MoveR { dst, src } => {
                let value = self.registers.get(src).clone();
                self.registers.set(dst, value);
            }

            Instruction::LoadGlobalR { dst, name_idx } => {
                let name = self.get_string_constant(name_idx)?;
                let value = self.state.globals.get(&name)
                    .cloned()
                    .unwrap_or(Value::Empty);
                self.registers.set(dst, value);
            }

            Instruction::StoreGlobalR { src, name_idx } => {
                let name = self.get_string_constant(name_idx)?;
                let value = self.registers.get(src).clone();
                self.state.globals.insert(name, value);
            }

            // Type Operations
            Instruction::DefineR { dst, type_id } => {
                let value_type = self.get_type_from_id(type_id);
                self.registers.set_type(dst, value_type);
            }

            Instruction::CheckTypeR { dst, src, type_id } => {
                let value_type = self.registers.get_type(src);
                let expected_type = self.get_type_from_id(type_id);
                let result = value_type == &expected_type;
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::CastR { dst, src, to_type } => {
                let value = self.registers.get(src);
                let target_type = self.get_type_from_id(to_type);
                let casted = self.cast_value(value, target_type)?;
                self.registers.set(dst, casted);
            }

            // Arithmetic
            Instruction::AddR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::add(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::SubR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::sub(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::MulR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::mul(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::DivR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::div(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::ModR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::modulo(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::NegR { dst, src } => {
                let value = self.registers.get(src);
                let result = ArithmeticOps::negate(value)?;
                self.registers.set(dst, result);
            }

            // Logical
            Instruction::NotR { dst, src } => {
                let value = self.registers.get(src);
                let result = LogicOps::not(value)?;
                self.registers.set(dst, result);
            }

            Instruction::AndR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = LogicOps::and(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::OrR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = LogicOps::or(lval, rval)?;
                self.registers.set(dst, result);
            }

            // Comparisons
            Instruction::EqR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::eq(lval, rval);
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::NeqR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::neq(lval, rval);
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::LtR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::lt(lval, rval)?;
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::GtR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::gt(lval, rval)?;
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::LteR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);

                if self.debug_mode {
                    println!("  LteR: r{} = r{} ({:?}) <= r{} ({:?})", dst, left, lval, right, rval);
                }

                let result = ArithmeticOps::lte(lval, rval)?;

                if self.debug_mode {
                    println!("    Result: {:?}", result);
                }

                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::GteR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::gte(lval, rval)?;
                self.registers.set(dst, Value::Bool(result));
            }

            // Control Flow
            Instruction::JumpR { offset } => {
                // Track predecessor for phi nodes
                self.state.predecessor_block = Some(self.state.pc as u16 - 1);
                self.state.pc = (self.state.pc as i32 + offset) as usize;
            }

            Instruction::JumpIfR { cond, offset } => {
                let condition = self.registers.get(cond);
                if condition.is_truthy() {
                    // Track predecessor for phi nodes
                    self.state.predecessor_block = Some(self.state.pc as u16 - 1);
                    self.state.pc = (self.state.pc as i32 + offset) as usize;
                }
            }

            Instruction::JumpIfNotR { cond, offset } => {
                let condition = self.registers.get(cond);
                if !condition.is_truthy() {
                    // Track predecessor for phi nodes
                    self.state.predecessor_block = Some(self.state.pc as u16 - 1);
                    self.state.pc = (self.state.pc as i32 + offset) as usize;
                }
            }

            Instruction::CallR { func, args, dst } => {
                if self.debug_mode {
                    println!("CallR: func=r{}, dst=r{}, args={:?}", func, dst, args);
                    for (i, &arg_reg) in args.iter().enumerate() {
                        println!("  arg[{}]: r{} = {:?}", i, arg_reg, self.registers.get(arg_reg));
                    }
                }
                // Get function entry point
                let func_value = self.registers.get(func);

                // For now, treat the function register as containing an index into the function table
                // In the future, this could be a FunctionRef value
                let func_name = match func_value {
                    Value::String(name) => name.as_ref().clone(),
                    Value::Int(idx) => {
                        // Look up function by index in function table
                        if let Some(module) = &self.module {
                            module.function_table.iter()
                                .find(|(_, &offset)| offset == *idx as usize)
                                .map(|(name, _)| name.clone())
                                .unwrap_or_else(|| format!("func_{}", idx))
                        } else {
                            return Err(RuntimeError::UndefinedFunction(format!("index {}", idx)));
                        }
                    }
                    _ => {
                        return Err(RuntimeError::UndefinedFunction("no function specified".to_string()));
                    }
                };

                // Look up function in function table
                if let Some(module) = &self.module {
                    if let Some(&func_offset) = module.function_table.get(&func_name) {
                        // Save current state
                        let saved_pc = self.state.pc;
                        let saved_fp = self.state.fp;

                        // Create new call frame
                        let mut frame = crate::vm::CallFrame::new(saved_pc, saved_fp);

                        // Save the destination register for the return value
                        frame.return_dst = Some(dst);

                        // Save ALL registers that might be used by the called function
                        // We need to save all registers because recursive calls can use many registers
                        // TODO: Optimize this by only saving registers actually used by the target function
                        for i in 0..64 {  // Save up to 64 registers (should be enough for most functions)
                            frame.saved_registers.push((i as u8, self.registers.get(i as u8).clone()));
                        }

                        // Then: Copy arguments to parameter registers
                        for (i, &arg_reg) in args.iter().enumerate() {
                            if i < 16 {
                                let value = self.registers.get(arg_reg).clone();
                                self.registers.set(i as u8, value.clone());
                                if self.debug_mode {
                                    println!("  Set r{} = {:?} (from r{})", i, value, arg_reg);
                                }
                            }
                        }

                        // Push frame
                        self.state.push_frame(frame)?;

                        // Jump to function
                        self.state.pc = func_offset;
                    } else {
                        return Err(RuntimeError::UndefinedFunction(func_name));
                    }
                } else {
                    return Err(RuntimeError::ModuleNotLoaded);
                }
            }

            Instruction::ReturnR { src } => {
                let value = src.map(|r| self.registers.get(r).clone());

                if let Some(frame) = self.state.pop_frame() {
                    self.state.pc = frame.return_address;
                    self.state.fp = frame.saved_fp;
                    self.registers.restore_registers(&frame.saved_registers);

                    // Store return value in the destination register if specified
                    if let (Some(return_dst), Some(ref ret_val)) = (frame.return_dst, &value) {
                        self.registers.set(return_dst, ret_val.clone());
                    }
                } else {
                    self.state.halt();
                    return Ok(value);
                }
            }

            // MIR Support
            Instruction::PhiR { dst, sources } => {
                // Phi resolution based on predecessor block
                if let Some(predecessor) = self.state.predecessor_block {
                    for (src_reg, block_id) in sources {
                        if block_id == predecessor {
                            let value = self.registers.get(src_reg).clone();
                            self.registers.set(dst, value);
                            break;
                        }
                    }
                }
            }

            Instruction::AssertR { reg, assert_type, msg_idx } => {
                let value = self.registers.get(reg);
                let assertion_failed = match assert_type {
                    AssertType::True => !value.is_truthy(),
                    AssertType::NonNull => matches!(value, Value::Empty),
                    AssertType::Range { min, max } => {
                        match value {
                            Value::Int(n) => *n < min || *n > max,
                            _ => true,
                        }
                    }
                };

                if assertion_failed {
                    let msg = self.get_string_constant(msg_idx)?;
                    return Err(RuntimeError::AssertionFailed(msg));
                }
            }

            Instruction::ScopeEnterR { scope_id } => {
                self.state.enter_scope(scope_id);
            }

            Instruction::ScopeExitR { scope_id } => {
                self.state.exit_scope(scope_id);
            }

            // String Operations
            Instruction::ConcatStrR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = StringOps::concat(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::StrLenR { dst, str_reg } => {
                let value = self.registers.get(str_reg);
                let result = StringOps::len(value)?;
                self.registers.set(dst, result);
            }

            // Arrays
            Instruction::NewArrayR { dst, size } => {
                let size_value = self.registers.get(size);
                let array_size = match size_value {
                    Value::Int(n) if *n >= 0 => *n as usize,
                    Value::Int(n) => {
                        return Err(RuntimeError::InvalidOperation {
                            op: "create array".to_string(),
                            type_name: format!("negative size: {}", n),
                        });
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "integer".to_string(),
                            found: size_value.type_of().to_string(),
                        });
                    }
                };

                let array = vec![Value::Empty; array_size];
                self.registers.set(dst, Value::Array(Arc::new(array)));
            }

            Instruction::ArrayGetR { dst, array, index } => {
                let array_value = self.registers.get(array);
                let index_value = self.registers.get(index);

                match (array_value, index_value) {
                    (Value::Array(arr), Value::Int(idx)) => {
                        if *idx < 0 {
                            return Err(RuntimeError::IndexOutOfBounds {
                                index: *idx,
                                length: arr.len(),
                            });
                        }
                        let idx = *idx as usize;
                        if idx >= arr.len() {
                            return Err(RuntimeError::IndexOutOfBounds {
                                index: idx as i64,
                                length: arr.len(),
                            });
                        }
                        self.registers.set(dst, arr[idx].clone());
                    }
                    (Value::Array(_), _) => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "integer index".to_string(),
                            found: index_value.type_of().to_string(),
                        });
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "array".to_string(),
                            found: array_value.type_of().to_string(),
                        });
                    }
                }
            }

            Instruction::ArraySetR { array, index, value } => {
                let array_value = self.registers.get(array);
                let index_value = self.registers.get(index);
                let new_value = self.registers.get(value).clone();

                match (array_value, index_value) {
                    (Value::Array(arr), Value::Int(idx)) => {
                        if *idx < 0 {
                            return Err(RuntimeError::IndexOutOfBounds {
                                index: *idx,
                                length: arr.len(),
                            });
                        }
                        let idx = *idx as usize;
                        if idx >= arr.len() {
                            return Err(RuntimeError::IndexOutOfBounds {
                                index: idx as i64,
                                length: arr.len(),
                            });
                        }

                        // Create a new array with the updated value (immutable approach)
                        let mut new_array = (**arr).clone();
                        new_array[idx] = new_value;
                        self.registers.set(array, Value::Array(Arc::new(new_array)));
                    }
                    (Value::Array(_), _) => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "integer index".to_string(),
                            found: index_value.type_of().to_string(),
                        });
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "array".to_string(),
                            found: array_value.type_of().to_string(),
                        });
                    }
                }
            }

            Instruction::ArrayLenR { dst, array } => {
                let array_value = self.registers.get(array);
                match array_value {
                    Value::Array(arr) => {
                        self.registers.set(dst, Value::Int(arr.len() as i64));
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "array".to_string(),
                            found: array_value.type_of().to_string(),
                        });
                    }
                }
            }

            // Dictionary operations
            Instruction::DictNewR { dst } => {
                use std::collections::HashMap;
                self.registers.set(dst, Value::Dict(Arc::new(HashMap::new())));
            }

            Instruction::DictGetR { dst, dict, key } => {
                let dict_value = self.registers.get(dict);
                let key_value = self.registers.get(key);

                match (dict_value, key_value) {
                    (Value::Dict(d), Value::String(k)) => {
                        let value = d.get(k.as_ref()).cloned().unwrap_or(Value::Empty);
                        self.registers.set(dst, value);
                    }
                    (Value::Dict(_), _) => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "string key".to_string(),
                            found: key_value.type_of().to_string(),
                        });
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "dict".to_string(),
                            found: dict_value.type_of().to_string(),
                        });
                    }
                }
            }

            Instruction::DictSetR { dict, key, value } => {
                let dict_value = self.registers.get(dict);
                let key_value = self.registers.get(key);
                let new_value = self.registers.get(value).clone();

                match (dict_value, key_value) {
                    (Value::Dict(d), Value::String(k)) => {
                        // Clone the Arc and use make_mut for copy-on-write semantics
                        let mut d_clone = d.clone();
                        let d_mut = Arc::make_mut(&mut d_clone);
                        d_mut.insert(k.as_ref().clone(), new_value);
                        self.registers.set(dict, Value::Dict(d_clone));
                    }
                    (Value::Dict(_), _) => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "string key".to_string(),
                            found: key_value.type_of().to_string(),
                        });
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "dict".to_string(),
                            found: dict_value.type_of().to_string(),
                        });
                    }
                }
            }

            Instruction::DictRemoveR { dict, key } => {
                let dict_value = self.registers.get(dict);
                let key_value = self.registers.get(key);

                match (dict_value, key_value) {
                    (Value::Dict(d), Value::String(k)) => {
                        let mut d_clone = d.clone();
                        let d_mut = Arc::make_mut(&mut d_clone);
                        d_mut.remove(k.as_ref());
                        self.registers.set(dict, Value::Dict(d_clone));
                    }
                    (Value::Dict(_), _) => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "string key".to_string(),
                            found: key_value.type_of().to_string(),
                        });
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "dict".to_string(),
                            found: dict_value.type_of().to_string(),
                        });
                    }
                }
            }

            Instruction::DictContainsR { dst, dict, key } => {
                let dict_value = self.registers.get(dict);
                let key_value = self.registers.get(key);

                match (dict_value, key_value) {
                    (Value::Dict(d), Value::String(k)) => {
                        let contains = d.contains_key(k.as_ref());
                        self.registers.set(dst, Value::Bool(contains));
                    }
                    (Value::Dict(_), _) => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "string key".to_string(),
                            found: key_value.type_of().to_string(),
                        });
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "dict".to_string(),
                            found: dict_value.type_of().to_string(),
                        });
                    }
                }
            }

            Instruction::DictKeysR { dst, dict } => {
                let dict_value = self.registers.get(dict);

                match dict_value {
                    Value::Dict(d) => {
                        let keys: Vec<Value> = d.keys()
                            .map(|k| Value::String(Arc::new(k.clone())))
                            .collect();
                        self.registers.set(dst, Value::Array(Arc::new(keys)));
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "dict".to_string(),
                            found: dict_value.type_of().to_string(),
                        });
                    }
                }
            }

            Instruction::DictValuesR { dst, dict } => {
                let dict_value = self.registers.get(dict);

                match dict_value {
                    Value::Dict(d) => {
                        let values: Vec<Value> = d.values().cloned().collect();
                        self.registers.set(dst, Value::Array(Arc::new(values)));
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "dict".to_string(),
                            found: dict_value.type_of().to_string(),
                        });
                    }
                }
            }

            Instruction::DictClearR { dict } => {
                let dict_value = self.registers.get(dict);

                match dict_value {
                    Value::Dict(_) => {
                        use std::collections::HashMap;
                        self.registers.set(dict, Value::Dict(Arc::new(HashMap::new())));
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "dict".to_string(),
                            found: dict_value.type_of().to_string(),
                        });
                    }
                }
            }

            Instruction::DictLenR { dst, dict } => {
                let dict_value = self.registers.get(dict);

                match dict_value {
                    Value::Dict(d) => {
                        self.registers.set(dst, Value::Int(d.len() as i64));
                    }
                    _ => {
                        return Err(RuntimeError::TypeMismatch {
                            expected: "dict".to_string(),
                            found: dict_value.type_of().to_string(),
                        });
                    }
                }
            }

            // Debug
            Instruction::DebugPrint { src } => {
                let value = self.registers.get(src);
                // Only show "DEBUG:" prefix when in debug mode
                if self.debug_mode {
                    println!("DEBUG: {:?}", value);
                } else {
                    // In normal mode, print clean output
                    match value {
                        Value::String(s) => println!("{}", s),
                        Value::Int(i) => println!("{}", i),
                        Value::Float(f) => println!("{}", f),
                        Value::Bool(b) => println!("{}", b),
                        Value::Empty => {}, // Empty should not print anything
                        _ => println!("{:?}", value),
                    }
                }
            }

            Instruction::BreakPoint => {
                if self.debug_mode {
                    println!("BREAKPOINT at PC: {}", self.state.pc - 1);
                    // TODO: Implement debugger
                }
            }

            Instruction::Halt => {
                self.state.halt();
            }

            Instruction::Nop => {
                // No operation - just continue
            }
        }

        Ok(None)
    }

    /// Get a string constant by index
    fn get_string_constant(&self, idx: u16) -> Result<String> {
        use crate::values::ConstantValue;

        match self.constants.get(idx) {
            Some(ConstantValue::String(s)) => Ok(s.clone()),
            _ => Err(RuntimeError::InvalidConstant(idx)),
        }
    }

    /// Get type from type ID
    fn get_type_from_id(&self, type_id: u16) -> Type {
        match type_id {
            0 => Type::Empty,
            1 => Type::Bool,
            2 => Type::Int,
            3 => Type::Float,
            4 => Type::String,
            5 => Type::Function,
            6 => Type::URL,
            _ => Type::Unknown,
        }
    }

    /// Cast a value to a type
    fn cast_value(&self, value: &Value, target_type: Type) -> Result<Value> {
        match target_type {
            Type::Bool => Ok(Value::Bool(value.to_bool())),
            Type::Int => value.to_int().map(Value::Int),
            Type::Float => value.to_float().map(Value::Float),
            Type::String => Ok(Value::String(std::sync::Arc::new(value.to_string()))),
            _ => Err(RuntimeError::TypeMismatch {
                expected: target_type.to_string(),
                found: value.type_of().to_string(),
            })
        }
    }

    /// Build a stack trace for errors
    pub fn build_stack_trace(&self) -> Vec<StackFrame> {
        let mut trace = Vec::new();

        // Add current location
        trace.push(StackFrame {
            function: "main".to_string(),
            pc: self.state.pc,
            source_location: None,
        });

        // Add call frames
        for frame in &self.state.call_stack {
            let func_name = frame.function.as_ref()
                .map(|f| f.name.clone())
                .unwrap_or_else(|| "anonymous".to_string());

            trace.push(StackFrame {
                function: func_name,
                pc: frame.return_address,
                source_location: None,
            });
        }

        trace
    }
}

impl Default for VM {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::instructions::Instruction;
    use crate::values::{Value, ConstantValue, ConstantPool};
    use crate::loader::BytecodeModule;
    use std::collections::HashMap;

    #[test]
    fn test_call_r_parameter_passing() {
        // This test verifies that CallR correctly passes parameters to functions
        // and that the bug with register saving/restoring is fixed

        let mut vm = VM::new();

        // Create a simple module with a function table
        let mut module = BytecodeModule {
            name: "test".to_string(),
            version: 1,
            flags: 0,
            constants: ConstantPool::new(),
            instructions: vec![
                // Main code (at offset 0):
                // Load 42 into r0
                Instruction::LoadConstR { dst: 0, const_idx: 0 },
                // Load 10 into r1
                Instruction::LoadConstR { dst: 1, const_idx: 1 },
                // Load function name into r2
                Instruction::LoadConstR { dst: 2, const_idx: 2 },
                // Call test_func(r0, r1) and put result in r3
                Instruction::CallR { func: 2, args: vec![0, 1], dst: 3 },
                // Return r3
                Instruction::ReturnR { src: Some(3) },

                // test_func code (at offset 5):
                // At this point r0=42, r1=10 (parameters)
                // Add r0 + r1 -> r2
                Instruction::AddR { dst: 2, left: 0, right: 1 },
                // Return r2
                Instruction::ReturnR { src: Some(2) },
            ],
            function_table: HashMap::new(),
            global_names: vec![],
        };

        // Add constants
        module.constants.add(ConstantValue::Int(42));
        module.constants.add(ConstantValue::Int(10));
        module.constants.add(ConstantValue::String("test_func".to_string()));

        // Add function to table
        module.function_table.insert("test_func".to_string(), 5);

        // Load module
        vm.load_module(module, None).unwrap();

        // Run the VM
        let result = vm.run().unwrap();

        // The result should be 42 + 10 = 52
        assert_eq!(result, Some(Value::Int(52)));
    }

    #[test]
    fn test_call_r_self_referential() {
        // Test case where r0 is both source and destination
        // This tests the edge case where a register passes itself as parameter

        let mut vm = VM::new();

        let mut module = BytecodeModule {
            name: "test".to_string(),
            version: 1,
            flags: 0,
            constants: ConstantPool::new(),
            instructions: vec![
                // Main code:
                // Load 100 into r0
                Instruction::LoadConstR { dst: 0, const_idx: 0 },
                // Load function name into r1
                Instruction::LoadConstR { dst: 1, const_idx: 1 },
                // Call identity(r0) with r0 as both arg and dst
                Instruction::CallR { func: 1, args: vec![0], dst: 0 },
                // Return r0
                Instruction::ReturnR { src: Some(0) },

                // identity function (at offset 4):
                // Just return r0 (the parameter)
                Instruction::ReturnR { src: Some(0) },
            ],
            function_table: HashMap::new(),
            global_names: vec![],
        };

        // Add constants
        module.constants.add(ConstantValue::Int(100));
        module.constants.add(ConstantValue::String("identity".to_string()));

        // Add function to table
        module.function_table.insert("identity".to_string(), 4);

        // Load module
        vm.load_module(module, None).unwrap();

        // Run the VM
        let result = vm.run().unwrap();

        // The result should still be 100
        assert_eq!(result, Some(Value::Int(100)));
    }
}
