import os
import sys
import argparse
import asyncio
from dotenv import load_dotenv


def require_env(var_name: str):
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {var_name}")
    return value


async def run_smoke(platform: str, ingredients):
    # Import here to avoid import side-effects before .env load
    from agents.search_order_agent_nova import SearchOrderAgentNova

    agent = SearchOrderAgentNova(platform)
    cart = await agent.search_and_add_all(ingredients)
    print(f"[ASYNC WRAPPER] {platform} items: {len(cart.items)} total=${cart.total:.2f}")
    for item in cart.items:
        print(f"  - {item.ingredient_requested} -> {item.status}")


def main():
    parser = argparse.ArgumentParser(description="Nova async-wrapper smoke test")
    parser.add_argument("-p", "--platform", default="instacart",
                        choices=["instacart", "ubereats", "doordash"])
    parser.add_argument("ingredients", nargs="*", default=["milk"])
    args = parser.parse_args()

    load_dotenv()
    require_env("NOVA_ACT_API_KEY")
    require_env("GEMINI_API_KEY")

    try:
        asyncio.run(run_smoke(args.platform, args.ingredients))
        print("[ASYNC WRAPPER] SUCCESS")
    except Exception as e:
        print("[ASYNC WRAPPER] FAILURE:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()


