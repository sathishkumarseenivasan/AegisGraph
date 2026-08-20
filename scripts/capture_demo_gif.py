#!/usr/bin/env python3
"""
AegisGraph Demo GIF Capture Script

Automated capture of AegisGraph dashboard demo flow using Playwright.
Records navigation through Map, Anomalies, Graph, and Analyst views.

Usage:
    python scripts/capture_demo_gif.py --output assets/screenshots/demo-flow.gif

Requirements:
    pip install playwright
    playwright install chromium
"""

import argparse
import time
import os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed.")
    print("Install with: pip install playwright")
    print("Then run: playwright install chromium")
    exit(1)


def capture_demo_flow(output_path: str, base_url: str = "http://localhost:3000"):
    """
    Capture automated demo flow GIF.
    
    Args:
        output_path: Path to save the output GIF
        base_url: Base URL of the running AegisGraph frontend
    """
    
    print("=" * 60)
    print("AegisGraph Demo GIF Capture")
    print("=" * 60)
    print(f"\nTarget URL: {base_url}")
    print(f"Output: {output_path}")
    print("\nStarting browser...")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
            headless=False,  # Set to True for automated runs without UI
            args=[
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Create page with fixed viewport
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        
        # Enable screen emulation for consistent rendering
        page.emulate_media(media="screen")
        
        print("\n📹 Starting capture sequence...\n")
        
        # Navigate to home page (Map view)
        print("1️⃣  Loading Map View...")
        page.goto(base_url, wait_until="networkidle")
        time.sleep(3)  # Wait for map and entities to load
        
        # Simulate map interaction
        print("   → Clicking on anomaly marker...")
        try:
            # Try to click a marker if visible
            markers = page.query_selector_all(".map-marker, .anomaly-marker, [class*='marker']")
            if markers:
                markers[0].click()
                time.sleep(2)
        except Exception:
            pass  # Markers may not be available in test mode
        
        # Navigate to Anomalies page
        print("2️⃣  Navigating to Anomalies Queue...")
        page.click('a[href*="anomalies"], a:has-text("Anomalies"), nav a:nth-child(2)')
        time.sleep(2)
        
        # Scroll through anomalies list
        print("   → Scrolling anomaly list...")
        page.evaluate("window.scrollBy(0, 300)")
        time.sleep(1.5)
        
        # Expand first anomaly detail
        print("   → Expanding anomaly detail...")
        try:
            first_item = page.query_selector("tr:first-child, [class*='anomaly']:first-child, li:first-child")
            if first_item:
                first_item.click()
                time.sleep(2)
        except Exception:
            pass
        
        # Navigate to Graph page
        print("3️⃣  Navigating to Graph Explorer...")
        page.click('a[href*="graph"], a:has-text("Graph"), nav a:nth-child(3)')
        time.sleep(2)
        
        # Simulate graph interaction
        print("   → Dragging graph nodes...")
        try:
            # Try to drag a node if cytoscape is loaded
            page.evaluate("""
                const canvas = document.querySelector('canvas');
                if (canvas) {
                    canvas.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: 400, clientY: 300 }));
                    setTimeout(() => {
                        canvas.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: 450, clientY: 350 }));
                        canvas.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                    }, 500);
                }
            """)
            time.sleep(2)
        except Exception:
            pass
        
        # Navigate to Analyst page
        print("4️⃣  Navigating to AI Analyst...")
        page.click('a[href*="analyst"], a:has-text("Analyst"), nav a:nth-child(4)')
        time.sleep(2)
        
        # Type a query
        print("   → Typing query...")
        try:
            input_field = page.query_selector('input[placeholder*="query"], textarea, [contenteditable]')
            if input_field:
                input_field.fill("Show me recent anomalies")
                time.sleep(1)
                
                # Submit
                submit_btn = page.query_selector('button:has-text("Ask"), button[type="submit"]')
                if submit_btn:
                    submit_btn.click()
                    time.sleep(3)  # Wait for AI response
        except Exception:
            pass
        
        # Navigate to Audit page (optional)
        print("5️⃣  Navigating to Audit Log...")
        page.click('a[href*="audit"], a:has-text("Audit"), nav a:nth-child(5)')
        time.sleep(2)
        
        # Scroll through audit timeline
        print("   → Scrolling audit timeline...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.5)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        
        # Return to home
        print("6️⃣  Returning to Map View...")
        page.click('a[href="/"], a:has-text("Home"), a:has-text("Dashboard"), nav a:first-child')
        time.sleep(2)
        
        print("\n✅ Capture sequence complete!")
        print(f"\nNote: Playwright doesn't directly export GIFs.")
        print(f"To create a GIF from this session:")
        print(f"  1. Use screen recording software during this automated run")
        print(f"  2. Or use browser devtools to record video")
        print(f"  3. Convert video to GIF with ffmpeg:")
        print(f"     ffmpeg -i recording.mp4 -vf 'fps=10,scale=1280:-1' {output_path}")
        
        browser.close()
    
    print("\n" + "=" * 60)
    print("Capture completed successfully!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Capture AegisGraph demo flow GIF"
    )
    parser.add_argument(
        "--output", "-o",
        default="assets/screenshots/demo-flow.gif",
        help="Output GIF path (default: assets/screenshots/demo-flow.gif)"
    )
    parser.add_argument(
        "--url", "-u",
        default="http://localhost:3000",
        help="AegisGraph frontend URL (default: http://localhost:3000)"
    )
    
    args = parser.parse_args()
    
    try:
        capture_demo_flow(args.output, args.url)
    except KeyboardInterrupt:
        print("\n\n⚠️  Capture interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during capture: {e}")
        print("\nMake sure:")
        print("  1. AegisGraph frontend is running at the specified URL")
        print("  2. Playwright is installed: pip install playwright")
        print("  3. Chromium is installed: playwright install chromium")
        exit(1)


if __name__ == "__main__":
    main()
