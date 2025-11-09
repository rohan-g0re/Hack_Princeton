"""
Agent orchestration and execution
"""
import asyncio
import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4
from server.models import IngredientItem
from server.ws_manager import manager as ws_manager


class AgentRunner:
    """Manages execution of browser automation agents"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.agents_dir = base_dir.parent / "agents" / "search_and_add_agents"
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    async def run_agents(
        self,
        session_id: str,
        ingredients: List[IngredientItem],
        platforms: List[str]
    ) -> str:
        """
        Execute Search & Order agents for specified platforms
        
        Returns:
            job_id: Unique identifier for this job
        """
        job_id = str(uuid4())
        
        # Create temporary shopping list for agents
        shopping_list = {
            "shopping_list": [
                {"item": ing.name, "quantity": ing.quantity}
                for ing in ingredients
            ]
        }
        
        # Save shopping list to temp file
        temp_list_path = self.base_dir.parent / f"shopping_list_{session_id}.json"
        with open(temp_list_path, "w") as f:
            json.dump(shopping_list, f, indent=2)
        
        # Initialize job status
        self.jobs[job_id] = {
            "session_id": session_id,
            "status": "running",
            "platforms": {platform: {"status": "pending"} for platform in platforms},
            "temp_file": temp_list_path
        }
        
        # Run agents asynchronously
        asyncio.create_task(self._execute_agents(job_id, session_id, platforms, temp_list_path))
        
        return job_id
    
    async def _execute_agents(
        self,
        job_id: str,
        session_id: str,
        platforms: List[str],
        shopping_list_path: Path
    ):
        """Execute agents for each platform"""
        
        for platform in platforms:
            await self._run_single_agent(job_id, session_id, platform, shopping_list_path)
        
        # Mark job as completed
        self.jobs[job_id]["status"] = "completed"
        
        await ws_manager.send_to_session(session_id, {
            "type": "job_completed",
            "job_id": job_id,
            "message": "All agents completed"
        })
        
        # Clean up temp file
        try:
            shopping_list_path.unlink()
        except Exception as e:
            print(f"Error deleting temp file: {e}")
    
    async def _run_single_agent(
        self,
        job_id: str,
        session_id: str,
        platform: str,
        shopping_list_path: Path
    ):
        """Run a single platform agent"""
        
        agent_script = self.agents_dir / f"{platform}.py"
        
        if not agent_script.exists():
            self.jobs[job_id]["platforms"][platform]["status"] = "failed"
            self.jobs[job_id]["platforms"][platform]["error"] = f"Agent script not found: {agent_script}"
            
            await ws_manager.send_to_session(session_id, {
                "type": "agent_update",
                "platform": platform,
                "status": "failed",
                "message": f"Agent script not found for {platform}"
            })
            return
        
        # Update status
        self.jobs[job_id]["platforms"][platform]["status"] = "running"
        
        await ws_manager.send_to_session(session_id, {
            "type": "agent_update",
            "platform": platform,
            "status": "running",
            "message": f"Starting {platform} agent..."
        })
        
        try:
            # Run agent as subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(agent_script),
                env={
                    **subprocess.os.environ,
                    "SHOPPING_LIST_PATH": str(shopping_list_path)
                },
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.base_dir.parent)
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.jobs[job_id]["platforms"][platform]["status"] = "completed"
                
                # Try to parse cart output from stdout
                try:
                    output_text = stdout.decode()
                    # Look for JSON cart data in output
                    cart_data = self._extract_cart_data(output_text, platform)
                    self.jobs[job_id]["platforms"][platform]["cart_data"] = cart_data
                except Exception as e:
                    print(f"Error parsing cart output: {e}")
                
                await ws_manager.send_to_session(session_id, {
                    "type": "agent_update",
                    "platform": platform,
                    "status": "completed",
                    "message": f"{platform} agent completed successfully"
                })
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.jobs[job_id]["platforms"][platform]["status"] = "failed"
                self.jobs[job_id]["platforms"][platform]["error"] = error_msg
                
                await ws_manager.send_to_session(session_id, {
                    "type": "agent_update",
                    "platform": platform,
                    "status": "failed",
                    "message": f"{platform} agent failed: {error_msg[:100]}"
                })
        
        except Exception as e:
            self.jobs[job_id]["platforms"][platform]["status"] = "failed"
            self.jobs[job_id]["platforms"][platform]["error"] = str(e)
            
            await ws_manager.send_to_session(session_id, {
                "type": "agent_update",
                "platform": platform,
                "status": "failed",
                "message": f"Error running {platform} agent: {str(e)}"
            })
    
    def _extract_cart_data(self, output: str, platform: str) -> Optional[Dict]:
        """Extract cart data from agent output"""
        # Look for JSON file created by agent
        cart_file = self.base_dir.parent / f"{platform}_cart_details.json"
        
        if cart_file.exists():
            try:
                with open(cart_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading cart file: {e}")
        
        return None
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a job"""
        return self.jobs.get(job_id)

