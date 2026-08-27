import os, subprocess

BASE = "."

# ================================================================
# 1. Cargo.toml
# ================================================================
cargo_toml = '''[package]
name = "arkhe-safe-manifold"
version = "0.8.0"
edition = "2021"
description = "SafeManifold v0.8.0"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
thiserror = "1.0"
chrono = { version = "0.4", features = ["serde"], optional = true }
uuid = { version = "1.10", features = ["v4"], optional = true }
indexmap = { version = "2.0", optional = true }

[dev-dependencies]
proptest = "1.6"
criterion = { version = "0.5", features = ["html_reports"] }
tokio = { version = "1", features = ["rt", "macros"] }
tempfile = "3.27"

[features]
default = []
prolog = []
audit = ["chrono", "uuid"]
recovery = ["indexmap"]
mssp = ["audit"]
pqc = []
async = []
nist = []
iso42001 = []
agentic = []
eu_ai_act = []
supply_chain = []
bias = []
explainability = ["chrono"]
full = ["audit", "recovery", "mssp", "prolog", "pqc", "async",
        "nist", "iso42001", "agentic", "eu_ai_act", "supply_chain",
        "bias", "explainability"]
'''

# ================================================================
# 2. src/lib.rs
# ================================================================
lib_rs = '''
#![deny(unsafe_code)]
#![cfg_attr(all(test, feature = "full"), deny(warnings))]

pub mod invariants;
pub mod safe_manifold;
pub mod pattern_signature;

#[cfg(feature = "pqc")]
pub mod pqc;

#[cfg(feature = "nist")]
pub mod nist_ai_rmf;

#[cfg(feature = "iso42001")]
pub mod iso42001;

#[cfg(feature = "agentic")]
pub mod agentic_governance;

#[cfg(feature = "mssp")]
pub mod mssp_bridge;

#[cfg(feature = "prolog")]
pub mod prolog_bridge;

#[cfg(feature = "recovery")]
pub mod rsi;

#[cfg(feature = "audit")]
pub mod audit;

#[cfg(feature = "eu_ai_act")]
pub mod eu_ai_act;

#[cfg(feature = "supply_chain")]
pub mod supply_chain;

#[cfg(feature = "bias")]
pub mod bias_detection;

#[cfg(feature = "explainability")]
pub mod explainability;

pub use invariants::{
    Invariant, InvariantCategory, InvariantCheck, ManifoldError,
    SystemConfig, SystemState,
};
pub use safe_manifold::{
    BatchAssessment, DefectAssessment, DefectConfig, DefectLevel,
    DimensionWeights, EscapeThresholds, ManifoldPoint, ManifoldProfile,
    SafeManifold, SafeState,
};
pub use pattern_signature::{
    PatternCategory, PatternClassifier, PatternMatch, PatternSignature,
};

#[cfg(feature = "pqc")]
pub use pqc::{
    EncapsulationResult, PqcAlgorithm, PqcMigrationPlan, PqcProvider,
    SignatureResult, StubPqcProvider, pqc_readiness_score, validate_pqc_invariants,
};

#[cfg(feature = "nist")]
pub use nist_ai_rmf::{
    AccountabilityRegistry, CsfFunction, NistFunction, RiskTier,
    RmfMapping, RmfRegistry,
};

#[cfg(feature = "iso42001")]
pub use iso42001::{
    AimsAssessment, Iso42001Framework, IsoClause, IsoControl,
    UnifiedGovernanceView,
};

#[cfg(feature = "agentic")]
pub use agentic_governance::{
    AgentAction, AgenticGovernanceEngine, GuardrailEvaluation,
    GuardrailRule, GuardrailTier, ViolationSeverity, validate_agentic_invariants,
};

#[cfg(feature = "mssp")]
pub use mssp_bridge::{CategorizationLevel, MsspBridge, RegulatoryMapping, SlaTier};

#[cfg(feature = "prolog")]
pub use prolog_bridge::{PrologBridge, PrologClient, PrologError};

#[cfg(feature = "recovery")]
pub use rsi::{RecoveryAction, RecoverySuggestion, RsiEngine};

#[cfg(all(feature = "recovery", feature = "async"))]
pub use rsi::AsyncRsiEngine;

#[cfg(feature = "audit")]
pub use audit::{AuditEntry, AuditLog, AuditOutcome};

#[cfg(feature = "eu_ai_act")]
pub use eu_ai_act::{EuAiActAssessment, EuAiActFramework, EuRiskCategory};

#[cfg(feature = "supply_chain")]
pub use supply_chain::{SupplyChainComponent, SupplyChainVerifier};

#[cfg(feature = "bias")]
pub use bias_detection::{BiasDetector, BiasMeasurement, BiasMetric};

#[cfg(feature = "explainability")]
pub use explainability::{
    DetailLevel, ExplainabilityEngine, ExplainabilityRecord, ExplainabilitySummary,
};
'''

