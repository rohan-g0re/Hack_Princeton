"""
Agent Orchestrator - Executes the main.py pipeline directly in-process
Replaces subprocess calls to main.py
"""
import sys
import json
import subprocess
import logging
import os
from pathlib import Path
from typing import List, Dict
from app.config import settings
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates agent execution (instacart, ubereats) and knot generation"""
    
    def __init__(self):
        self.base_dir = settings.data_dir_path
        # Agents are now in backend/app/agents/
        from pathlib import Path
        backend_root = Path(__file__).parent.parent.parent
        self.agents_dir = backend_root / "app" / "agents" / "search_and_add_agents"
        self.cart_dir = self.base_dir / "cart_jsons"
        self.knot_dir = self.base_dir / "knot_api_jsons"
        
        # Load environment variables from backend/.env for agent subprocesses
        backend_env_file = backend_root / ".env"
        if backend_env_file.exists():
            load_dotenv(backend_env_file)
            logger.info(f"[ORCHESTRATOR] Loaded environment from {backend_env_file}")
        else:
            logger.warning(f"[ORCHESTRATOR] .env file not found at {backend_env_file}")
        
        # Prepare environment for subprocesses (includes current env + loaded .env vars)
        self.subprocess_env = os.environ.copy()
        
    def run_agents(self, platforms: List[str]) -> Dict[str, any]:
        """
        Run browser agents for specified platforms
        
        Args:
            platforms: List of platform names (e.g., ['instacart', 'ubereats'])
            
        Returns:
            Dict with success status and results
        """
        if not platforms:
            logger.error("[ORCHESTRATOR] No platforms specified")
            return {"success": False, "error": "No platforms specified"}
        
        logger.info(f"[ORCHESTRATOR] Running agents for platforms: {platforms}")
        results = {}
        python_exe = sys.executable
        
        for platform in platforms:
            agent_script = self.agents_dir / f"{platform}.py"
            
            if not agent_script.exists():
                logger.error(f"[ORCHESTRATOR] Agent script not found for {platform}: {agent_script}")
                results[platform] = {"success": False, "error": f"Agent script not found: {agent_script}"}
                continue
            
            logger.info(f"[ORCHESTRATOR] Running {platform} agent from {agent_script}")
            
            try:
                # Run agent script
                # Working directory is backend/data so agents can find shopping_list.json
                # Pass environment variables so agents can access .env vars
                result = subprocess.run(
                    [python_exe, str(agent_script)],
                    cwd=str(self.base_dir),  # backend/data
                    env=self.subprocess_env,  # Pass environment with .env vars loaded
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout per agent
                )
                
                if result.returncode == 0:
                    results[platform] = {
                        "success": True,
                        "stdout": result.stdout[-500:] if result.stdout else "",  # Last 500 chars
                        "stderr": result.stderr[-500:] if result.stderr else ""
                    }
                    logger.info(f"[ORCHESTRATOR] ✓ {platform} agent completed successfully")
                else:
                    results[platform] = {
                        "success": False,
                        "error": f"Agent exited with code {result.returncode}",
                        "stdout": result.stdout[-500:] if result.stdout else "",
                        "stderr": result.stderr[-500:] if result.stderr else ""
                    }
                    logger.error(f"[ORCHESTRATOR] ✗ {platform} agent failed with code {result.returncode}")
                    if result.stderr:
                        logger.error(f"[ORCHESTRATOR] {platform} stderr: {result.stderr[-200:]}")
                    
            except subprocess.TimeoutExpired:
                results[platform] = {"success": False, "error": "Agent timed out"}
                logger.error(f"[ORCHESTRATOR] ✗ {platform} agent timed out after 600s")
            except Exception as e:
                results[platform] = {"success": False, "error": str(e)}
                logger.exception(f"[ORCHESTRATOR] ✗ {platform} agent failed with exception: {e}")
        
        return {"success": True, "platform_results": results}
    
    def build_knot_jsons(self) -> Dict[str, any]:
        """
        Build Knot-style JSONs from cart_jsons using mock_response
        This is Step 3 from main.py
        
        Returns:
            Dict with success status and count of generated files
        """
        logger.info("[ORCHESTRATOR] Building Knot JSONs from cart files")
        try:
            # Import the build function from app/knot_api
            from app.knot_api.mock_response import build_knot_like_from_cart
            
            # Create output directory
            self.knot_dir.mkdir(parents=True, exist_ok=True)
            
            generated_count = 0
            
            if self.cart_dir.exists():
                cart_files = list(self.cart_dir.glob("*.json"))
                logger.info(f"[ORCHESTRATOR] Found {len(cart_files)} cart file(s) to process")
                
                for cart_file in cart_files:
                    logger.info(f"[ORCHESTRATOR] Processing {cart_file.name}...")
                    knot_obj = build_knot_like_from_cart(str(cart_file))
                    
                    if not knot_obj:
                        logger.warning(f"[ORCHESTRATOR] Failed to build Knot JSON from {cart_file.name}")
                        continue
                    
                    out_path = self.knot_dir / cart_file.name
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(knot_obj, f, ensure_ascii=False, indent=2)
                    
                    generated_count += 1
                    logger.info(f"[ORCHESTRATOR] ✓ Generated {out_path.name}")
            else:
                logger.warning(f"[ORCHESTRATOR] Cart directory does not exist: {self.cart_dir}")
            
            logger.info(f"[ORCHESTRATOR] Knot JSON generation complete. Generated {generated_count} file(s)")
            return {
                "success": True,
                "generated_count": generated_count,
                "output_dir": str(self.knot_dir)
            }
            
        except Exception as e:
            logger.exception(f"[ORCHESTRATOR] Failed to build Knot JSONs: {e}")
            return {"success": False, "error": str(e)}
    
    def _clear_old_outputs(self):
        """Clear old cart and knot JSON files before new run"""
        logger.info("[ORCHESTRATOR] Clearing old output files")
        try:
            # Clear cart_jsons directory
            if self.cart_dir.exists():
                cart_files = list(self.cart_dir.glob("*.json"))
                for json_file in cart_files:
                    json_file.unlink()
                    logger.debug(f"[ORCHESTRATOR] Deleted old cart file: {json_file.name}")
                logger.info(f"[ORCHESTRATOR] Cleared {len(cart_files)} cart file(s)")
            
            # Clear knot_api_jsons directory
            if self.knot_dir.exists():
                knot_files = list(self.knot_dir.glob("*.json"))
                for json_file in knot_files:
                    json_file.unlink()
                    logger.debug(f"[ORCHESTRATOR] Deleted old knot file: {json_file.name}")
                logger.info(f"[ORCHESTRATOR] Cleared {len(knot_files)} knot file(s)")
            
            logger.info("[ORCHESTRATOR] Cache cleared successfully")
            
        except Exception as e:
            logger.warning(f"[ORCHESTRATOR] Could not clear old outputs: {e}")
    
    def execute_full_pipeline(self, platforms: List[str]) -> Dict[str, any]:
        """
        Execute the complete pipeline:
        1. Clear old cache files
        2. Run agents for specified platforms
        3. Build Knot JSONs from cart data
        
        Returns:
            Dict with success status and results from each step
        """
        logger.info(f"[ORCHESTRATOR] ═══════════════════════════════════════")
        logger.info(f"[ORCHESTRATOR] Starting full pipeline for platforms: {platforms}")
        logger.info(f"[ORCHESTRATOR] ═══════════════════════════════════════")
        
        # Clear old output files before running
        self._clear_old_outputs()
        
        # Step 1: Run agents
        logger.info("[ORCHESTRATOR] Step 1/2: Running browser agents")
        agent_results = self.run_agents(platforms)
        
        if not agent_results.get("success"):
            logger.error("[ORCHESTRATOR] ✗ Pipeline failed during agent execution")
            return {
                "success": False,
                "error": "Agent execution failed",
                "agent_results": agent_results
            }
        
        # Step 2: Build Knot JSONs
        logger.info("[ORCHESTRATOR] Step 2/2: Building Knot JSONs")
        knot_results = self.build_knot_jsons()
        
        # Overall success if we generated at least one Knot JSON
        success = knot_results.get("success") and knot_results.get("generated_count", 0) > 0
        
        if success:
            logger.info(f"[ORCHESTRATOR] ═══════════════════════════════════════")
            logger.info(f"[ORCHESTRATOR] ✓ Pipeline completed successfully!")
            logger.info(f"[ORCHESTRATOR] Generated {knot_results.get('generated_count', 0)} platform summary/summaries")
            logger.info(f"[ORCHESTRATOR] ═══════════════════════════════════════")
        else:
            logger.error(f"[ORCHESTRATOR] ✗ Pipeline completed but no outputs generated")
        
        return {
            "success": success,
            "agent_results": agent_results,
            "knot_results": knot_results
        }


# Singleton
agent_orchestrator = AgentOrchestrator()

