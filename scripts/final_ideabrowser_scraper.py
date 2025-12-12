#!/usr/bin/env python3
"""
Final comprehensive IdeaBrowser scraper with full content extraction and screenshots
"""

import asyncio
import json
import re
from datetime import datetime
import aiohttp
from aiohttp import ClientSession

class FinalIdeaBrowserScraper:
    def __init__(self):
        self.base_url = "https://www.ideabrowser.com"
        self.api_url = "http://localhost:11235/crawl"

    async def crawl_with_details(self, session: ClientSession, url: str, description: str) -> dict:
        """Crawl a page with comprehensive details"""

        print(f"\n🔍 Crawling: {description}")
        print(f"   URL: {url}")

        params = {
            "urls": [url],
            "session_id": f"final_crawl_{description.replace(' ', '_')}",
            "page_timeout": 120000,  # 2 minutes
            "screenshot": True,
            "include_raw_html": True,
            "screenshot_wait_for": 3000,  # Wait 3 seconds before screenshot
            "remove_overlay_elements": True,
            "word_count_threshold": 10,
            "extraction_strategy": "NoExtractionStrategy",
            "css_selector": "body",
            "wait_for": "js:document.readyState === 'complete' && document.body.innerText.length > 500",
        }

        async with session.post(
            self.api_url,
            json=params,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"API error ({response.status}): {error}")

            result = await response.json()

            if not result.get("success"):
                raise Exception(f"Crawling failed: {result.get('error')}")

            page_result = result["results"][0] if result.get("results") else {}

            # Extract key information
            info = {
                "url": url,
                "description": description,
                "status_code": page_result.get("status_code"),
                "success": page_result.get("success"),
                "title": page_result.get("metadata", {}).get("title"),
                "content_length": len(page_result.get("html", "")),
                "text_length": len(page_result.get("markdown", "")),
                "screenshot_path": page_result.get("screenshot"),
                "has_media": bool(page_result.get("media", {}).get("images")),
                "links_found": len(page_result.get("links", {}).get("internal", [])),
                "timestamp": datetime.now().isoformat()
            }

            # Save raw HTML for analysis
            html_file = f"ideabrowser_{description.replace(' ', '_').lower()}_raw.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(page_result.get("html", ""))

            # Save markdown version
            md_file = f"ideabrowser_{description.replace(' ', '_').lower()}.md"
            markdown_content = page_result.get("markdown", "")
            if isinstance(markdown_content, str):
                with open(md_file, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

            print(f"   ✅ Success: {info['success']}")
            print(f"   📄 Content length: {info['content_length']:,} characters")
            print(f"   📝 Text extracted: {info['text_length']:,} characters")
            print(f"   🔗 Links found: {info['links_found']}")
            if info['screenshot_path']:
                print(f"   📸 Screenshot: {info['screenshot_path']}")

            return {
                "info": info,
                "raw_data": page_result
            }

    def extract_comprehensive_content(self, html: str) -> dict:
        """Extract all possible content from HTML"""

        # Clean HTML
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

        extracted = {
            "pet_health_scanner": None,
            "other_ideas": [],
            "navigation_items": [],
            "headings": [],
            "key_phrases": [],
            "pricing_info": []
        }

        # 1. Extract Pet Health Scanner details
        phs_patterns = [
            r'Pet Health Scanner([^<]*(?:problem|solution|ideal|perfect)[^<]*.{0,500})',
            r'You brush your teeth[^.]*\.[^.]*\.[^.]*\. But your dog[^.]*\.[^.]*\.[^.]*',
            r'Ideal for founders with AI and pet healthcare experience',
            r'The perfect moment for launching a Pet Health Scanner[^.]*\.[^.]*\.[^.]*\.'
        ]

        for pattern in phs_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            if matches:
                if not extracted["pet_health_scanner"]:
                    extracted["pet_health_scanner"] = {
                        "title": "Pet Health Scanner",
                        "details": []
                    }
                extracted["pet_health_scanner"]["details"].extend(matches)

        # 2. Extract other idea patterns
        idea_patterns = [
            r'Get ideas for profitable startups[^.]*\.[^.]*\.',
            r'Dive into deep research[^.]*\.[^.]*\.',
            r'Have your own business idea[^.]*\.[^.]*\.'
        ]

        for pattern in idea_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            extracted["other_ideas"].extend(matches)

        # 3. Extract navigation
        nav_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*(?:idea|browse|explore|startup)[^<]*)</a>'
        nav_matches = re.findall(nav_pattern, html, re.IGNORECASE)
        extracted["navigation_items"] = [{"url": url, "text": text} for url, text in nav_matches]

        # 4. Extract headings
        heading_pattern = r'<h([1-6])[^>]*>([^<]+)</h[1-6]>'
        heading_matches = re.findall(heading_pattern, html, re.IGNORECASE)
        extracted["headings"] = [{"level": int(level), "text": text} for level, text in heading_matches]

        # 5. Extract key phrases and pricing
        pricing_pattern = r'\$([0-9,]+(?:\.\d{2})?)'
        extracted["pricing_info"] = re.findall(pricing_pattern, html)

        # Extract important phrases
        important_phrases = [
            r'pet care spending[^.]*\$[0-9,]+ billion',
            r'AI technology[^.]*revolutionizing[^.]*',
            r'strong signals of demand[^.]*',
            r'community interest[^.]*'
        ]

        for phrase_pattern in important_phrases:
            matches = re.findall(phrase_pattern, html, re.IGNORECASE)
            extracted["key_phrases"].extend(matches)

        return extracted

    async def run(self):
        """Main execution method"""
        print("=" * 60)
        print("🚀 FINAL IdeaBrowser Comprehensive Scraper")
        print("Full content extraction with screenshots")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)

        async with ClientSession() as session:
            try:
                # Crawl multiple pages
                crawl_results = []

                urls_to_crawl = [
                    (self.base_url, "Homepage"),
                    (f"{self.base_url}/ideas", "Ideas Page"),
                    (f"{self.base_url}/idea/pet-health-scanner", "Pet Scanner Detail"),
                ]

                for url, description in urls_to_crawl:
                    try:
                        result = await self.crawl_with_details(session, url, description)
                        crawl_results.append(result)
                    except Exception as e:
                        print(f"   ❌ Failed: {str(e)}")
                        continue

                # Process all extracted content
                print("\n" + "=" * 60)
                print("📊 PROCESSING EXTRACTED CONTENT")
                print("=" * 60)

                all_extracted = {
                    "summary": {
                        "pages_crawled": len(crawl_results),
                        "timestamp": datetime.now().isoformat(),
                        "total_screenshots": sum(1 for r in crawl_results if r["info"].get("screenshot_path"))
                    },
                    "pet_health_scanner": None,
                    "all_ideas": [],
                    "navigation_structure": [],
                    "pricing_data": []
                }

                for result in crawl_results:
                    html = result["raw_data"].get("html", "")
                    extracted = self.extract_comprehensive_content(html)

                    # Consolidate Pet Health Scanner info
                    if extracted["pet_health_scanner"]:
                        if not all_extracted["pet_health_scanner"]:
                            all_extracted["pet_health_scanner"] = extracted["pet_health_scanner"]
                        else:
                            # Merge details
                            all_extracted["pet_health_scanner"]["details"].extend(
                                extracted["pet_health_scanner"]["details"]
                            )

                    # Collect other ideas
                    all_extracted["all_ideas"].extend(extracted["other_ideas"])

                    # Collect navigation
                    all_extracted["navigation_structure"].extend(extracted["navigation_items"])

                    # Collect pricing
                    all_extracted["pricing_data"].extend(extracted["pricing_info"])

                # Display results
                print(f"\n📈 Crawling Summary:")
                print(f"   • Pages successfully crawled: {all_extracted['summary']['pages_crawled']}")
                print(f"   • Screenshots captured: {all_extracted['summary']['total_screenshots']}")

                # Display Pet Health Scanner details
                if all_extracted["pet_health_scanner"]:
                    print(f"\n🐾 Pet Health Scanner Details:")
                    print("-" * 40)
                    phs = all_extracted["pet_health_scanner"]
                    for detail in phs["details"][:5]:  # Show first 5 details
                        clean_detail = re.sub(r'<[^>]+>', ' ', detail)
                        clean_detail = re.sub(r'\s+', ' ', clean_detail).strip()
                        if len(clean_detail) > 20:
                            print(f"   • {clean_detail[:200]}...")

                # Display pricing data
                if all_extracted["pricing_data"]:
                    unique_prices = list(set(all_extracted["pricing_data"]))
                    print(f"\n💰 Pricing Information Found:")
                    for price in sorted(unique_prices, key=lambda x: float(x.replace(',', '')), reverse=True)[:5]:
                        print(f"   • ${price}")

                # Save comprehensive report
                report_file = "ideabrowser_comprehensive_report.json"
                with open(report_file, "w", encoding="utf-8") as f:
                    json.dump(all_extracted, f, indent=2, ensure_ascii=False)

                print(f"\n💾 Comprehensive report saved to: {report_file}")

                # Create human-readable summary
                summary_file = "ideabrowser_summary.txt"
                with open(summary_file, "w", encoding="utf-8") as f:
                    f.write("IDEABROWSER SCRAPING SUMMARY\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"URL: {self.base_url}\n\n")

                    if all_extracted["pet_health_scanner"]:
                        f.write("FEATURED IDEA: PET HEALTH SCANNER\n")
                        f.write("-" * 30 + "\n")
                        for detail in all_extracted["pet_health_scanner"]["details"][:3]:
                            clean = re.sub(r'<[^>]+>', ' ', detail)
                            clean = re.sub(r'\s+', ' ', clean).strip()
                            f.write(f"{clean}\n\n")

                    if all_extracted["pricing_data"]:
                        f.write("\nPRICING INSIGHTS:\n")
                        f.write("-" * 20 + "\n")
                        for price in sorted(set(all_extracted["pricing_data"]), key=lambda x: float(x.replace(',', '')), reverse=True):
                            f.write(f"• ${price}\n")

                print(f"   📄 Human-readable summary: {summary_file}")

                # Check for screenshot files
                print("\n📸 Checking for screenshots...")
                import subprocess
                import os

                try:
                    # List recent PNG files
                    result = subprocess.run(
                        ["docker", "exec", "crawl4ai", "find", "/app", "-name", "*.png", "-type", "f", "-mmin", "-2"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if result.stdout.strip():
                        print(f"   Found {len(result.stdout.strip().split())} screenshot(s) in container")

                        # Try to copy them
                        for file_path in result.stdout.strip().split()[:3]:  # Copy up to 3 screenshots
                            if file_path:
                                filename = f"screenshot_{os.path.basename(file_path)}"
                                copy_result = subprocess.run(
                                    ["docker", "cp", f"crawl4ai:{file_path}", f"./{filename}"],
                                    capture_output=True,
                                    timeout=10
                                )
                                if copy_result.returncode == 0:
                                    print(f"   ✅ Copied: {filename}")
                except:
                    print("   Could not access screenshots in container")

                print("\n" + "=" * 60)
                print("✅ Comprehensive scraping completed!")
                print("=" * 60)

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()


async def main():
    scraper = FinalIdeaBrowserScraper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())