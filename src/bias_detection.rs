//! Bias detection and measurement (v0.8.0).

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum BiasMetric {
    DemographicParity,
    EqualizedOdds,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct BiasMeasurement {
    pub metric: BiasMetric,
    pub value: f64,
    pub passed: bool,
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct BiasDetector {
    thresholds: HashMap<BiasMetric, f64>,
}

impl Default for BiasDetector {
    fn default() -> Self {
        Self::new()
    }
}

impl BiasDetector {
    pub fn new() -> Self {
        Self {
            thresholds: HashMap::new(),
        }
    }
}
