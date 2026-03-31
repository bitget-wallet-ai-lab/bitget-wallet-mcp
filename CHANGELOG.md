# Changelog

All notable changes to the Bitget Wallet MCP Server are documented here.

Format: date-based versioning (`YYYY.M.DD-N`), aligned with [bitget-wallet-skill](https://github.com/bitget-wallet-ai-lab/bitget-wallet-skill).

---

## [2026.3.31-1] - 2026-03-31

### Breaking Changes
- **API migration**: `bopenapi.bgwapi.io` (ToB API) → `copenapi.bgwapi.io` (Skill internal API)
- **Auth rewrite**: HMAC-SHA256 + API Key → SHA256 hash signing (BKHmacAuth), zero secrets
- **Removed**: `API_KEY`, `API_SECRET`, `PARTNER_CODE` env vars and all HMAC/base64 signing
- **Removed tools**: `order_quote`, `order_create`, `order_submit`, `order_status`, `swap_calldata`
- **Endpoint migration**: `/bgw-pro/market/` → `/market/`, `/bgw-pro/swapx/` → `/swap-go/swapx/`

### Added — Swap Flow (aligned with Skill)
- `swap_quote` — first quote with multi-market results, includes `requestId`
- `swap_confirm` — second quote with `mevProtection`, `features`, `gasLevel`, `recommendSlippage`
- `swap_make_order` — create order with `orderId` (from confirm), returns unsigned txs
- `swap_send` — submit signed txs (`orderId` + `txs` array)
- `swap_get_order_details` — query order status
- `check_swap_token` — pre-trade risk check (body key `list`)
- `get_token_list` — popular tokens per chain (with `isAllNetWork: 1`)

### Added — Token Analysis (10 tools)
- `search_tokens` — v3 token search with ordering
- `search_tokens_v2` — v2 broader search (DEX tokens)
- `coin_market_info` — price, MC, FDV, liquidity, holders, narratives
- `coin_dev` — developer history and rug rate analysis
- `launchpad_tokens` — launchpad scanning with filters (pump.fun, etc.)
- `simple_kline` — K-line with smart money/KOL/developer overlays
- `trading_dynamics` — buy/sell pressure across time windows
- `transaction_list` — recent transactions with tag filtering
- `holders_info` — holder distribution and top holders
- `profit_address_analysis` — profitable vs losing address stats
- `top_profit` — top profitable addresses per token

### Added — Smart Money (1 tool)
- `smart_money_addresses` — KOL/smart money address discovery with performance filters

### Added — RWA Stock Trading (6 tools)
- `rwa_ticker_list` — available RWA stocks (NVDA, TSLA, AAPL, etc.)
- `rwa_config` — trading config (stablecoins, limits, gas info)
- `rwa_stock_info` — stock info via GET request
- `rwa_order_price` — pre-trade buy/sell price
- `rwa_kline` — K-line for RWA stocks
- `rwa_my_holdings` — user's RWA portfolio

### Added — Balance (1 tool)
- `balance` — batch balance + USD values (with `nocache`, `appointCurrency`, `noreport`)

### Added — Infrastructure
- `_request_get` — GET request support with BKHmacAuth signing (for RWA stock info)
- `BGW_WALLET_ID` env var for Social Login Wallet users

### Security
- ✅ Zero hardcoded secrets (removed API Key/Secret/Partner Code)
- ✅ Single outbound target: `copenapi.bgwapi.io`
- ✅ No file system access, no dynamic code execution, no persistence
- ✅ SlowMist security review: 🟢 LOW risk

### Stats
- 36 MCP tools (was 11)
- 33 API endpoints covered (100% Skill parity)

---

## [2026.3.5-1] - 2026-03-05

### Added
- **Order Mode API**: 4 new MCP tools for gasless + cross-chain swaps
  - `order_quote` — get swap price with cross-chain and gasless support
  - `order_create` — create order, receive unsigned tx/signature data
  - `order_submit` — submit signed transactions
  - `order_status` — query order lifecycle status (init → processing → success/failed)
- New chain: Morph (`morph`)
- Updated MCP instructions string with Order Mode and Polygon/Morph

### Audit
- ✅ `server.py`: 4 new tools added, no existing logic changed
- ✅ All new endpoints use same `bopenapi.bgwapi.io` base URL
- ✅ Same auth mechanism (HMAC-SHA256 + Partner-Code)
- ✅ No new dependencies

---

## [2026.3.3-1] - 2026-03-03

### Changed
- Version scheme aligned to date-based format (`YYYY.M.DD-N`), matching the skill repo
- Added `CHANGELOG.md`

### Added
- `deadline` parameter to `swap_calldata` tool (transaction expiry in seconds, mitigates sandwich attacks)
- `from_symbol` and `to_symbol` parameters to `swap_quote` and `swap_calldata` tools

### Fixed
- Added missing `matic` (Polygon) to supported chains

### Audit
- ✅ `server.py`: parameter additions + chain code fix
- ✅ No dependency changes
- ✅ Full parity with skill repo parameters and chain codes

---

## [1.0.0] - 2026-02-20

### Added
- Initial release
- 13 MCP tools: token_info, token_price, batch_token_info, kline, tx_info, batch_tx_info, historical_coins, rankings, liquidity, security_audit, swap_quote, swap_calldata, swap_send
- Built-in public demo API credentials
- FastMCP server with HMAC-SHA256 signing
