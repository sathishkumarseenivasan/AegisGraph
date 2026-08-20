#!/usr/bin/env python3
"""
Export Mermaid diagrams to SVG/PNG.

Requires: @mermaid-js/mermaid-cli (mmdc)

Usage:
    python scripts/export_diagrams.py [--output assets/diagrams/]
    
If mmdc is not available, prints instructions for installation.
"""

import subprocess
import sys
from pathlib import Path


def find_mmdc():
    """Check if mermaid-cli is installed."""
    try:
        result = subprocess.run(
            ["mmdc", "--version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def export_diagram(input_path: Path, output_dir: Path, format: str = "svg"):
    """Export a single diagram."""
    output_path = output_dir / f"{input_path.stem}.{format}"
    
    cmd = [
        "mmdc",
        "-i", str(input_path),
        "-o", str(output_path),
        "-b", "transparent"  # Transparent background
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✓ Exported: {output_path.name}")
            return True
        else:
            print(f"✗ Failed: {input_path.name}")
            print(f"  Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout: {input_path.name}")
        return False
    except Exception as e:
        print(f"✗ Error: {input_path.name} - {e}")
        return False


def main():
    # Check for mmdc
    if not find_mmdc():
        print("=" * 60)
        print("Mermaid CLI (mmdc) not found.")
        print()
        print("To install:")
        print("  npm install -g @mermaid-js/mermaid-cli")
        print()
        print("Or with yarn:")
        print("  yarn global add @mermaid-js/mermaid-cli")
        print()
        print("After installation, run this script again.")
        print("=" * 60)
        
        # Provide fallback: just list the .mmd files
        print("\nAvailable diagrams (.mmd source files):")
        diagrams_dir = Path(__file__).parent.parent / "assets" / "diagrams"
        if diagrams_dir.exists():
            for f in sorted(diagrams_dir.glob("*.mmd")):
                print(f"  - {f.name}")
        sys.exit(0)
    
    # Find all .mmd files
    diagrams_dir = Path(__file__).parent.parent / "assets" / "diagrams"
    output_dir = diagrams_dir  # Export to same directory
    
    if not diagrams_dir.exists():
        print(f"Error: Diagrams directory not found: {diagrams_dir}")
        sys.exit(1)
    
    mmd_files = sorted(diagrams_dir.glob("*.mmd"))
    
    if not mmd_files:
        print("No .mmd files found.")
        sys.exit(0)
    
    print(f"Found {len(mmd_files)} diagram(s)")
    print()
    
    # Export each diagram
    success_count = 0
    for mmd_file in mmd_files:
        if export_diagram(mmd_file, output_dir, "svg"):
            success_count += 1
    
    print()
    print(f"Exported {success_count}/{len(mmd_files)} diagrams")
    
    if success_count < len(mmd_files):
        print("\nSome exports failed. Check error messages above.")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
