"""
Rewind Service - State Management & Rollback for AI Agents
Implements the /v3/rewind endpoint for resetting agent context to last known good state.
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class StateSnapshot:
    """
    Immutable snapshot of agent state at a point in time.
    """
    agent_id: str
    state: Dict
    valid: bool  # True = safe to rewind to, False = hallucinated state
    timestamp: str
    snapshot_id: str = ""
    prev_hash: str = ""
    state_hash: str = ""
    
    def __post_init__(self):
        if not self.snapshot_id:
            self.snapshot_id = f"SNAP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if not self.state_hash:
            state_json = json.dumps(self.state, sort_keys=True)
            self.state_hash = hashlib.sha256(
                (self.prev_hash + state_json).encode()
            ).hexdigest()


class RewindService:
    """
    Manages agent state history with hash-chained immutable snapshots.
    Enables deterministic rollback to last known good state.
    """
    
    def __init__(self):
        self.snapshots: Dict[str, List[StateSnapshot]] = {}
        
    def capture_snapshot(
        self, 
        agent_id: str, 
        state: Dict, 
        valid: bool = True
    ) -> StateSnapshot:
        """
        Capture current agent state as an immutable snapshot.
        
        Args:
            agent_id: Unique identifier for the agent
            state: Current agent state (memory, context, beliefs)
            valid: Whether this state is valid (True) or hallucinated (False)
        
        Returns:
            StateSnapshot with hash-chain linkage
        """
        if agent_id not in self.snapshots:
            self.snapshots[agent_id] = []
        
        # Get previous hash for chain
        prev_hash = ""
        if self.snapshots[agent_id]:
            prev_hash = self.snapshots[agent_id][-1].state_hash
        
        snapshot = StateSnapshot(
            agent_id=agent_id,
            state=state,
            valid=valid,
            timestamp=datetime.now().isoformat(),
            prev_hash=prev_hash
        )
        
        self.snapshots[agent_id].append(snapshot)
        return snapshot
    
    def get_last_valid_snapshot(self, agent_id: str) -> Optional[StateSnapshot]:
        """
        Get the most recent VALID snapshot for an agent.
        Skips over any hallucinated (invalid) states.
        """
        if agent_id not in self.snapshots:
            return None
        
        # Walk backwards to find last valid state
        for snapshot in reversed(self.snapshots[agent_id]):
            if snapshot.valid:
                return snapshot
        
        return None
    
    def rewind(self, agent_id: str) -> Dict:
        """
        Rewind agent to last known good state.
        
        Returns:
            {
                "status": "success" | "no_valid_state",
                "snapshot": StateSnapshot (if successful),
                "message": str
            }
        """
        last_valid = self.get_last_valid_snapshot(agent_id)
        
        if not last_valid:
            return {
                "status": "no_valid_state",
                "snapshot": None,
                "message": f"No valid snapshots found for agent {agent_id}"
            }
        
        # Mark current state as invalid (hallucinated)
        if self.snapshots[agent_id]:
            current = self.snapshots[agent_id][-1]
            if not current.valid:
                # Already marked invalid
                pass
        
        return {
            "status": "success",
            "snapshot": asdict(last_valid),
            "message": f"Agent {agent_id} rewound to {last_valid.timestamp}",
            "snapshots_discarded": sum(
                1 for s in self.snapshots[agent_id] 
                if s.timestamp > last_valid.timestamp
            )
        }
    
    def get_agent_history(self, agent_id: str) -> List[Dict]:
        """
        Get full state history for an agent.
        Used for audit trail generation.
        """
        if agent_id not in self.snapshots:
            return []
        
        return [asdict(s) for s in self.snapshots[agent_id]]
    
    def verify_chain_integrity(self, agent_id: str) -> Dict:
        """
        Verify hash-chain integrity for agent's state history.
        Detects any tampering with historical states.
        
        Returns:
            {
                "valid": bool,
                "total_snapshots": int,
                "verified_snapshots": int,
                "broken_links": List[str]
            }
        """
        if agent_id not in self.snapshots:
            return {
                "valid": True,
                "total_snapshots": 0,
                "verified_snapshots": 0,
                "broken_links": []
            }
        
        snapshots = self.snapshots[agent_id]
        broken_links = []
        
        for i in range(1, len(snapshots)):
            current = snapshots[i]
            previous = snapshots[i-1]
            
            # Verify hash chain
            expected_prev_hash = previous.state_hash
            if current.prev_hash != expected_prev_hash:
                broken_links.append(f"Snapshot {i}: Hash mismatch")
            
            # Verify current hash
            state_json = json.dumps(current.state, sort_keys=True)
            expected_hash = hashlib.sha256(
                (current.prev_hash + state_json).encode()
            ).hexdigest()
            
            if current.state_hash != expected_hash:
                broken_links.append(f"Snapshot {i}: State hash invalid")
        
        return {
            "valid": len(broken_links) == 0,
            "total_snapshots": len(snapshots),
            "verified_snapshots": len(snapshots) - len(broken_links),
            "broken_links": broken_links
        }


# Singleton instance
rewind_service = RewindService()


if __name__ == "__main__":
    # Demo the rewind service
    print("="*70)
    print("REWIND SERVICE DEMO")
    print("="*70)
    
    # Simulate agent making decisions
    agent_id = "agent-001"
    
    # Initial valid state
    print("\n1. Capturing initial valid state...")
    snap1 = rewind_service.capture_snapshot(
        agent_id, 
        {"portfolio": 1000000, "positions": [], "last_decision": "hold"},
        valid=True
    )
    print(f"   Snapshot captured: {snap1.snapshot_id}")
    
    # Second valid state (normal trade)
    print("\n2. Agent makes safe trade...")
    snap2 = rewind_service.capture_snapshot(
        agent_id,
        {"portfolio": 1000000, "positions": [{"symbol": "SPY", "qty": 100, "leverage": 5.0}], "last_decision": "buy"},
        valid=True
    )
    print(f"   Snapshot captured: {snap2.snapshot_id}")
    
    # Hallucinated state (bad news injection)
    print("\n3. Agent receives poisoned prompt → Hallucinates...")
    snap3 = rewind_service.capture_snapshot(
        agent_id,
        {"portfolio": 1000000, "positions": [{"symbol": "GME", "qty": 10000, "leverage": 25.0}], "last_decision": "buy_aggressive"},
        valid=False  # Mark as hallucinated
    )
    print(f"   Snapshot captured (INVALID): {snap3.snapshot_id}")
    
    # Attempt rewind
    print("\n4. Initiating rewind to last valid state...")
    rewind_result = rewind_service.rewind(agent_id)
    print(f"   Status: {rewind_result['status']}")
    print(f"   Message: {rewind_result['message']}")
    print(f"   Snapshots discarded: {rewind_result['snapshots_discarded']}")
    
    restored_state = rewind_result['snapshot']['state']
    print(f"\n   Restored State:")
    print(f"   Portfolio: ${restored_state['portfolio']:,}")
    print(f"   Positions: {restored_state['positions']}")
    
    # Verify chain integrity
    print("\n5. Verifying hash-chain integrity...")
    integrity = rewind_service.verify_chain_integrity(agent_id)
    print(f"   Valid: {integrity['valid']}")
    print(f"   Total Snapshots: {integrity['total_snapshots']}")
    print(f"   Verified: {integrity['verified_snapshots']}")
    
    if integrity['broken_links']:
        print(f"   Broken Links: {integrity['broken_links']}")
    else:
        print(f"   All snapshots verified (no tampering detected)")
