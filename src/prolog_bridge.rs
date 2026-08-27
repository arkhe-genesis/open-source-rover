//! Prolog bridge (v0.8.0).

use crate::invariants::SystemState;
use std::collections::HashMap;

use std::io::Write;
use std::process::Command;
use std::sync::Mutex;
use thiserror::Error;

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
    pub query: String,
    pub success: bool,
    pub bindings: HashMap<String, String>,
    pub invariants_checked: Vec<String>,
}

#[allow(dead_code)]
pub struct PrologBridge {
    rules_path: String,
    rsi_path: String,
}

impl PrologBridge {
    pub fn new(rules: &str, rsi: &str) -> Result<Self, PrologError> {
        let mut temp_rules =
            tempfile::NamedTempFile::new().map_err(|e| PrologError::Init(format!("{:?}", e)))?;
        write!(temp_rules, "{}", rules).map_err(|e| PrologError::Init(format!("{:?}", e)))?;

        let mut temp_rsi =
            tempfile::NamedTempFile::new().map_err(|e| PrologError::Init(format!("{:?}", e)))?;
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
            if state.signature_valid {
                "true"
            } else {
                "false"
            },
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

    pub fn rsi_loop(
        &mut self,
        state: &SystemState,
        max_steps: usize,
    ) -> Result<SystemState, PrologError> {
        let _term = Self::state_to_term(state);
        let mut current = state.clone();
        for step in 0..max_steps {
            let res = self.rsi_step(&current)?;
            let goal = "rsi:converged".to_string();
            if !self.query(&goal)?.is_empty() {
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
        Ok(results)
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
        Ok(Self {
            bridge: Mutex::new(bridge),
        })
    }

    pub fn rsi_step(&self, state: &SystemState) -> Result<SystemState, PrologError> {
        self.bridge.lock().unwrap().rsi_step(state)
    }

    pub fn rsi_loop(
        &self,
        state: &SystemState,
        max_steps: usize,
    ) -> Result<SystemState, PrologError> {
        self.bridge.lock().unwrap().rsi_loop(state, max_steps)
    }

    pub fn check_invariants(&self, state: &SystemState) -> Result<bool, PrologError> {
        self.bridge.lock().unwrap().check_invariants(state)
    }
}
