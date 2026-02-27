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
| `batch_tx_info` | Batch transaction statistics for multiple tokens |
| `historical_coins` | Discover new tokens by timestamp |
| `swap_send` | Broadcast signed transactions (MEV-protected) |
| `swap_calldata` | Generate unsigned swap transaction data |

> ⚠️ **Swap amounts are human-readable** — pass `"0.1"` for 0.1 USDT, NOT `"100000000000000000"`. Response `toAmount` is also human-readable.

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

## Security

- Only communicates with `https://bopenapi.bgwapi.io` — no other external endpoints
- No `eval()` / `exec()` or dynamic code execution
- No file system access outside the project directory
- Built-in API keys are public demo credentials (safe to commit)
- No data collection, telemetry, or analytics
- No access to sensitive files (SSH keys, credentials, wallet files, etc.)
- Swap calldata only generates unsigned transaction data — actual execution requires wallet signing
- Dependencies: `requests`, `mcp` (stdlib: `hmac`, `hashlib`, `json`, `base64`)
- We recommend auditing the source yourself before installation

## License

MIT
