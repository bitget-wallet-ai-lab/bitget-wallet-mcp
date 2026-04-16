# Bitget Wallet MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that exposes Bitget Wallet on-chain API as tools for AI agents.

## Features

### 📊 Market Data (21 tools)
- **Token Search** — v3 keyword search with ordering + v2 broader DEX search
- **Token Info** — price, market cap, holders, social links (single + batch)
- **Market Info** — price, MC, FDV, liquidity, holders, narratives, pool list
- **K-line** — candlestick data + simplified K-line with smart money/KOL overlays
- **Transaction Stats** — buy/sell volume, trader counts (single + batch)
- **Trading Dynamics** — buy/sell pressure across time windows
- **Transaction List** — recent trades with tag filtering (KOL, smart money)
- **Holder Analysis** — distribution, top holders, special holder filters
- **Profit Analysis** — profitable vs losing addresses, top earners per token
- **Developer Analysis** — dev history, rug rate, project migration status
- **Rankings** — top gainers, top losers, hot picks
- **Liquidity Pools** — LP pool information per token
- **Launchpad Scanning** — new tokens on pump.fun etc. with filters
- **Historical Tokens** — discover tokens by creation timestamp
- **Security Audit** — honeypot detection, permission checks, tax analysis

### 🔍 Smart Money (1 tool)
- **Address Discovery** — find KOL and smart money wallets with PnL, win rate, trade count filters

### 📈 RWA Stock Trading (6 tools)
- **Ticker List** — available RWA stocks (NVDA, TSLA, AAPL, etc.) on BNB/ETH
- **Stock Info** — market status, trading limits, description
- **Order Price** — pre-trade buy/sell price display
- **K-line** — stock price charts
- **Trading Config** — stablecoins, slippage, amount limits, gas info
- **Portfolio** — user's RWA holdings

### 💱 Swap (7 tools)
- **Quote** — multi-market quotes with `requestId`
- **Confirm** — second quote with MEV protection, gas features
- **Make Order** — create order, get unsigned txs
- **Send** — submit signed transactions
- **Order Details** — track order status (init → processing → success/failed)
- **Check Token** — pre-trade risk check
- **Token List** — popular tokens per chain

### 🔁 Token Transfer (3 tools)
- **Make Transfer Order** — create transfer order, get unsigned tx data (supports gasless)
- **Submit Transfer** — submit signed transfer transaction
- **Get Transfer Order** — poll transfer order status (PENDING → PROCESSING → SUCCESS/FAILED)

### 💰 Balance (1 tool)
- **Batch Balance** — multi-chain token balances with USD values

### Supported Chains

Ethereum · Solana · BNB Chain · Base · Arbitrum · Tron · TON · Sui · Optimism · Polygon · Morph

## Quick Start

### Install

```bash
pip install -e .
```

### Run

```bash
python server.py
```

Or via MCP CLI:

```bash
mcp run server.py
```

### Configure in Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bitget-wallet": {
      "command": "python",
      "args": ["/path/to/bitget-wallet-mcp/server.py"]
    }
  }
}
```

### Configure in Cursor / Windsurf

Add to your MCP settings:

```json
{
  "bitget-wallet": {
    "command": "python",
    "args": ["/path/to/bitget-wallet-mcp/server.py"]
  }
}
```

## Tools (39)

### Market Data
| Tool | Description |
|------|-------------|
| `token_info` | Detailed token info (price, market cap, supply, holders) |
| `token_price` | Quick price lookup |
| `batch_token_info` | Multi-token info in one call |
| `search_tokens` | v3 token search with ordering |
| `search_tokens_v2` | v2 broader search (DEX tokens) |
| `coin_market_info` | Market info + pool list + narratives |
| `coin_dev` | Developer history and rug rate |
| `kline` | Candlestick data (1s to 1w periods) |
| `simple_kline` | K-line with smart money/KOL/developer overlays |
| `tx_info` | Transaction volume and trader stats |
| `batch_tx_info` | Batch transaction stats |
| `trading_dynamics` | Buy/sell pressure across time windows |
| `transaction_list` | Recent trades with tag filtering |
| `holders_info` | Holder distribution and top holders |
| `profit_address_analysis` | Profitable vs losing address stats |
| `top_profit` | Top profitable addresses per token |
| `rankings` | Top gainers / losers / hot picks |
| `liquidity` | Liquidity pool info |
| `launchpad_tokens` | Launchpad scanning with filters |
| `historical_coins` | Discover tokens by creation time |
| `security_audit` | Contract security checks |

### Smart Money
| Tool | Description |
|------|-------------|
| `smart_money_addresses` | KOL/smart money address discovery with filters |

### RWA Stock Trading
| Tool | Description |
|------|-------------|
| `rwa_ticker_list` | Available RWA stocks |
| `rwa_config` | Trading config (stablecoins, limits) |
| `rwa_stock_info` | Stock info and market status |
| `rwa_order_price` | Pre-trade buy/sell price |
| `rwa_kline` | Stock K-line charts |
| `rwa_my_holdings` | User's RWA portfolio |

### Swap
| Tool | Description |
|------|-------------|
| `swap_quote` | Multi-market swap quotes |
| `swap_confirm` | Confirm with MEV protection |
| `swap_make_order` | Create order (unsigned txs) |
| `swap_send` | Submit signed transactions |
| `swap_get_order_details` | Track order status |
| `check_swap_token` | Pre-trade risk check |
| `get_token_list` | Popular tokens per chain |

### Token Transfer
| Tool | Description |
|------|-------------|
| `transfer_make_order` | Create transfer order (unsigned tx data, supports gasless) |
| `transfer_submit` | Submit signed transfer transaction |
| `transfer_get_order` | Poll transfer order status |

### Balance
| Tool | Description |
|------|-------------|
| `balance` | Batch balance + USD values |

> ⚠️ **Amounts are human-readable** — pass `"0.1"` for 0.1 USDT, NOT wei/lamports.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BGW_WALLET_ID` | _(empty)_ | Wallet ID for Social Login Wallet users (optional) |

No API key required — uses SHA256 hash signing (BKHmacAuth).

## Security

- Only communicates with `https://copenapi.bgwapi.io` — no other external endpoints
- No API keys or secrets — SHA256 hash signing with zero credentials
- No `eval()` / `exec()` or dynamic code execution
- No file system access outside the project directory
- No data collection, telemetry, or analytics
- No access to sensitive files (SSH keys, credentials, wallet files, etc.)
- Dependencies: `requests`, `mcp` only
- SlowMist security review: 🟢 LOW risk
- We recommend auditing the source yourself before installation

## Related Projects

- [bitget-wallet-skill](https://github.com/bitget-wallet-ai-lab/bitget-wallet-skill) — OpenClaw AI Agent skill
- [bitget-wallet-cli](https://github.com/bitget-wallet-ai-lab/bitget-wallet-cli) — CLI tool for terminal users

## License

MIT
