# orchestrator_playwright.py

import asyncio
from typing import List, Dict
import logging
from agents.search_order_agent_playwright import SearchOrderAgentPlaywright
from agents.cart_detail_agent import CartDetailAgent
from models.cart_models import CartState
from config.platforms import PLATFORM_CONFIGS

logger = logging.getLogger(__name__)

class ParallelOrchestratorPlaywright:
    """
    Orchestrates parallel execution of Playwright-based agents
    
    Uses pure Playwright agents (no LLM) based on instacart_agent.py pattern
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
        print(f"PARALLEL SEARCH & ORDER - {len(platform_names)} PLATFORMS (Playwright)")
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
        """Run Search_&_Order agent for ONE platform (Playwright version)"""
        try:
            agent = SearchOrderAgentPlaywright(platform_name)
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
        
        Note: Not implemented for Playwright MVP - would need edit_cart_agent_playwright.py
        """
        print(f"\n{'=' * 70}")
        print("APPLYING CART EDITS (DIFFS)")
        print("=" * 70)
        
        platforms_with_diffs = set(diff.platform for diff in self.cart_state.diffs if not diff.applied)
        
        if not platforms_with_diffs:
            print("No pending diffs to apply.")
            return self.cart_state
        
        print(f"[NOTE] Diff application not yet implemented for Playwright agents")
        print(f"Platforms with pending edits: {list(platforms_with_diffs)}")
        
        return self.cart_state

