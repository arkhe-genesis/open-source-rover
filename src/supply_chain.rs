//! Software supply chain integrity (v0.8.0).

#[allow(unused_imports)]
use crate::invariants::SystemState;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct SupplyChainComponent {
    pub name: String,
    pub version: String,
    pub verified: bool,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct SupplyChainVerifier {
    components: Vec<SupplyChainComponent>,
}

impl Default for SupplyChainVerifier {
    fn default() -> Self {
        Self::new()
    }
}

impl SupplyChainVerifier {
    pub fn new() -> Self {
        Self {
            components: Vec::new(),
        }
    }
}
