//! Post-Quantum Cryptography stubs (v0.8.0).

use crate::invariants::{ManifoldError, SystemState};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub enum PqcAlgorithm {
    #[default]
    MlKem768,
    MlKem1024,
    MlDsa65,
    MlDsa87,
}

impl PqcAlgorithm {
    pub fn security_level(&self) -> u8 {
        match self {
            Self::MlKem768 | Self::MlDsa65 => 3,
            Self::MlKem1024 | Self::MlDsa87 => 5,
        }
    }
    pub fn nist_standard(&self) -> &'static str {
        match self {
            Self::MlKem768 | Self::MlKem1024 => "FIPS 203",
            Self::MlDsa65 | Self::MlDsa87 => "FIPS 204",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
#[allow(dead_code)]
pub struct EncapsulationResult {
    pub ciphertext: Vec<u8>,
    pub shared_secret: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
#[allow(dead_code)]
pub struct SignatureResult {
    pub signature: Vec<u8>,
    pub public_key_hash: String,
}

pub trait PqcProvider: Send + Sync {
    fn algorithm(&self) -> PqcAlgorithm;
    fn encapsulate(&self, public_key: &[u8]) -> Result<EncapsulationResult, ManifoldError>;
    fn decapsulate(&self, secret_key: &[u8], ciphertext: &[u8]) -> Result<Vec<u8>, ManifoldError>;
    fn sign(&self, secret_key: &[u8], message: &[u8]) -> Result<SignatureResult, ManifoldError>;
    fn verify(
        &self,
        public_key: &[u8],
        message: &[u8],
        signature: &[u8],
    ) -> Result<bool, ManifoldError>;
}

fn simple_hash(data: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for &b in data {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

#[derive(Debug, Clone, Default)]
#[allow(dead_code)]
pub struct StubPqcProvider {
    algorithm: PqcAlgorithm,
}

impl StubPqcProvider {
    pub fn new(algorithm: PqcAlgorithm) -> Self {
        Self { algorithm }
    }
}

impl PqcProvider for StubPqcProvider {
    fn algorithm(&self) -> PqcAlgorithm {
        self.algorithm
    }
    fn encapsulate(&self, _: &[u8]) -> Result<EncapsulationResult, ManifoldError> {
        Ok(EncapsulationResult {
            ciphertext: vec![0u8; 1088],
            shared_secret: vec![0u8; 32],
        })
    }
    fn decapsulate(&self, _: &[u8], _: &[u8]) -> Result<Vec<u8>, ManifoldError> {
        Ok(vec![0u8; 32])
    }
    fn sign(&self, _: &[u8], msg: &[u8]) -> Result<SignatureResult, ManifoldError> {
        Ok(SignatureResult {
            signature: vec![0u8; 3309],
            public_key_hash: format!("{:016x}", simple_hash(msg)),
        })
    }
    fn verify(&self, _: &[u8], _: &[u8], _: &[u8]) -> Result<bool, ManifoldError> {
        Ok(true)
    }
}

pub fn validate_pqc_invariants(state: &SystemState) -> Result<(), ManifoldError> {
    if state.config.require_pqc_encapsulation && !state.pqc_key_encapsulation {
        return Err(ManifoldError::PqcError(
            "I-09: PQC key encapsulation not enforced".into(),
        ));
    }
    if state.config.require_pqc_signatures && !state.pqc_signature_valid {
        return Err(ManifoldError::PqcError(
            "I-10: PQC signature not valid".into(),
        ));
    }
    Ok(())
}

pub fn pqc_readiness_score(state: &SystemState) -> f64 {
    let mut s = 0.0f64;
    let mut t = 0.0f64;
    if state.config.require_pqc_encapsulation {
        t += 1.0;
        if state.pqc_key_encapsulation {
            s += 1.0;
        }
    }
    if state.config.require_pqc_signatures {
        t += 1.0;
        if state.pqc_signature_valid {
            s += 1.0;
        }
    }
    if t == 0.0 {
        1.0
    } else {
        s / t
    }
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
            estimated_effort_days: if state.pqc_key_encapsulation && state.pqc_signature_valid {
                0
            } else {
                180
            },
        }
    }
}