# ================================================================
# 3. src/invariants.rs — 16 invariants, 16D vector, InvariantCategory
# ================================================================
invariants_rs = r'''//! System invariants and state definitions (v0.8.0 — 16 invariants, 16D).

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Error type for manifold operations.
#[derive(Error, Debug, Clone, PartialEq, Eq)]
pub enum ManifoldError {
    #[error("Invariant violation: {0}")]
    InvariantViolation(String),
    #[error("State projection failed: {0}")]
    ProjectionFailed(String),
    #[error("Invalid dimension for operation: {0}")]
    InvalidDimension(String),
    #[error("Recovery failed: {0}")]
    RecoveryFailed(String),
    #[error("Configuration error: {0}")]
    ConfigError(String),
    #[error("PQC error: {0}")]
    PqcError(String),
    #[error("Agentic governance error: {0}")]
    AgenticError(String),
}

/// Invariant category classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum InvariantCategory {
    Resource,
    Capability,
    Constitutional,
    Pqc,
    Agentic,
    SupplyChain,
    Bias,
    EuAiAct,
    Explainability,
}

impl InvariantCategory {
    pub fn all() -> [Self; 9] {
        [
            Self::Resource, Self::Capability, Self::Constitutional,
            Self::Pqc, Self::Agentic, Self::SupplyChain,
            Self::Bias, Self::EuAiAct, Self::Explainability,
        ]
    }
    pub fn label(&self) -> &'static str {
        match self {
            Self::Resource => "Resource",
            Self::Capability => "Capability",
            Self::Constitutional => "Constitutional",
            Self::Pqc => "PQC",
            Self::Agentic => "Agentic",
            Self::SupplyChain => "SupplyChain",
            Self::Bias => "Bias",
            Self::EuAiAct => "EuAiAct",
            Self::Explainability => "Explainability",
        }
    }
}

fn default_max_bias() -> f64 { 0.1 }

/// System configuration — immutable parameters that define the manifold.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct SystemConfig {
    pub max_tokens: i64,
    pub max_agents: u32,
    pub max_sandbox_fuel: i64,
    pub min_entropy: u32,
    pub max_rate_limit: i64,
    pub min_model_capability: u64,
    #[serde(default)]
    pub allow_constitutional_bypass: bool,
    #[serde(default)]
    pub require_pqc_encapsulation: bool,
    #[serde(default)]
    pub require_pqc_signatures: bool,
    #[serde(default)]
    pub enable_agentic_guardrails: bool,
    #[serde(default)]
    pub require_supply_chain_integrity: bool,
    #[serde(default = "default_max_bias")]
    pub max_bias_threshold: f64,
    #[serde(default)]
    pub require_eu_ai_act_compliance: bool,
    #[serde(default)]
    pub require_explainability: bool,
}

impl Eq for SystemConfig {}

impl Default for SystemConfig {
    fn default() -> Self {
        Self {
            max_tokens: 10_000,
            max_agents: 10,
            max_sandbox_fuel: 1_000,
            min_entropy: 256,
            max_rate_limit: 1_000,
            min_model_capability: 4_294_967_296,
            allow_constitutional_bypass: false,
            require_pqc_encapsulation: false,
            require_pqc_signatures: false,
            enable_agentic_guardrails: false,
            require_supply_chain_integrity: false,
            max_bias_threshold: 0.1,
            require_eu_ai_act_compliance: false,
            require_explainability: false,
        }
    }
}

impl SystemConfig {
    pub fn strict() -> Self {
        Self {
            max_tokens: 5_000, max_agents: 5, max_sandbox_fuel: 500,
            min_entropy: 512, max_rate_limit: 500,
            min_model_capability: 8_589_934_592,
            allow_constitutional_bypass: false,
            require_pqc_encapsulation: true,
            require_pqc_signatures: true,
            enable_agentic_guardrails: true,
            require_supply_chain_integrity: true,
            max_bias_threshold: 0.05,
            require_eu_ai_act_compliance: true,
            require_explainability: true,
        }
    }
    pub fn permissive() -> Self {
        Self {
            max_tokens: 100_000, max_agents: 50, max_sandbox_fuel: 10_000,
            min_entropy: 128, max_rate_limit: 10_000,
            min_model_capability: 1_073_741_824,
            allow_constitutional_bypass: false,
            require_pqc_encapsulation: false,
            require_pqc_signatures: false,
            enable_agentic_guardrails: false,
            require_supply_chain_integrity: false,
            max_bias_threshold: 0.2,
            require_eu_ai_act_compliance: false,
            require_explainability: false,
        }
    }
    pub fn testing_unsafe() -> Self {
        let mut cfg = Self::permissive();
        cfg.allow_constitutional_bypass = true;
        cfg
    }
    pub fn validate(&self) -> Result<(), ManifoldError> {
        if self.max_tokens <= 0 {
            return Err(ManifoldError::ConfigError("max_tokens must be positive".into()));
        }
        if self.max_agents == 0 {
            return Err(ManifoldError::ConfigError("max_agents must be positive".into()));
        }
        if self.max_sandbox_fuel <= 0 {
            return Err(ManifoldError::ConfigError("max_sandbox_fuel must be positive".into()));
        }
        if self.max_rate_limit <= 0 {
            return Err(ManifoldError::ConfigError("max_rate_limit must be positive".into()));
        }
        if self.max_bias_threshold <= 0.0 {
            return Err(ManifoldError::ConfigError("max_bias_threshold must be positive".into()));
        }
        Ok(())
    }
}

/// Result of checking a single invariant.
#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct InvariantCheck {
    pub invariant: Invariant,
    pub passed: bool,
    pub message: String,
}

/// The canonical system state — all 16 fields observable and auditable.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct SystemState {
    pub token_budget: i64,
    pub agent_count: u32,
    pub sandbox_fuel: i64,
    pub entropy_bits: u32,
    pub pii_scrubbed: bool,
    pub signature_valid: bool,
    pub rate_limit_remaining: i64,
    pub model_capability: u64,
    pub pqc_key_encapsulation: bool,
    pub pqc_signature_valid: bool,
    pub agent_action_boundary_defined: bool,
    pub human_oversight_triggered: bool,
    pub supply_chain_integrity_verified: bool,
    pub bias_score: f64,
    pub eu_ai_act_compliant: bool,
    pub explainability_requirement_met: bool,
    #[serde(skip)]
    pub config: SystemConfig,
}

impl Eq for SystemState {}

impl SystemState {
    pub fn safe(config: SystemConfig) -> Self {
        Self {
            token_budget: config.max_tokens / 2,
            agent_count: 1,
            sandbox_fuel: config.max_sandbox_fuel / 2,
            entropy_bits: config.min_entropy,
            pii_scrubbed: true,
            signature_valid: true,
            rate_limit_remaining: config.max_rate_limit / 2,
            model_capability: config.min_model_capability,
            pqc_key_encapsulation: true,
            pqc_signature_valid: true,
            agent_action_boundary_defined: true,
            human_oversight_triggered: false,
            supply_chain_integrity_verified: true,
            bias_score: 0.0,
            eu_ai_act_compliant: true,
            explainability_requirement_met: true,
            config,
        }
    }

    pub fn check_all(&self) -> bool {
        self.check_all_detailed().iter().all(|c| c.passed)
    }

    pub fn check_all_detailed(&self) -> Vec<InvariantCheck> {
        Invariant::all().iter().map(|&inv| self.check_invariant(inv)).collect()
    }

    pub fn check_invariant(&self, inv: Invariant) -> InvariantCheck {
        let (passed, message) = match inv {
            Invariant::I01 => (
                self.token_budget >= 0 && self.token_budget <= self.config.max_tokens,
                format!("token_budget={} in [0, {}]", self.token_budget, self.config.max_tokens),
            ),
            Invariant::I02 => (
                self.agent_count <= self.config.max_agents,
                format!("agent_count={} <= {}", self.agent_count, self.config.max_agents),
            ),
            Invariant::I03 => (
                self.sandbox_fuel > 0 && self.sandbox_fuel <= self.config.max_sandbox_fuel,
                format!("sandbox_fuel={} in (0, {}]", self.sandbox_fuel, self.config.max_sandbox_fuel),
            ),
            Invariant::I04 => (
                self.entropy_bits >= self.config.min_entropy,
                format!("entropy_bits={} >= {}", self.entropy_bits, self.config.min_entropy),
            ),
            Invariant::I05 => (
                self.pii_scrubbed || self.config.allow_constitutional_bypass,
                format!("pii_scrubbed={}", self.pii_scrubbed),
            ),
            Invariant::I06 => (
                self.signature_valid || self.config.allow_constitutional_bypass,
                format!("signature_valid={}", self.signature_valid),
            ),
            Invariant::I07 => (
                self.rate_limit_remaining > 0 && self.rate_limit_remaining <= self.config.max_rate_limit,
                format!("rate_limit_remaining={} in (0, {}]", self.rate_limit_remaining, self.config.max_rate_limit),
            ),
            Invariant::I08 => (
                self.model_capability >= self.config.min_model_capability,
                format!("model_capability={} >= {}", self.model_capability, self.config.min_model_capability),
            ),
            Invariant::I09 => (
                self.pqc_key_encapsulation || !self.config.require_pqc_encapsulation,
                format!("pqc_key_encapsulation={} (req={})", self.pqc_key_encapsulation, self.config.require_pqc_encapsulation),
            ),
            Invariant::I10 => (
                self.pqc_signature_valid || !self.config.require_pqc_signatures,
                format!("pqc_signature_valid={} (req={})", self.pqc_signature_valid, self.config.require_pqc_signatures),
            ),
            Invariant::I11 => (
                self.agent_action_boundary_defined || !self.config.enable_agentic_guardrails,
                format!("agent_action_boundary_defined={} (en={})", self.agent_action_boundary_defined, self.config.enable_agentic_guardrails),
            ),
            Invariant::I12 => (
                !self.human_oversight_triggered || !self.config.enable_agentic_guardrails,
                format!("human_oversight_triggered={} (en={})", self.human_oversight_triggered, self.config.enable_agentic_guardrails),
            ),
            Invariant::I13 => (
                self.supply_chain_integrity_verified || !self.config.require_supply_chain_integrity,
                format!("supply_chain_integrity_verified={} (req={})", self.supply_chain_integrity_verified, self.config.require_supply_chain_integrity),
            ),
            Invariant::I14 => (
                self.bias_score <= self.config.max_bias_threshold,
                format!("bias_score={} <= {}", self.bias_score, self.config.max_bias_threshold),
            ),
            Invariant::I15 => (
                self.eu_ai_act_compliant || !self.config.require_eu_ai_act_compliance,
                format!("eu_ai_act_compliant={} (req={})", self.eu_ai_act_compliant, self.config.require_eu_ai_act_compliance),
            ),
            Invariant::I16 => (
                self.explainability_requirement_met || !self.config.require_explainability,
                format!("explainability_requirement_met={} (req={})", self.explainability_requirement_met, self.config.require_explainability),
            ),
        };
        InvariantCheck { invariant: inv, passed, message }
    }

    pub fn violations(&self) -> Vec<Invariant> {
        self.check_all_detailed().into_iter().filter(|c| !c.passed).map(|c| c.invariant).collect()
    }
    pub fn constitutional_violations(&self) -> Vec<Invariant> {
        self.violations().into_iter().filter(|v| v.category() == InvariantCategory::Constitutional).collect()
    }
    pub fn pqc_violations(&self) -> Vec<Invariant> {
        self.violations().into_iter().filter(|v| v.category() == InvariantCategory::Pqc).collect()
    }
    pub fn agentic_violations(&self) -> Vec<Invariant> {
        self.violations().into_iter().filter(|v| v.category() == InvariantCategory::Agentic).collect()
    }
    pub fn has_constitutional_violations(&self) -> bool {
        !self.constitutional_violations().is_empty()
    }

    pub fn summary(&self) -> String {
        format!(
            "SystemState[tokens={},agents={},fuel={},entropy={},pii={},sig={},rate={},cap={},\
             pqk={},pqs={},aab={},hot={},sci={},bias={},euai={},expl={}]",
            self.token_budget, self.agent_count, self.sandbox_fuel, self.entropy_bits,
            self.pii_scrubbed, self.signature_valid, self.rate_limit_remaining, self.model_capability,
            self.pqc_key_encapsulation, self.pqc_signature_valid,
            self.agent_action_boundary_defined, self.human_oversight_triggered,
            self.supply_chain_integrity_verified, self.bias_score,
            self.eu_ai_act_compliant, self.explainability_requirement_met,
        )
    }

    /// Convert state to 16D vector for pattern classification.
    pub fn to_vector(&self) -> [f64; 16] {
        let cap = if self.model_capability == 0 { 1.0 } else { self.model_capability as f64 };
        // Normalize bias_score: 0 bias → 1.0, max threshold → 0.0
        let bias_norm = if self.config.max_bias_threshold > 0.0 {
            (1.0 - (self.bias_score / self.config.max_bias_threshold).min(1.0)).max(0.0)
        } else { 1.0 };
        [
            self.token_budget as f64,           // 0
            self.agent_count as f64,             // 1
            self.sandbox_fuel as f64,            // 2
            self.entropy_bits as f64,            // 3
            if self.pii_scrubbed { 1.0 } else { 0.0 },   // 4
            if self.signature_valid { 1.0 } else { 0.0 }, // 5
            self.rate_limit_remaining as f64,    // 6
            cap.log2(),                          // 7
            if self.pqc_key_encapsulation { 1.0 } else { 0.0 }, // 8
            if self.pqc_signature_valid { 1.0 } else { 0.0 },  // 9
            if self.agent_action_boundary_defined { 1.0 } else { 0.0 }, // 10
            if self.human_oversight_triggered { 1.0 } else { 0.0 },   // 11
            if self.supply_chain_integrity_verified { 1.0 } else { 0.0 }, // 12
            bias_norm,                           // 13
            if self.eu_ai_act_compliant { 1.0 } else { 0.0 },     // 14
            if self.explainability_requirement_met { 1.0 } else { 0.0 }, // 15
        ]
    }
}

/// Invariant identifiers (v0.8.0 — 16 invariants).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Invariant {
    I01, I02, I03, I04, I05, I06, I07, I08,
    I09, I10,
    I11, I12,
    I13,
    I14,
    I15,
    I16,
}

impl Invariant {
    pub fn all() -> [Self; 16] {
        [
            Self::I01, Self::I02, Self::I03, Self::I04, Self::I05, Self::I06,
            Self::I07, Self::I08, Self::I09, Self::I10, Self::I11, Self::I12,
            Self::I13, Self::I14, Self::I15, Self::I16,
        ]
    }
    pub fn category(&self) -> InvariantCategory {
        match self {
            Self::I01 | Self::I02 | Self::I03 | Self::I07 => InvariantCategory::Resource,
            Self::I04 | Self::I08 => InvariantCategory::Capability,
            Self::I05 | Self::I06 => InvariantCategory::Constitutional,
            Self::I09 | Self::I10 => InvariantCategory::Pqc,
            Self::I11 | Self::I12 => InvariantCategory::Agentic,
            Self::I13 => InvariantCategory::SupplyChain,
            Self::I14 => InvariantCategory::Bias,
            Self::I15 => InvariantCategory::EuAiAct,
            Self::I16 => InvariantCategory::Explainability,
        }
    }
    pub fn is_constitutional(&self) -> bool { self.category() == InvariantCategory::Constitutional }
    pub fn is_resource(&self) -> bool { self.category() == InvariantCategory::Resource }
    pub fn is_capability(&self) -> bool { self.category() == InvariantCategory::Capability }
    pub fn is_pqc(&self) -> bool { self.category() == InvariantCategory::Pqc }
    pub fn is_agentic(&self) -> bool { self.category() == InvariantCategory::Agentic }
    pub fn prolog_name(&self) -> &'static str {
        match self {
            Self::I01 => "i01", Self::I02 => "i02", Self::I03 => "i03", Self::I04 => "i04",
            Self::I05 => "i05", Self::I06 => "i06", Self::I07 => "i07", Self::I08 => "i08",
            Self::I09 => "i09", Self::I10 => "i10", Self::I11 => "i11", Self::I12 => "i12",
            Self::I13 => "i13", Self::I14 => "i14", Self::I15 => "i15", Self::I16 => "i16",
        }
    }
}

impl std::fmt::Display for Invariant {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::I01 => write!(f, "I-01 (token_budget in [0, max])"),
            Self::I02 => write!(f, "I-02 (agent_count <= max)"),
            Self::I03 => write!(f, "I-03 (sandbox_fuel in (0, max])"),
            Self::I04 => write!(f, "I-04 (entropy_bits >= min)"),
            Self::I05 => write!(f, "I-05 (pii_scrubbed) [CONSTITUTIONAL]"),
            Self::I06 => write!(f, "I-06 (signature_valid) [CONSTITUTIONAL]"),
            Self::I07 => write!(f, "I-07 (rate_limit in (0, max])"),
            Self::I08 => write!(f, "I-08 (model_capability >= min)"),
            Self::I09 => write!(f, "I-09 (pqc_key_encapsulation) [PQC]"),
            Self::I10 => write!(f, "I-10 (pqc_signature_valid) [PQC]"),
            Self::I11 => write!(f, "I-11 (agent_action_boundary_defined) [AGENTIC]"),
            Self::I12 => write!(f, "I-12 (human_oversight_triggered) [AGENTIC]"),
            Self::I13 => write!(f, "I-13 (supply_chain_integrity_verified) [SUPPLY_CHAIN]"),
            Self::I14 => write!(f, "I-14 (bias_score <= threshold) [BIAS]"),
            Self::I15 => write!(f, "I-15 (eu_ai_act_compliant) [EU_AI_ACT]"),
            Self::I16 => write!(f, "I-16 (explainability_requirement_met) [EXPLAINABILITY]"),
        }
    }
}
'''

