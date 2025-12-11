#!/usr/bin/env python3
"""
DataForSEO Keyword Research Script
Queries real search volume data for positioning angles
"""

import os
import json
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv('.env.local')

class DataForSEOClient:
    """Client for DataForSEO API"""

    def __init__(self):
        self.login = os.getenv('DATAFORSEO_LOGIN')
        self.password = os.getenv('DATAFORSEO_PASSWORD')
        self.base_url = os.getenv('DATAFORSEO_API_URL', 'https://api.dataforseo.com')
        self.location = os.getenv('DATAFORSEO_LOCATION', 'United States')
        self.language = os.getenv('DATAFORSEO_LANGUAGE', 'English')
        self.min_search_volume = int(os.getenv('DATAFORSEO_MIN_SEARCH_VOLUME', '10'))

        if not self.login or not self.password:
            raise ValueError("DataForSEO credentials not found in .env.local")

    def get_keyword_ideas(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Get keyword ideas and search volume data from DataForSEO

        Args:
            keywords: List of keywords to research

        Returns:
            Dict with keyword data including search volume, competition, CPC
        """
        endpoint = f"{self.base_url}/v3/dataforseo_labs/google/keyword_ideas/live"

        payload = [{
            "keywords": keywords,
            "location_name": self.location,
            "language_name": self.language,
            "filters": [
                ["keyword_info.search_volume", ">", self.min_search_volume]
            ],
            "limit": 100
        }]

        try:
            response = requests.post(
                endpoint,
                json=payload,
                auth=(self.login, self.password),
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('status_code') == 20000:
                    return data
                else:
                    raise Exception(f"API Error: {data.get('status_message')}")
            else:
                raise Exception(f"HTTP Error: {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def extract_keyword_metrics(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract search volume and metrics from API response"""
        results = []

        try:
            tasks = response.get('tasks', [])
            if not tasks:
                return results

            task = tasks[0]
            result = task.get('result', [])

            for item in result:
                keyword_data = item.get('keyword_info', {})
                results.append({
                    'keyword': item.get('keyword'),
                    'search_volume': keyword_data.get('search_volume', 0),
                    'competition': keyword_data.get('competition_index', 0),
                    'cpc': keyword_data.get('cpc', 0),
                    'monthly_searches': keyword_data.get('search_volume', 0)
                })
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error parsing response: {str(e)}")

        return results


def research_positioning_angles():
    """Research all 4 positioning angles with real data"""

    # Keywords for each angle
    angles = {
        "angle_1_function_count": {
            "name": "Pre-filtered 1-3 Function Ideas",
            "keywords": [
                "1-3 function app ideas",
                "minimal feature app",
                "scope constrained projects",
                "focused side projects",
                "simple profitable apps",
                "lean side project ideas"
            ]
        },
        "angle_2_reddit_validation": {
            "name": "Real Reddit Problems Turned Into Opportunities",
            "keywords": [
                "reddit ideas for building",
                "reddit project ideas",
                "validated product ideas",
                "real user problems",
                "reddit startup ideas",
                "reddit side hustle ideas"
            ]
        },
        "angle_3_revenue_focus": {
            "name": "Make $30k/Year With Side Project Ideas",
            "keywords": [
                "$30k year side project",
                "profitable side project ideas",
                "side hustle ideas 2025",
                "make money side projects",
                "passive income app ideas",
                "revenue generating ideas",
                "side hustle ideas",
                "make money online ideas"
            ]
        },
        "angle_4_speed_to_market": {
            "name": "Find Ideas That Launch In 6 Weeks",
            "keywords": [
                "quick launch ideas",
                "fast MVP ideas",
                "6 week project ideas",
                "rapid prototyping ideas",
                "quick side project ideas",
                "fast startup ideas"
            ]
        }
    }

    client = DataForSEOClient()
    results = {}

    print("=" * 80)
    print("DATAFORSEO KEYWORD RESEARCH - REAL SEARCH VOLUME DATA")
    print("=" * 80)

    for angle_id, angle_data in angles.items():
        print(f"\n\nRESEARCHING: {angle_data['name']}")
        print("-" * 80)

        try:
            # Query DataForSEO API
            response = client.get_keyword_ideas(angle_data['keywords'])
            metrics = client.extract_keyword_metrics(response)

            # Sort by search volume
            metrics.sort(key=lambda x: x['search_volume'], reverse=True)

            # Calculate totals
            total_volume = sum(m['search_volume'] for m in metrics)
            avg_volume = total_volume / len(metrics) if metrics else 0

            results[angle_id] = {
                "angle_name": angle_data['name'],
                "keywords_researched": len(angle_data['keywords']),
                "keywords_with_data": len(metrics),
                "total_search_volume": total_volume,
                "average_search_volume": avg_volume,
                "top_keywords": metrics[:5],
                "all_keywords": metrics
            }

            # Print summary
            print(f"Total Search Volume: {total_volume:,} searches/month")
            print(f"Average Volume per Keyword: {avg_volume:,.0f} searches/month")
            print(f"Keywords Found: {len(metrics)} of {len(angle_data['keywords'])} researched")

            if metrics:
                print(f"\nTop 5 Keywords:")
                for i, m in enumerate(metrics[:5], 1):
                    print(f"  {i}. {m['keyword']}: {m['search_volume']:,} searches/month (Competition: {m['competition']:.1f})")

        except Exception as e:
            print(f"❌ Error researching {angle_id}: {str(e)}")
            results[angle_id] = {"error": str(e)}

    # Save results to JSON
    output_file = '/tmp/dataforseo_keyword_research.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n\n" + "=" * 80)
    print("RESEARCH COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {output_file}")

    # Print rankings
    print("\n\nANGLE RANKINGS BY SEARCH VOLUME:")
    print("-" * 80)

    rankings = []
    for angle_id, data in results.items():
        if 'error' not in data:
            rankings.append({
                'angle': data['angle_name'],
                'total_volume': data['total_search_volume'],
                'avg_volume': data['average_search_volume'],
                'keywords_found': data['keywords_with_data']
            })

    rankings.sort(key=lambda x: x['total_volume'], reverse=True)

    for i, r in enumerate(rankings, 1):
        print(f"\n{i}. {r['angle']}")
        print(f"   Total Volume: {r['total_volume']:,} searches/month")
        print(f"   Avg per Keyword: {r['avg_volume']:,.0f} searches/month")
        print(f"   Keywords Found: {r['keywords_found']}")

    return results


if __name__ == "__main__":
    try:
        research_positioning_angles()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        exit(1)
