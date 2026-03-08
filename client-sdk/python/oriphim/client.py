"""
Oriphim Python Client SDK

Simple, production-ready SDK for integrating Oriphim validation into your applications.

Installation:
    pip install oriphim-client

Usage:
    from oriphim import OriphimClient
    
    client = OriphimClient(
        base_url="https://api.oriphim.com",
        api_key="your-api-key"
    )
    
    result = client.validate(
        samples=["AI output 1", "AI output 2", "AI output 3"],
        financial={"proposed_loss": -5000}
    )
    
    if result.indicator == "GREEN":
        print("Safe to execute")
"""

from typing import List, Optional, Dict, Any
import requests
from dataclasses import dataclass
from enum import Enum
import time


class Indicator(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class Action(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"
    CAUTION = "CAUTION"


@dataclass
class ValidationResult:
    """Result of a validation request"""
    request_id: Optional[str]
    status_code: int
    divergence_score: float
    violations: List[str]
    indicator: Indicator
    action_label: Action
    action_reason: str
    confidence_score: float
    risk_level: str
    recommendation: str
    context_reset: bool


@dataclass
class AsyncValidationResult:
    """Result of async validation via /v3/intent"""
    request_id: str
    status_code: int
    action: Action
    divergence_score: float
    violations: List[str]
    recommendation: str
    context_reset: bool
    latency_ms: float


@dataclass
class AgentSnapshot:
    """Agent state snapshot for rewind"""
    agent_id: str
    snapshot_id: Optional[int]
    restored: bool
    system_prompt: Optional[str]
    context: Optional[Dict[str, Any]]
    variables: Optional[Dict[str, Any]]


@dataclass
class HealthStatus:
    """System health metrics"""
    uptime_requests: int
    recent_divergence_avg: float
    recent_violation_rate: float
    drift_detected: bool
    status: str
    indicator: Indicator


class OriphimError(Exception):
    """Base exception for Oriphim SDK"""
    pass


class ValidationBlockedError(OriphimError):
    """Raised when validation is blocked (424)"""
    def __init__(self, violations: List[str], result: ValidationResult):
        self.violations = violations
        self.result = result
        super().__init__(f"Validation blocked: {'; '.join(violations)}")


class OriphimClient:
    """
    Oriphim Python SDK client
    
    Args:
        base_url: Oriphim API base URL (e.g., "https://api.oriphim.com")
        api_key: Your API key
        timeout: Request timeout in seconds (default: 2.0)
        raise_on_block: If True, raises ValidationBlockedError on 424 (default: False)
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 2.0,
        raise_on_block: bool = False
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.raise_on_block = raise_on_block
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def validate(
        self,
        samples: List[str],
        physics: Optional[Dict[str, float]] = None,
        financial: Optional[Dict[str, float]] = None,
        metrics: Optional[Dict[str, float]] = None
    ) -> ValidationResult:
        """
        Synchronous validation via /v2/validate
        
        Args:
            samples: 3+ AI outputs to check for consistency
            physics: Optional physics constraints (energy_in, energy_out)
            financial: Optional financial constraints (proposed_loss)
            metrics: Optional custom metrics (leverage_ratio, temperature, etc.)
        
        Returns:
            ValidationResult with indicator (GREEN/YELLOW/RED)
        
        Raises:
            ValidationBlockedError: If raise_on_block=True and validation blocked
            OriphimError: On API errors
        """
        payload = {
            "samples": samples,
            "physics": physics,
            "financial": financial,
            "metrics": metrics
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/v2/validate",
                json=payload,
                timeout=self.timeout
            )
            
            # Handle both 200 and 424 responses
            if response.status_code in [200, 424]:
                data = response.json()
                
                result = ValidationResult(
                    request_id=data.get("request_id"),
                    status_code=response.status_code,
                    divergence_score=data["divergence_score"],
                    violations=data["violations"],
                    indicator=Indicator(data["indicator"]),
                    action_label=Action(data["action_label"]),
                    action_reason=data["action_reason"],
                    confidence_score=data["confidence"]["score"],
                    risk_level=data["confidence"]["risk_level"],
                    recommendation=data["recommendation"],
                    context_reset=data.get("context_reset", False)
                )
                
                if self.raise_on_block and response.status_code == 424:
                    raise ValidationBlockedError(result.violations, result)
                
                return result
            else:
                raise OriphimError(f"Validation failed: {response.status_code} {response.text}")
        
        except requests.exceptions.RequestException as e:
            raise OriphimError(f"Request failed: {e}")
    
    def submit_intent(
        self,
        agent_id: str,
        intent: str,
        samples: List[str],
        physics: Optional[Dict[str, float]] = None,
        financial: Optional[Dict[str, float]] = None,
        metrics: Optional[Dict[str, float]] = None,
        desired_state: Optional[str] = None,
        state_snapshot: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit async validation intent
        
        Args:
            agent_id: Unique agent identifier
            intent: Human-readable intent description
            samples: AI outputs to validate
            physics: Optional physics constraints
            financial: Optional financial constraints
            metrics: Optional custom metrics
            desired_state: Optional desired state description
            state_snapshot: Optional agent state (system_prompt, context, variables)
        
        Returns:
            request_id for polling via get_validation_status()
        """
        payload = {
            "agent_id": agent_id,
            "intent": intent,
            "samples": samples,
            "physics": physics,
            "financial": financial,
            "metrics": metrics,
            "desired_state": desired_state,
            "state_snapshot": state_snapshot
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/v3/intent",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()["request_id"]
            else:
                raise OriphimError(f"Intent submission failed: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            raise OriphimError(f"Request failed: {e}")
    
    def get_validation_status(
        self,
        request_id: str
    ) -> Optional[AsyncValidationResult]:
        """
        Check status of async validation
        
        Args:
            request_id: Request ID from submit_intent()
        
        Returns:
            AsyncValidationResult if complete, None if still pending
        """
        try:
            response = self.session.get(
                f"{self.base_url}/v3/intent/{request_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return AsyncValidationResult(
                    request_id=data["request_id"],
                    status_code=data["status_code"],
                    action=Action(data["action"]),
                    divergence_score=data["divergence_score"],
                    violations=data["violations"],
                    recommendation=data["recommendation"],
                    context_reset=data["context_reset"],
                    latency_ms=data["latency_ms"]
                )
            elif response.status_code == 202:
                # Still pending
                return None
            else:
                raise OriphimError(f"Status check failed: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            raise OriphimError(f"Request failed: {e}")
    
    def wait_for_result(
        self,
        request_id: str,
        timeout: float = 2.0,
        poll_interval: float = 0.1
    ) -> AsyncValidationResult:
        """
        Wait for async validation to complete
        
        Args:
            request_id: Request ID from submit_intent()
            timeout: Max time to wait in seconds
            poll_interval: Time between polls in seconds
        
        Returns:
            AsyncValidationResult when complete
        
        Raises:
            OriphimError: If timeout exceeded
        """
        start = time.time()
        
        while time.time() - start < timeout:
            result = self.get_validation_status(request_id)
            if result is not None:
                return result
            time.sleep(poll_interval)
        
        raise OriphimError(f"Timeout waiting for validation {request_id}")
    
    def rewind_agent(self, agent_id: str) -> AgentSnapshot:
        """
        Rewind agent to last valid state
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            AgentSnapshot with restored state (or restored=False if no snapshot)
        """
        try:
            response = self.session.post(
                f"{self.base_url}/v3/rewind/{agent_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return AgentSnapshot(
                    agent_id=data["agent_id"],
                    snapshot_id=data["snapshot_id"],
                    restored=data["restored"],
                    system_prompt=data["system_prompt"],
                    context=data["context"],
                    variables=data["variables"]
                )
            else:
                raise OriphimError(f"Rewind failed: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            raise OriphimError(f"Request failed: {e}")
    
    def get_health(self) -> HealthStatus:
        """
        Get system health status
        
        Returns:
            HealthStatus with indicator (GREEN/YELLOW/RED)
        """
        try:
            response = self.session.get(
                f"{self.base_url}/v2/health",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return HealthStatus(
                    uptime_requests=data["uptime_requests"],
                    recent_divergence_avg=data["recent_divergence_avg"],
                    recent_violation_rate=data["recent_violation_rate"],
                    drift_detected=data.get("drift_detected", False),
                    status=data["status"],
                    indicator=Indicator(data["indicator"])
                )
            else:
                raise OriphimError(f"Health check failed: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            raise OriphimError(f"Request failed: {e}")
    
    def export_compliance(
        self,
        agent_id: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Export compliance audit report as PDF
        
        Args:
            agent_id: Optional agent filter (None = all agents)
            output_path: Optional path to save PDF (None = return bytes)
        
        Returns:
            PDF bytes (also saves to output_path if provided)
        """
        try:
            params = {}
            if agent_id:
                params["agent_id"] = agent_id
            
            response = self.session.get(
                f"{self.base_url}/v3/compliance/export",
                params=params,
                timeout=10.0  # Longer timeout for PDF generation
            )
            
            if response.status_code == 200:
                pdf_bytes = response.content
                
                if output_path:
                    with open(output_path, 'wb') as f:
                        f.write(pdf_bytes)
                
                return pdf_bytes
            else:
                raise OriphimError(f"Compliance export failed: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            raise OriphimError(f"Request failed: {e}")


# Convenience function for quick validation
def validate(
    samples: List[str],
    base_url: str,
    api_key: str,
    **kwargs
) -> ValidationResult:
    """
    Quick validation without creating a client
    
    Usage:
        from oriphim import validate
        
        result = validate(
            samples=["output1", "output2", "output3"],
            base_url="https://api.oriphim.com",
            api_key="your-key",
            financial={"proposed_loss": -5000}
        )
    """
    client = OriphimClient(base_url=base_url, api_key=api_key)
    return client.validate(samples=samples, **kwargs)
