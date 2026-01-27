#!/usr/bin/env python3
"""
Basic tests for Polymarket MCP Server.

Run with: python test_server.py
"""

import asyncio
from polymarket_mcp_server import execute_tool


async def test_search_markets():
    """Test search_markets tool."""
    print("\n=== Testing search_markets ===")
    result = await execute_tool("search_markets", {
        "query": "trump",
        "active": True,
        "limit": 5,
        "sort_by": "volume"
    })
    print(f"Found {len(result.get('events', []))} events")
    print(f"Found {len(result.get('markets', []))} markets")
    if result.get('events'):
        print(f"Top event: {result['events'][0]['title']}")
        print(f"  Volume: {result['events'][0]['volume']}")
    return True


async def test_get_trending_markets():
    """Test get_trending_markets tool."""
    print("\n=== Testing get_trending_markets ===")
    result = await execute_tool("get_trending_markets", {
        "limit": 5
    })
    events = result.get('trending_events', [])
    print(f"Found {len(events)} trending events")
    for e in events[:3]:
        print(f"  - {e['title'][:60]}... (Volume: {e['volume']})")
    return len(events) > 0


async def test_get_market_details():
    """Test get_market_details tool."""
    print("\n=== Testing get_market_details ===")

    # First find a market
    search_result = await execute_tool("search_markets", {"query": "bitcoin", "limit": 1})
    if not search_result.get('events'):
        print("No markets found to test")
        return False

    event = search_result['events'][0]
    if not event.get('slug'):
        print("No slug available")
        return False

    # Get event to find a market
    event_result = await execute_tool("get_event_details", {"event_slug": event['slug']})
    if not event_result.get('markets'):
        print("No markets in event")
        return False

    market_slug = event_result['markets'][0].get('slug')
    if not market_slug:
        print("No market slug available")
        return False

    result = await execute_tool("get_market_details", {"market_slug": market_slug})
    print(f"Market: {result.get('question', 'N/A')[:60]}...")
    print(f"Outcomes: {result.get('outcomes', [])}")
    print(f"Condition ID: {result.get('condition_id', 'N/A')[:40]}..." if result.get('condition_id') else "No condition_id")
    return True


async def test_list_categories():
    """Test list_categories tool."""
    print("\n=== Testing list_categories ===")
    result = await execute_tool("list_categories", {"limit": 10})
    tags = result.get('tags', [])
    categories = result.get('main_categories', [])
    print(f"Found {result.get('total_tags_found', 0)} total tags")
    print(f"Main categories: {categories}")
    print(f"Sample tags: {[t['label'] for t in tags[:5]]}")
    return len(tags) > 0


async def test_get_market_prices():
    """Test get_market_prices tool."""
    print("\n=== Testing get_market_prices ===")

    # Find a market with good liquidity
    trending = await execute_tool("get_trending_markets", {"limit": 1})
    if not trending.get('trending_events'):
        print("No trending events found")
        return False

    event_slug = trending['trending_events'][0]['slug']
    event = await execute_tool("get_event_details", {"event_slug": event_slug})

    if not event.get('markets'):
        print("No markets in event")
        return False

    market_slug = event['markets'][0].get('slug')
    if not market_slug:
        print("No market slug available")
        return False

    result = await execute_tool("get_market_prices", {"market_slug": market_slug})
    print(f"Market: {result.get('question', 'N/A')[:60]}...")
    print(f"Prices: {result.get('prices', [])}")
    print(f"Order book: {result.get('order_book', {})}")
    return True


async def test_get_price_history():
    """Test get_price_history tool."""
    print("\n=== Testing get_price_history ===")

    # Find a market with a condition_id
    search_result = await execute_tool("search_markets", {"query": "trump", "limit": 5})

    condition_id = None
    for event in search_result.get('events', []):
        if not event.get('slug'):
            continue
        event_details = await execute_tool("get_event_details", {"event_slug": event['slug']})
        for market in event_details.get('markets', []):
            if market.get('slug'):
                market_details = await execute_tool("get_market_details", {"market_slug": market['slug']})
                if market_details.get('condition_id'):
                    condition_id = market_details['condition_id']
                    print(f"Found market: {market_details['question'][:50]}...")
                    break
        if condition_id:
            break

    if not condition_id:
        print("Could not find a market with condition_id")
        return False

    result = await execute_tool("get_price_history", {
        "condition_id": condition_id,
        "limit": 10
    })

    trades = result.get('trades', [])
    stats = result.get('stats', {})
    print(f"Found {len(trades)} trades")
    print(f"Stats: {stats}")
    if trades:
        print(f"Latest trade: {trades[0]}")
    return len(trades) > 0


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Polymarket MCP Server Tests")
    print("=" * 60)

    tests = [
        ("search_markets", test_search_markets),
        ("get_trending_markets", test_get_trending_markets),
        ("get_market_details", test_get_market_details),
        ("list_categories", test_list_categories),
        ("get_market_prices", test_get_market_prices),
        ("get_price_history", test_get_price_history),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = await test_func()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"ERROR: {e}")

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)

    for name, passed, error in results:
        status = "PASS" if passed else "FAIL"
        error_msg = f" - {error}" if error else ""
        print(f"  {status}: {name}{error_msg}")

    passed_count = sum(1 for _, p, _ in results if p)
    print(f"\nTotal: {passed_count}/{len(results)} passed")

    return all(p for _, p, _ in results)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
