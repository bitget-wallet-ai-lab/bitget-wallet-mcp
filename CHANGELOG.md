# Changelog

All notable changes to the Bitget Wallet MCP Server are documented here.

Format: date-based versioning (`YYYY.M.DD-N`), aligned with [bitget-wallet-skill](https://github.com/bitget-wallet-ai-lab/bitget-wallet-skill).

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
