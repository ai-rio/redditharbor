#!/usr/bin/env python3
"""
IdeaBrowser Screenshot Scraper
Captures screenshots of the IdeaBrowser site
"""

import asyncio
import json
import base64
import aiohttp
from aiohttp import ClientSession
from datetime import datetime

class IdeaBrowserScreenshotScraper:
    def __init__(self):
        self.base_url = "https://www.ideabrowser.com"
        self.api_url = "http://localhost:11235/crawl"

    async def capture_screenshot(self, session: ClientSession, url: str, filename: str) -> str:
        """Capture screenshot of a page"""

        print(f"📸 Capturing screenshot: {filename}")

        params = {
            "urls": [url],
            "session_id": f"screenshot_{filename}",
            "page_timeout": 90000,
            "screenshot": True,
            "include_raw_html": True,
            "remove_overlay_elements": True,
            "wait_for_selector": "body",
            "delay_before_return_html": 3000,  # Wait 3 seconds for full render
        }

        async with session.post(
            self.api_url,
            json=params,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Crawl4AI API error ({response.status}): {error_text}")

            result = await response.json()

            if not result.get("success"):
                raise Exception(f"Crawling failed: {result.get('error', 'Unknown error')}")

            page_result = result["results"][0] if result.get("results") else {}

            # Save screenshot if available
            if page_result.get("screenshot"):
                screenshot_path = f"{filename}.png"

                # The screenshot might be base64 encoded or a file path
                if isinstance(page_result["screenshot"], str) and page_result["screenshot"].startswith("data:image"):
                    # Base64 encoded image
                    header, data = page_result["screenshot"].split(",", 1)
                    with open(screenshot_path, "wb") as f:
                        f.write(base64.b64decode(data))
                    print(f"✅ Screenshot saved: {screenshot_path}")
                else:
                    # File path or other format
                    print(f"📸 Screenshot info: {page_result['screenshot']}")
                    screenshot_path = page_result["screenshot"]

                return screenshot_path

            return None

    async def run(self):
        """Main execution method"""
        print("=" * 60)
        print("📸 IdeaBrowser Screenshot Scraper")
        print("Capturing screenshots of IdeaBrowser pages")
        print("=" * 60)

        async with ClientSession() as session:
            try:
                # URLs to screenshot
                urls_to_capture = [
                    (self.base_url, "ideabrowser_homepage"),
                    (f"{self.base_url}/ideas", "ideabrowser_ideas_page"),
                    (f"{self.base_url}/idea/pet-health-scanner", "ideabrowser_pet_scanner"),
                ]

                screenshots = []

                for url, filename in urls_to_capture:
                    try:
                        screenshot_path = await self.capture_screenshot(session, url, filename)
                        if screenshot_path:
                            screenshots.append({
                                "url": url,
                                "screenshot": screenshot_path,
                                "timestamp": datetime.now().isoformat()
                            })
                    except Exception as e:
                        print(f"⚠️ Failed to screenshot {url}: {str(e)}")
                        continue

                # Save screenshot info
                if screenshots:
                    with open("ideabrowser_screenshots.json", "w") as f:
                        json.dump(screenshots, f, indent=2)

                    print("\n" + "=" * 60)
                    print("✅ Screenshot capture completed!")
                    print("=" * 60)
                    print(f"\n📸 Screenshots captured: {len(screenshots)}")

                    for info in screenshots:
                        print(f"\n📍 URL: {info['url']}")
                        print(f"   Screenshot: {info['screenshot']}")

                    print("\n💾 Metadata saved to: ideabrowser_screenshots.json")

                    # Try to copy screenshots from container if they're stored there
                    print("\n🔄 Checking for screenshots in Docker container...")
                    await self.copy_screenshots_from_container()

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()

    async def copy_screenshots_from_container(self):
        """Try to copy screenshots from Docker container"""

        import subprocess
        import os

        try:
            # Find recent screenshot files in container
            result = subprocess.run(
                ["docker", "exec", "crawl4ai", "find", "/app", "-name", "*.png", "-type", "f", "-mmin", "-5"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                files = result.stdout.strip().split('\n')
                print(f"\n📁 Found {len(files)} recent screenshots in container")

                for file_path in files:
                    if file_path.strip():
                        # Copy file from container
                        filename = os.path.basename(file_path)
                        copy_result = subprocess.run(
                            ["docker", "cp", f"crawl4ai:{file_path}", f"./{filename}"],
                            capture_output=True
                        )
                        if copy_result.returncode == 0:
                            print(f"   ✅ Copied: {filename}")
                        else:
                            print(f"   ❌ Failed to copy: {filename}")
            else:
                print("\n   No recent PNG files found in container")

        except Exception as e:
            print(f"\n   Error copying from container: {str(e)}")


async def main():
    scraper = IdeaBrowserScreenshotScraper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())