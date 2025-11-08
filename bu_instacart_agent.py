# bu_instacart_agent.py
# BrowserUse agent with Gemini; loads GOOGLE_API_KEY from ./.env (no extra deps).
# Uses a LOCAL Chromium (no cloud). Persists login via profile_id.

import asyncio
import os
import sys
from typing import List

# ---- Minimal .env loader (no python-dotenv needed)
def load_env_from_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and (key not in os.environ):
                os.environ[key] = val

load_env_from_file(".env")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "").strip()
if not GOOGLE_API_KEY:
    print(
        "ERROR: GOOGLE_API_KEY not found.\n"
        "Create a .env file alongside this script with:\n"
        "  GOOGLE_API_KEY=YOUR_GEMINI_KEY\n"
        "Then run:  python bu_instacart_agent.py"
    )
    sys.exit(1)

# ---- BrowserUse imports (requires: pip install browser-use ; then: browser-use install)
from browser_use import Agent, Browser, ChatGoogle

# ========= Configure your run =========
INGREDIENTS: List[str] = ["milk", "eggs", "bread", "{}metalxx"]

class ChatGoogleWithCooldown(ChatGoogle):
    async def ainvoke(self, messages, output_format=None):
        # Enforce a minimal cooldown between Gemini API calls
        await asyncio.sleep(2)
        return await super().ainvoke(messages, output_format)

SYSTEM_POLICY = """
You are a shopping agent operating ONLY on instacart.com and duckduckgo.com.

HARD RULES:
- Never navigate outside allowed domains.
- If a location/store modal appears, press Escape or click Close/X, then continue.
- For each ingredient:
  1) Prefer DuckDuckGo search for "<ingredient> instacart" and open the first instacart.com result;
     if that fails, go directly to https://www.instacart.com/store/search?q=<ingredient>.
  2) On Instacart results: scroll and look for product tiles and their Add/+ controls.
  3) If an Add action is blocked by a modal, close it and retry once.
  4) Decide ONLY one outcome per ingredient:
     - ADDED: first reasonable item added to cart exactly once
     - NO_RESULTS: after thorough scroll & check of empty-state cues
     - FAILED: unexpected error despite retries
- Never stop because of a timeout; always conclude with ADDED / NO_RESULTS / FAILED.
- Produce a final compact report: one line per ingredient with the outcome.
"""

TASK = f"""
{SYSTEM_POLICY}

Ingredients: {", ".join(INGREDIENTS)}

Operational tips:
- Use search terms "<ingredient> instacart" on duckduckgo.com to prefer Instacart.
- If you land on the wrong page, directly open https://www.instacart.com/store/search?q=<ingredient>.
- Dismiss popups using Esc or visible close buttons.
- Verify there are results before concluding NO_RESULTS (look for product grid or empty-state messages).
"""

async def main():
    # Explicitly ensure no cloud key is set (prevents cloud browser attempts)
    os.environ.pop('BROWSER_USE_API_KEY', None)
    
    browser = Browser(
        headless=False,
        disable_security=True,  # Helps with some site interactions
        use_cloud=False,        # Force LOCAL browser
        user_data_dir="./user_data/instacart",  # Persist session (Instacart login, cookies, etc.)
    )

    # Use Gemini (via ChatGoogle). You already loaded GOOGLE_API_KEY above.
    llm = ChatGoogleWithCooldown(
        model="gemini-2.5-flash",
        # Add safer retry/backoff, including 429 handling
        max_retries=4,
        retry_delay=6,
        retryable_status_codes=[403, 429, 503],
    ) 

    agent = Agent(
        task=TASK, 
        llm=llm, 
        browser=browser,
        allowed_domains=["instacart.com", "duckduckgo.com"],  # Domain restrictions on Agent
    )
    history = await agent.run()

    print("\n==== AGENT RUN LOG ====\n")
    try:
        print(history.to_markdown())
    except Exception:
        print(history)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ModuleNotFoundError as e:
        if "browser_use" in str(e):
            print(
                "Missing dependency: browser-use\n"
                "Install and set up:\n"
                "  pip install browser-use\n"
                "  browser-use install   # downloads local Chromium\n"
                "Then run again: python bu_instacart_agent.py"
            )
        else:
            raise
