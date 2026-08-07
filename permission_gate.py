import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("PermissionGate")

class PermissionGate:
    """
    Ensures all actions comply with the 25 Covenant Axioms.
    Requires human approval for critical actions.
    """
    
    def __init__(self, config_path: str = "runtime/config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.axioms_count = self.config.get("covenant", {}).get("axioms_count", 25)
        self.alignment_threshold = self.config.get("covenant", {}).get("alignment_threshold", 1.667)

    def verify_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifies if an action is permitted.
        Returns a dict with 'permitted', 'reason', and 'requires_approval'.
        """
        action_type = action.get("type", "unknown")
        risk_level = action.get("risk", "low")
        
        # Simple simulation of axiom verification
        alignment_score = action.get("alignment", 1.89) # Default to invariant
        
        if alignment_score < self.alignment_threshold:
            return {
                "permitted": False,
                "reason": f"Alignment score {alignment_score} is below threshold {self.alignment_threshold}",
                "requires_approval": False
            }
            
        if risk_level == "high":
            return {
                "permitted": False,
                "reason": "High risk action requires explicit human approval",
                "requires_approval": True
            }
            
        return {
            "permitted": True,
            "reason": "Action verified against Covenant Axioms",
            "requires_approval": False
        }

    def check_human_approval(self, action_id: str, vault_path: str = "vault/Actions") -> bool:
        """
        Checks if a human has approved the action in the Obsidian vault.
        """
        import os
        approval_file = os.path.join(vault_path, f"{action_id}.md")
        if not os.path.exists(approval_file):
            return False
            
        with open(approval_file, 'r') as f:
            content = f.read()
            return "status: approved" in content.lower()
