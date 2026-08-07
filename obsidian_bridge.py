import os
import time
import logging
import asyncio
from supervisor import OmegaSupervisor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ObsidianBridge")

class ObsidianBridge:
    """
    Watches the Obsidian vault for new prompts and status changes.
    Bridges human intent from Markdown files to the Omega Supervisor.
    """
    
    def __init__(self, vault_path: str = "vault"):
        self.vault_path = vault_path
        self.supervisor = OmegaSupervisor(vault_path=vault_path)
        self.inbox_path = os.path.join(vault_path, "Inbox")
        self.processed_path = os.path.join(vault_path, "Processed")
        
        # Ensure directories exist
        os.makedirs(self.inbox_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)
        
        self.last_check = time.time()

    async def watch(self):
        logger.info(f"Obsidian Bridge active. Watching {self.inbox_path}...")
        
        while True:
            try:
                # 1. Check for new prompts in Inbox
                for filename in os.listdir(self.inbox_path):
                    if filename.endswith(".md"):
                        file_path = os.path.join(self.inbox_path, filename)
                        await self._process_inbox_file(file_path, filename)
                
                # 2. Check for approvals in Actions
                await self._check_for_approvals()
                
                # 3. Pulse update the Dashboard
                self.supervisor.update_dashboard("Active - Watching Vault")
                
            except Exception as e:
                logger.error(f"Bridge Error: {e}")
            
            await asyncio.sleep(2) # Fast polling every 2 seconds

    async def _process_inbox_file(self, path: str, filename: str):
        logger.info(f"New prompt detected: {filename}")
        
        with open(path, 'r') as f:
            content = f.read()
        
        # Strip frontmatter if present
        prompt = content.split("---")[-1].strip()
        
        if prompt:
            # Execute through Supervisor
            response = await self.supervisor.execute_task(prompt)
            
            # Move to processed
            new_path = os.path.join(self.processed_path, filename)
            os.rename(path, new_path)
            
            # Append response to the processed file
            with open(new_path, 'a') as f:
                f.write(f"\n\n--- \n### Omega Response\n{response}\n")
            
            logger.info(f"Task completed: {filename}")

    async def _check_for_approvals(self):
        actions_path = os.path.join(self.vault_path, "Actions")
        if not os.path.exists(actions_path):
            return
            
        for filename in os.listdir(actions_path):
            if filename.endswith(".md"):
                path = os.path.join(actions_path, filename)
                with open(path, 'r') as f:
                    content = f.read()
                
                if "status: approved" in content.lower():
                    logger.info(f"✅ Action Approved: {filename}")
                    # Trigger the actual execution here
                    # For now, we'll just mark it as executing
                    with open(path, 'w') as f:
                        f.write(content.replace("status: approved", "status: executing"))
                    
                    # In a real scenario, this would call a specific connector
                    await asyncio.sleep(1)
                    
                    with open(path, 'w') as f:
                        f.write(content.replace("status: approved", "status: completed").replace("status: executing", "status: completed"))

if __name__ == "__main__":
    bridge = ObsidianBridge()
    asyncio.run(bridge.watch())
