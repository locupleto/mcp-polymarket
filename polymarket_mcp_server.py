#!/usr/bin/env python3
"""
Polymarket MCP Server - Read-only access to prediction market data.

Provides tools to browse, search, and analyze Polymarket prediction markets.
NO betting functionality - purely for research and discovery.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from polymarket_apis import PolymarketGammaClient, PolymarketDataClient
from polymarket_apis.types.gamma_types import Event, GammaMarket


# Initialize MCP server
server = Server("polymarket")

# Initialize Polymarket clients (no auth needed for read operations)
gamma_client = PolymarketGammaClient()
data_client = PolymarketDataClient()


def format_price_as_probability(price: float) -> str:
    """Convert decimal price to percentage probability."""
    return f"{price * 100:.1f}%"


def format_volume(volume: Optional[float]) -> str:
    """Format volume with K/M suffixes."""
    if volume is None:
        return "N/A"
    # Handle string volumes from API
    if isinstance(volume, str):
        try:
            volume = float(volume)
        except (ValueError, TypeError):
            return "N/A"
    if volume >= 1_000_000:
        return f"${volume / 1_000_000:.1f}M"
    if volume >= 1_000:
        return f"${volume / 1_000:.1f}K"
    return f"${volume:.2f}"


def parse_outcomes(outcomes) -> list:
    """Parse outcomes field which may be a JSON string or list."""
    if outcomes is None:
        return ["Yes", "No"]
    if isinstance(outcomes, str):
        try:
            return json.loads(outcomes)
        except json.JSONDecodeError:
            return ["Yes", "No"]
    return list(outcomes)


def format_market_summary(market: GammaMarket) -> dict:
    """Format a market into a concise summary."""
    outcome_prices = market.outcome_prices or []
    outcomes = parse_outcomes(market.outcomes)

    # Build odds string
    odds = []
    for i, outcome in enumerate(outcomes):
        if i < len(outcome_prices):
            odds.append(f"{outcome}: {format_price_as_probability(outcome_prices[i])}")

    return {
        "id": market.id,
        "slug": getattr(market, 'slug', None),
        "question": market.question,
        "odds": odds,
        "volume": format_volume(market.volume),
        "volume_24h": format_volume(getattr(market, 'volume_24hr', None)),
        "liquidity": format_volume(market.liquidity),
        "active": market.active,
        "end_date": market.end_date.isoformat() if market.end_date else None,
    }


def format_event_summary(event: Event) -> dict:
    """Format an event into a concise summary."""
    return {
        "id": event.id,
        "slug": event.slug,
        "title": event.title,
        "description": (event.description[:200] + "...") if event.description and len(event.description) > 200 else event.description,
        "volume": format_volume(event.volume),
        "volume_24h": format_volume(getattr(event, 'volume_24hr', None)),
        "liquidity": format_volume(event.liquidity),
        "active": event.active,
        "markets_count": len(event.markets) if event.markets else 0,
        "end_date": event.end_date.isoformat() if event.end_date else None,
    }


def format_market_details(market: GammaMarket) -> dict:
    """Format detailed market information."""
    outcome_prices = market.outcome_prices or []
    outcomes = parse_outcomes(market.outcomes)
    token_ids = getattr(market, 'token_ids', []) or []

    # Build detailed outcomes
    detailed_outcomes = []
    for i, outcome in enumerate(outcomes):
        outcome_info = {
            "outcome": outcome,
            "probability": format_price_as_probability(outcome_prices[i]) if i < len(outcome_prices) else "N/A",
            "price": outcome_prices[i] if i < len(outcome_prices) else None,
        }
        if i < len(token_ids):
            outcome_info["token_id"] = token_ids[i]
        detailed_outcomes.append(outcome_info)

    return {
        "id": market.id,
        "slug": getattr(market, 'slug', None),
        "question": market.question,
        "description": market.description,
        "outcomes": detailed_outcomes,
        "volume": {
            "total": format_volume(market.volume),
            "24h": format_volume(getattr(market, 'volume_24hr', None)),
            "1w": format_volume(getattr(market, 'volume_1wk', None)),
            "1m": format_volume(getattr(market, 'volume_1mo', None)),
        },
        "liquidity": format_volume(market.liquidity),
        "order_book": {
            "best_bid": getattr(market, 'best_bid', None),
            "best_ask": getattr(market, 'best_ask', None),
            "spread": getattr(market, 'spread', None),
        },
        "condition_id": getattr(market, 'condition_id', None),
        "active": market.active,
        "closed": market.closed,
        "start_date": market.start_date.isoformat() if market.start_date else None,
        "end_date": market.end_date.isoformat() if market.end_date else None,
        "resolution_source": getattr(market, 'resolution_source', None),
    }


def format_event_details(event: Event) -> dict:
    """Format detailed event information."""
    result = {
        "id": event.id,
        "slug": event.slug,
        "title": event.title,
        "description": event.description,
        "volume": {
            "total": format_volume(event.volume),
            "24h": format_volume(getattr(event, 'volume_24hr', None)),
            "1w": format_volume(getattr(event, 'volume_1wk', None)),
            "1m": format_volume(getattr(event, 'volume_1mo', None)),
        },
        "liquidity": format_volume(event.liquidity),
        "active": event.active,
        "closed": event.closed,
        "start_date": event.start_date.isoformat() if event.start_date else None,
        "end_date": event.end_date.isoformat() if event.end_date else None,
        "resolution_source": getattr(event, 'resolution_source', None),
        "category": event.category,
        "subcategory": getattr(event, 'subcategory', None),
        "markets": [],
    }

    if event.markets:
        result["markets"] = [format_market_summary(m) for m in event.markets]

    return result


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Polymarket tools."""
    return [
        Tool(
            name="search_markets",
            description="Search for prediction markets by text query. Returns matching events and markets with current odds.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search text (e.g., 'trump', 'bitcoin', 'super bowl')"
                    },
                    "active": {
                        "type": "boolean",
                        "description": "Only return active markets (default: true)",
                        "default": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 20)",
                        "default": 20
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["volume", "volume_24hr", "liquidity", "start_date", "end_date"],
                        "description": "Sort results by this field (default: volume)",
                        "default": "volume"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_trending_markets",
            description="Get trending/popular prediction markets sorted by volume or activity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of markets to return (default: 10)",
                        "default": 10
                    },
                    "tag": {
                        "type": "string",
                        "description": "Filter by tag slug (e.g., 'politics', 'crypto', 'sports')"
                    },
                    "min_volume": {
                        "type": "number",
                        "description": "Minimum total volume in USD"
                    },
                    "min_liquidity": {
                        "type": "number",
                        "description": "Minimum liquidity in USD"
                    }
                }
            }
        ),
        Tool(
            name="get_market_details",
            description="Get full details and current odds for a specific market.",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_id": {
                        "type": "integer",
                        "description": "Market ID number"
                    },
                    "market_slug": {
                        "type": "string",
                        "description": "Market URL slug (e.g., 'will-bitcoin-hit-100k-in-2024')"
                    }
                }
            }
        ),
        Tool(
            name="get_event_details",
            description="Get an event with all its related markets. Events group multiple related markets together.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "Event ID number"
                    },
                    "event_slug": {
                        "type": "string",
                        "description": "Event URL slug (e.g., '2024-presidential-election')"
                    }
                }
            }
        ),
        Tool(
            name="list_categories",
            description="List popular market categories/tags for filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum tags to return (default: 50)",
                        "default": 50
                    },
                    "search": {
                        "type": "string",
                        "description": "Filter tags containing this text"
                    }
                }
            }
        ),
        Tool(
            name="get_market_prices",
            description="Get current bid/ask prices and spread for market outcomes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_id": {
                        "type": "integer",
                        "description": "Market ID number"
                    },
                    "market_slug": {
                        "type": "string",
                        "description": "Market URL slug"
                    }
                }
            }
        ),
        Tool(
            name="get_price_history",
            description="Get recent trade history for a market, showing price movements over time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition_id": {
                        "type": "string",
                        "description": "Market condition ID (from market details)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of trades to return (default: 50)",
                        "default": 50
                    }
                },
                "required": ["condition_id"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a Polymarket tool."""
    try:
        result = await execute_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        error_result = {"error": str(e), "tool": name, "arguments": arguments}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def execute_tool(name: str, arguments: dict) -> Any:
    """Execute the appropriate tool based on name."""

    if name == "search_markets":
        query = arguments["query"]
        active = arguments.get("active", True)
        limit = arguments.get("limit", 20)
        sort_by = arguments.get("sort_by", "volume")

        status = "active" if active else None
        results = gamma_client.search(
            query=query,
            status=status,
            limit_per_type=limit,
            sort=sort_by
        )

        response = {
            "query": query,
            "events": [],
            "markets": []
        }

        if results.events:
            response["events"] = [format_event_summary(e) for e in results.events[:limit]]
            # Also extract markets from events
            for event in results.events[:limit]:
                if event.markets:
                    for market in event.markets[:5]:  # Limit markets per event
                        response["markets"].append(format_market_summary(market))

        return response

    elif name == "get_trending_markets":
        limit = arguments.get("limit", 10)
        tag_slug = arguments.get("tag")
        min_volume = arguments.get("min_volume")
        min_liquidity = arguments.get("min_liquidity")

        events = gamma_client.get_events(
            limit=100,  # Get more to filter/sort
            active=True,
            tag_slug=tag_slug,
            volume_min=min_volume,
            liquidity_min=min_liquidity,
            order="volume",
            ascending=False
        )

        # Sort by volume descending and take top N
        events_sorted = sorted(events, key=lambda e: e.volume or 0, reverse=True)[:limit]

        return {
            "trending_events": [format_event_summary(e) for e in events_sorted],
            "filters_applied": {
                "tag": tag_slug,
                "min_volume": min_volume,
                "min_liquidity": min_liquidity
            }
        }

    elif name == "get_market_details":
        market_id = arguments.get("market_id")
        market_slug = arguments.get("market_slug")

        if not market_id and not market_slug:
            raise ValueError("Either market_id or market_slug is required")

        if market_id:
            market = gamma_client.get_market_by_id(market_id)
        else:
            market = gamma_client.get_market_by_slug(market_slug)

        if not market:
            raise ValueError(f"Market not found: {market_id or market_slug}")

        return format_market_details(market)

    elif name == "get_event_details":
        event_id = arguments.get("event_id")
        event_slug = arguments.get("event_slug")

        if not event_id and not event_slug:
            raise ValueError("Either event_id or event_slug is required")

        if event_id:
            event = gamma_client.get_event_by_id(event_id)
        else:
            event = gamma_client.get_event_by_slug(event_slug)

        if not event:
            raise ValueError(f"Event not found: {event_id or event_slug}")

        return format_event_details(event)

    elif name == "list_categories":
        limit = arguments.get("limit", 50)
        search_text = arguments.get("search", "").lower()

        all_tags = gamma_client.get_all_tags()

        # Filter by search text if provided
        if search_text:
            all_tags = [t for t in all_tags if search_text in t.label.lower() or search_text in t.slug.lower()]

        # Get popular tags (limit the output)
        tags_list = []
        for tag in all_tags[:limit]:
            tags_list.append({
                "label": tag.label,
                "slug": tag.slug,
                "id": tag.id if hasattr(tag, 'id') else None
            })

        # Also get unique categories from events
        events = gamma_client.get_events(limit=200, active=True)
        categories = set()
        for e in events:
            if e.category:
                categories.add(e.category)

        return {
            "tags": tags_list,
            "main_categories": sorted(list(categories)),
            "total_tags_found": len(all_tags) if not search_text else len([t for t in gamma_client.get_all_tags() if search_text in t.label.lower() or search_text in t.slug.lower()])
        }

    elif name == "get_market_prices":
        market_id = arguments.get("market_id")
        market_slug = arguments.get("market_slug")

        if not market_id and not market_slug:
            raise ValueError("Either market_id or market_slug is required")

        if market_id:
            market = gamma_client.get_market_by_id(market_id)
        else:
            market = gamma_client.get_market_by_slug(market_slug)

        if not market:
            raise ValueError(f"Market not found: {market_id or market_slug}")

        outcome_prices = market.outcome_prices or []
        outcomes = parse_outcomes(market.outcomes)

        prices = []
        for i, outcome in enumerate(outcomes):
            price_info = {
                "outcome": outcome,
                "mid_price": outcome_prices[i] if i < len(outcome_prices) else None,
                "probability": format_price_as_probability(outcome_prices[i]) if i < len(outcome_prices) else "N/A",
            }
            prices.append(price_info)

        return {
            "market_id": market.id,
            "question": market.question,
            "prices": prices,
            "order_book": {
                "best_bid": getattr(market, 'best_bid', None),
                "best_ask": getattr(market, 'best_ask', None),
                "spread": getattr(market, 'spread', None),
                "spread_pct": f"{getattr(market, 'spread', 0) * 100:.2f}%" if getattr(market, 'spread', None) else None
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    elif name == "get_price_history":
        condition_id = arguments["condition_id"]
        limit = arguments.get("limit", 50)

        trades = data_client.get_trades(
            limit=limit,
            condition_id=condition_id
        )

        trade_history = []
        for trade in trades:
            trade_history.append({
                "timestamp": trade.timestamp.isoformat() if trade.timestamp else None,
                "price": trade.price,
                "probability": format_price_as_probability(trade.price) if trade.price else None,
                "size": trade.size,
                "side": trade.side,
                "outcome": trade.outcome,
            })

        # Calculate price stats
        prices = [t.price for t in trades if t.price is not None]
        stats = {}
        if prices:
            stats = {
                "current_price": prices[0],
                "current_probability": format_price_as_probability(prices[0]),
                "high": max(prices),
                "low": min(prices),
                "avg": sum(prices) / len(prices),
                "trades_count": len(trades)
            }

        return {
            "condition_id": condition_id,
            "trades": trade_history,
            "stats": stats
        }

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
