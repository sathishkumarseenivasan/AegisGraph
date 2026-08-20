#!/usr/bin/env python3
"""
AegisGraph Logo Generator

Generates SVG logo variants with a shield silhouette built from a node-and-edge graph mesh.
Run this script to regenerate all logo assets with custom configuration.

Usage:
    python scripts/make_logo.py

Configuration:
    Edit the CONFIG dictionary below to customize colors, dimensions, and styling.
"""

import math
import os

# =============================================================================
# CONFIGURATION - Edit these values to regenerate variants
# =============================================================================
CONFIG = {
    # Colors
    "bg_color": "#0B1220",       # Dark navy background
    "line_color": "#22D3EE",     # Cyan lines/nodes (outer/inner rings)
    "core_color": "#F59E0B",     # Amber core cluster
    "text_color": "#FFFFFF",     # White wordmark
    
    # Dimensions
    "viewbox_full": "0 0 512 640",  # Full lockup (emblem + wordmark)
    "viewbox_mark": "0 0 512 512",  # Emblem only
    "viewbox_favicon": "0 0 64 64", # Simplified for small sizes
    
    # Node styling
    "outer_node_radius": 6,
    "inner_node_radius": 5,
    "core_node_radius": 8,
    "core_small_radius": 3,
    "stroke_width": 2.5,
    "cross_brace_width": 1.5,
    
    # Text styling
    "font_family": "Inter, ui-sans-serif, system-ui, sans-serif",
    "font_size": 48,
    "letter_spacing": 8,
    "text_y_position": 580,  # Y position for wordmark in full lockup
    
    # Effects
    "glow_blur": 3,          # Gaussian blur for node glow (set to 0 for no glow)
    "glow_opacity": 0.4,
    
    # Output paths
    "output_dir": "assets",
}

# Light theme variant config (uncomment to use)
# CONFIG_LIGHT = {
#     "bg_color": "#FFFFFF",
#     "line_color": "#0891B2",
#     "core_color": "#D97706",
#     "text_color": "#0B1220",
# }

# Monochrome variant config (uncomment to use)
# CONFIG_MONO = {
#     "bg_color": "#FFFFFF",
#     "line_color": "#000000",
#     "core_color": "#000000",
#     "text_color": "#000000",
# }


def generate_shield_points(cx: float, cy: float, width: float, height: float, n: int) -> list:
    """
    Generate n points along a shield-shaped path.
    Shield: broad rounded top, straight sides, pointed bottom.
    """
    points = []
    
    # Shield parametric definition
    top_width = width * 0.9
    mid_width = width * 0.7
    bottom_point = height * 0.95
    
    for i in range(n):
        t = i / n * 2 * math.pi
        
        # Custom shield shape interpolation
        if t < math.pi:  # Top half (rounded)
            x = cx + (top_width / 2) * math.cos(t)
            y = cy - (height * 0.3) + (height * 0.35) * math.sin(t)
        else:  # Bottom half (pointed)
            progress = (t - math.pi) / math.pi  # 0 to 1
            x = cx + (mid_width / 2) * math.cos(t) * (1 - progress)
            y = cy + (height * 0.35) + (bottom_point - cy - height * 0.35) * progress
    
        points.append((x, y))
    
    return points


def generate_inner_points(cx: float, cy: float, width: float, height: float, n: int) -> list:
    """Generate inner ring points (smaller shield shape)."""
    scale = 0.55
    return generate_shield_points(cx, cy, width * scale, height * scale, n)


def generate_core_points(cx: float, cy: float, radius: float, n: int) -> list:
    """Generate circular core points."""
    points = []
    for i in range(n):
        angle = i / n * 2 * math.pi - math.pi / 2  # Start from top
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))
    return points


def create_svg_header(viewbox: str, width: str = None, height: str = None) -> str:
    """Create SVG header with definitions."""
    attrs = [f'xmlns="http://www.w3.org/2000/svg"', f'viewBox="{viewbox}"']
    if width:
        attrs.append(f'width="{width}"')
    if height:
        attrs.append(f'height="{height}"')
    
    svg_start = f'<svg {" ".join(attrs)}>\n'
    
    # Add glow filter
    if CONFIG["glow_blur"] > 0:
        svg_start += f'''  <defs>
    <filter id="nodeGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="{CONFIG["glow_blur"]}" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="noGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="0"/>
    </filter>
  </defs>
'''
    else:
        svg_start += '''  <defs>
    <filter id="noGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="0"/>
    </filter>
  </defs>
'''
    
    return svg_start


