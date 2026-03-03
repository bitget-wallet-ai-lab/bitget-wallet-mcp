# Changelog

All notable changes to the Bitget Wallet MCP Server are documented here.

Format: date-based versioning (`YYYY.M.DD-N`), aligned with [bitget-wallet-skill](https://github.com/bitget-wallet-ai-lab/bitget-wallet-skill).

---

## [2026.3.3-1] - 2026-03-03

### Changed
- Version scheme aligned to date-based format (`YYYY.M.DD-N`), matching the skill repo
- Added `CHANGELOG.md`

### Added
- `deadline` parameter to `swap_calldata` tool (transaction expiry in seconds, mitigates sandwich attacks)
- `from_symbol` and `to_symbol` parameters to `swap_quote` and `swap_calldata` tools

### Audit
- ✅ `server.py`: parameter additions only, no logic changes
- ✅ No dependency changes
- ✅ Full parity with skill repo parameters

---

## [1.0.0] - 2026-02-20

### Added
- Initial release
- 13 MCP tools: token_info, token_price, batch_token_info, kline, tx_info, batch_tx_info, historical_coins, rankings, liquidity, security_audit, swap_quote, swap_calldata, swap_send
- Built-in public demo API credentials
- FastMCP server with HMAC-SHA256 signing
