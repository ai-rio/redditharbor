#!/usr/bin/env python3
"""
Get Real Search Volume Data from DataForSEO
Uses the Keyword Data API to get actual monthly search volumes
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv('.env.local')

login = os.getenv('DATAFORSEO_LOGIN')
password = os.getenv('DATAFORSEO_PASSWORD')
base_url = 'https://api.dataforseo.com'

# Keywords grouped by positioning angle
research_data = {
    "angle_1_function_count": {
        "name": "Pre-filtered 1-3 Function Ideas",
        "keywords": [
            "1-3 function app ideas",
            "minimal feature app",
            "scope constrained projects",
            "simple profitable apps",
            "lean side project ideas"
        ]
    },
    "angle_2_reddit_validation": {
        "name": "Real Reddit Problems Turned Into Opportunities",
        "keywords": [
            "reddit ideas for building",
            "reddit project ideas",
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
            "side hustle ideas",
            "make money online ideas",
            "side project income"
        ]
    },
    "angle_4_speed_to_market": {
        "name": "Find Ideas That Launch In 6 Weeks",
        "keywords": [
            "quick launch ideas",
            "fast MVP ideas",
            "rapid prototyping ideas",
            "quick side project ideas",
            "fast startup ideas"
        ]
    }
}

def get_search_volume(keywords):
    """Get search volume for keywords from DataForSEO"""
    endpoint = f"{base_url}/v3/keywords_data/google/search_volume/task_post"

    payload = [{
        "keywords": keywords,
        "location_code": 2840  # United States
    }]

    try:
        response = requests.post(
            endpoint,
            json=payload,
            auth=(login, password),
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            return None

        data = response.json()

        if data.get('status_code') != 20000:
            print(f"API Error: {data.get('status_message')}")
            return None

        # Return the task ID for polling
        tasks = data.get('tasks', [])
        if tasks:
            return tasks[0].get('id')

        return None

    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def get_task_results(task_id, max_wait=60):
    """Poll for task results"""
    endpoint = f"{base_url}/v3/keywords_data/google/search_volume/task_get/{task_id}"

    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                endpoint,
                auth=(login, password),
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code != 200:
                time.sleep(1)
                continue

            data = response.json()

            if data.get('status_code') != 20000:
                time.sleep(1)
                continue

            tasks = data.get('tasks', [])
            if tasks:
                task = tasks[0]
                result = task.get('result')

                # Check if task is still processing
                if result is None or len(result) == 0:
                    time.sleep(1)
                    continue

                # We have results
                return result[0] if result else None

            time.sleep(1)

        except Exception as e:
            print(f"Exception waiting for results: {str(e)}")
            time.sleep(1)

    return None

def research_all_angles():
    """Research all 4 positioning angles"""

    all_results = {}

    print("=" * 90)
    print("REAL SEARCH VOLUME RESEARCH - DATAFORSEO")
    print("=" * 90)

    for angle_id, angle_data in research_data.items():
        print(f"\n\nRESEARCHING: {angle_data['name']}")
        print("-" * 90)

        keywords = angle_data['keywords']
        print(f"Keywords to research: {len(keywords)}")
        print(f"Submitting task...")

        # Submit task
        task_id = get_search_volume(keywords)

        if not task_id:
            print(f"Failed to submit task")
            all_results[angle_id] = {"error": "Failed to submit task"}
            continue

        print(f"Task ID: {task_id}")
        print(f"Waiting for results (max 60 seconds)...")

        # Wait for results
        result = get_task_results(task_id)

        if not result:
            print(f"No results returned")
            all_results[angle_id] = {"error": "No results returned"}
            continue

        # Parse results
        items = result.get('items', [])

        if not items:
            print(f"No keyword data found")
            all_results[angle_id] = {
                "name": angle_data['name'],
                "keywords_researched": len(keywords),
                "keywords_with_data": 0,
                "total_search_volume": 0,
                "average_search_volume": 0,
                "keywords": []
            }
            continue

        # Process keyword data
        keyword_list = []
        total_volume = 0

        for item in items:
            keyword_entry = {
                "keyword": item.get('keyword'),
                "search_volume": item.get('search_volume', 0),
                "competition": item.get('competition_index', 0),
                "cpc": item.get('cpc', 0)
            }
            keyword_list.append(keyword_entry)
            total_volume += item.get('search_volume', 0)

        # Sort by search volume
        keyword_list.sort(key=lambda x: x['search_volume'], reverse=True)

        avg_volume = total_volume / len(items) if items else 0

        all_results[angle_id] = {
            "name": angle_data['name'],
            "keywords_researched": len(keywords),
            "keywords_with_data": len(items),
            "total_search_volume": total_volume,
            "average_search_volume": avg_volume,
            "top_keywords": keyword_list[:5],
            "all_keywords": keyword_list
        }

        # Print summary
        print(f"\nResults:")
        print(f"  Keywords with data: {len(items)}/{len(keywords)}")
        print(f"  Total monthly searches: {total_volume:,}")
        print(f"  Average per keyword: {avg_volume:,.0f}")

        if keyword_list[:5]:
            print(f"\n  Top 5 keywords:")
            for i, kw in enumerate(keyword_list[:5], 1):
                print(f"    {i}. {kw['keyword']}: {kw['search_volume']:,} searches/month")

    # Save results
    output_file = '/tmp/real_keyword_research_dataforseo.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    # Print rankings
    print("\n\n" + "=" * 90)
    print("FINAL RANKINGS BY SEARCH VOLUME")
    print("=" * 90)

    rankings = []
    for angle_id, data in all_results.items():
        if 'error' not in data:
            rankings.append({
                'angle_id': angle_id,
                'angle': data['name'],
                'total_volume': data['total_search_volume'],
                'avg_volume': data['average_search_volume'],
                'keywords_found': data['keywords_with_data']
            })

    rankings.sort(key=lambda x: x['total_volume'], reverse=True)

    print("\nRanked by total monthly search volume:\n")
    for i, r in enumerate(rankings, 1):
        print(f"{i}. {r['angle']}")
        print(f"   Total: {r['total_volume']:,} searches/month")
        print(f"   Avg: {r['avg_volume']:,.0f} per keyword")
        print(f"   Keywords: {r['keywords_found']}")
        print()

    print(f"\nResults saved to: {output_file}")

    return all_results

if __name__ == "__main__":
    try:
        research_all_angles()
    except KeyboardInterrupt:
        print("\n\nResearch interrupted by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        exit(1)
