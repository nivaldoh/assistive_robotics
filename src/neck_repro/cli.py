from pathlib import Path
import argparse
import json
import webbrowser

from .experiment import run
from .plotting import render
from .sources import fetch


def main():
    parser = argparse.ArgumentParser(description="Abbott 2024 Figure 2 reproduction")
    parser.add_argument("command", choices=["fetch", "reproduce", "explore", "inspect"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--config", default="configs/figure2.json")
    args = parser.parse_args()
    root = args.root.resolve()
    config = json.loads((root / args.config).read_text())
    out = root / config["output_directory"]
    if args.command == "fetch":
        fetch(root)
        print("Original files cached and SHA-256 verified.")
    elif args.command == "reproduce":
        result = run(root, args.config)
        render(root, result)
        print(f"75 tasks solved. Results: {out.relative_to(root)}")
        print(json.dumps(result["validation"], indent=2))
        print(f"Figure 2 digitization RMSE: {result['reference_comparison']['rmse_N']:.3f} N")
    elif args.command == "explore":
        path = out / "explorer.html"
        if not path.exists():
            parser.error("Run uv run neck-repro reproduce first")
        print(path)
        webbrowser.open(path.as_uri())
    else:
        from .model import load_model
        print(json.dumps(load_model(root, config).source_audit, indent=2))


if __name__ == "__main__":
    main()
