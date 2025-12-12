#!/usr/bin/env python3
"""
IdeaBrowser Scraper v2 - Enhanced version with better content extraction
Uses Crawl4AI Docker container with JavaScript execution
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os
import aiohttp
from aiohttp import ClientSession

class IdeaBrowserScraperV2:
    def __init__(self):
        self.base_url = "https://www.ideabrowser.com"
        self.api_url = "http://localhost:11235/crawl"
        self.credentials = {
            "email": "carlos@apto.rio.br",
            "password": "Luliflora1@"
        }

    async def crawl_with_session(self, session: ClientSession, url: str, **kwargs) -> Dict:
        """Helper to make crawl requests to Docker container"""

        # Default parameters
        params = {
            "urls": [url],
            "session_id": kwargs.get("session_id", "ideabrowser_session"),
            "page_timeout": kwargs.get("page_timeout", 90000),  # Increased timeout
            "screenshot": kwargs.get("screenshot", False),
            "include_raw_html": True,
            "remove_overlay_elements": True,
        }

        # Add optional parameters
        if kwargs.get("js_code"):
            params["js_code"] = kwargs["js_code"]
        if kwargs.get("wait_for"):
            params["wait_for"] = kwargs["wait_for"]
        if kwargs.get("css_selector"):
            params["css_selector"] = kwargs["css_selector"]

        # Make request
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

            # Return first result
            return result["results"][0] if result.get("results") else {}

    async def scrape_ideabrowser(self, session: ClientSession) -> Dict:
        """Main scraping method with login and data extraction"""

        print("🚀 Starting IdeaBrowser scraper v2...")

        # Step 1: Try to login first
        print("\n🔐 Attempting to login...")

        try:
            # Get login page
            login_result = await self.crawl_with_session(
                session,
                f"{self.base_url}/login",
                session_id="ideabrowser_auth",
                page_timeout=60000,
                screenshot=True
            )

            # JavaScript to fill and submit login form
            login_js = f"""
                console.log('Starting login process...');

                // Wait a bit for any dynamic content
                await new Promise(resolve => setTimeout(resolve, 2000));

                // Try multiple login strategies
                const strategies = [
                    // Strategy 1: Standard form
                    () => {{
                        const emailField = document.querySelector('input[name="email"], input[type="email"]');
                        const passwordField = document.querySelector('input[name="password"], input[type="password"]');
                        const submitBtn = document.querySelector('button[type="submit"], input[type="submit"]');

                        if (emailField && passwordField) {{
                            emailField.value = '{self.credentials["email"]}';
                            passwordField.value = '{self.credentials["password"]}';

                            // Trigger change events
                            emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));

                            if (submitBtn) {{
                                submitBtn.click();
                                return true;
                            }}
                        }}
                        return false;
                    }},

                    // Strategy 2: Look for any form with email/password
                    () => {{
                        const forms = document.querySelectorAll('form');
                        for (let form of forms) {{
                            const emailInput = form.querySelector('input[type*="email"]');
                            const passwordInput = form.querySelector('input[type*="password"]');

                            if (emailInput && passwordInput) {{
                                emailInput.value = '{self.credentials["email"]}';
                                passwordInput.value = '{self.credentials["password"]}';

                                form.submit();
                                return true;
                            }}
                        }}
                        return false;
                    }},

                    // Strategy 3: Look for auth buttons or links
                    () => {{
                        const authLinks = document.querySelectorAll('a[href*="login"], a[href*="signin"], button[class*="login"]');
                        if (authLinks.length > 0) {{
                            authLinks[0].click();
                            return true;
                        }}
                        return false;
                    }}
                ];

                // Try strategies
                for (let i = 0; i < strategies.length; i++) {{
                    if (strategies[i]()) {{
                        console.log(`Login strategy ${{i + 1}} executed`);
                        break;
                    }}
                }}

                return {{
                    loginAttempted: true,
                    url: window.location.href
                }};
            """

            # Execute login
            login_attempt = await self.crawl_with_session(
                session,
                f"{self.base_url}/login",
                session_id="ideabrowser_logged_in",
                js_code=login_js,
                page_timeout=90000,
                wait_for="js:document.readyState === 'complete'",
                screenshot=True
            )

            print("✅ Login attempt completed")

        except Exception as e:
            print(f"⚠️ Login step encountered issues: {str(e)}")
            print("🔄 Continuing with public content...")

        # Step 2: Get the main page with enhanced JavaScript execution
        print("\n📄 Loading main page with dynamic content...")

        main_page_js = """
            // Wait for React/Next.js to render
            await new Promise(resolve => setTimeout(resolve, 5000));

            // Try to scroll to trigger lazy loading
            window.scrollTo(0, document.body.scrollHeight / 2);
            await new Promise(resolve => setTimeout(resolve, 2000));
            window.scrollTo(0, 0);
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Click on any "Load more" or "Show more" buttons
            const loadMoreButtons = document.querySelectorAll('button[class*="load"], button[class*="more"], [class*="show-more"]');
            loadMoreButtons.forEach(btn => btn.click());
            await new Promise(resolve => setTimeout(resolve, 3000));

            return {
                title: document.title,
                url: window.location.href,
                contentHeight: document.body.scrollHeight,
                ideaElements: document.querySelectorAll('[class*="idea"], [class*="startup"], [class*="business"]').length,
                allText: document.body.innerText.slice(0, 5000)
            };
        """

        main_result = await self.crawl_with_session(
            session,
            self.base_url,
            session_id="ideabrowser_main",
            js_code=main_page_js,
            page_timeout=120000,  # 2 minutes
            wait_for="js:document.querySelector('body') && document.body.innerText.length > 500",
            screenshot=True
        )

        print("✅ Main page loaded with dynamic content")

        # Step 3: Look for ideas with specific navigation
        print("\n🔍 Searching for ideas section...")

        # Try to find and click on navigation links
        nav_js = """
            // Look for navigation links
            const navLinks = Array.from(document.querySelectorAll('a, button')).filter(el => {
                const text = el.textContent.toLowerCase();
                return text.includes('idea') || text.includes('browse') || text.includes('explore') || text.includes('startup');
            });

            if (navLinks.length > 0) {
                // Click the first relevant link
                navLinks[0].click();
                return { clicked: true, linkText: navLinks[0].textContent };
            }

            return { clicked: false, foundLinks: navLinks.length };
        """

        # Try navigating to ideas section
        try:
            nav_result = await self.crawl_with_session(
                session,
                self.base_url,
                session_id="ideabrowser_ideas",
                js_code=nav_js,
                page_timeout=90000,
                wait_for="js:document.readyState === 'complete'",
                screenshot=True
            )
        except:
            print("⚠️ Navigation attempt failed, using main page content")

        # Step 4: Extract all content with enhanced patterns
        print("\n📊 Extracting content with enhanced patterns...")

        extract_js = """
            // Enhanced content extraction
            const results = {
                ideas: [],
                ideaOfTheDay: null,
                sections: []
            };

            // 1. Look for idea cards with various selectors
            const ideaSelectors = [
                '[class*="idea"]',
                '[class*="startup"]',
                '[class*="business"]',
                '[class*="card"]',
                'article',
                '[data-testid*="idea"]'
            ];

            ideaSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    const text = el.textContent.trim();
                    if (text.length > 50 && text.length < 1000) {
                        const titleEl = el.querySelector('h1, h2, h3, h4, [class*="title"]');
                        const title = titleEl ? titleEl.textContent.trim() : text.slice(0, 100);

                        results.ideas.push({
                            title: title,
                            content: text,
                            element: el.tagName.toLowerCase(),
                            className: el.className
                        });
                    }
                });
            });

            // 2. Look for "Idea of the Day" or featured content
            const iotdSelectors = [
                '*[class*="daily"]',
                '*[class*="featured"]',
                '*[class*="today"]',
                'h1, h2'
            ];

            iotdSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    const text = el.textContent.toLowerCase();
                    if (text.includes('idea') && (text.includes('day') || text.includes('today') || text.includes('featured'))) {
                        const parent = el.closest('div, section, article');
                        if (parent) {
                            results.ideaOfTheDay = {
                                title: el.textContent.trim(),
                                content: parent.textContent.trim().slice(0, 2000),
                                element: parent.tagName.toLowerCase()
                            };
                        }
                    }
                });
            });

            // 3. Extract all section headings
            document.querySelectorAll('h1, h2, h3').forEach(el => {
                results.sections.push({
                    level: parseInt(el.tagName.charAt(1)),
                    text: el.textContent.trim()
                });
            });

            return results;
        """

        # Run extraction on current page
        current_url = nav_result.get("url", self.base_url) if 'nav_result' in locals() else self.base_url

        extract_result = await self.crawl_with_session(
            session,
            current_url,
            session_id="ideabrowser_extract",
            js_code=extract_js,
            page_timeout=60000,
            wait_for="js:document.readyState === 'complete'",
            screenshot=True
        )

        return {
            "main_page": main_result,
            "navigation": nav_result if 'nav_result' in locals() else None,
            "extraction": extract_result,
            "current_url": current_url
        }

    def process_extracted_data(self, extraction_result: Dict) -> Dict:
        """Process and format the extracted data"""

        if not extraction_result or not extraction_result.get("success"):
            return {"ideas": [], "idea_of_the_day": None}

        # Get the data returned from JavaScript
        extracted_data = extraction_result.get("result", {})

        # Process ideas
        ideas = []
        if "ideas" in extracted_data:
            for idea in extracted_data["ideas"]:
                # Clean up the content
                title = idea.get("title", "")[:200]
                content = idea.get("content", "")[:1000]

                # Try to extract more structured info
                lines = content.split('\n')
                description = None

                # Look for description patterns
                for line in lines:
                    if len(line) > 30 and not line.lower().startswith(('http', 'www', '$', '€', '£')):
                        description = line[:300]
                        break

                if title and title not in [i.get("title") for i in ideas]:
                    ideas.append({
                        "title": title,
                        "description": description or content[:200] + "...",
                        "full_content": content,
                        "source": "ideabrowser_extracted"
                    })

        # Process idea of the day
        idea_of_day = None
        if "ideaOfTheDay" in extracted_data and extracted_data["ideaOfTheDay"]:
            iotd = extracted_data["ideaOfTheDay"]

            # Extract additional details
            content = iotd.get("content", "")
            lines = content.split('\n')

            # Try to extract structured info
            details = {
                "title": iotd.get("title", ""),
                "content": content[:2000],
                "extracted_at": datetime.now().isoformat(),
                "lines": lines
            }

            # Look for patterns
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['problem:', 'challenge:', 'pain point']):
                    details["problem"] = line
                elif any(keyword in line.lower() for keyword in ['solution:', 'answer:', 'fix']):
                    details["solution"] = line
                elif any(keyword in line.lower() for keyword in ['market:', 'industry:', 'sector:']):
                    details["market"] = line

            idea_of_day = details

        return {
            "ideas": ideas[:20],  # Limit to 20 ideas
            "idea_of_the_day": idea_of_day,
            "total_found": len(ideas),
            "sections": extracted_data.get("sections", [])
        }

    async def run(self):
        """Main execution method"""
        print("=" * 60)
        print("🚀 IdeaBrowser Scraper v2")
        print("Enhanced with Dynamic Content Extraction")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"User: {self.credentials['email']}")
        print("=" * 60)

        async with ClientSession() as session:
            try:
                # Scrape data
                results = await self.scrape_ideabrowser(session)

                # Process extracted data
                print("\n📊 Processing extracted data...")
                processed_data = self.process_extracted_data(results.get("extraction", {}))

                # Save ideas
                if processed_data.get("ideas"):
                    ideas_file = "ideabrowser_ideas_v2.json"
                    with open(ideas_file, "w", encoding='utf-8') as f:
                        json.dump(processed_data["ideas"], f, indent=2, ensure_ascii=False)

                    print(f"\n💾 Saved {len(processed_data['ideas'])} ideas to {ideas_file}")

                    # Display sample ideas
                    print("\n📌 Sample Ideas Found:")
                    print("-" * 40)
                    for i, idea in enumerate(processed_data["ideas"][:5], 1):
                        print(f"\n{i}. {idea['title']}")
                        print(f"   {idea['description'][:150]}...")

                # Process idea of the day
                if processed_data.get("idea_of_the_day"):
                    iotd = processed_data["idea_of_the_day"]
                    print(f"\n\n⭐ IDEA OF THE DAY ⭐")
                    print("=" * 60)
                    print(f"\n📌 Title: {iotd.get('title', 'N/A')}")

                    if iotd.get('problem'):
                        print(f"\n❗ Problem: {iotd['problem'][:300]}...")

                    if iotd.get('solution'):
                        print(f"\n✅ Solution: {iotd['solution'][:300]}...")

                    if iotd.get('market'):
                        print(f"\n🎯 Market: {iotd['market'][:200]}...")

                    if iotd.get('content'):
                        print(f"\n📝 Content Preview:\n{iotd['content'][:1000]}...")

                    print(f"\n⏰ Extracted at: {iotd.get('extracted_at')}")

                    # Save idea of the day
                    iotd_file = "ideabrowser_idea_of_day_v2.json"
                    with open(iotd_file, "w", encoding='utf-8') as f:
                        json.dump(iotd, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 Saved idea of the day to {iotd_file}")
                else:
                    print("\n⚠️ Idea of the day not found in extracted content")
                    print("   (The site might require authentication or have different structure)")

                # Save screenshots
                for name, result in results.items():
                    if result and isinstance(result, dict) and result.get("screenshot_path"):
                        print(f"\n📸 Screenshot saved: {result['screenshot_path']}")

                print("\n" + "=" * 60)
                print("✅ Scraping completed successfully!")
                print("=" * 60)

                # Summary
                print(f"\n📈 Summary:")
                print(f"   • Ideas extracted: {len(processed_data.get('ideas', []))}")
                print(f"   • Idea of the day: {'✅ Found' if processed_data.get('idea_of_the_day') else '❌ Not found'}")
                print(f"   • Current URL: {results.get('current_url', 'N/A')}")

                if processed_data.get("sections"):
                    print(f"   • Sections found: {len(processed_data['sections'])}")
                    for section in processed_data["sections"][:5]:
                        print(f"     - H{section['level']}: {section['text'][:50]}...")

            except Exception as e:
                print(f"\n❌ Error during scraping: {str(e)}")
                import traceback
                traceback.print_exc()


async def main():
    scraper = IdeaBrowserScraperV2()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())