def generate_emblem(cx: float, cy: float, width: float, height: float, 
                    include_glow: bool = True, simplified: bool = False) -> str:
    """Generate the emblem (shield graph) SVG content."""
    
    svg_content = ""
    
    # Background rectangle (only for full viewboxes)
    if not simplified:
        svg_content += f'  <rect width="100%" height="100%" fill="{CONFIG["bg_color"]}"/>\n\n'
    
    # Calculate node positions
    n_outer = 10 if not simplified else 8
    n_inner = 8 if not simplified else 6
    n_core = 8 if not simplified else 6
    
    outer_nodes = generate_shield_points(cx, cy, width, height, n_outer)
    inner_nodes = generate_inner_points(cx, cy, width, height, n_inner)
    core_nodes = generate_core_points(cx, cy, 25 if not simplified else 15, n_core)
    center = (cx, cy)
    
    # Determine stroke widths for simplified version
    sw = CONFIG["stroke_width"] if not simplified else 1.5
    cbw = CONFIG["cross_brace_width"] if not simplified else 1
    onr = CONFIG["outer_node_radius"] if not simplified else 3
    inr = CONFIG["inner_node_radius"] if not simplified else 2
    cnr = CONFIG["core_node_radius"] if not simplified else 4
    csr = CONFIG["core_small_radius"] if not simplified else 1.5
    
    # Draw cross-bracing lines (back)
    svg_content += '  <!-- Cross-bracing lines -->\n'
    for i, (ox, oy) in enumerate(outer_nodes):
        # Connect to opposite or nearby nodes for bracing
        target_idx = (i + n_outer // 2) % n_outer
        tx, ty = outer_nodes[target_idx]
        svg_content += f'  <line x1="{ox:.2f}" y1="{oy:.2f}" x2="{tx:.2f}" y2="{ty:.2f}" '
        svg_content += f'stroke="{CONFIG["line_color"]}" stroke-width="{cbw}" '
        svg_content += f'opacity="0.3" />\n'
    
    # Connect outer to inner
    svg_content += '\n  <!-- Outer to inner connections -->\n'
    for i, (ox, oy) in enumerate(outer_nodes):
        inner_idx = i % len(inner_nodes)
        ix, iy = inner_nodes[inner_idx]
        svg_content += f'  <line x1="{ox:.2f}" y1="{oy:.2f}" x2="{ix:.2f}" y2="{iy:.2f}" '
        svg_content += f'stroke="{CONFIG["line_color"]}" stroke-width="{sw}" '
        svg_content += f'opacity="0.5" />\n'
    
    # Connect inner to core
    svg_content += '\n  <!-- Inner to core connections -->\n'
    for i, (ix, iy) in enumerate(inner_nodes):
        core_idx = i % len(core_nodes)
        cx_node, cy_node = core_nodes[core_idx]
        svg_content += f'  <line x1="{ix:.2f}" y1="{iy:.2f}" x2="{cx_node:.2f}" y2="{cy_node:.2f}" '
        svg_content += f'stroke="{CONFIG["line_color"]}" stroke-width="{sw}" '
        svg_content += f'opacity="0.6" />\n'
    
    # Connect core nodes to center
    svg_content += '\n  <!-- Core to center connections -->\n'
    for cx_node, cy_node in core_nodes:
        svg_content += f'  <line x1="{cx_node:.2f}" y1="{cy_node:.2f}" x2="{center[0]:.2f}" y2="{center[1]:.2f}" '
        svg_content += f'stroke="{CONFIG["core_color"]}" stroke-width="{sw}" '
        svg_content += f'opacity="0.8" />\n'
    
    # Interconnect core nodes (ring)
    svg_content += '\n  <!-- Core interconnections -->\n'
    for i in range(len(core_nodes)):
        next_i = (i + 1) % len(core_nodes)
        x1, y1 = core_nodes[i]
        x2, y2 = core_nodes[next_i]
        svg_content += f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        svg_content += f'stroke="{CONFIG["core_color"]}" stroke-width="{sw}" '
        svg_content += f'opacity="0.7" />\n'
    
    # Draw outer ring edges
    svg_content += '\n  <!-- Outer ring edges -->\n'
    for i in range(len(outer_nodes)):
        next_i = (i + 1) % len(outer_nodes)
        x1, y1 = outer_nodes[i]
        x2, y2 = outer_nodes[next_i]
        svg_content += f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        svg_content += f'stroke="{CONFIG["line_color"]}" stroke-width="{sw}" />\n'
    
    # Draw inner ring edges
    svg_content += '\n  <!-- Inner ring edges -->\n'
    for i in range(len(inner_nodes)):
        next_i = (i + 1) % len(inner_nodes)
        x1, y1 = inner_nodes[i]
        x2, y2 = inner_nodes[next_i]
        svg_content += f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        svg_content += f'stroke="{CONFIG["line_color"]}" stroke-width="{sw}" opacity="0.7" />\n'
    
    # Draw nodes with glow effect
    glow_filter = 'filter="url(#nodeGlow)"' if include_glow else 'filter="url(#noGlow)"'
    
    # Outer nodes
    svg_content += f'\n  <!-- Outer nodes -->\n'
    for ox, oy in outer_nodes:
        svg_content += f'  <circle cx="{ox:.2f}" cy="{oy:.2f}" r="{onr}" '
        svg_content += f'fill="{CONFIG["line_color"]}" {glow_filter} />\n'
    
    # Inner nodes
    svg_content += f'\n  <!-- Inner nodes -->\n'
    for ix, iy in inner_nodes:
        svg_content += f'  <circle cx="{ix:.2f}" cy="{iy:.2f}" r="{inr}" '
        svg_content += f'fill="{CONFIG["line_color"]}" {glow_filter} opacity="0.9" />\n'
    
    # Core nodes (amber)
    svg_content += f'\n  <!-- Core nodes -->\n'
    for cx_node, cy_node in core_nodes:
        svg_content += f'  <circle cx="{cx_node:.2f}" cy="{cy_node:.2f}" r="{csr}" '
        svg_content += f'fill="{CONFIG["core_color"]}" {glow_filter} />\n'
    
    # Center node (larger amber)
    svg_content += f'\n  <!-- Center node -->\n'
    svg_content += f'  <circle cx="{center[0]:.2f}" cy="{center[1]:.2f}" r="{cnr}" '
    svg_content += f'fill="{CONFIG["core_color"]}" {glow_filter} />\n'
    
    return svg_content


def generate_wordmark() -> str:
    """Generate the AEGISGRAPH wordmark."""
    return f'''
  <!-- Wordmark -->
  <text x="50%" y="{CONFIG["text_y_position"]}" 
        font-family="{CONFIG["font_family"]}" 
        font-size="{CONFIG["font_size"]}" 
        font-weight="700"
        fill="{CONFIG["text_color"]}" 
        text-anchor="middle"
        letter-spacing="{CONFIG["letter_spacing"]}">
    AEGISGRAPH
  </text>
'''


def generate_full_lockup() -> str:
    """Generate full logo lockup (emblem + wordmark)."""
    svg = create_svg_header(CONFIG["viewbox_full"])
    svg += generate_emblem(256, 256, 400, 400, include_glow=True, simplified=False)
    svg += generate_wordmark()
    svg += '</svg>\n'
    return svg


def generate_emblem_only() -> str:
    """Generate emblem-only mark."""
    svg = create_svg_header(CONFIG["viewbox_mark"])
    svg += generate_emblem(256, 256, 450, 450, include_glow=True, simplified=False)
    svg += '</svg>\n'
    return svg


def generate_favicon() -> str:
    """Generate simplified favicon (no glow, fewer nodes)."""
    svg = create_svg_header(CONFIG["viewbox_favicon"], "64", "64")
    svg += generate_emblem(32, 32, 56, 56, include_glow=False, simplified=True)
    svg += '</svg>\n'
    return svg


def save_file(filename: str, content: str):
    """Save content to file."""
    filepath = os.path.join(CONFIG["output_dir"], filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Generated: {filepath}")


def main():
    """Generate all logo variants."""
    print("=" * 60)
    print("AegisGraph Logo Generator")
    print("=" * 60)
    print(f"\nUsing configuration:")
    print(f"  Background: {CONFIG['bg_color']}")
    print(f"  Line Color: {CONFIG['line_color']}")
    print(f"  Core Color: {CONFIG['core_color']}")
    print(f"  Text Color: {CONFIG['text_color']}")
    print(f"  Glow Blur:  {CONFIG['glow_blur']}")
    print()
    
    # Generate all variants
    save_file("logo.svg", generate_full_lockup())
    save_file("logo-mark.svg", generate_emblem_only())
    save_file("favicon.svg", generate_favicon())
    
    print("\n✓ All logos generated successfully!")
    print("\nTo regenerate with different themes, modify CONFIG and re-run:")
    print("  Light theme: Uncomment CONFIG_LIGHT and replace CONFIG at end of script")
    print("  Monochrome:  Uncomment CONFIG_MONO and replace CONFIG at end of script")
    print("\nCommands:")
    print("  python scripts/make_logo.py              # Regenerate with current config")
    print("  # For light theme, edit CONFIG then run again")
    print("  # For monochrome, edit CONFIG then run again")


if __name__ == "__main__":
    main()
