#![deny(unsafe_code)]
#![cfg_attr(all(test, feature = "full"), deny(warnings))]

pub mod invariants;
pub mod pattern_signature;
pub mod safe_manifold;

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
    Invariant, InvariantCategory, InvariantCheck, ManifoldError, SystemConfig, SystemState,
};
pub use pattern_signature::{PatternCategory, PatternClassifier, PatternMatch, PatternSignature};
pub use safe_manifold::{
    BatchAssessment, DefectAssessment, DefectConfig, DefectLevel, DimensionWeights,
    EscapeThresholds, ManifoldPoint, ManifoldProfile, SafeManifold, SafeState,
};

#[cfg(feature = "pqc")]
pub use pqc::{
    pqc_readiness_score, validate_pqc_invariants, EncapsulationResult, PqcAlgorithm,
    PqcMigrationPlan, PqcProvider, SignatureResult, StubPqcProvider,
};

#[cfg(feature = "nist")]
pub use nist_ai_rmf::{
    AccountabilityRegistry, CsfFunction, NistFunction, RiskTier, RmfMapping, RmfRegistry,
};

#[cfg(feature = "iso42001")]
pub use iso42001::{
    AimsAssessment, Iso42001Framework, IsoClause, IsoControl, UnifiedGovernanceView,
};

#[cfg(feature = "agentic")]
pub use agentic_governance::{
    validate_agentic_invariants, AgentAction, AgenticGovernanceEngine, GuardrailEvaluation,
    GuardrailRule, GuardrailTier, ViolationSeverity,
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
