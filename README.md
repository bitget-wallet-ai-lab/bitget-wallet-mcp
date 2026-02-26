# Bitget Wallet MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that exposes Bitget Wallet ToB API as tools for AI agents.

## Features

- **Token Info** — price, market cap, holders, social links
- **Batch Price Query** — multi-token lookup in one call
- **K-line Data** — candlestick data across multiple timeframes
- **Transaction Stats** — buy/sell volume and trader counts
- **Rankings** — top gainers and top losers
- **Liquidity Pools** — LP pool information
- **Security Audit** — honeypot detection, permission checks, blacklist analysis
- **Swap Quote** — best-route quotes for same-chain and cross-chain swaps
- **Swap Calldata** — generate unsigned transaction data for wallet signing

### Supported Chains

Ethereum · Solana · BNB Chain · Base · Arbitrum · Tron · TON · Sui · Optimism

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

## Tools

| Tool | Description |
|------|-------------|
| `token_info` | Detailed token information (price, market cap, supply, holders) |
| `token_price` | Quick price lookup |
| `batch_token_info` | Multi-token info in one call |
| `kline` | Candlestick data (1s to 1w periods) |
| `tx_info` | Transaction volume and trader statistics |
| `rankings` | Top gainers / top losers |
| `liquidity` | Liquidity pool information |
| `security_audit` | Contract security checks |
| `swap_quote` | Best-route swap quotes |
| `swap_calldata` | Generate unsigned swap transaction data |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BGW_API_KEY` | Built-in demo key | Bitget Wallet ToB API appId |
| `BGW_API_SECRET` | Built-in demo secret | Bitget Wallet ToB API apiSecret |
| `BGW_PARTNER_CODE` | `bgw_swap_public` | Partner code for swap endpoints |

> **Note:** The built-in demo keys are for testing purposes and may change over time. If they stop working, please update to get the latest keys.

## Related Projects

- [bitget-wallet-skill](https://github.com/bitget-wallet-ai-lab/bitget-wallet-skill) — OpenClaw AI Agent skill (with [platform compatibility guide](https://github.com/bitget-wallet-ai-lab/bitget-wallet-skill/blob/main/COMPATIBILITY.md))
- [bitget-wallet-cli](https://github.com/bitget-wallet-ai-lab/bitget-wallet-cli) — CLI tool for terminal users

## Security

- Swap calldata only generates unsigned transaction data — **actual execution requires wallet signing**
- Demo API keys are public and read-only safe
- For production use, set your own credentials via environment variables

## License

MIT