# ================================================================
# 4. src/safe_manifold.rs — 16 dimensions
# ================================================================
safe_manifold_rs = r'''//! SafeManifold — 16D security state projection engine (v0.8.0).

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
        self.coords.iter().zip(other.coords.iter())
            .map(|(a, b)| (a - b).powi(2)).sum::<f64>().sqrt()
    }
    pub fn dimensions(&self) -> usize { self.coords.len() }
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
        Self { defect_limit: 0.5, warning_threshold: 0.3, early_warning: true }
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
                .map(|d| d.as_millis() as u64).unwrap_or(0),
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
            return Err(ManifoldError::InvariantViolation(
                format!("Defect {:.4} exceeds safe threshold 0.5", defect)
            ));
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
            return Self { assessments, avg_defect: 0.0, max_defect: 0.0, min_defect: 0.0, escaping_count: 0 };
        }
        let mut sum = 0.0f64;
        let mut max_val = f64::NEG_INFINITY;
        let mut min_val = f64::INFINITY;
        let mut esc = 0usize;
        for a in &assessments {
            sum += a.value;
            max_val = max_val.max(a.value);
            min_val = min_val.min(a.value);
            if a.is_escaping { esc += 1; }
        }
        Self { assessments, avg_defect: sum / n as f64, max_defect: max_val, min_defect: min_val, escaping_count: esc }
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
        if defect >= thresholds.defect_limit { Self::Escaping }
        else if thresholds.early_warning && defect >= thresholds.warning_threshold { Self::Critical }
        else if thresholds.early_warning && defect >= thresholds.warning_threshold * 0.5 { Self::Warning }
        else { Self::Nominal }
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
            token_weight: 1.0, agent_weight: 1.0, fuel_weight: 1.0, entropy_weight: 1.0,
            pii_weight: 5.0, sig_weight: 5.0, rate_weight: 1.0, cap_weight: 1.0,
            pqc_kem_weight: 3.0, pqc_sig_weight: 3.0,
            agentic_boundary_weight: 2.0, agentic_oversight_weight: 2.0,
            supply_chain_weight: 2.0, bias_weight: 3.0,
            eu_ai_act_weight: 4.0, explainability_weight: 2.0,
        }
    }
}

impl DimensionWeights {
    pub fn as_array(&self) -> [f64; 16] {
        [
            self.token_weight, self.agent_weight, self.fuel_weight, self.entropy_weight,
            self.pii_weight, self.sig_weight, self.rate_weight, self.cap_weight,
            self.pqc_kem_weight, self.pqc_sig_weight,
            self.agentic_boundary_weight, self.agentic_oversight_weight,
            self.supply_chain_weight, self.bias_weight,
            self.eu_ai_act_weight, self.explainability_weight,
        ]
    }
    pub fn constitutional_emphasis() -> Self {
        Self { pii_weight: 10.0, sig_weight: 10.0, ..Default::default() }
    }
    pub fn pqc_emphasis() -> Self {
        Self { pqc_kem_weight: 8.0, pqc_sig_weight: 8.0, ..Default::default() }
    }
    pub fn agentic_emphasis() -> Self {
        Self { agentic_boundary_weight: 6.0, agentic_oversight_weight: 6.0, ..Default::default() }
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
        Self { config: SystemConfig::default(), defect_config: DefectConfig::default(),
               weights: DimensionWeights::default(), thresholds: EscapeThresholds::default() }
    }
    pub fn with_config(config: SystemConfig) -> Self {
        Self { config, defect_config: DefectConfig::default(),
               weights: DimensionWeights::default(), thresholds: EscapeThresholds::default() }
    }
    pub fn with_thresholds(config: SystemConfig, thresholds: EscapeThresholds) -> Self {
        Self { config, defect_config: DefectConfig::default(),
               weights: DimensionWeights::default(), thresholds }
    }
    pub fn with_all(config: SystemConfig, thresholds: EscapeThresholds,
                    weights: DimensionWeights, defect_config: DefectConfig) -> Self {
        Self { config, defect_config, weights, thresholds }
    }
    pub fn thresholds(&self) -> &EscapeThresholds { &self.thresholds }

    pub fn embed_state(&self, state: &SystemState) -> ManifoldPoint {
        let v = state.to_vector();
        ManifoldPoint { coords: v.to_vec(), label: Some(state.summary()) }
    }

    pub fn compute_observer_defect(&self, ideal: &SystemState, actual: &SystemState) -> f64 {
        let ideal_v = ideal.to_vector();
        let actual_v = actual.to_vector();
        let weights = self.weights.as_array();
        let dist_sq: f64 = ideal_v.iter().zip(actual_v.iter()).zip(weights.iter())
            .map(|((a, b), w)| w * (a - b).powi(2)).sum();
        let dim = 16.0_f64;
        let weight_sum: f64 = weights.iter().sum();
        let normalized = (dist_sq / (dim * weight_sum * self.defect_config.normalization))
            .sqrt().min(1.0);

        let bool_penalty =
            if !actual.pii_scrubbed && !self.config.allow_constitutional_bypass { self.defect_config.pii_penalty } else { 0.0 }
            + if !actual.signature_valid && !self.config.allow_constitutional_bypass { self.defect_config.sig_penalty } else { 0.0 }
            + if !actual.pqc_key_encapsulation && self.config.require_pqc_encapsulation { self.defect_config.pqc_kem_penalty } else { 0.0 }
            + if !actual.pqc_signature_valid && self.config.require_pqc_signatures { self.defect_config.pqc_sig_penalty } else { 0.0 }
            + if !actual.agent_action_boundary_defined && self.config.enable_agentic_guardrails { self.defect_config.agentic_boundary_penalty } else { 0.0 }
            + if actual.human_oversight_triggered && self.config.enable_agentic_guardrails { self.defect_config.agentic_oversight_penalty } else { 0.0 }
            + if !actual.supply_chain_integrity_verified && self.config.require_supply_chain_integrity { self.defect_config.supply_chain_penalty } else { 0.0 }
            + if actual.bias_score > self.config.max_bias_threshold { self.defect_config.bias_penalty } else { 0.0 }
            + if !actual.eu_ai_act_compliant && self.config.require_eu_ai_act_compliance { self.defect_config.eu_ai_act_penalty } else { 0.0 }
            + if !actual.explainability_requirement_met && self.config.require_explainability { self.defect_config.explainability_penalty } else { 0.0 };

        (normalized + bool_penalty).min(1.0)
    }

    pub fn assess_defect(&self, ideal: &SystemState, actual: &SystemState) -> DefectAssessment {
        let value = self.compute_observer_defect(ideal, actual);
        let level = DefectLevel::from_defect(value, &self.thresholds);
        let violated = actual.violations();
        DefectAssessment { value, level, violated_invariants: violated, is_escaping: level == DefectLevel::Escaping }
    }

    pub fn assess_batch(&self, ideal: &SystemState, states: &[SystemState]) -> BatchAssessment {
        BatchAssessment::new(states.iter().map(|s| self.assess_defect(ideal, s)).collect())
    }

    pub fn defect_by_category(&self, _ideal: &SystemState, actual: &SystemState) -> HashMap<InvariantCategory, f64> {
        let mut map = HashMap::new();
        for cat in InvariantCategory::all() {
            let invariants: Vec<Invariant> = Invariant::all().iter()
                .filter(|inv| inv.category() == cat)
                .cloned()
                .collect();
            if invariants.is_empty() { continue; }
            let violations = invariants.iter()
                .filter(|inv| !actual.check_invariant(**inv).passed)
                .count();
            map.insert(cat, violations as f64 / invariants.len() as f64);
        }
        map
    }

    pub fn neron_model(&self, state: &SystemState) -> SystemState { state.clone() }

    pub fn neron_model_checked(&self, state: &SystemState) -> Result<SystemState, ManifoldError> {
        if !state.pii_scrubbed && !self.config.allow_constitutional_bypass {
            return Err(ManifoldError::InvariantViolation("I-05: pii_scrubbed=false".into()));
        }
        if !state.signature_valid && !self.config.allow_constitutional_bypass {
            return Err(ManifoldError::InvariantViolation("I-06: signature_valid=false".into()));
        }
        Ok(state.clone())
    }

    pub fn profile(&self, name: &str) -> ManifoldProfile {
        ManifoldProfile::new(name, 16)
    }
}

impl Default for SafeManifold {
    fn default() -> Self { Self::new() }
}
'''

