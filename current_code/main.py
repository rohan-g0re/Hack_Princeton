import sys
import argparse
import json
import subprocess
from pathlib import Path
from knot_api.mock_response import build_knot_like_from_cart


def ask_yes_no(prompt: str) -> bool:
    """
    Prompt user with a yes/no question until a valid response is given.
    Returns True for yes, False for no.
    """
    while True:
        answer = input(f"{prompt} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer with 'y' or 'n'.")


def run_agent_by_file(script_path: Path, name: str, cwd: Path) -> None:
    """
    Run an agent Python script as a separate process.
    """
    print(f"\n[RUNNING] {name} agent ...")
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=True, cwd=str(cwd))
        print(f"[DONE] {name} agent exited with code {result.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {name} agent failed with code {e.returncode}")


def main() -> None:
    base_dir = Path(__file__).parent.resolve()

    # CLI toggles with interactive fallback
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--instacart", choices=["on", "off"], help="Enable or disable Instacart")
    parser.add_argument("--ubereats", choices=["on", "off"], help="Enable or disable UberEats")
    args = parser.parse_args()

    # Map platform names to their script paths
    scripts = {
        "instacart": base_dir / "agents" / "search_and_add_agents" / "instacart.py",
        "ubereats": base_dir / "agents" / "search_and_add_agents" / "ubereats.py",
    }

    # Step 1: Run Gemini recipe (interactive)
    gemini_script = base_dir / "gemini_recipe.py"
    if gemini_script.exists():
        subprocess.run([sys.executable, str(gemini_script)], check=True, cwd=str(base_dir))

    # Determine toggles (CLI has priority; missing flags fall back to prompts)
    if args.instacart is None:
        enable_instacart = ask_yes_no("Enable Instacart?")
    else:
        enable_instacart = args.instacart == "on"

    if args.ubereats is None:
        enable_ubereats = ask_yes_no("Enable UberEats?")
    else:
        enable_ubereats = args.ubereats == "on"

    selected_platforms = []
    if enable_instacart:
        selected_platforms.append("instacart")
    if enable_ubereats:
        selected_platforms.append("ubereats")

    if not selected_platforms:
        print("No platforms selected. Exiting.")
        return

    # Validate and run selected platforms sequentially
    for platform in selected_platforms:
        script_path = scripts.get(platform)
        if not script_path or not script_path.exists():
            print(f"[ERROR] Script not found for {platform}: {script_path}")
            continue
        run_agent_by_file(script_path, platform, base_dir)

    # Step 3: Build Knot-style JSONs into knot_api_jsons using mock_response
    cart_dir = base_dir / "cart_jsons"
    out_dir = base_dir / "knot_api_jsons"
    out_dir.mkdir(parents=True, exist_ok=True)

    if cart_dir.exists():
        for cart_file in cart_dir.glob("*.json"):
            knot_obj = build_knot_like_from_cart(str(cart_file))
            if not knot_obj:
                continue
            out_path = out_dir / cart_file.name
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(knot_obj, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()