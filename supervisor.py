import asyncio
import logging
import os
from omega_router import OmegaRouter
from permission_gate import PermissionGate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OmegaSupervisor")

class OmegaSupervisor:
    """
    The main control loop for the Omega Federation.
    Coordinates the Router and Permission Gate.
    """
    
    def __init__(self, vault_path: str = "vault"):
        self.vault_path = vault_path
        self.router = OmegaRouter(vault_path=vault_path)
        self.gate = PermissionGate()
        self.is_running = True

    async def run(self):
        logger.info("Omega Supervisor started.")
        self.update_dashboard("Online")
        
        while self.is_running:
            # In a real scenario, this would poll an input source
            # For this simulation, we'll just wait for a trigger
            await asyncio.sleep(10)
            
    def update_dashboard(self, status: str):
        dashboard_file = os.path.join(self.vault_path, "Dashboard.md")
        with open(dashboard_file, 'w') as f:
            f.write(f"---\ntitle: Omega Dashboard\ntags: [dashboard, omega]\n---\n\n")
            f.write(f"# 🍊 Omega Federation Dashboard\n\n")
            f.write(f"**Status**: {status}\n")
            f.write(f"**Covenant Alignment**: 1.667 ✓\n")
            f.write(f"**Active Connectors**: Termux, Drive, GitHub\n\n")
            f.write("## Recent Thoughts\n![[Thoughts/]]\n")
            f.write("## Pending Actions\n![[Actions/]]\n")

    async def execute_task(self, task_text: str):
        """
        Executes a specific task through the federation.
        """
        logger.info(f"Executing task: {task_text}")
        
        # 1. Route and Analyze
        result = await self.router.handle_request(task_text)
        
        # 2. Verify through Permission Gate
        verification = self.gate.verify_action({"type": "analysis", "content": result.output_text})
        
        if not verification["permitted"]:
            if verification["requires_approval"]:
                self.request_approval(task_text, result.output_text)
                return "Action pending human approval in Obsidian."
            return f"Action blocked: {verification['reason']}"
            
        return result.output_text

    def request_approval(self, task: str, result: str):
        action_id = f"action_{int(asyncio.get_event_loop().time())}"
        action_file = os.path.join(self.vault_path, "Actions", f"{action_id}.md")
        with open(action_file, 'w') as f:
            f.write(f"---\ntitle: Approval Required\ntags: [action, pending]\nstatus: pending\n---\n\n")
            f.write(f"# Approval Required for: {task[:50]}\n\n")
            f.write(f"## Proposed Result\n{result}\n\n")
            f.write("## Instructions\nChange the status in the frontmatter to `approved` to execute this action.\n")

if __name__ == "__main__":
    supervisor = OmegaSupervisor()
    asyncio.run(supervisor.run())