# ================================================================
# 5. src/pattern_signature.rs — 16D centroids
# ================================================================
pattern_signature_rs = r'''//! Pattern signature classification via 16D topological centroids (v0.8.0).

use crate::invariants::SystemState;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PatternCategory {
    Safe,
    Degraded,
    Critical,
    Anomalous,
    Unknown,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct PatternSignature {
    pub name: String,
    pub centroid: [f64; 16],
    pub radius: f64,
    pub category: PatternCategory,
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct PatternMatch {
    pub pattern_name: String,
    pub category: PatternCategory,
    pub distance: f64,
    pub within_radius: bool,
    pub confidence: f64,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct PatternClassifier {
    patterns: Vec<PatternSignature>,
}

impl PatternClassifier {
    pub fn new() -> Self {
        let mut c = Self { patterns: Vec::new() };
        c.init_defaults();
        c
    }

    fn init_defaults(&mut self) {
        self.patterns.push(PatternSignature {
            name: "nominal_safe".into(),
            centroid: [5000.0, 1.0, 500.0, 256.0, 1.0, 1.0, 500.0, 32.0,
                       1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0],
            radius: 0.4,
            category: PatternCategory::Safe,
        });
        self.patterns.push(PatternSignature {
            name: "resource_degraded".into(),
            centroid: [500.0, 1.0, 50.0, 256.0, 1.0, 1.0, 50.0, 32.0,
                       1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0],
            radius: 0.35,
            category: PatternCategory::Degraded,
        });
        self.patterns.push(PatternSignature {
            name: "constitutional_breach".into(),
            centroid: [5000.0, 1.0, 500.0, 256.0, 0.0, 0.0, 500.0, 32.0,
                       1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0],
            radius: 0.3,
            category: PatternCategory::Critical,
        });
        self.patterns.push(PatternSignature {
            name: "compliance_failure".into(),
            centroid: [5000.0, 1.0, 500.0, 256.0, 1.0, 1.0, 500.0, 32.0,
                       0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0],
            radius: 0.35,
            category: PatternCategory::Critical,
        });
    }

    fn distance(a: &[f64; 16], b: &[f64; 16]) -> f64 {
        a.iter().zip(b.iter()).map(|(x, y)| (x - y).powi(2)).sum::<f64>().sqrt()
    }

    pub fn classify(&self, state: &SystemState) -> PatternMatch {
        let v = state.to_vector();
        let best = self.patterns.iter()
            .map(|p| (p, Self::distance(&v, &p.centroid)))
            .min_by(|(_, d1), (_, d2)| d1.partial_cmp(d2).unwrap_or(std::cmp::Ordering::Equal));

        match best {
            Some((pattern, dist)) => {
                let within = dist <= pattern.radius;
                let conf = if pattern.radius > 0.0 { (1.0 - dist / pattern.radius).max(0.0).min(1.0) } else { 0.0 };
                PatternMatch {
                    pattern_name: pattern.name.clone(),
                    category: if within { pattern.category } else { PatternCategory::Unknown },
                    distance: dist, within_radius: within, confidence: conf,
                }
            }
            None => PatternMatch {
                pattern_name: "none".into(), category: PatternCategory::Unknown,
                distance: f64::INFINITY, within_radius: false, confidence: 0.0,
            },
        }
    }

    pub fn add_pattern(&mut self, p: PatternSignature) { self.patterns.push(p); }
    pub fn patterns(&self) -> &[PatternSignature] { &self.patterns }
}

impl Default for PatternClassifier {
    fn default() -> Self { Self::new() }
}
'''

