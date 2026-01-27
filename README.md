# Polymarket MCP Server

Read-only MCP server for browsing and analyzing Polymarket prediction markets.

**NO betting functionality** - purely for research, discovery, and analysis of prediction market odds.

## Features

- Search markets by text query
- Get trending/popular markets
- View detailed market odds and prices
- Browse market categories
- View price history via trade data

## Installation

```bash
cd /Volumes/Work/development/projects/git/mcp-polymarket
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage with Claude Code

Register the server:

```bash
claude mcp add -s user polymarket \
    "/Volumes/Work/development/projects/git/mcp-polymarket/venv/bin/python3" \
    "/Volumes/Work/development/projects/git/mcp-polymarket/polymarket_mcp_server.py"
```

Verify:

```bash
claude mcp list
```

## Available Tools

### search_markets
Search for prediction markets by text query.

```
Parameters:
- query (required): Search text (e.g., 'trump', 'bitcoin', 'super bowl')
- active: Only return active markets (default: true)
- limit: Maximum results (default: 20)
- sort_by: Sort by 'volume', 'volume_24hr', 'liquidity', 'start_date', 'end_date'
```

### get_trending_markets
Get popular markets sorted by volume.

```
Parameters:
- limit: Number of markets to return (default: 10)
- tag: Filter by tag slug (e.g., 'politics', 'crypto', 'sports')
- min_volume: Minimum total volume in USD
- min_liquidity: Minimum liquidity in USD
```

### get_market_details
Get full details for a specific market.

```
Parameters:
- market_id: Market ID number
- market_slug: Market URL slug (e.g., 'will-bitcoin-hit-100k-in-2024')
```

### get_event_details
Get an event with all its related markets.

```
Parameters:
- event_id: Event ID number
- event_slug: Event URL slug
```

### list_categories
List available market categories/tags.

```
Parameters:
- limit: Maximum tags to return (default: 50)
- search: Filter tags containing this text
```

### get_market_prices
Get current bid/ask prices and spread.

```
Parameters:
- market_id: Market ID number
- market_slug: Market URL slug
```

### get_price_history
Get recent trade history for price movements.

```
Parameters:
- condition_id (required): Market condition ID (from market details)
- limit: Number of trades to return (default: 50)
```

## API Notes

- Uses Polymarket's Gamma API (no authentication required for read operations)
- Prices are decimal format where 0.65 = 65% implied probability
- Markets have YES/NO outcomes where prices sum to approximately $1.00
- Volume and liquidity are in USD

## Examples

### Find trending political markets
```
get_trending_markets(tag="politics", limit=5)
```

### Search for crypto markets
```
search_markets(query="bitcoin", active=true, sort_by="volume")
```

### Get details on a specific market
```
get_market_details(market_slug="will-bitcoin-hit-100k-in-2024")
```

### View price history
```
# First get condition_id from market details, then:
get_price_history(condition_id="0x...", limit=100)
```

## License

MIT
