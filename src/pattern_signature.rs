//! Pattern signature classification via 16D topological centroids (v0.8.0).

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
        let mut c = Self {
            patterns: Vec::new(),
        };
        c.init_defaults();
        c
    }

    fn init_defaults(&mut self) {
        self.patterns.push(PatternSignature {
            name: "nominal_safe".into(),
            centroid: [
                5000.0, 1.0, 500.0, 256.0, 1.0, 1.0, 500.0, 32.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0,
                1.0, 1.0,
            ],
            radius: 0.4,
            category: PatternCategory::Safe,
        });
        self.patterns.push(PatternSignature {
            name: "resource_degraded".into(),
            centroid: [
                500.0, 1.0, 50.0, 256.0, 1.0, 1.0, 50.0, 32.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0,
                1.0,
            ],
            radius: 0.35,
            category: PatternCategory::Degraded,
        });
        self.patterns.push(PatternSignature {
            name: "constitutional_breach".into(),
            centroid: [
                5000.0, 1.0, 500.0, 256.0, 0.0, 0.0, 500.0, 32.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0,
                1.0, 1.0,
            ],
            radius: 0.3,
            category: PatternCategory::Critical,
        });
        self.patterns.push(PatternSignature {
            name: "compliance_failure".into(),
            centroid: [
                5000.0, 1.0, 500.0, 256.0, 1.0, 1.0, 500.0, 32.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5,
                0.0, 0.0,
            ],
            radius: 0.35,
            category: PatternCategory::Critical,
        });
    }

    fn distance(a: &[f64; 16], b: &[f64; 16]) -> f64 {
        a.iter()
            .zip(b.iter())
            .map(|(x, y)| (x - y).powi(2))
            .sum::<f64>()
            .sqrt()
    }

    pub fn classify(&self, state: &SystemState) -> PatternMatch {
        let v = state.to_vector();
        let best = self
            .patterns
            .iter()
            .map(|p| (p, Self::distance(&v, &p.centroid)))
            .min_by(|(_, d1), (_, d2)| d1.partial_cmp(d2).unwrap_or(std::cmp::Ordering::Equal));

        match best {
            Some((pattern, dist)) => {
                let within = dist <= pattern.radius;
                let conf = if pattern.radius > 0.0 {
                    (1.0 - dist / pattern.radius).max(0.0).min(1.0)
                } else {
                    0.0
                };
                PatternMatch {
                    pattern_name: pattern.name.clone(),
                    category: if within {
                        pattern.category
                    } else {
                        PatternCategory::Unknown
                    },
                    distance: dist,
                    within_radius: within,
                    confidence: conf,
                }
            }
            None => PatternMatch {
                pattern_name: "none".into(),
                category: PatternCategory::Unknown,
                distance: f64::INFINITY,
                within_radius: false,
                confidence: 0.0,
            },
        }
    }

    pub fn add_pattern(&mut self, p: PatternSignature) {
        self.patterns.push(p);
    }
    pub fn patterns(&self) -> &[PatternSignature] {
        &self.patterns
    }
}

impl Default for PatternClassifier {
    fn default() -> Self {
        Self::new()
    }
}
