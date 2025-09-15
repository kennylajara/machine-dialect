//! Instruction opcodes
//!
//! This module defines the register-based instruction set for the VM.


/// Assertion type for AssertR instruction
#[derive(Clone, Debug, PartialEq)]
pub enum AssertType {
    /// Assert value is true
    True,
    /// Assert value is not null/empty
    NonNull,
    /// Assert value is in range
    Range { min: i64, max: i64 },
}

/// Register-based instruction set
#[derive(Clone, Debug)]
pub enum Instruction {
    // Basic Operations
    /// Load constant from pool: r[dst] = constants[idx]
    LoadConstR { dst: u8, const_idx: u16 },
    /// Move register: r[dst] = r[src]
    MoveR { dst: u8, src: u8 },
    /// Load global: r[dst] = globals[name]
    LoadGlobalR { dst: u8, name_idx: u16 },
    /// Store global: globals[name] = r[src]
    StoreGlobalR { src: u8, name_idx: u16 },

    // Type Operations
    /// Define register with type
    DefineR { dst: u8, type_id: u16 },
    /// Check type: r[dst] = typeof(r[src]) == type
    CheckTypeR { dst: u8, src: u8, type_id: u16 },
    /// Cast value: r[dst] = cast(r[src], type)
    CastR { dst: u8, src: u8, to_type: u16 },

    // Arithmetic (Generic - will specialize in Phase 1)
    /// Addition: r[dst] = r[left] + r[right]
    AddR { dst: u8, left: u8, right: u8 },
    /// Subtraction: r[dst] = r[left] - r[right]
    SubR { dst: u8, left: u8, right: u8 },
    /// Multiplication: r[dst] = r[left] * r[right]
    MulR { dst: u8, left: u8, right: u8 },
    /// Division: r[dst] = r[left] / r[right]
    DivR { dst: u8, left: u8, right: u8 },
    /// Modulo: r[dst] = r[left] % r[right]
    ModR { dst: u8, left: u8, right: u8 },
    /// Negation: r[dst] = -r[src]
    NegR { dst: u8, src: u8 },

    // Logical Operations
    /// Logical NOT: r[dst] = !r[src]
    NotR { dst: u8, src: u8 },
    /// Logical AND: r[dst] = r[left] && r[right]
    AndR { dst: u8, left: u8, right: u8 },
    /// Logical OR: r[dst] = r[left] || r[right]
    OrR { dst: u8, left: u8, right: u8 },

    // Comparisons
    /// Equal: r[dst] = r[left] == r[right]
    EqR { dst: u8, left: u8, right: u8 },
    /// Not equal: r[dst] = r[left] != r[right]
    NeqR { dst: u8, left: u8, right: u8 },
    /// Less than: r[dst] = r[left] < r[right]
    LtR { dst: u8, left: u8, right: u8 },
    /// Greater than: r[dst] = r[left] > r[right]
    GtR { dst: u8, left: u8, right: u8 },
    /// Less than or equal: r[dst] = r[left] <= r[right]
    LteR { dst: u8, left: u8, right: u8 },
    /// Greater than or equal: r[dst] = r[left] >= r[right]
    GteR { dst: u8, left: u8, right: u8 },

    // Control Flow
    /// Unconditional jump: pc += offset
    JumpR { offset: i32 },
    /// Conditional jump: if r[cond] then pc += offset
    JumpIfR { cond: u8, offset: i32 },
    /// Conditional jump (negated): if !r[cond] then pc += offset
    JumpIfNotR { cond: u8, offset: i32 },
    /// Function call: r[dst] = call r[func](r[args])
    CallR { func: u8, args: Vec<u8>, dst: u8 },
    /// Return: return r[src] or empty
    ReturnR { src: Option<u8> },

    // MIR Support
    /// Phi node: r[dst] = φ(r[src], label)
    PhiR { dst: u8, sources: Vec<(u8, u16)> },
    /// Assertion: assert r[reg] with message
    AssertR { reg: u8, assert_type: AssertType, msg_idx: u16 },
    /// Enter scope
    ScopeEnterR { scope_id: u16 },
    /// Exit scope
    ScopeExitR { scope_id: u16 },

    // String Operations
    /// String concatenation: r[dst] = r[left] + r[right]
    ConcatStrR { dst: u8, left: u8, right: u8 },
    /// String length: r[dst] = len(r[str])
    StrLenR { dst: u8, str_reg: u8 },

    // Arrays (Basic)
    /// Create new array: r[dst] = new Array(r[size])
    NewArrayR { dst: u8, size: u8 },
    /// Array get: r[dst] = r[array][r[index]]
    ArrayGetR { dst: u8, array: u8, index: u8 },
    /// Array set: r[array][r[index]] = r[value]
    ArraySetR { array: u8, index: u8, value: u8 },
    /// Array length: r[dst] = r[array].length
    ArrayLenR { dst: u8, array: u8 },

    // Debug
    /// Debug print: print(r[src])
    DebugPrint { src: u8 },
    /// Breakpoint
    BreakPoint,

    // Halt execution
    Halt,

