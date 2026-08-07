import json
import logging
import os
from typing import Dict, Any, List
from omega_orchestrator import OmegaOrchestrator, UnifiedAnalysisRequest

logger = logging.getLogger("OmegaRouter")

class OmegaRouter:
    """
    Routes capabilities to implementations and handles Obsidian-ready output.
    """
    
    def __init__(self, config_path: str = "runtime/config.json", vault_path: str = "vault"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.vault_path = vault_path
        self.orchestrator = OmegaOrchestrator()
        self.registry = self.config.get("capability_registry", {})
        
        # Ensure vault structure exists
        os.makedirs(os.path.join(self.vault_path, "Thoughts"), exist_ok=True)
        os.makedirs(os.path.join(self.vault_path, "Actions"), exist_ok=True)
        os.makedirs(os.path.join(self.vault_path, "Logs"), exist_ok=True)

    async def handle_request(self, input_text: str):
        """
        Processes a request, logs thoughts to Obsidian, and determines the best capability.
        """
        # 1. Generate Thought in Obsidian
        thought_id = f"thought_{int(os.path.getmtime(os.path.join(self.vault_path, 'Thoughts')) * 1000) % 100000}"
        thought_file = os.path.join(self.vault_path, "Thoughts", f"{thought_id}.md")
        
        with open(thought_file, 'w') as f:
            f.write(f"---\ntitle: {thought_id}\ntags: [thought, omega]\nstatus: processing\n---\n\n")
            f.write(f"# Thought: {input_text[:50]}...\n\n")
            f.write("## Analysis\nProcessing through Omega Orchestrator...\n")

        # 2. Run Orchestrator
        req = UnifiedAnalysisRequest(input_text=input_text)
        result = await self.orchestrator.analyze(req)
        
        # 3. Update Thought with Result
        with open(thought_file, 'a') as f:
            f.write(f"\n## Result\n{result.output_text}\n\n")
            f.write(f"**Confidence**: {result.confidence_score}\n")
            f.write(f"**Engines**: {', '.join(result.engines_used)}\n")
            f.write("\n---\nstatus: completed\n")

        return result

    def get_connector(self, capability: str) -> str:
        """
        Determines the best connector for a capability.
        """
        entry = self.registry.get(capability, {})
        preferred = entry.get("preferred", [])
        if preferred:
            return preferred[0]
        return "fallback"