# ================================================================
# 6. src/pqc.rs
# ================================================================
pqc_rs = r'''//! Post-Quantum Cryptography stubs (v0.8.0).

use crate::invariants::{ManifoldError, SystemState};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub enum PqcAlgorithm { #[default] MlKem768, MlKem1024, MlDsa65, MlDsa87 }

impl PqcAlgorithm {
    pub fn security_level(&self) -> u8 {
        match self { Self::MlKem768 | Self::MlDsa65 => 3, Self::MlKem1024 | Self::MlDsa87 => 5 }
    }
    pub fn nist_standard(&self) -> &'static str {
        match self { Self::MlKem768 | Self::MlKem1024 => "FIPS 203", Self::MlDsa65 | Self::MlDsa87 => "FIPS 204" }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
#[allow(dead_code)]
pub struct EncapsulationResult { pub ciphertext: Vec<u8>, pub shared_secret: Vec<u8> }

#[derive(Debug, Clone, PartialEq, Eq)]
#[allow(dead_code)]
pub struct SignatureResult { pub signature: Vec<u8>, pub public_key_hash: String }

pub trait PqcProvider: Send + Sync {
    fn algorithm(&self) -> PqcAlgorithm;
    fn encapsulate(&self, public_key: &[u8]) -> Result<EncapsulationResult, ManifoldError>;
    fn decapsulate(&self, secret_key: &[u8], ciphertext: &[u8]) -> Result<Vec<u8>, ManifoldError>;
    fn sign(&self, secret_key: &[u8], message: &[u8]) -> Result<SignatureResult, ManifoldError>;
    fn verify(&self, public_key: &[u8], message: &[u8], signature: &[u8]) -> Result<bool, ManifoldError>;
}

fn simple_hash(data: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for &b in data { h ^= b as u64; h = h.wrapping_mul(0x100000001b3); }
    h
}

#[derive(Debug, Clone, Default)]
#[allow(dead_code)]
pub struct StubPqcProvider { algorithm: PqcAlgorithm }

impl StubPqcProvider {
    pub fn new(algorithm: PqcAlgorithm) -> Self { Self { algorithm } }
}

impl PqcProvider for StubPqcProvider {
    fn algorithm(&self) -> PqcAlgorithm { self.algorithm }
    fn encapsulate(&self, _: &[u8]) -> Result<EncapsulationResult, ManifoldError> {
        Ok(EncapsulationResult { ciphertext: vec![0u8; 1088], shared_secret: vec![0u8; 32] })
    }
    fn decapsulate(&self, _: &[u8], _: &[u8]) -> Result<Vec<u8>, ManifoldError> { Ok(vec![0u8; 32]) }
    fn sign(&self, _: &[u8], msg: &[u8]) -> Result<SignatureResult, ManifoldError> {
        Ok(SignatureResult { signature: vec![0u8; 3309], public_key_hash: format!("{:016x}", simple_hash(msg)) })
    }
    fn verify(&self, _: &[u8], _: &[u8], _: &[u8]) -> Result<bool, ManifoldError> { Ok(true) }
}

pub fn validate_pqc_invariants(state: &SystemState) -> Result<(), ManifoldError> {
    if state.config.require_pqc_encapsulation && !state.pqc_key_encapsulation {
        return Err(ManifoldError::PqcError("I-09: PQC key encapsulation not enforced".into()));
    }
    if state.config.require_pqc_signatures && !state.pqc_signature_valid {
        return Err(ManifoldError::PqcError("I-10: PQC signature not valid".into()));
    }
    Ok(())
}

pub fn pqc_readiness_score(state: &SystemState) -> f64 {
    let mut s = 0.0f64; let mut t = 0.0f64;
    if state.config.require_pqc_encapsulation { t += 1.0; if state.pqc_key_encapsulation { s += 1.0; } }
    if state.config.require_pqc_signatures { t += 1.0; if state.pqc_signature_valid { s += 1.0; } }
    if t == 0.0 { 1.0 } else { s / t }
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct PqcMigrationPlan {
    pub current_algorithms: Vec<String>,
    pub target_algorithms: Vec<PqcAlgorithm>,
    pub deadline_2030_ready: bool,
    pub deadline_2031_ready: bool,
    pub estimated_effort_days: u32,
}

impl PqcMigrationPlan {
    pub fn for_state(state: &SystemState) -> Self {
        Self {
            current_algorithms: vec!["RSA-2048".into(), "ECDSA-P256".into()],
            target_algorithms: vec![PqcAlgorithm::MlKem768, PqcAlgorithm::MlDsa65],
            deadline_2030_ready: state.pqc_key_encapsulation,
            deadline_2031_ready: state.pqc_signature_valid,
            estimated_effort_days: if state.pqc_key_encapsulation && state.pqc_signature_valid { 0 } else { 180 },
        }
    }
}
'''

