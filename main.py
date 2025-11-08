# main.py

import asyncio
import logging
from models.cart_models import CartState
from knot_api.client import get_knot_client
from knot_api.config import MERCHANT_IDS
import sys
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """
    Complete workflow for grocery delivery super app
    
    Steps:
    1. User provides ingredients
    2. Search & Order agents add items to all platform carts (parallel)
    3. Cart Detail agents extract cart info (parallel)
    4. [User edits carts in UI - simulated with diffs]
    5. Edit Cart agents apply diffs (parallel)
    6. Cart Detail agents re-extract final cart info
    7. Mock payment with Knot API transaction demonstration
    """
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Grocery Delivery Super App')
    parser.add_argument('-1', '--browseruse', action='store_true', 
                       help='Use BrowserUse agents (AI-powered, requires Gemini)')
    parser.add_argument('-2', '--playwright', action='store_true',
                       help='Use Playwright agents (pure DOM selectors, no LLM)')
    parser.add_argument('ingredients', nargs='*', 
                       help='Ingredients to order (e.g., milk eggs bread)')
    
    args = parser.parse_args()
    
    # Determine agent type
    if args.playwright or (not args.browseruse and not args.playwright):
        # Default to Playwright if nothing specified, or if -2 specified
        agent_type = "playwright"
        from orchestrator_playwright import ParallelOrchestratorPlaywright as Orchestrator
    elif args.browseruse:
        agent_type = "browseruse"
        from orchestrator import ParallelOrchestrator as Orchestrator
    else:
        agent_type = "playwright"
        from orchestrator_playwright import ParallelOrchestratorPlaywright as Orchestrator
    
    print("\n" + "=" * 70)
    print("GROCERY DELIVERY SUPER APP - MVP")
    print(f"Agent Type: {agent_type.upper()}")
    print("=" * 70)
    
    # STEP 1: Get ingredients
    if args.ingredients:
        ingredients = args.ingredients
    else:
        ingredients = ["milk", "eggs", "paneer", "tomatoes"]
    
    print(f"\nIngredients: {ingredients}")
    
    # Platforms to use
    platforms = ["instacart", "ubereats", "doordash"]
    print(f"Platforms: {platforms}\n")
    
    # Create orchestrator (type determined by CLI args)
    orchestrator = Orchestrator(ingredients)
    
    # STEP 2: Search & Order (parallel across platforms)
    print("\n[STEP 1] SEARCHING AND ADDING TO CARTS...")
    cart_state = await orchestrator.run_search_and_order_all_platforms(platforms)
    
    # STEP 3: Extract detailed cart info
    print("\n[STEP 2] EXTRACTING CART DETAILS...")
    cart_state = await orchestrator.extract_cart_details_all_platforms(platforms)
    
    # Display initial cart state
    print("\n" + "=" * 70)
    print("INITIAL CART STATE")
    print("=" * 70)
    for platform_name, cart in cart_state.platform_carts.items():
        print(f"\n{platform_name.upper()}:")
        print(f"  Items: {len(cart.items)}")
        print(f"  Total: ${cart.total:.2f}")
        for item in cart.items:
            print(f"    - {item.product_name}: ${item.price:.2f} x {item.quantity}")
    
    # STEP 4: Simulate user edits (in real app, this comes from UI)
    print("\n[STEP 3] SIMULATING USER EDITS...")
    # Example: User removes "milk" from ubereats
    if cart_state.get_cart("ubereats"):
        milk_item = next((item for item in cart_state.get_cart("ubereats").items if "milk" in item.product_name.lower()), None)
        if milk_item:
            cart_state.record_diff("ubereats", "remove", milk_item)
            print(f"  [EDIT] Recorded: Remove '{milk_item.product_name}' from UberEats")
    
    # STEP 5: Apply diffs (if any)
    if cart_state.diffs:
        print("\n[STEP 4] APPLYING CART EDITS...")
        cart_state = await orchestrator.apply_diffs_all_platforms()
        
        # Re-extract cart details after edits
        print("\n[STEP 5] RE-EXTRACTING CART DETAILS AFTER EDITS...")
        cart_state = await orchestrator.extract_cart_details_all_platforms(platforms)
    
    # Display final cart state
    print("\n" + "=" * 70)
    print("FINAL CART STATE (BEFORE PAYMENT)")
    print("=" * 70)
    total_across_all = 0.0
    for platform_name, cart in cart_state.platform_carts.items():
        print(f"\n{platform_name.upper()}:")
        print(f"  Items: {len(cart.items)}")
        print(f"  Total: ${cart.total:.2f}")
        total_across_all += cart.total
        for item in cart.items:
            print(f"    - {item.product_name}: ${item.price:.2f} x {item.quantity}")
    
    print(f"\n{'=' * 70}")
    print(f"TOTAL ACROSS ALL PLATFORMS: ${total_across_all:.2f}")
    print("=" * 70)
    
    # STEP 6: Mock payment with Knot API demonstration
    print("\n[STEP 6] MOCK PAYMENT & KNOT API DEMONSTRATION...")
    knot_client = get_knot_client()
    
    print("\nFetching sample transaction data from Knot API...")
    for platform_name in platforms:
        merchant_id = MERCHANT_IDS.get(platform_name)
        if merchant_id:
            print(f"\n{platform_name.upper()} Transaction Sample:")
            txn_data = knot_client.sync_transactions(
                merchant_id=merchant_id,
                external_user_id="demo_user",
                limit=1
            )
            
            if txn_data.get("transactions"):
                txn = txn_data["transactions"][0]
                print(f"  Transaction ID: {txn.get('id')}")
                
                # Calculate amount if not provided by API
                amount = txn.get('amount')
                if amount is None:
                    # Calculate from items
                    amount = sum(
                        item.get('price', 0) * item.get('quantity', 1) 
                        for item in txn.get('items', [])
                    )
                
                print(f"  Amount: ${amount:.2f}")
                print(f"  SKU Items: {len(txn.get('items', []))}")
                for item in txn.get("items", []):
                    print(f"    - {item.get('name')} (SKU: {item.get('sku')})")
    
    print("\n" + "=" * 70)
    print("[SUCCESS] WORKFLOW COMPLETE")
    print("=" * 70)
    print("\nCart state saved to: data/cart_state.json")

if __name__ == "__main__":
    asyncio.run(main())

