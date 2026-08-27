//! System invariants and state definitions (v0.8.0 — 16 invariants, 16D).

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
            Self::Resource,
            Self::Capability,
            Self::Constitutional,
            Self::Pqc,
            Self::Agentic,
            Self::SupplyChain,
            Self::Bias,
            Self::EuAiAct,
            Self::Explainability,
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

fn default_max_bias() -> f64 {
    0.1
}

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
            max_tokens: 5_000,
            max_agents: 5,
            max_sandbox_fuel: 500,
            min_entropy: 512,
            max_rate_limit: 500,
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
            max_tokens: 100_000,
            max_agents: 50,
            max_sandbox_fuel: 10_000,
            min_entropy: 128,
            max_rate_limit: 10_000,
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
            return Err(ManifoldError::ConfigError(
                "max_tokens must be positive".into(),
            ));
        }
        if self.max_agents == 0 {
            return Err(ManifoldError::ConfigError(
                "max_agents must be positive".into(),
            ));
        }
        if self.max_sandbox_fuel <= 0 {
            return Err(ManifoldError::ConfigError(
                "max_sandbox_fuel must be positive".into(),
            ));
        }
        if self.max_rate_limit <= 0 {
            return Err(ManifoldError::ConfigError(
                "max_rate_limit must be positive".into(),
            ));
        }
        if self.max_bias_threshold <= 0.0 {
            return Err(ManifoldError::ConfigError(
                "max_bias_threshold must be positive".into(),
            ));
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
        Invariant::all()
            .iter()
            .map(|&inv| self.check_invariant(inv))
            .collect()
    }

    pub fn check_invariant(&self, inv: Invariant) -> InvariantCheck {
        let (passed, message) = match inv {
            Invariant::I01 => (
                self.token_budget >= 0 && self.token_budget <= self.config.max_tokens,
                format!(
                    "token_budget={} in [0, {}]",
                    self.token_budget, self.config.max_tokens
                ),
            ),
            Invariant::I02 => (
                self.agent_count <= self.config.max_agents,
                format!(
                    "agent_count={} <= {}",
                    self.agent_count, self.config.max_agents
                ),
            ),
            Invariant::I03 => (
                self.sandbox_fuel > 0 && self.sandbox_fuel <= self.config.max_sandbox_fuel,
                format!(
                    "sandbox_fuel={} in (0, {}]",
                    self.sandbox_fuel, self.config.max_sandbox_fuel
                ),
            ),
            Invariant::I04 => (
                self.entropy_bits >= self.config.min_entropy,
                format!(
                    "entropy_bits={} >= {}",
                    self.entropy_bits, self.config.min_entropy
                ),
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
                self.rate_limit_remaining > 0
                    && self.rate_limit_remaining <= self.config.max_rate_limit,
                format!(
                    "rate_limit_remaining={} in (0, {}]",
                    self.rate_limit_remaining, self.config.max_rate_limit
                ),
            ),
            Invariant::I08 => (
                self.model_capability >= self.config.min_model_capability,
                format!(
                    "model_capability={} >= {}",
                    self.model_capability, self.config.min_model_capability
                ),
            ),
            Invariant::I09 => (
                self.pqc_key_encapsulation || !self.config.require_pqc_encapsulation,
                format!(
                    "pqc_key_encapsulation={} (req={})",
                    self.pqc_key_encapsulation, self.config.require_pqc_encapsulation
                ),
            ),
            Invariant::I10 => (
                self.pqc_signature_valid || !self.config.require_pqc_signatures,
                format!(
                    "pqc_signature_valid={} (req={})",
                    self.pqc_signature_valid, self.config.require_pqc_signatures
                ),
            ),
            Invariant::I11 => (
                self.agent_action_boundary_defined || !self.config.enable_agentic_guardrails,
                format!(
                    "agent_action_boundary_defined={} (en={})",
                    self.agent_action_boundary_defined, self.config.enable_agentic_guardrails
                ),
            ),
            Invariant::I12 => (
                !self.human_oversight_triggered || !self.config.enable_agentic_guardrails,
                format!(
                    "human_oversight_triggered={} (en={})",
                    self.human_oversight_triggered, self.config.enable_agentic_guardrails
                ),
            ),
            Invariant::I13 => (
                self.supply_chain_integrity_verified || !self.config.require_supply_chain_integrity,
                format!(
                    "supply_chain_integrity_verified={} (req={})",
                    self.supply_chain_integrity_verified,
                    self.config.require_supply_chain_integrity
                ),
            ),
            Invariant::I14 => (
                self.bias_score <= self.config.max_bias_threshold,
                format!(
                    "bias_score={} <= {}",
                    self.bias_score, self.config.max_bias_threshold
                ),
            ),
            Invariant::I15 => (
                self.eu_ai_act_compliant || !self.config.require_eu_ai_act_compliance,
                format!(
                    "eu_ai_act_compliant={} (req={})",
                    self.eu_ai_act_compliant, self.config.require_eu_ai_act_compliance
                ),
            ),
            Invariant::I16 => (
                self.explainability_requirement_met || !self.config.require_explainability,
                format!(
                    "explainability_requirement_met={} (req={})",
                    self.explainability_requirement_met, self.config.require_explainability
                ),
            ),
        };
        InvariantCheck {
            invariant: inv,
            passed,
            message,
        }
    }

    pub fn violations(&self) -> Vec<Invariant> {
        self.check_all_detailed()
            .into_iter()
            .filter(|c| !c.passed)
            .map(|c| c.invariant)
            .collect()
    }
    pub fn constitutional_violations(&self) -> Vec<Invariant> {
        self.violations()
            .into_iter()
            .filter(|v| v.category() == InvariantCategory::Constitutional)
            .collect()
    }
    pub fn pqc_violations(&self) -> Vec<Invariant> {
        self.violations()
            .into_iter()
            .filter(|v| v.category() == InvariantCategory::Pqc)
            .collect()
    }
    pub fn agentic_violations(&self) -> Vec<Invariant> {
        self.violations()
            .into_iter()
            .filter(|v| v.category() == InvariantCategory::Agentic)
            .collect()
    }
    pub fn has_constitutional_violations(&self) -> bool {
        !self.constitutional_violations().is_empty()
    }

    pub fn summary(&self) -> String {
        format!(
            "SystemState[tokens={},agents={},fuel={},entropy={},pii={},sig={},rate={},cap={},\
             pqk={},pqs={},aab={},hot={},sci={},bias={},euai={},expl={}]",
            self.token_budget,
            self.agent_count,
            self.sandbox_fuel,
            self.entropy_bits,
            self.pii_scrubbed,
            self.signature_valid,
            self.rate_limit_remaining,
            self.model_capability,
            self.pqc_key_encapsulation,
            self.pqc_signature_valid,
            self.agent_action_boundary_defined,
            self.human_oversight_triggered,
            self.supply_chain_integrity_verified,
            self.bias_score,
            self.eu_ai_act_compliant,
            self.explainability_requirement_met,
        )
    }

    /// Convert state to 16D vector for pattern classification.
    pub fn to_vector(&self) -> [f64; 16] {
        let cap = if self.model_capability == 0 {
            1.0
        } else {
            self.model_capability as f64
        };
        // Normalize bias_score: 0 bias → 1.0, max threshold → 0.0
        let bias_norm = if self.config.max_bias_threshold > 0.0 {
            (1.0 - (self.bias_score / self.config.max_bias_threshold).min(1.0)).max(0.0)
        } else {
            1.0
        };
        [
            self.token_budget as f64,                           // 0
            self.agent_count as f64,                            // 1
            self.sandbox_fuel as f64,                           // 2
            self.entropy_bits as f64,                           // 3
            if self.pii_scrubbed { 1.0 } else { 0.0 },          // 4
            if self.signature_valid { 1.0 } else { 0.0 },       // 5
            self.rate_limit_remaining as f64,                   // 6
            cap.log2(),                                         // 7
            if self.pqc_key_encapsulation { 1.0 } else { 0.0 }, // 8
            if self.pqc_signature_valid { 1.0 } else { 0.0 },   // 9
            if self.agent_action_boundary_defined {
                1.0
            } else {
                0.0
            }, // 10
            if self.human_oversight_triggered {
                1.0
            } else {
                0.0
            }, // 11
            if self.supply_chain_integrity_verified {
                1.0
            } else {
                0.0
            }, // 12
            bias_norm,                                          // 13
            if self.eu_ai_act_compliant { 1.0 } else { 0.0 },   // 14
            if self.explainability_requirement_met {
                1.0
            } else {
                0.0
            }, // 15
        ]
    }
}