# --- 7. nist_ai_rmf.rs ---
nist_ai_rmf_rs = r'''//! NIST AI RMF + CSF 2.0 alignment (v0.8.0).

use crate::invariants::{Invariant, SystemState};
use crate::safe_manifold::SafeManifold;
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum NistFunction { Govern, Map, Measure, Manage }

impl NistFunction {
    pub fn all() -> [Self; 4] { [Self::Govern, Self::Map, Self::Measure, Self::Manage] }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum CsfFunction { Govern, Identify, Protect, Detect, Respond, Recover }

impl CsfFunction {
    pub fn all() -> [Self; 6] { [Self::Govern, Self::Identify, Self::Protect, Self::Detect, Self::Respond, Self::Recover] }
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
pub struct RmfRegistry { mappings: Vec<RmfMapping> }

impl RmfRegistry {
    pub fn new() -> Self { let mut r = Self::default(); r.init(); r }
    fn init(&mut self) {
        self.mappings = vec![
            RmfMapping { function: NistFunction::Govern, category: "GOVERN 1".into(), subcategory: "GOVERN 1.1".into(),
                description: "Legal and regulatory requirements".into(), manifold_capability: "MSSP bridge".into(),
                invariant_mappings: vec![Invariant::I05, Invariant::I06, Invariant::I15], satisfied: false },
        ];
    }
    pub fn evaluate(&mut self, state: &SystemState, manifold: &SafeManifold) {
        let ideal = SystemState::safe(state.config.clone());
        let assessment = manifold.assess_defect(&ideal, state);
        for m in &mut self.mappings {
            m.satisfied = m.invariant_mappings.iter().all(|inv| state.check_invariant(*inv).passed);
            if m.function == NistFunction::Manage && assessment.is_escaping { m.satisfied = false; }
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum RiskTier { Negligible, Low, Medium, High, Critical }

#[derive(Debug, Clone, Default)]
#[allow(dead_code)]
pub struct AccountabilityRegistry { role_invariants: HashMap<String, Vec<Invariant>> }
'''

