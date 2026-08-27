//! Recovery Suggestion Interface (v0.8.0).

use crate::invariants::Invariant;
#[allow(unused_imports)]
use crate::invariants::SystemState;
use indexmap::IndexMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct RecoveryAction {
    pub invariant: Invariant,
    pub action: String,
    pub priority: u8,
    pub estimated_recovery_ms: u64,
    pub automatic: bool,
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct RecoverySuggestion {
    pub invariant: Invariant,
    pub current_status: String,
    pub actions: Vec<RecoveryAction>,
    pub best_action: Option<RecoveryAction>,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct RsiEngine {
    db: IndexMap<Invariant, Vec<RecoveryAction>>,
}

impl RsiEngine {
    pub fn new() -> Self {
        Self {
            db: IndexMap::new(),
        }
    }
}
impl Default for RsiEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(feature = "async")]
pub use async_impl::AsyncRsiEngine;

#[cfg(feature = "async")]
mod async_impl {
    use super::*;
    #[derive(Debug, Clone, Default)]
    #[allow(dead_code)]
    pub struct AsyncRsiEngine {
        inner: RsiEngine,
    }
}
