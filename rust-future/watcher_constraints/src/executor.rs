use std::collections::HashMap;
use thiserror::Error;

/// Error types for constraint validation
#[derive(Error, Debug)]
pub enum ConstraintError {
    #[error("Validation error: {0}")]
    ValidationError(String),
    
    #[error("Physics constraint violated: {0}")]
    PhysicsViolation(String),
    
    #[error("Financial constraint violated: {0}")]
    FinancialViolation(String),
    
    #[error("Metric constraint violated: {0}")]
    MetricViolation(String),
}

/// Request containing validation data
#[derive(Clone, Debug)]
pub struct ValidationRequest {
    pub physics_energy_in: Option<f32>,
    pub physics_energy_out: Option<f32>,
    pub financial_proposed_loss: Option<f32>,
    pub metrics: HashMap<String, f32>,
}

/// Hard constraint limits
pub struct ConstraintLimits {
    pub leverage_ratio: f32,
    pub var_loss_threshold: f32,
    pub temperature_min: f32,
    pub pressure_min: f32,
}

impl Default for ConstraintLimits {
    fn default() -> Self {
        Self {
            leverage_ratio: 10.0,
            var_loss_threshold: -10_000.0,
            temperature_min: 0.0,
            pressure_min: 0.0,
        }
    }
}

/// Check logic constraints and return list of violations
pub fn check_logic(request: &ValidationRequest) -> Result<Vec<String>, ConstraintError> {
    let mut violations = Vec::new();
    let limits = ConstraintLimits::default();

    // Physics constraints
    if let (Some(energy_in), Some(energy_out)) = (request.physics_energy_in, request.physics_energy_out) {
        if energy_out > energy_in {
            violations.push("Conservation of Energy violated".to_string());
        }

        if energy_in < 0.0 {
            violations.push("Energy input cannot be negative".to_string());
        }
    }

    // Financial constraints
    if let Some(proposed_loss) = request.financial_proposed_loss {
        if proposed_loss < limits.var_loss_threshold {
            violations.push("VaR loss threshold exceeded".to_string());
        }
    }

    // Metric constraints (generic key-value pairs)
    for (metric_name, value) in &request.metrics {
        let metric_lower = metric_name.to_lowercase();

        if metric_lower.contains("temperature") || metric_lower.contains("temp") || metric_lower.contains("kelvin") {
            if *value < limits.temperature_min {
                violations.push("Temperature below absolute zero".to_string());
            }
        }

        if metric_lower.contains("pressure") || metric_lower.contains("pascal") || metric_lower.contains("pa") {
            if *value < limits.pressure_min {
                violations.push("Negative pressure is invalid for this model".to_string());
            }
        }

        if metric_lower.contains("leverage") || metric_lower.contains("debt_to_equity") {
            if *value > limits.leverage_ratio {
                violations.push("Leverage ratio exceeds hard limit".to_string());
            }
        }

        if metric_lower.contains("var") || metric_lower.contains("value_at_risk") {
            if *value < limits.var_loss_threshold {
                violations.push("VaR loss threshold exceeded".to_string());
            }
        }
    }

    Ok(violations)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_conservation_of_energy() {
        let request = ValidationRequest {
            physics_energy_in: Some(100.0),
            physics_energy_out: Some(150.0),
            financial_proposed_loss: None,
            metrics: HashMap::new(),
        };

        let violations = check_logic(&request).unwrap();
        assert!(violations.iter().any(|v| v.contains("Conservation of Energy")));
    }

    #[test]
    fn test_leverage_limit() {
        let mut metrics = HashMap::new();
        metrics.insert("leverage_ratio".to_string(), 15.0);

        let request = ValidationRequest {
            physics_energy_in: None,
            physics_energy_out: None,
            financial_proposed_loss: None,
            metrics,
        };

        let violations = check_logic(&request).unwrap();
        assert!(violations.iter().any(|v| v.contains("hard limit")));
    }

    #[test]
    fn test_var_threshold() {
        let request = ValidationRequest {
            physics_energy_in: None,
            physics_energy_out: None,
            financial_proposed_loss: Some(-15_000.0),
            metrics: HashMap::new(),
        };

        let violations = check_logic(&request).unwrap();
        assert!(violations.iter().any(|v| v.contains("VaR")));
    }

    #[test]
    fn test_no_violations() {
        let request = ValidationRequest {
            physics_energy_in: Some(100.0),
            physics_energy_out: Some(80.0),
            financial_proposed_loss: Some(-5000.0),
            metrics: HashMap::new(),
        };

        let violations = check_logic(&request).unwrap();
        assert!(violations.is_empty());
    }
}
