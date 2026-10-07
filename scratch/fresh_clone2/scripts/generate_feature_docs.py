import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.features.registry import FEATURE_REGISTRY


def main():
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    lines = [
        "# Features Registry",
        "This document is auto-generated. Do not edit directly.",
        "",
        "| Feature Name | Group | Type | Description | Units |",
        "|---|---|---|---|---|"
    ]
    
    for f in FEATURE_REGISTRY:
        lines.append(f"| `{f['name']}` | {f['group']} | {f['dtype']} | {f['desc']} | {f['units']} |")
        
    with open(docs_dir / "FEATURES.md", "w") as f:
        f.write("\n".join(lines) + "\n")
        
    print("Generated docs/FEATURES.md")

if __name__ == "__main__":
    main()
