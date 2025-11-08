# orchestrator.py

import asyncio
from typing import List, Dict
import logging
from agents.search_order_agent import SearchOrderAgent
from agents.edit_cart_agent import EditCartAgent
from agents.cart_detail_agent import CartDetailAgent
from models.cart_models import CartState
from config.platforms import PLATFORM_CONFIGS

logger = logging.getLogger(__name__)

class ParallelOrchestrator:
    """
    Orchestrates parallel execution of agents across platforms
    
    Key Features:
    - Runs all platforms simultaneously using asyncio.gather()
    - Handles exceptions per platform (one failure doesn't stop others)
    - Updates CartState with results
    """
    
    def __init__(self, ingredients: List[str]):
        self.ingredients = ingredients
        self.cart_state = CartState()
        self.cart_state.ingredients_requested = ingredients
    
    async def run_search_and_order_all_platforms(self, platform_names: List[str]) -> CartState:
        """
        STEP 1: Run Search_&_Order agents for all platforms in parallel
        
        Args:
            platform_names: List of platforms to process (e.g., ["instacart", "ubereats", "doordash"])
        
        Returns:
            CartState with initial cart data from all platforms
        """
        print(f"\n{'=' * 70}")
        print(f"PARALLEL SEARCH & ORDER - {len(platform_names)} PLATFORMS")
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
        """
        Run Search_&_Order agent for ONE platform
        
        Wrapped in try/except to prevent one platform's failure from affecting others
        """
        try:
            agent = SearchOrderAgent(platform_name)
            cart = await agent.search_and_add_all(self.ingredients)
            return cart
        except Exception as e:
            logger.error(f"Search & Order failed for {platform_name}: {e}")
            raise
    
    async def extract_cart_details_all_platforms(self, platform_names: List[str]) -> CartState:
        """
        STEP 2: Extract detailed cart info from all platforms
        
        Used AFTER Search_&_Order OR after Edit_Cart
        
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
        """Extract cart details for ONE platform"""
        try:
            agent = CartDetailAgent(platform_name)
            cart = await agent.extract_cart_details()
            return cart
        except Exception as e:
            logger.error(f"Cart detail extraction failed for {platform_name}: {e}")
            raise
    
    async def apply_diffs_all_platforms(self) -> CartState:
        """
        STEP 3: Apply user edits (diffs) to actual platform carts
        
        Only runs for platforms that have pending diffs
        
        Returns:
            Updated CartState after applying diffs
        """
        print(f"\n{'=' * 70}")
        print("APPLYING CART EDITS (DIFFS)")
        print("=" * 70)
        
        # Group diffs by platform
        platforms_with_diffs = set(diff.platform for diff in self.cart_state.diffs if not diff.applied)
        
        if not platforms_with_diffs:
            print("No pending diffs to apply.")
            return self.cart_state
        
        print(f"Platforms with edits: {list(platforms_with_diffs)}")
        
        tasks = [
            self._apply_diffs_single_platform(platform_name)
            for platform_name in platforms_with_diffs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for platform_name, result in zip(platforms_with_diffs, results):
            if isinstance(result, Exception):
                print(f"[FAIL] {platform_name} diff application FAILED: {result}")
            else:
                print(f"[PASS] {platform_name} diffs applied: {result} successful")
                self.cart_state.mark_diffs_applied(platform_name)
        
        self.cart_state.save_to_file()
        
        return self.cart_state
    
    async def _apply_diffs_single_platform(self, platform_name: str) -> int:
        """Apply diffs for ONE platform"""
        try:
            diffs = self.cart_state.get_pending_diffs(platform_name)
            agent = EditCartAgent(platform_name)
            success_count = await agent.apply_all_diffs(diffs)
            return success_count
        except Exception as e:
            logger.error(f"Diff application failed for {platform_name}: {e}")
            raise

