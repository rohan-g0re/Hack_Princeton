import sys
import subprocess
from pathlib import Path


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


def run_agent_by_file(script_path: Path, name: str) -> None:
    """
    Run an agent Python script as a separate process.
    """
    print(f"\n[RUNNING] {name} agent ...")
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=True)
        print(f"[DONE] {name} agent exited with code {result.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {name} agent failed with code {e.returncode}")


def main() -> None:
    base_dir = Path(__file__).parent

    # Map platform names to their script paths
    scripts = {
        "instacart": base_dir / "agents" / "search_and_add_agents" / "instacart.py",
        "ubereats": base_dir / "agents" / "search_and_add_agents" / "ubereats.py",
    }

    print("\n=== Platform Selection ===")
    enable_instacart = ask_yes_no("Enable Instacart?")
    enable_ubereats = ask_yes_no("Enable UberEats?")

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
        run_agent_by_file(script_path, platform)


if __name__ == "__main__":
    main()


