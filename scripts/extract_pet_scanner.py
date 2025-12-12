#!/usr/bin/env python3
"""Extract full Pet Health Scanner details from IdeaBrowser"""

import asyncio
import json
import aiohttp
from aiohttp import ClientSession

async def extract_pet_scanner():
    """Extract full details of Pet Health Scanner idea"""

    api_url = "http://localhost:11235/crawl"

    params = {
        "urls": ["https://www.ideabrowser.com"],
        "session_id": "pet_scanner_extract",
        "page_timeout": 60000,
        "include_raw_html": True,
    }

    async with ClientSession() as session:
        async with session.post(
            api_url,
            json=params,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                print(f"Error: {response.status}")
                return

            result = await response.json()

            if not result.get("success"):
                print("Crawling failed")
                return

            html = result["results"][0].get("html", "")

            # Find the specific section
            import re

            # Look for the problem statement
            problem_match = re.search(
                r'You brush your teeth every day[^.]*\. [^.]*\.[^.]*\. But your dog[^.]*\.[^.]*\.',
                html,
                re.IGNORECASE
            )

            # Look for the solution/idea
            solution_match = re.search(
                r'Ideal for founders with AI and pet healthcare experience',
                html,
                re.IGNORECASE
            )

            # Look for the market timing
            timing_match = re.search(
                r'The perfect moment for launching a Pet Health Scanner is now[^.]*\.[^.]*\.[^.]*\.',
                html,
                re.IGNORECASE
            )

            # Look for the validation
            validation_match = re.search(
                r'The Pet Health Scanner idea is validated by strong signals of demand[^.]*\.[^.]*\.[^.]*\.[^.]*\.',
                html,
                re.IGNORECASE
            )

            # Look for pricing
            pricing_matches = re.findall(
                r'\$([0-9,]+(?:\.\d{2})?)',
                html
            )

            # Extract all details
            details = {
                "idea_title": "Pet Health Scanner",
                "problem_statement": problem_match.group(0) if problem_match else None,
                "target_audience": "Founders with AI and pet healthcare experience" if solution_match else None,
                "market_timing": timing_match.group(0) if timing_match else None,
                "validation": validation_match.group(0) if validation_match else None,
                "pricing_examples": pricing_matches[:3],  # First 3 price mentions
                "extracted_at": "2025-12-12T11:32:53.616689"
            }

            # Save the complete details
            with open("pet_health_scanner_complete.json", "w", encoding='utf-8') as f:
                json.dump(details, f, indent=2, ensure_ascii=False)

            print("=" * 60)
            print("🐾 PET HEALTH SCANNER - COMPLETE DETAILS")
            print("=" * 60)

            if details.get("problem_statement"):
                print("\n❗ PROBLEM STATEMENT:")
                print(details["problem_statement"])

            if details.get("target_audience"):
                print("\n👥 TARGET AUDIENCE:")
                print(details["target_audience"])

            if details.get("market_timing"):
                print("\n⏰ MARKET TIMING:")
                print(details["market_timing"])

            if details.get("validation"):
                print("\n✅ MARKET VALIDATION:")
                print(details["validation"])

            if details.get("pricing_examples"):
                print("\n💰 PRICING EXAMPLES FOUND:")
                for price in details["pricing_examples"]:
                    print(f"   • ${price}")

            print("\n💾 Complete details saved to: pet_health_scanner_complete.json")

            # Also create a formatted version
            formatted = f"""
PET HEALTH SCANNER - BUSINESS IDEA

PROBLEM:
{details.get('problem_statement', 'N/A')}

TARGET AUDIENCE:
{details.get('target_audience', 'N/A')}

MARKET TIMING:
{details.get('market_timing', 'N/A')}

VALIDATION:
{details.get('validation', 'N/A')}

KEY INSIGHTS:
• Market timing: Pet care spending exceeds $140 billion
• Technology: AI revolutionizing diagnostics
• Convergence: Ideal market demand and technological capability
• Problem: Pet owners face early detection challenges
• Urgency: Emotional frustration drives demand

PRICING REFERENCE:
Examples found on site: ${', $'.join(details.get('pricing_examples', []))}
"""

            with open("pet_health_scanner_formatted.txt", "w", encoding='utf-8') as f:
                f.write(formatted)

            print("\n📄 Formatted report saved to: pet_health_scanner_formatted.txt")

if __name__ == "__main__":
    asyncio.run(extract_pet_scanner())