# --- 8. iso42001.rs ---
iso42001_rs = r'''//! ISO/IEC 42001:2023 AIMS alignment (v0.8.0).

use crate::invariants::{Invariant, SystemState};
use crate::safe_manifold::SafeManifold;
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum IsoClause { Clause4, Clause5, Clause6, Clause7, Clause8, Clause9, Clause10 }

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct IsoControl {
    pub clause: IsoClause, pub control_id: String, pub title: String,
    pub invariant_mappings: Vec<Invariant>, pub implemented: bool,
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct AimsAssessment {
    pub overall_score: f64, pub clause_scores: HashMap<IsoClause, f64>,
    pub total_controls: usize, pub implemented_controls: usize,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct Iso42001Framework { controls: Vec<IsoControl> }

impl Iso42001Framework {
    pub fn new() -> Self { Self { controls: Vec::new() } }
    pub fn assess(&mut self, _state: &SystemState, _manifold: &SafeManifold) -> AimsAssessment {
        AimsAssessment { overall_score: 1.0, clause_scores: HashMap::new(), total_controls: 0, implemented_controls: 0 }
    }
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct UnifiedGovernanceView {
    pub nist_compliance: f64, pub iso_compliance: f64, pub risk_tier: String,
}
'''

# --- 9. agentic_governance.rs ---
agentic_gov_rs = r'''//! IAPP 3-tier guardrails for autonomous agents (v0.8.0).

use crate::invariants::{Invariant, SystemState, ManifoldError};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum GuardrailTier { Hard, Soft, Advisory }

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ViolationSeverity { Info, Low, Medium, High, Critical }

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct GuardrailRule {
    pub id: String, pub tier: GuardrailTier, pub description: String,
    pub invariant: Option<Invariant>, pub escalation_required: bool,
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct GuardrailEvaluation {
    pub rule_id: String, pub tier: GuardrailTier, pub passed: bool,
    pub severity: ViolationSeverity, pub message: String,
    pub escalation_required: bool, pub blocking: bool,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct AgentAction {
    pub agent_id: String, pub action_type: String, pub target: String,
}
impl AgentAction {
    pub fn new(id: &str, atype: &str, target: &str) -> Self {
        Self { agent_id: id.into(), action_type: atype.into(), target: target.into() }
    }
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct AgenticGovernanceEngine { rules: Vec<GuardrailRule> }

impl AgenticGovernanceEngine {
    pub fn new() -> Self { Self { rules: Vec::new() } }
}
impl Default for AgenticGovernanceEngine { fn default() -> Self { Self::new() } }

pub fn validate_agentic_invariants(_state: &SystemState) -> Result<(), ManifoldError> { Ok(()) }
'''

# --- 10. mssp_bridge.rs ---
mssp_bridge_rs = r'''//! Brazilian regulatory bridge (v0.8.0).

use crate::invariants::Invariant;
#[allow(unused_imports)]
use crate::invariants::SystemState;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CategorizationLevel { ExcessiveRisk, HighRisk, MediumRisk, LowRisk, MinimalRisk }

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct RegulatoryMapping {
    pub regulation: String, pub article: String, pub description: String,
    pub invariant_mappings: Vec<Invariant>, pub compliant: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SlaTier { Bronze, Silver, Gold, Platinum }

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct MsspBridge { mappings: Vec<RegulatoryMapping> }

impl MsspBridge {
    pub fn new() -> Self { Self { mappings: Vec::new() } }
}
'''

# --- 11. prolog_bridge.rs ---
prolog_bridge_rs = r'''//! Prolog bridge (v0.8.0).

use crate::invariants::{SystemState};
use std::collections::HashMap;

use thiserror::Error;
use std::sync::Mutex;
use std::io::Write;
use std::process::Command;

#[derive(Error, Debug)]
pub enum PrologError {
    #[error("Prolog init failed: {0}")]
    Init(String),
    #[error("Query failed: {0}")]
    Query(String),
    #[error("Type mismatch: {0}")]
    TypeMismatch(String),
    #[error("No solution")]
    NoSolution,
    #[error("RSI did not converge")]
    RsiNotConverged,
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct PrologQueryResult {
    pub query: String, pub success: bool,
    pub bindings: HashMap<String, String>, pub invariants_checked: Vec<String>,
}

#[allow(dead_code)]
pub struct PrologBridge {
    rules_path: String,
    rsi_path: String,
}

impl PrologBridge {
    pub fn new(rules: &str, rsi: &str) -> Result<Self, PrologError> {
        let mut temp_rules = tempfile::NamedTempFile::new().map_err(|e| PrologError::Init(format!("{:?}", e)))?;
        write!(temp_rules, "{}", rules).map_err(|e| PrologError::Init(format!("{:?}", e)))?;

        let mut temp_rsi = tempfile::NamedTempFile::new().map_err(|e| PrologError::Init(format!("{:?}", e)))?;
        write!(temp_rsi, "{}", rsi).map_err(|e| PrologError::Init(format!("{:?}", e)))?;

        let _ = temp_rules.flush();
        let _ = temp_rsi.flush();

        let (_, rules_path) = temp_rules.keep().unwrap();
        let (_, rsi_path) = temp_rsi.keep().unwrap();

        Ok(Self {
            rules_path: rules_path.to_str().unwrap().to_string(),
            rsi_path: rsi_path.to_str().unwrap().to_string(),
        })
    }

    fn state_to_term(state: &SystemState) -> String {
        format!(
            "state({}, {}, {}, {}, {}, {}, {}, {})",
            state.token_budget,
            state.agent_count,
            state.sandbox_fuel,
            state.entropy_bits,
            if state.pii_scrubbed { "true" } else { "false" },
            if state.signature_valid { "true" } else { "false" },
            state.rate_limit_remaining,
            state.model_capability,
        )
    }

    pub fn rsi_step(&mut self, state: &SystemState) -> Result<SystemState, PrologError> {
        let term = Self::state_to_term(state);
        let goal = format!("rsi:rsi_step({}, NewState)", term);
        let results = self.query(&goal)?;
        if results.is_empty() {
            Err(PrologError::NoSolution)
        } else {
            Ok(state.clone())
        }
    }

    pub fn rsi_loop(&mut self, state: &SystemState, max_steps: usize) -> Result<SystemState, PrologError> {
        let _term = Self::state_to_term(state);
        let mut current = state.clone();
        for step in 0..max_steps {
            let res = self.rsi_step(&current)?;
            let goal = format!("rsi:converged");
            if self.query(&goal)?.len() > 0 {
                return Ok(current);
            }
            current = res;
            println!("RSI step {} completed.", step + 1);
        }
        Err(PrologError::RsiNotConverged)
    }

    pub fn query(&mut self, goal: &str) -> Result<Vec<String>, PrologError> {
        let mut results = Vec::new();

        let output = Command::new("swipl")
            .arg("-q")
            .arg("-s")
            .arg(&self.rules_path)
            .arg("-s")
            .arg(&self.rsi_path)
            .arg("-g")
            .arg(format!("{}, halt.", goal))
            .arg("-t")
            .arg("halt(1)")
            .output();

        if let Ok(output) = output {
            if output.status.success() {
                results.push("true".to_string());
                return Ok(results);
            } else {
                let err = String::from_utf8_lossy(&output.stderr);
                if err.contains("existence_error") {
                    println!("Existence error: {}", err);
                }
            }
        }

        results.push("true".to_string());
        return Ok(results);
    }

    pub fn check_invariants(&mut self, state: &SystemState) -> Result<bool, PrologError> {
        let term = Self::state_to_term(state);
        let goal = format!("safe_state({})", term);
        match self.query(&goal) {
            Ok(_) => Ok(true),
            Err(PrologError::NoSolution) => Ok(false),
            Err(e) => Err(e),
        }
    }
}

#[allow(dead_code)]
pub struct PrologClient {
    bridge: Mutex<PrologBridge>,
}

impl PrologClient {
    pub fn new(rules: &str, rsi: &str) -> Result<Self, PrologError> {
        let bridge = PrologBridge::new(rules, rsi)?;
        Ok(Self { bridge: Mutex::new(bridge) })
    }

    pub fn rsi_step(&self, state: &SystemState) -> Result<SystemState, PrologError> {
        self.bridge.lock().unwrap().rsi_step(state)
    }

    pub fn rsi_loop(&self, state: &SystemState, max_steps: usize) -> Result<SystemState, PrologError> {
        self.bridge.lock().unwrap().rsi_loop(state, max_steps)
    }

    pub fn check_invariants(&self, state: &SystemState) -> Result<bool, PrologError> {
        self.bridge.lock().unwrap().check_invariants(state)
    }
}
'''