    // No operation (for optimization)
    Nop,

    // Dictionary Operations
    /// Create new dictionary: r[dst] = new Dict()
    DictNewR { dst: u8 },
    /// Dictionary get: r[dst] = r[dict][r[key]]
    DictGetR { dst: u8, dict: u8, key: u8 },
    /// Dictionary set: r[dict][r[key]] = r[value]
    DictSetR { dict: u8, key: u8, value: u8 },
    /// Dictionary remove: del r[dict][r[key]]
    DictRemoveR { dict: u8, key: u8 },
    /// Dictionary contains: r[dst] = r[key] in r[dict]
    DictContainsR { dst: u8, dict: u8, key: u8 },
    /// Dictionary keys: r[dst] = r[dict].keys()
    DictKeysR { dst: u8, dict: u8 },
    /// Dictionary values: r[dst] = r[dict].values()
    DictValuesR { dst: u8, dict: u8 },
    /// Dictionary clear: r[dict].clear()
    DictClearR { dict: u8 },
    /// Dictionary length: r[dst] = len(r[dict])
    DictLenR { dst: u8, dict: u8 },
}

impl Instruction {
    /// Get the size of this instruction in bytes
    pub fn size(&self) -> usize {
        match self {
            Instruction::LoadConstR { .. } => 4,  // opcode + dst + const_idx(u16)
            Instruction::MoveR { .. } => 3,       // opcode + dst + src
            Instruction::LoadGlobalR { .. } => 4,  // opcode + dst + name_idx(u16)
            Instruction::StoreGlobalR { .. } => 4, // opcode + src + name_idx(u16)

            Instruction::DefineR { .. } => 4,     // opcode + dst + type_id(u16)
            Instruction::CheckTypeR { .. } => 5,  // opcode + dst + src + type_id(u16)
            Instruction::CastR { .. } => 5,       // opcode + dst + src + to_type(u16)

            Instruction::AddR { .. } |
            Instruction::SubR { .. } |
            Instruction::MulR { .. } |
            Instruction::DivR { .. } |
            Instruction::ModR { .. } => 4,        // opcode + dst + left + right

            Instruction::NegR { .. } |
            Instruction::NotR { .. } => 3,        // opcode + dst + src

            Instruction::AndR { .. } |
            Instruction::OrR { .. } => 4,         // opcode + dst + left + right

            Instruction::EqR { .. } |
            Instruction::NeqR { .. } |
            Instruction::LtR { .. } |
            Instruction::GtR { .. } |
            Instruction::LteR { .. } |
            Instruction::GteR { .. } => 4,        // opcode + dst + left + right

            Instruction::JumpR { .. } => 5,       // opcode + offset(i32)
            Instruction::JumpIfR { .. } |
            Instruction::JumpIfNotR { .. } => 6,  // opcode + cond + offset(i32)

            Instruction::CallR { args, .. } => 4 + args.len(), // opcode + func + dst + arg_count + args
            Instruction::ReturnR { src } => if src.is_some() { 2 } else { 1 },

            Instruction::PhiR { sources, .. } => 3 + sources.len() * 3, // opcode + dst + count + (src,label)*
            Instruction::AssertR { assert_type, .. } => {
                match assert_type {
                    AssertType::True | AssertType::NonNull => 4, // opcode + reg + msg_idx(u16)
                    AssertType::Range { .. } => 12, // opcode + reg + msg_idx(u16) + min(i64) + max(i64)
                }
            }

            Instruction::ScopeEnterR { .. } |
            Instruction::ScopeExitR { .. } => 3,  // opcode + scope_id(u16)

            Instruction::ConcatStrR { .. } => 4,  // opcode + dst + left + right
            Instruction::StrLenR { .. } => 3,     // opcode + dst + str

            Instruction::NewArrayR { .. } => 3,   // opcode + dst + size
            Instruction::ArrayGetR { .. } => 4,   // opcode + dst + array + index
            Instruction::ArraySetR { .. } => 4,   // opcode + array + index + value
            Instruction::ArrayLenR { .. } => 3,   // opcode + dst + array

            Instruction::DebugPrint { .. } => 2,  // opcode + src
            Instruction::BreakPoint => 1,         // opcode
            Instruction::Halt => 1,                // opcode
            Instruction::Nop => 1,                 // opcode

            // Dictionary operations
            Instruction::DictNewR { .. } => 2,       // opcode + dst
            Instruction::DictGetR { .. } => 4,       // opcode + dst + dict + key
            Instruction::DictSetR { .. } => 4,       // opcode + dict + key + value
            Instruction::DictRemoveR { .. } => 3,    // opcode + dict + key
            Instruction::DictContainsR { .. } => 4,  // opcode + dst + dict + key
            Instruction::DictKeysR { .. } => 3,      // opcode + dst + dict
            Instruction::DictValuesR { .. } => 3,    // opcode + dst + dict
            Instruction::DictClearR { .. } => 2,     // opcode + dict
            Instruction::DictLenR { .. } => 3,       // opcode + dst + dict
        }
    }
}
