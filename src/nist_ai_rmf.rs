//! NIST AI RMF + CSF 2.0 alignment (v0.8.0).

use crate::invariants::{Invariant, SystemState};
use crate::safe_manifold::SafeManifold;
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum NistFunction {
    Govern,
    Map,
    Measure,
    Manage,
}

impl NistFunction {
    pub fn all() -> [Self; 4] {
        [Self::Govern, Self::Map, Self::Measure, Self::Manage]
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum CsfFunction {
    Govern,
    Identify,
    Protect,
    Detect,
    Respond,
    Recover,
}

impl CsfFunction {
    pub fn all() -> [Self; 6] {
        [
            Self::Govern,
            Self::Identify,
            Self::Protect,
            Self::Detect,
            Self::Respond,
            Self::Recover,
        ]
    }
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct RmfMapping {
    pub function: NistFunction,
    pub category: String,
    pub subcategory: String,
    pub description: String,
    pub manifold_capability: String,
    pub invariant_mappings: Vec<Invariant>,
    pub satisfied: bool,
}

#[derive(Debug, Clone, Default)]
#[allow(dead_code)]
pub struct RmfRegistry {
    mappings: Vec<RmfMapping>,
}

impl RmfRegistry {
    pub fn new() -> Self {
        let mut r = Self::default();
        r.init();
        r
    }
    fn init(&mut self) {
        self.mappings = vec![RmfMapping {
            function: NistFunction::Govern,
            category: "GOVERN 1".into(),
            subcategory: "GOVERN 1.1".into(),
            description: "Legal and regulatory requirements".into(),
            manifold_capability: "MSSP bridge".into(),
            invariant_mappings: vec![Invariant::I05, Invariant::I06, Invariant::I15],
            satisfied: false,
        }];
    }
    pub fn evaluate(&mut self, state: &SystemState, manifold: &SafeManifold) {
        let ideal = SystemState::safe(state.config.clone());
        let assessment = manifold.assess_defect(&ideal, state);
        for m in &mut self.mappings {
            m.satisfied = m
                .invariant_mappings
                .iter()
                .all(|inv| state.check_invariant(*inv).passed);
            if m.function == NistFunction::Manage && assessment.is_escaping {
                m.satisfied = false;
            }
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum RiskTier {
    Negligible,
    Low,
    Medium,
    High,
    Critical,
}

#[derive(Debug, Clone, Default)]
#[allow(dead_code)]
pub struct AccountabilityRegistry {
    role_invariants: HashMap<String, Vec<Invariant>>,
}