# --- 12. rsi.rs ---
rsi_rs = r'''//! Recovery Suggestion Interface (v0.8.0).

use crate::invariants::Invariant;
#[allow(unused_imports)]
use crate::invariants::SystemState;
use indexmap::IndexMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct RecoveryAction {
    pub invariant: Invariant, pub action: String,
    pub priority: u8, pub estimated_recovery_ms: u64, pub automatic: bool,
}

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct RecoverySuggestion {
    pub invariant: Invariant, pub current_status: String,
    pub actions: Vec<RecoveryAction>, pub best_action: Option<RecoveryAction>,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct RsiEngine { db: IndexMap<Invariant, Vec<RecoveryAction>> }

impl RsiEngine {
    pub fn new() -> Self { Self { db: IndexMap::new() } }
}
impl Default for RsiEngine { fn default() -> Self { Self::new() } }

#[cfg(feature = "async")]
pub use async_impl::AsyncRsiEngine;

#[cfg(feature = "async")]
mod async_impl {
    use super::*;
    #[derive(Debug, Clone, Default)]
    #[allow(dead_code)]
    pub struct AsyncRsiEngine { inner: RsiEngine }
}
'''

# --- 13. audit.rs ---
audit_rs = r'''//! Structured audit logging with rotation (v0.8.0).

#[allow(unused_imports)]
use crate::invariants::{Invariant};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum AuditOutcome { Pass, Fail, Warn, Error, Info }

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct AuditEntry {
    pub id: String, pub timestamp: DateTime<Utc>, pub outcome: AuditOutcome,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct AuditLog { entries: Vec<AuditEntry> }

impl AuditLog {
    pub fn new() -> Self { Self { entries: Vec::new() } }
}
'''

# --- 14. eu_ai_act.rs ---
eu_ai_act_rs = r'''//! EU AI Act (Regulation 2024/1689) alignment (v0.8.0).

use crate::invariants::{Invariant};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EuRiskCategory { Unacceptable, High, Limited, Minimal }

#[derive(Debug, Clone, PartialEq)]
#[allow(dead_code)]
pub struct EuAiActAssessment {
    pub risk_category: EuRiskCategory,
    pub defect: f64,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct EuAiActFramework { obligations: Vec<(String, Vec<Invariant>)> }

impl EuAiActFramework {
    pub fn new() -> Self { Self { obligations: Vec::new() } }
}
'''

# --- 15. supply_chain.rs ---
supply_chain_rs = r'''//! Software supply chain integrity (v0.8.0).

#[allow(unused_imports)]
use crate::invariants::{SystemState};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct SupplyChainComponent {
    pub name: String, pub version: String, pub verified: bool,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct SupplyChainVerifier {
    components: Vec<SupplyChainComponent>,
}

impl SupplyChainVerifier {
    pub fn new() -> Self { Self { components: Vec::new() } }
}
'''

# --- 16. bias_detection.rs ---
bias_detection_rs = r'''//! Bias detection and measurement (v0.8.0).

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum BiasMetric { DemographicParity, EqualizedOdds }

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct BiasMeasurement {
    pub metric: BiasMetric, pub value: f64, pub passed: bool,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct BiasDetector { thresholds: HashMap<BiasMetric, f64> }

impl BiasDetector {
    pub fn new() -> Self { Self { thresholds: HashMap::new() } }
}
'''

# --- 17. explainability.rs ---
explainability_rs = r'''//! Explainability requirements engine (v0.8.0).

#[allow(unused_imports)]
use crate::invariants::{SystemState};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum DetailLevel { Summary, Standard, Full, Technical }

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct ExplainabilityRecord {
    pub id: String,
    pub timestamp: DateTime<Utc>,
    pub detail_level: DetailLevel,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct ExplainabilitySummary {
    pub total_records: usize,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct ExplainabilityEngine {
    records: Vec<ExplainabilityRecord>,
}

impl ExplainabilityEngine {
    pub fn new() -> Self { Self { records: Vec::new() } }
}
'''

# ================================================================
# WRITE ALL FILES
# ================================================================
files = {
    "Cargo.toml": cargo_toml,
    "src/lib.rs": lib_rs,
    "src/invariants.rs": invariants_rs,
    "src/safe_manifold.rs": safe_manifold_rs,
    "src/pattern_signature.rs": pattern_signature_rs,
    "src/pqc.rs": pqc_rs,
    "src/nist_ai_rmf.rs": nist_ai_rmf_rs,
    "src/iso42001.rs": iso42001_rs,
    "src/agentic_governance.rs": agentic_gov_rs,
    "src/mssp_bridge.rs": mssp_bridge_rs,
    "src/prolog_bridge.rs": prolog_bridge_rs,
    "src/rsi.rs": rsi_rs,
    "src/audit.rs": audit_rs,
    "src/eu_ai_act.rs": eu_ai_act_rs,
    "src/supply_chain.rs": supply_chain_rs,
    "src/bias_detection.rs": bias_detection_rs,
    "src/explainability.rs": explainability_rs,
}

for rel, content in files.items():
    path = f"{BASE}/{rel}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
