# CLAUDE.md - Polymarket MCP Server

## Overview

This MCP server provides **read-only** access to Polymarket prediction markets. Use it to browse, search, and analyze live prediction market odds on various topics.

**NO betting functionality** - this is purely for research and discovery.

## Available Tools

### 1. search_markets
**Primary tool for finding markets.** Search by text query with sorting options.

Example: "Search for markets about Trump" → `search_markets(query="trump", sort_by="volume")`

### 2. get_trending_markets
Get popular/high-volume markets. Can filter by tag.

Example: "What are the hottest crypto markets?" → `get_trending_markets(tag="crypto", limit=10)`

### 3. get_market_details
Deep dive into a specific market. Returns full question, description, outcomes with probabilities, volume, liquidity, and token IDs for price history.

### 4. get_event_details
Events group related markets together (e.g., "2024 Election" event contains multiple candidate markets).

### 5. list_categories
Discover available tags/categories for filtering.

### 6. get_market_prices
Get current bid/ask spread and implied probabilities.

### 7. get_price_history
View recent trades showing price movements. Requires `condition_id` from market details.

## Price Format

- Prices are decimal: `0.65` = 65% implied probability
- YES + NO prices sum to approximately $1.00
- Volume/liquidity displayed with K/M suffixes

## Common Workflows

### Discover interesting markets
1. `search_markets(query="interesting topic")` or `get_trending_markets()`
2. Review returned events/markets
3. `get_market_details(market_slug="...")` for deeper analysis

### Track price movements
1. `get_market_details()` to get `condition_id`
2. `get_price_history(condition_id="...")` for trade history

### Explore categories
1. `list_categories(search="politics")` to find relevant tags
2. `get_trending_markets(tag="found-tag")` to filter

## Environment

- Python 3.12+
- Virtual environment at `./venv/`
- Dependencies: `mcp`, `polymarket-apis`

## Running Standalone

```bash
source venv/bin/activate
python polymarket_mcp_server.py
```

## Limitations

- Read-only (no betting)
- No real-time websocket feeds
- Price history via trades (not candlesticks)
- API rate limits apply
