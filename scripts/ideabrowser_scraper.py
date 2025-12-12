#!/usr/bin/env python3
"""
IdeaBrowser Scraper using Crawl4AI Docker container
Scrapes ideas from https://www.ideabrowser.com/ with authentication
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

class IdeaBrowserScraper:
    def __init__(self):
        self.base_url = "https://www.ideabrowser.com"
        self.login_url = f"{self.base_url}/login"
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
            "page_timeout": kwargs.get("page_timeout", 60000),
            "screenshot": kwargs.get("screenshot", False),
            "include_raw_html": True,
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

            # Return first result (we're only crawling one URL)
            return result["results"][0] if result.get("results") else {}

    async def scrape_with_docker(self, session: ClientSession) -> Dict:
        """Use Crawl4AI Docker REST API to scrape with authentication"""

        print("🔐 Logging into IdeaBrowser...")

        # Step 1: Login
        try:
            # First, try to find the login page
            login_result = await self.crawl_with_session(
                session,
                self.login_url,
                session_id="ideabrowser_login",
                page_timeout=60000,
                screenshot=True
            )

            if not login_result.get("html"):
                raise Exception("Failed to load login page")

            print("✅ Login page loaded successfully")

            # Now try to login
            login_js = f"""
                // Look for common login form selectors
                const emailSelectors = [
                    'input[name="email"]',
                    'input[type="email"]',
                    '#email',
                    '.email-input',
                    'input[placeholder*="email" i]',
                    'input[placeholder*="Email" i]'
                ];

                const passwordSelectors = [
                    'input[name="password"]',
                    'input[type="password"]',
                    '#password',
                    '.password-input',
                    'input[placeholder*="password" i]',
                    'input[placeholder*="Password" i]'
                ];

                const submitSelectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    '.login-btn',
                    '.signin-btn',
                    '#login',
                    '#signin',
                    'button:contains("Login")',
                    'button:contains("Sign in")',
                    'button:contains("Log in")'
                ];

                // Fill email
                let emailField = null;
                for (let selector of emailSelectors) {{
                    emailField = document.querySelector(selector);
                    if (emailField) {{
                        emailField.value = '{self.credentials["email"]}';
                        console.log('Email filled using selector:', selector);
                        break;
                    }}
                }}

                // Fill password
                let passwordField = null;
                for (let selector of passwordSelectors) {{
                    passwordField = document.querySelector(selector);
                    if (passwordField) {{
                        passwordField.value = '{self.credentials["password"]}';
                        console.log('Password filled using selector:', selector);
                        break;
                    }}
                }}

                // Submit form
                let submitButton = null;
                for (let selector of submitSelectors) {{
                    try {{
                        submitButton = document.querySelector(selector);
                        if (submitButton) {{
                            console.log('Submit button found:', selector);
                            submitButton.click();
                            break;
                        }}
                    }} catch(e) {{
                        // Some selectors might fail
                    }}
                }}

                // Fallback: submit the form directly
                if (!submitButton && emailField && passwordField) {{
                    const form = emailField.closest('form') || passwordField.closest('form');
                    if (form) {{
                        console.log('Submitting form directly');
                        form.submit();
                    }}
                }}

                // Return debugging info
                return {{
                    emailFound: !!emailField,
                    passwordFound: !!passwordField,
                    submitFound: !!submitButton,
                    emailSelector: emailField ? emailField.tagName + (emailField.name ? '[name=' + emailField.name + ']' : '') : null,
                    passwordSelector: passwordField ? passwordField.tagName + (passwordField.name ? '[name=' + passwordField.name + ']' : '') : null
                }};
            """

            # Attempt login
            login_attempt = await self.crawl_with_session(
                session,
                self.login_url,
                session_id="ideabrowser_session",
                js_code=login_js,
                page_timeout=60000,
                wait_for="js:document.querySelector('.dashboard, .main-content, .user-menu, .logout, [href*=\"logout\"], [href*=\"signout\"]') !== null || document.querySelector('.error, .alert, [class*=\"error\"], [class*=\"alert\"]) !== null",
                screenshot=True
            )

            print("✅ Login attempt completed")

            # Check if login was successful
            html = login_attempt.get("html", "")
            if any(indicator in html.lower() for indicator in ["dashboard", "welcome", "logout", "profile", "my account"]):
                print("✅ Login successful!")
            else:
                print("⚠️ Login might have failed. Continuing anyway...")

        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            print("🔄 Continuing without login...")

        # Step 2: Get ideas list
        print("\n📝 Fetching ideas list...")

        try:
            # Try multiple possible URLs for ideas
            ideas_urls = [
                f"{self.base_url}/ideas",
                f"{self.base_url}/browse",
                f"{self.base_url}/explore",
                f"{self.base_url}/discover",
                self.base_url  # fallback to home page
            ]

            ideas_result = None
            for url in ideas_urls:
                try:
                    ideas_result = await self.crawl_with_session(
                        session,
                        url,
                        session_id="ideabrowser_session",
                        page_timeout=60000,
                        wait_for="js:document.querySelector('body') !== null",
                        screenshot=True
                    )

                    if ideas_result.get("html"):
                        print(f"✅ Successfully loaded: {url}")
                        break
                except Exception as e:
                    print(f"⚠️ Failed to load {url}: {str(e)}")
                    continue

            if not ideas_result:
                raise Exception("Failed to load any ideas page")

            # Step 3: Look for idea of the day
            print("\n⭐ Searching for 'Idea of the day'...")

            iotd_urls = [
                f"{self.base_url}/idea-of-the-day",
                f"{self.base_url}/daily-idea",
                f"{self.base_url}/featured",
                f"{self.base_url}/idea/daily"
            ]

            iotd_result = None
            for url in iotd_urls:
                try:
                    iotd_result = await self.crawl_with_session(
                        session,
                        url,
                        session_id="ideabrowser_session",
                        page_timeout=60000,
                        wait_for="js:document.querySelector('body') !== null",
                        screenshot=True
                    )

                    if iotd_result.get("html"):
                        print(f"✅ Successfully loaded: {url}")
                        break
                except Exception as e:
                    print(f"⚠️ Failed to load {url}: {str(e)}")
                    continue

            # If specific URLs don't work, search in the main page
            if not iotd_result and ideas_result:
                print("🔍 Searching for 'Idea of the day' in main page...")
                iotd_result = ideas_result

            return {
                "login": login_attempt if 'login_attempt' in locals() else None,
                "ideas": ideas_result,
                "idea_of_day": iotd_result
            }

        except Exception as e:
            print(f"❌ Error fetching ideas: {str(e)}")
            raise

    def extract_data_from_html(self, html: str, url: str) -> Dict:
        """Extract structured data from HTML content"""

        # Clean HTML
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Extract ideas list
        ideas = []

        # Multiple patterns for idea cards
        idea_patterns = [
            r'<(?:div|article|section)[^>]*(?:idea-card|idea-item|idea-post|startup-idea|business-idea)[^>]*>.*?</(?:div|article|section)>',
            r'<(?:div|article|li)[^>]*class="[^"]*(?:card|item|post)[^"]*"[^>]*>.*?h[2-4][^>]*>.*?</(?:div|article|li)>',
            r'<a[^>]*href="[^"]*(?:idea|startup|business)[^"]*"[^>]*>.*?h[2-4][^>]*>.*?</a>',
        ]

        for pattern in idea_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

            for match in matches[:20]:  # Limit to first 20 matches
                # Extract title
                title_patterns = [
                    r'<h[1-4][^>]*>(.*?)</h[1-4]>',
                    r'<a[^>]*class="[^"]*(?:title|heading)[^"]*"[^>]*>(.*?)</a>',
                    r'<div[^>]*class="[^"]*(?:title|heading)[^"]*"[^>]*>(.*?)</div>',
                ]

                title = None
                for tp in title_patterns:
                    title_match = re.search(tp, match, re.IGNORECASE)
                    if title_match:
                        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                        if len(title) > 10:  # Reasonable title length
                            break

                if not title:
                    continue

                # Extract description
                desc_patterns = [
                    r'<p[^>]*>(.*?)</p>',
                    r'<div[^>]*class="[^"]*(?:description|excerpt|summary|content)[^"]*"[^>]*>(.*?)</div>',
                ]

                description = None
                for dp in desc_patterns:
                    desc_match = re.search(dp, match, re.IGNORECASE)
                    if desc_match:
                        description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
                        if len(description) > 20:  # Reasonable description length
                            break

                # Extract link
                link_match = re.search(r'href="([^"]*)"', match, re.IGNORECASE)
                link = link_match.group(1) if link_match else None

                # Extract category/tag
                category_patterns = [
                    r'<span[^>]*class="[^"]*(?:category|tag|label)[^"]*"[^>]*>(.*?)</span>',
                    r'<div[^>]*class="[^"]*(?:category|tag|label)[^"]*"[^>]*>(.*?)</div>',
                ]

                category = None
                for cp in category_patterns:
                    cat_match = re.search(cp, match, re.IGNORECASE)
                    if cat_match:
                        category = re.sub(r'<[^>]+>', '', cat_match.group(1)).strip()
                        if category:
                            break

                if title and title not in [i.get("title") for i in ideas]:
                    ideas.append({
                        "title": title,
                        "description": description or "No description available",
                        "link": f"{self.base_url}{link}" if link and link.startswith("/") else link,
                        "category": category,
                        "source_url": url
                    })

        # Extract idea of the day
        idea_of_day = None

        # Look for "Idea of the day" or similar patterns
        iotd_patterns = [
            r'<(?:div|section|article)[^>]*(?:idea-of-the-day|idea-of-today|daily-idea|featured-idea|iotd)[^>]*>.*?</(?:div|section|article)>',
            r'<h[1-2][^>]*>(?:Idea of the Day|Idea of Today|Daily Idea|Featured Idea)[^<]*</h[1-2]>.*?(?:</div>|</section>|</article>|$)',
            r'class="[^"]*(?:featured|daily|today)[^"]*"[^>]*>.*?h[1-2][^>]*>.*?Idea.*?</h[1-2]>.*?(?:</div>|</section>|</article>|$)',
        ]

        for pattern in iotd_patterns:
            iotd_match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if iotd_match:
                iotd_html = iotd_match.group(0)

                # Extract title
                title_match = re.search(r'<h[1-2][^>]*>(.*?)</h[1-2]>', iotd_html, re.IGNORECASE)
                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else None

                # Extract all content
                content_parts = []

                # Extract paragraphs
                p_matches = re.findall(r'<p[^>]*>(.*?)</p>', iotd_html, re.IGNORECASE)
                for p in p_matches:
                    clean_p = re.sub(r'<[^>]+>', '', p).strip()
                    if clean_p and len(clean_p) > 20:
                        content_parts.append(clean_p)

                # Extract div content
                div_matches = re.findall(r'<div[^>]*class="[^"]*(?:content|description|details)[^"]*"[^>]*>(.*?)</div>', iotd_html, re.IGNORECASE)
                for div in div_matches:
                    clean_div = re.sub(r'<[^>]+>', '', div).strip()
                    if clean_div and len(clean_div) > 20 and clean_div not in content_parts:
                        content_parts.append(clean_div)

                # Extract metadata
                author_match = re.search(r'(?:author|by|founder|creator)[:\s]*([^<\n]{3,50})', iotd_html, re.IGNORECASE)
                author = author_match.group(1).strip() if author_match else None

                # Extract date
                date_patterns = [
                    r'(?:date|posted|published|created)[:\s]*([^<\n]{8,30})',
                    r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    r'([A-Z][a-z]{2,9}\s+\d{1,2},?\s+\d{4})',
                ]

                date = None
                for dp in date_patterns:
                    date_match = re.search(dp, iotd_html, re.IGNORECASE)
                    if date_match:
                        date = date_match.group(1).strip()
                        break

                # Extract categories/tags
                tags = []
                tag_matches = re.findall(r'<(?:span|a|div)[^>]*class="[^"]*(?:tag|category|label|industry)[^"]*"[^>]*>([^<]{3,30})</(?:span|a|div)>', iotd_html, re.IGNORECASE)
                tags = [tag.strip() for tag in tag_matches if tag.strip() and len(tag.strip()) > 2]

                # Extract problem/solution
                problem_match = re.search(r'(?:problem|challenge|pain point)[^:]*[:\s]*([^<\n]{20,200})', iotd_html, re.IGNORECASE)
                solution_match = re.search(r'(?:solution|answer|fix)[^:]*[:\s]*([^<\n]{20,200})', iotd_html, re.IGNORECASE)

                idea_of_day = {
                    "title": title,
                    "content": "\n\n".join(content_parts[:10]) if content_parts else None,
                    "author": author,
                    "date": date,
                    "tags": tags[:10],  # Limit tags
                    "problem": problem_match.group(1).strip() if problem_match else None,
                    "solution": solution_match.group(1).strip() if solution_match else None,
                    "url": url,
                    "extracted_at": datetime.now().isoformat()
                }

                if title or content_parts:
                    break

        return {
            "ideas": ideas[:50],  # Limit to 50 ideas
            "idea_of_the_day": idea_of_day,
            "total_ideas_found": len(ideas),
            "source_url": url
        }

    async def run(self):
        """Main scraping method"""
        print("=" * 60)
        print("🚀 IdeaBrowser Scraper")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"User: {self.credentials['email']}")
        print("=" * 60)

        async with ClientSession() as session:
            try:
                # Scrape data
                results = await self.scrape_with_docker(session)

                print("\n📊 Extracting structured data...")

                # Process ideas page
                all_ideas = []
                if results.get("ideas") and results["ideas"].get("html"):
                    ideas_data = self.extract_data_from_html(
                        results["ideas"]["html"],
                        results["ideas"].get("url", self.base_url)
                    )
                    all_ideas.extend(ideas_data["ideas"])
                    print(f"✅ Found {ideas_data['total_ideas_found']} ideas on ideas page")

                # Save ideas to file
                if all_ideas:
                    with open("ideas_list.json", "w", encoding='utf-8') as f:
                        json.dump(all_ideas, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 Saved {len(all_ideas)} ideas to ideas_list.json")

                    # Display first few ideas
                    print("\n📌 Sample Ideas:")
                    print("-" * 40)
                    for i, idea in enumerate(all_ideas[:5], 1):
                        print(f"\n{i}. {idea['title']}")
                        if idea.get('category'):
                            print(f"   Category: {idea['category']}")
                        print(f"   {idea['description'][:150]}...")

                # Process idea of the day
                iotd_data = None
                iotd_source = None

                # Check dedicated idea of the day page first
                if results.get("idea_of_day") and results["idea_of_day"].get("html"):
                    iotd_data = self.extract_data_from_html(
                        results["idea_of_day"]["html"],
                        results["idea_of_day"].get("url", "")
                    )
                    iotd_source = results["idea_of_day"].get("url")

                # If not found, check the main ideas page
                if not iotd_data or not iotd_data.get("idea_of_the_day"):
                    if results.get("ideas") and results["ideas"].get("html"):
                        iotd_data = self.extract_data_from_html(
                            results["ideas"]["html"],
                            results["ideas"].get("url", "")
                        )
                        iotd_source = results["ideas"].get("url")

                if iotd_data and iotd_data.get("idea_of_the_day"):
                    iotd = iotd_data["idea_of_the_day"]
                    print(f"\n\n⭐ IDEA OF THE DAY ⭐")
                    print("=" * 60)
                    if iotd.get('title'):
                        print(f"\n📌 Title: {iotd['title']}")
                    if iotd.get('author'):
                        print(f"👤 Author: {iotd['author']}")
                    if iotd.get('date'):
                        print(f"📅 Date: {iotd['date']}")
                    if iotd.get('tags'):
                        print(f"🏷️  Tags: {', '.join(iotd['tags'])}")
                    if iotd.get('problem'):
                        print(f"\n❗ Problem: {iotd['problem'][:300]}...")
                    if iotd.get('solution'):
                        print(f"\n✅ Solution: {iotd['solution'][:300]}...")
                    if iotd.get('content'):
                        print(f"\n📝 Content:\n{iotd['content'][:1000]}...")
                    print(f"\n🔗 Source: {iotd.get('url', iotd_source)}")
                    print(f"⏰ Extracted at: {iotd.get('extracted_at')}")

                    # Save idea of the day to file
                    with open("idea_of_the_day.json", "w", encoding='utf-8') as f:
                        json.dump(iotd, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 Saved idea of the day to idea_of_the_day.json")
                else:
                    print("\n⚠️ Idea of the day not found")
                    print("   (It might require authentication or be on a different page)")

                # Save screenshots if available
                for name, result in results.items():
                    if result and result.get("screenshot_path"):
                        print(f"\n📸 Screenshot saved for {name}: {result['screenshot_path']}")

                print("\n" + "=" * 60)
                print("✅ Scraping completed successfully!")
                print("=" * 60)

                # Summary
                print(f"\n📈 Summary:")
                print(f"   • Total ideas found: {len(all_ideas)}")
                print(f"   • Idea of the day: {'✅ Found' if iotd_data and iotd_data.get('idea_of_the_day') else '❌ Not found'}")
                print(f"   • Files created: ideas_list.json, idea_of_the_day.json")

            except Exception as e:
                print(f"\n❌ Error during scraping: {str(e)}")
                import traceback
                traceback.print_exc()


async def main():
    scraper = IdeaBrowserScraper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())