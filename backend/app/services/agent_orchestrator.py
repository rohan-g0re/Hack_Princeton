"""
Agent Orchestrator - Executes the main.py pipeline directly in-process
Replaces subprocess calls to main.py
"""
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict
from app.config import settings


class AgentOrchestrator:
    """Orchestrates agent execution (instacart, ubereats) and knot generation"""
    
    def __init__(self):
        self.base_dir = settings.data_dir_path
        self.agents_dir = self.base_dir / "agents" / "search_and_add_agents"
        self.cart_dir = self.base_dir / "cart_jsons"
        self.knot_dir = self.base_dir / "knot_api_jsons"
        
    def run_agents(self, platforms: List[str]) -> Dict[str, any]:
        """
        Run browser agents for specified platforms
        
        Args:
            platforms: List of platform names (e.g., ['instacart', 'ubereats'])
            
        Returns:
            Dict with success status and results
        """
        if not platforms:
            return {"success": False, "error": "No platforms specified"}
        
        results = {}
        python_exe = sys.executable
        
        for platform in platforms:
            agent_script = self.agents_dir / f"{platform}.py"
            
            if not agent_script.exists():
                results[platform] = {"success": False, "error": f"Agent script not found: {agent_script}"}
                continue
            
            print(f"[INFO] Running {platform} agent...")
            
            try:
                # Run agent script
                result = subprocess.run(
                    [python_exe, str(agent_script)],
                    cwd=str(self.base_dir),
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
                    print(f"[SUCCESS] {platform} agent completed")
                else:
                    results[platform] = {
                        "success": False,
                        "error": f"Agent exited with code {result.returncode}",
                        "stdout": result.stdout[-500:] if result.stdout else "",
                        "stderr": result.stderr[-500:] if result.stderr else ""
                    }
                    print(f"[ERROR] {platform} agent failed with code {result.returncode}")
                    
            except subprocess.TimeoutExpired:
                results[platform] = {"success": False, "error": "Agent timed out"}
                print(f"[ERROR] {platform} agent timed out")
            except Exception as e:
                results[platform] = {"success": False, "error": str(e)}
                print(f"[ERROR] {platform} agent failed: {e}")
        
        return {"success": True, "platform_results": results}
    
    def build_knot_jsons(self) -> Dict[str, any]:
        """
        Build Knot-style JSONs from cart_jsons using mock_response
        This is Step 3 from main.py
        
        Returns:
            Dict with success status and count of generated files
        """
        try:
            # Import the build function
            sys.path.insert(0, str(self.base_dir))
            from knot_api.mock_response import build_knot_like_from_cart
            
            # Create output directory
            self.knot_dir.mkdir(parents=True, exist_ok=True)
            
            generated_count = 0
            
            if self.cart_dir.exists():
                for cart_file in self.cart_dir.glob("*.json"):
                    print(f"[INFO] Processing {cart_file.name}...")
                    knot_obj = build_knot_like_from_cart(str(cart_file))
                    
                    if not knot_obj:
                        print(f"[WARNING] Failed to build Knot JSON from {cart_file.name}")
                        continue
                    
                    out_path = self.knot_dir / cart_file.name
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(knot_obj, f, ensure_ascii=False, indent=2)
                    
                    generated_count += 1
                    print(f"[SUCCESS] Generated {out_path.name}")
            
            return {
                "success": True,
                "generated_count": generated_count,
                "output_dir": str(self.knot_dir)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_full_pipeline(self, platforms: List[str]) -> Dict[str, any]:
        """
        Execute the complete pipeline:
        1. Run agents for specified platforms
        2. Build Knot JSONs from cart data
        
        Returns:
            Dict with success status and results from each step
        """
        print(f"[INFO] Starting pipeline for platforms: {platforms}")
        
        # Step 1: Run agents
        agent_results = self.run_agents(platforms)
        
        if not agent_results.get("success"):
            return {
                "success": False,
                "error": "Agent execution failed",
                "agent_results": agent_results
            }
        
        # Step 2: Build Knot JSONs
        knot_results = self.build_knot_jsons()
        
        # Overall success if we generated at least one Knot JSON
        success = knot_results.get("success") and knot_results.get("generated_count", 0) > 0
        
        return {
            "success": success,
            "agent_results": agent_results,
            "knot_results": knot_results
        }


# Singleton
agent_orchestrator = AgentOrchestrator()

