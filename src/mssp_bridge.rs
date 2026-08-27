//! Brazilian regulatory bridge (v0.8.0).

use crate::invariants::Invariant;
#[allow(unused_imports)]
use crate::invariants::SystemState;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CategorizationLevel {
    ExcessiveRisk,
    HighRisk,
    MediumRisk,
    LowRisk,
    MinimalRisk,
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct RegulatoryMapping {
    pub regulation: String,
    pub article: String,
    pub description: String,
    pub invariant_mappings: Vec<Invariant>,
    pub compliant: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SlaTier {
    Bronze,
    Silver,
    Gold,
    Platinum,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct MsspBridge {
    mappings: Vec<RegulatoryMapping>,
}

impl Default for MsspBridge {
    fn default() -> Self {
        Self::new()
    }
}

impl MsspBridge {
    pub fn new() -> Self {
        Self {
            mappings: Vec::new(),
        }
    }
}
