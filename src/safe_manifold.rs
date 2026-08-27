//! SafeManifold — 16D security state projection engine (v0.8.0).

use crate::invariants::{Invariant, InvariantCategory, ManifoldError, SystemConfig, SystemState};
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct DefectConfig {
    pub normalization: f64,
    pub pii_penalty: f64,
    pub sig_penalty: f64,
    pub pqc_kem_penalty: f64,
    pub pqc_sig_penalty: f64,
    pub agentic_boundary_penalty: f64,
    pub agentic_oversight_penalty: f64,
    pub supply_chain_penalty: f64,
    pub bias_penalty: f64,
    pub eu_ai_act_penalty: f64,
    pub explainability_penalty: f64,
}

impl Default for DefectConfig {
    fn default() -> Self {
        Self {
            normalization: 1e12,
            pii_penalty: 1.0 / 5.0_f64.sqrt(),
            sig_penalty: 1.0 / 5.0_f64.sqrt(),
            pqc_kem_penalty: 0.3,
            pqc_sig_penalty: 0.3,
            agentic_boundary_penalty: 0.4,
            agentic_oversight_penalty: 0.4,
            supply_chain_penalty: 0.3,
            bias_penalty: 0.4,
            eu_ai_act_penalty: 0.5,
            explainability_penalty: 0.2,
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct ManifoldPoint {
    pub coords: Vec<f64>,
    pub label: Option<String>,
}

impl ManifoldPoint {
    pub fn distance_to(&self, other: &ManifoldPoint) -> f64 {
        self.coords
            .iter()
            .zip(other.coords.iter())
            .map(|(a, b)| (a - b).powi(2))
            .sum::<f64>()
            .sqrt()
    }
    pub fn dimensions(&self) -> usize {
        self.coords.len()
    }
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct EscapeThresholds {
    pub defect_limit: f64,
    pub warning_threshold: f64,
    pub early_warning: bool,
}

impl Default for EscapeThresholds {
    fn default() -> Self {
        Self {
            defect_limit: 0.5,
            warning_threshold: 0.3,
            early_warning: true,
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct ManifoldProfile {
    pub name: String,
    pub dimensions: usize,
    pub created_at_ms: u64,
}

impl ManifoldProfile {
    pub fn new(name: &str, dimensions: usize) -> Self {
        Self {
            name: name.to_string(),
            dimensions,
            created_at_ms: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_millis() as u64)
                .unwrap_or(0),
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct SafeState {
    pub state: SystemState,
    pub defect: f64,
}

impl SafeState {
    pub fn new(state: SystemState, defect: f64) -> Result<Self, ManifoldError> {
        if defect >= 0.5 {
            return Err(ManifoldError::InvariantViolation(format!(
                "Defect {:.4} exceeds safe threshold 0.5",
                defect
            )));
        }
        Ok(Self { state, defect })
    }
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct DefectAssessment {
    pub value: f64,
    pub level: DefectLevel,
    pub violated_invariants: Vec<Invariant>,
    pub is_escaping: bool,
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct BatchAssessment {
    pub assessments: Vec<DefectAssessment>,
    pub avg_defect: f64,
    pub max_defect: f64,
    pub min_defect: f64,
    pub escaping_count: usize,
}

impl BatchAssessment {
    pub fn new(assessments: Vec<DefectAssessment>) -> Self {
        let n = assessments.len();
        if n == 0 {
            return Self {
                assessments,
                avg_defect: 0.0,
                max_defect: 0.0,
                min_defect: 0.0,
                escaping_count: 0,
            };
        }
        let mut sum = 0.0f64;
        let mut max_val = f64::NEG_INFINITY;
        let mut min_val = f64::INFINITY;
        let mut esc = 0usize;
        for a in &assessments {
            sum += a.value;
            max_val = max_val.max(a.value);
            min_val = min_val.min(a.value);
            if a.is_escaping {
                esc += 1;
            }
        }
        Self {
            assessments,
            avg_defect: sum / n as f64,
            max_defect: max_val,
            min_defect: min_val,
            escaping_count: esc,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum DefectLevel {
    Nominal,
    Warning,
    Critical,
    Escaping,
}

impl DefectLevel {
    pub fn from_defect(defect: f64, thresholds: &EscapeThresholds) -> Self {
        if defect >= thresholds.defect_limit {
            Self::Escaping
        } else if thresholds.early_warning && defect >= thresholds.warning_threshold {
            Self::Critical
        } else if thresholds.early_warning && defect >= thresholds.warning_threshold * 0.5 {
            Self::Warning
        } else {
            Self::Nominal
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct DimensionWeights {
    pub token_weight: f64,
    pub agent_weight: f64,
    pub fuel_weight: f64,
    pub entropy_weight: f64,
    pub pii_weight: f64,
    pub sig_weight: f64,
    pub rate_weight: f64,
    pub cap_weight: f64,
    pub pqc_kem_weight: f64,
    pub pqc_sig_weight: f64,
    pub agentic_boundary_weight: f64,
    pub agentic_oversight_weight: f64,
    pub supply_chain_weight: f64,
    pub bias_weight: f64,
    pub eu_ai_act_weight: f64,
    pub explainability_weight: f64,
}

impl Default for DimensionWeights {
    fn default() -> Self {
        Self {
            token_weight: 1.0,
            agent_weight: 1.0,
            fuel_weight: 1.0,
            entropy_weight: 1.0,
            pii_weight: 5.0,
            sig_weight: 5.0,
            rate_weight: 1.0,
            cap_weight: 1.0,
            pqc_kem_weight: 3.0,
            pqc_sig_weight: 3.0,
            agentic_boundary_weight: 2.0,
            agentic_oversight_weight: 2.0,
            supply_chain_weight: 2.0,
            bias_weight: 3.0,
            eu_ai_act_weight: 4.0,
            explainability_weight: 2.0,
        }
    }
}

impl DimensionWeights {
    pub fn as_array(&self) -> [f64; 16] {
        [
            self.token_weight,
            self.agent_weight,
            self.fuel_weight,
            self.entropy_weight,
            self.pii_weight,
            self.sig_weight,
            self.rate_weight,
            self.cap_weight,
            self.pqc_kem_weight,
            self.pqc_sig_weight,
            self.agentic_boundary_weight,
            self.agentic_oversight_weight,
            self.supply_chain_weight,
            self.bias_weight,
            self.eu_ai_act_weight,
            self.explainability_weight,
        ]
    }
    pub fn constitutional_emphasis() -> Self {
        Self {
            pii_weight: 10.0,
            sig_weight: 10.0,
            ..Default::default()
        }
    }
    pub fn pqc_emphasis() -> Self {
        Self {
            pqc_kem_weight: 8.0,
            pqc_sig_weight: 8.0,
            ..Default::default()
        }
    }
    pub fn agentic_emphasis() -> Self {
        Self {
            agentic_boundary_weight: 6.0,
            agentic_oversight_weight: 6.0,
            ..Default::default()
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct SafeManifold {
    pub config: SystemConfig,
    pub defect_config: DefectConfig,
    pub weights: DimensionWeights,
    thresholds: EscapeThresholds,
}

impl SafeManifold {
    pub fn new() -> Self {
        Self {
            config: SystemConfig::default(),
            defect_config: DefectConfig::default(),
            weights: DimensionWeights::default(),
            thresholds: EscapeThresholds::default(),
        }
    }
    pub fn with_config(config: SystemConfig) -> Self {
        Self {
            config,
            defect_config: DefectConfig::default(),
            weights: DimensionWeights::default(),
            thresholds: EscapeThresholds::default(),
        }
    }
    pub fn with_thresholds(config: SystemConfig, thresholds: EscapeThresholds) -> Self {
        Self {
            config,
            defect_config: DefectConfig::default(),
            weights: DimensionWeights::default(),
            thresholds,
        }
    }
    pub fn with_all(
        config: SystemConfig,
        thresholds: EscapeThresholds,
        weights: DimensionWeights,
        defect_config: DefectConfig,
    ) -> Self {
        Self {
            config,
            defect_config,
            weights,
            thresholds,
        }
    }
    pub fn thresholds(&self) -> &EscapeThresholds {
        &self.thresholds
    }

    pub fn embed_state(&self, state: &SystemState) -> ManifoldPoint {
        let v = state.to_vector();
        ManifoldPoint {
            coords: v.to_vec(),
            label: Some(state.summary()),
        }
    }

    pub fn compute_observer_defect(&self, ideal: &SystemState, actual: &SystemState) -> f64 {
        let ideal_v = ideal.to_vector();
        let actual_v = actual.to_vector();
        let weights = self.weights.as_array();
        let dist_sq: f64 = ideal_v
            .iter()
            .zip(actual_v.iter())
            .zip(weights.iter())
            .map(|((a, b), w)| w * (a - b).powi(2))
            .sum();
        let dim = 16.0_f64;
        let weight_sum: f64 = weights.iter().sum();
        let normalized = (dist_sq / (dim * weight_sum * self.defect_config.normalization))
            .sqrt()
            .min(1.0);

        let bool_penalty =
            if !actual.pii_scrubbed && !self.config.allow_constitutional_bypass {
                self.defect_config.pii_penalty
            } else {
                0.0
            } + if !actual.signature_valid && !self.config.allow_constitutional_bypass {
                self.defect_config.sig_penalty
            } else {
                0.0
            } + if !actual.pqc_key_encapsulation && self.config.require_pqc_encapsulation {
                self.defect_config.pqc_kem_penalty
            } else {
                0.0
            } + if !actual.pqc_signature_valid && self.config.require_pqc_signatures {
                self.defect_config.pqc_sig_penalty
            } else {
                0.0
            } + if !actual.agent_action_boundary_defined && self.config.enable_agentic_guardrails {
                self.defect_config.agentic_boundary_penalty
            } else {
                0.0
            } + if actual.human_oversight_triggered && self.config.enable_agentic_guardrails {
                self.defect_config.agentic_oversight_penalty
            } else {
                0.0
            } + if !actual.supply_chain_integrity_verified
                && self.config.require_supply_chain_integrity
            {
                self.defect_config.supply_chain_penalty
            } else {
                0.0
            } + if actual.bias_score > self.config.max_bias_threshold {
                self.defect_config.bias_penalty
            } else {
                0.0
            } + if !actual.eu_ai_act_compliant && self.config.require_eu_ai_act_compliance {
                self.defect_config.eu_ai_act_penalty
            } else {
                0.0
            } + if !actual.explainability_requirement_met && self.config.require_explainability {
                self.defect_config.explainability_penalty
            } else {
                0.0
            };

        (normalized + bool_penalty).min(1.0)
    }

    pub fn assess_defect(&self, ideal: &SystemState, actual: &SystemState) -> DefectAssessment {
        let value = self.compute_observer_defect(ideal, actual);
        let level = DefectLevel::from_defect(value, &self.thresholds);
        let violated = actual.violations();
        DefectAssessment {
            value,
            level,
            violated_invariants: violated,
            is_escaping: level == DefectLevel::Escaping,
        }
    }

    pub fn assess_batch(&self, ideal: &SystemState, states: &[SystemState]) -> BatchAssessment {
        BatchAssessment::new(
            states
                .iter()
                .map(|s| self.assess_defect(ideal, s))
                .collect(),
        )
    }

    pub fn defect_by_category(
        &self,
        _ideal: &SystemState,
        actual: &SystemState,
    ) -> HashMap<InvariantCategory, f64> {
        let mut map = HashMap::new();
        for cat in InvariantCategory::all() {
            let invariants: Vec<Invariant> = Invariant::all()
                .iter()
                .filter(|inv| inv.category() == cat)
                .cloned()
                .collect();
            if invariants.is_empty() {
                continue;
            }
            let violations = invariants
                .iter()
                .filter(|inv| !actual.check_invariant(**inv).passed)
                .count();
            map.insert(cat, violations as f64 / invariants.len() as f64);
        }
        map
    }

    pub fn neron_model(&self, state: &SystemState) -> SystemState {
        state.clone()
    }

    pub fn neron_model_checked(&self, state: &SystemState) -> Result<SystemState, ManifoldError> {
        if !state.pii_scrubbed && !self.config.allow_constitutional_bypass {
            return Err(ManifoldError::InvariantViolation(
                "I-05: pii_scrubbed=false".into(),
            ));
        }
        if !state.signature_valid && !self.config.allow_constitutional_bypass {
            return Err(ManifoldError::InvariantViolation(
                "I-06: signature_valid=false".into(),
            ));
        }
        Ok(state.clone())
    }

    pub fn profile(&self, name: &str) -> ManifoldProfile {
        ManifoldProfile::new(name, 16)
    }
}

impl Default for SafeManifold {
    fn default() -> Self {
        Self::new()
    }
}