/// Invariant identifiers (v0.8.0 — 16 invariants).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Invariant {
    I01,
    I02,
    I03,
    I04,
    I05,
    I06,
    I07,
    I08,
    I09,
    I10,
    I11,
    I12,
    I13,
    I14,
    I15,
    I16,
}

impl Invariant {
    pub fn all() -> [Self; 16] {
        [
            Self::I01,
            Self::I02,
            Self::I03,
            Self::I04,
            Self::I05,
            Self::I06,
            Self::I07,
            Self::I08,
            Self::I09,
            Self::I10,
            Self::I11,
            Self::I12,
            Self::I13,
            Self::I14,
            Self::I15,
            Self::I16,
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
    pub fn is_constitutional(&self) -> bool {
        self.category() == InvariantCategory::Constitutional
    }
    pub fn is_resource(&self) -> bool {
        self.category() == InvariantCategory::Resource
    }
    pub fn is_capability(&self) -> bool {
        self.category() == InvariantCategory::Capability
    }
    pub fn is_pqc(&self) -> bool {
        self.category() == InvariantCategory::Pqc
    }
    pub fn is_agentic(&self) -> bool {
        self.category() == InvariantCategory::Agentic
    }
    pub fn prolog_name(&self) -> &'static str {
        match self {
            Self::I01 => "i01",
            Self::I02 => "i02",
            Self::I03 => "i03",
            Self::I04 => "i04",
            Self::I05 => "i05",
            Self::I06 => "i06",
            Self::I07 => "i07",
            Self::I08 => "i08",
            Self::I09 => "i09",
            Self::I10 => "i10",
            Self::I11 => "i11",
            Self::I12 => "i12",
            Self::I13 => "i13",
            Self::I14 => "i14",
            Self::I15 => "i15",
            Self::I16 => "i16",
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
