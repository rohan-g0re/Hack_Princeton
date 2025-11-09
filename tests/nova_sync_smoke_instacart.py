import os
import sys
from dotenv import load_dotenv
from nova_act import NovaAct


def require_env(var_name: str):
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {var_name}")
    return value


def main():
    # Load .env and ensure required keys exist
    load_dotenv()
    require_env("NOVA_ACT_API_KEY")
    require_env("GEMINI_API_KEY")  # used elsewhere; ensure present for parity

    # Minimal NovaAct smoke on Instacart homepage (SYNC, no asyncio!)
    nova = NovaAct(starting_page="https://www.instacart.com")
    try:
        nova.start()
        result = nova.act(
            "Open the Instacart homepage. If any popups appear, close them. "
            "Confirm page is loaded by returning the page title. Then stop."
            , max_steps=10
        )
        print("[SYNC SMOKE] NovaAct result:", result)
        print("[SYNC SMOKE] SUCCESS")
    except Exception as e:
        print("[SYNC SMOKE] FAILURE:", e)
        sys.exit(1)
    finally:
        try:
            nova.stop()
        except Exception:
            pass


if __name__ == "__main__":
    main()


