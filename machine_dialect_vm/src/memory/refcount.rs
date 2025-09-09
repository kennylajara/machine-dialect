//! Reference counting
//!
//! Basic reference counting for memory management.

use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};

use crate::values::Value;

/// Reference counted value
pub struct RefCountedValue {
    /// The value
    pub value: Value,
    /// Reference count
    pub ref_count: AtomicUsize,
}

impl RefCountedValue {
    /// Create a new reference counted value
    pub fn new(value: Value) -> Arc<Self> {
        Arc::new(Self {
            value,
            ref_count: AtomicUsize::new(1),
        })
    }

    /// Increment reference count
    pub fn inc_ref(&self) {
        self.ref_count.fetch_add(1, Ordering::Relaxed);
    }

    /// Decrement reference count
    pub fn dec_ref(&self) -> usize {
        self.ref_count.fetch_sub(1, Ordering::Release)
    }

    /// Get current reference count
    pub fn ref_count(&self) -> usize {
        self.ref_count.load(Ordering::Acquire)
    }
}
