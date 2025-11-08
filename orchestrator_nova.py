# orchestrator_nova.py

import asyncio
from typing import List
import logging
from agents.search_order_agent_nova import SearchOrderAgentNova
from agents.cart_detail_agent_nova import CartDetailAgentNova
from agents.edit_cart_agent_nova import EditCartAgentNova
from models.cart_models import CartState
from config.platforms import PLATFORM_CONFIGS

logger = logging.getLogger(__name__)

class ParallelOrchestratorNova:
    """
    Orchestrates parallel execution of Amazon Nova Auto agents
    
    Uses NovaAct with natural language instructions - much simpler!
    """
    
    def __init__(self, ingredients: List[str]):
        self.ingredients = ingredients
        self.cart_state = CartState()
        self.cart_state.ingredients_requested = ingredients
    
    async def run_search_and_order_all_platforms(self, platform_names: List[str]) -> CartState:
        """
        STEP 1: Run Search_&_Order agents for all platforms in parallel
        
        Args:
            platform_names: List of platforms to process
        
        Returns:
            CartState with initial cart data from all platforms
        """
        print(f"\n{'=' * 70}")
        print(f"PARALLEL SEARCH & ORDER - {len(platform_names)} PLATFORMS (Nova Auto)")
        print(f"Ingredients: {self.ingredients}")
        print("=" * 70)
        
        # Create task for each platform
        tasks = [
            self._run_search_order_single_platform(platform_name)
            for platform_name in platform_names
        ]
        
        # Execute ALL in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for platform_name, result in zip(platform_names, results):
            if isinstance(result, Exception):
                print(f"[FAIL] {platform_name} FAILED: {result}")
                logger.error(f"{platform_name} failed: {result}")
            else:
                print(f"[PASS] {platform_name} COMPLETED: {len(result.items)} items, ${result.total:.2f}")
                self.cart_state.add_platform_cart(result)
        
        # Save state
        self.cart_state.save_to_file()
        
        return self.cart_state
    
    async def _run_search_order_single_platform(self, platform_name: str):
        """Run Search_&_Order agent for ONE platform (Nova version)"""
        try:
            agent = SearchOrderAgentNova(platform_name)
            cart = await agent.search_and_add_all(self.ingredients)
            return cart
        except Exception as e:
            logger.error(f"Search & Order failed for {platform_name}: {e}")
            raise
    
    async def extract_cart_details_all_platforms(self, platform_names: List[str]) -> CartState:
        """
        STEP 2: Extract detailed cart info from all platforms
        
        Returns:
            Updated CartState with detailed cart information
        """
        print(f"\n{'=' * 70}")
        print(f"EXTRACTING CART DETAILS - {len(platform_names)} PLATFORMS")
        print("=" * 70)
        
        tasks = [
            self._extract_cart_single_platform(platform_name)
            for platform_name in platform_names
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for platform_name, result in zip(platform_names, results):
            if isinstance(result, Exception):
                print(f"[FAIL] {platform_name} cart detail extraction FAILED: {result}")
            else:
                print(f"[PASS] {platform_name} cart details: {len(result.items)} items, ${result.total:.2f}")
                self.cart_state.add_platform_cart(result)
        
        self.cart_state.save_to_file()
        
        return self.cart_state
    
    async def _extract_cart_single_platform(self, platform_name: str):
        """Extract cart details for ONE platform (Nova version)"""
        try:
            agent = CartDetailAgentNova(platform_name)
            cart = await agent.extract_cart_details()
            return cart
        except Exception as e:
            logger.error(f"Cart detail extraction failed for {platform_name}: {e}")
            raise
    
    async def apply_diffs_all_platforms(self) -> CartState:
        """
        STEP 3: Apply user edits (diffs) to actual platform carts
        """
        print(f"\n{'=' * 70}")
        print("APPLYING CART EDITS (DIFFS)")
        print("=" * 70)
        
        platforms_with_diffs = set(diff.platform for diff in self.cart_state.diffs if not diff.applied)
        
        if not platforms_with_diffs:
            print("No pending diffs to apply.")
            return self.cart_state
        
        print(f"Platforms with pending edits: {list(platforms_with_diffs)}")
        
        # Create tasks for each platform with diffs
        tasks = [
            self._apply_diffs_single_platform(platform_name)
            for platform_name in platforms_with_diffs
        ]
        
        # Execute ALL in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for platform_name, result in zip(platforms_with_diffs, results):
            if isinstance(result, Exception):
                print(f"[FAIL] {platform_name} diff application FAILED: {result}")
            elif result:
                print(f"[PASS] {platform_name} diffs applied successfully")
            else:
                print(f"[WARN] {platform_name} some diffs failed to apply")
        
        # Save state
        self.cart_state.save_to_file()
        
        return self.cart_state
    
    async def _apply_diffs_single_platform(self, platform_name: str) -> bool:
        """Apply diffs for ONE platform"""
        try:
            # Get diffs for this platform
            platform_diffs = [diff for diff in self.cart_state.diffs 
                            if diff.platform == platform_name and not diff.applied]
            
            if not platform_diffs:
                return True
            
            agent = EditCartAgentNova(platform_name)
            success = await agent.apply_diffs(platform_diffs)
            return success
        except Exception as e:
            logger.error(f"Diff application failed for {platform_name}: {e}")
            raise

