//! EU AI Act (Regulation 2024/1689) alignment (v0.8.0).

use crate::invariants::Invariant;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EuRiskCategory {
    Unacceptable,
    High,
    Limited,
    Minimal,
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct EuAiActAssessment {
    pub risk_category: EuRiskCategory,
    pub defect: f64,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct EuAiActFramework {
    obligations: Vec<(String, Vec<Invariant>)>,
}

impl Default for EuAiActFramework {
    fn default() -> Self {
        Self::new()
    }
}

impl EuAiActFramework {
    pub fn new() -> Self {
        Self {
            obligations: Vec::new(),
        }
    }
}
