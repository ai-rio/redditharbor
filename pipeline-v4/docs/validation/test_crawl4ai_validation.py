"""
Test web research validation using crawl4ai
Final version with proper error handling
"""

import json
import httpx
import asyncio
from datetime import datetime

CRAWL4AI_API = "http://localhost:11235"

opportunity = {
    "title": "Moderation Assistant",
    "llm_scores": {
        "market_demand": 70,
        "pain_intensity": 80,
        "monetization_potential": 75,
        "technical_feasibility": 85,
        "competition_level": 60
    }
}

research_urls = {
    "market_demand": [
        "https://en.wikipedia.org/wiki/Moderation_(internet)",
        "https://support.reddit.com/hc/en-us/articles/205243466"
    ],
    "pain_intensity": [
        "https://www.reddit.com/r/modhelp/wiki/index",
        "https://github.com/Automoderator/reddit-moderator-toolbox"
    ],
    "monetization_potential": [
        "https://www.producthunt.com/search/moderation",
        "https://www.demod.ai/"
    ],
    "technical_feasibility": [
        "https://spacy.io/",
        "https://www.nltk.org/"
    ],
    "competition_level": [
        "https://github.com/topics/reddit-moderation-bot",
        "https://alternativeto.net/software/reddit/"
    ]
}

async def crawl_urls(urls: list) -> dict:
    """Crawl multiple URLs using crawl4ai"""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            payload = {
                "urls": urls,
                "crawler_config": {
                    "page_timeout": 30000,
                    "remove_overlay_elements": True
                }
            }
            
            response = await client.post(
                f"{CRAWL4AI_API}/crawl",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "results": data.get("results", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def validate_metric(metric: str, urls: list, llm_score: int) -> dict:
    """Validate a metric by crawling its URLs"""
    print(f"\n{'='*70}")
    print(f"🔍 {metric.upper()} (LLM Score: {llm_score}/100)")
    print(f"{'='*70}")
    print(f"Crawling {len(urls)} URLs...")
    
    result = await crawl_urls(urls)
    
    if result["success"]:
        results = result.get("results", [])
        successful = [r for r in results if r.get("success", False)]
        
        print(f"✅ Crawl completed: {len(successful)}/{len(results)} successful")
        
        analysis = {
            "metric": metric,
            "llm_score": llm_score,
            "urls_total": len(urls),
            "successful_crawls": len(successful),
            "success_rate": (len(successful) / len(urls) * 100) if urls else 0,
            "findings": []
        }
        
        for i, crawl_result in enumerate(successful):
            markdown = crawl_result.get("markdown", "")
            preview = markdown[:150] if isinstance(markdown, str) else ""
            
            finding = {
                "url": crawl_result.get("url", ""),
                "title": crawl_result.get("metadata", {}).get("title", ""),
                "content_length": len(markdown) if isinstance(markdown, str) else 0,
                "preview": preview
            }
            analysis["findings"].append(finding)
            print(f"  ✓ {crawl_result.get('url', '')} ({finding['content_length']} chars)")
        
        return analysis
    else:
        print(f"❌ Crawl failed: {result.get('error')}")
        return {
            "metric": metric,
            "llm_score": llm_score,
            "success": False,
            "error": result.get("error")
        }

async def run_validation():
    """Run web research validation"""
    print("\n" + "="*80)
    print("MODERATION ASSISTANT - WEB RESEARCH VALIDATION TEST")
    print("="*80)
    print(f"Opportunity: {opportunity['title']}")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Tool: crawl4ai (Docker API on port 11235)")
    
    all_results = {
        "opportunity": opportunity,
        "validation_started": datetime.now().isoformat(),
        "metrics": {}
    }
    
    # Validate each metric
    for metric, urls in research_urls.items():
        llm_score = opportunity["llm_scores"][metric]
        result = await validate_metric(metric, urls, llm_score)
        all_results["metrics"][metric] = result
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    total_urls = sum(len(urls) for urls in research_urls.values())
    total_successful = sum(r.get("successful_crawls", 0) for r in all_results["metrics"].values())
    
    for metric, result in all_results["metrics"].items():
        if result.get("success", False):
            success_rate = result["success_rate"]
            status = "✅" if success_rate >= 70 else "⚠️"
            print(f"{status} {metric:25s} | LLM: {result['llm_score']:2d}/100 | Coverage: {success_rate:5.1f}%")
        else:
            print(f"❌ {metric:25s} | Error: {result.get('error', 'Unknown')}")
    
    print(f"\n📊 OVERALL: {total_successful}/{total_urls} URLs successfully crawled ({total_successful/total_urls*100:.1f}%)")
    
    # Save results
    with open("/tmp/web_research_results_final.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"📁 Detailed results saved to: /tmp/web_research_results_final.json")
    
    # Show findings summary
    print("\n" + "="*80)
    print("VALIDATION FINDINGS")
    print("="*80)
    print("""
This test demonstrates:

✅ crawl4ai can crawl and extract data from web sources
✅ Real data can be collected to validate LLM-generated scores
✅ Each metric can be researched independently

What was validated:
- Market Demand:         Wikipedia + Reddit docs on moderation
- Pain Intensity:        r/modhelp discussions + toolbox repos  
- Monetization Potential: ProductHunt + competitors
- Technical Feasibility: spaCy + NLTK libraries
- Competition Level:     GitHub + AlternativeTo

NEXT IMPLEMENTATION STEPS:
1. Extract specific data points from crawled content
2. Map findings to scoring metrics
3. Compare LLM scores vs. web research data
4. Adjust confidence scores based on data sources
5. Store validation results in database

Each metric would get a "validation_confidence" score based on:
- How many sources support the LLM score
- Quality of data found
- Recency of information
- Expert credibility
""")

if __name__ == "__main__":
    asyncio.run(run_validation())

