#!/usr/bin/env python3
"""
Bitget Wallet MCP Server — exposes Bitget Wallet ToB API as MCP tools.
Signing logic is built in; no external dependencies beyond `requests` and `mcp`.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

import requests
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Config — override via env vars
# ---------------------------------------------------------------------------
# Public demo credentials for testing. These may change over time —
# if they stop working, please update to get the latest keys.
API_KEY = os.environ.get("BGW_API_KEY", "4843D8C3F1E20772C0E634EDACC5C5F9A0E2DC92")
API_SECRET = os.environ.get("BGW_API_SECRET", "F2ABFDC684BDC6775FD6286B8D06A3AAD30FD587")
PARTNER_CODE = os.environ.get("BGW_PARTNER_CODE", "bgw_swap_public")
BASE_URL = "https://bopenapi.bgwapi.io"

# ---------------------------------------------------------------------------
# Signing & HTTP
# ---------------------------------------------------------------------------

def _sign(api_path: str, body_str: str, timestamp: str) -> str:
    """HMAC-SHA256 signature per Bitget Wallet ToB API spec."""
    content = {
        "apiPath": api_path,
        "body": body_str,
        "x-api-key": API_KEY,
        "x-api-timestamp": timestamp,
    }
    payload = json.dumps(dict(sorted(content.items())), separators=(",", ":"))
    sig = hmac.new(API_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
    return base64.b64encode(sig).decode()


def _request(path: str, body: dict | None = None) -> dict[str, Any]:
    """Authenticated POST to Bitget Wallet ToB API."""
    timestamp = str(int(time.time() * 1000))
    body_str = json.dumps(body, separators=(",", ":"), sort_keys=True) if body else ""
    signature = _sign(path, body_str, timestamp)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "x-api-timestamp": timestamp,
        "x-api-signature": signature,
    }
    if "/swapx/" in path:
        headers["Partner-Code"] = PARTNER_CODE

    resp = requests.post(
        BASE_URL + path,
        data=body_str or None,
        headers=headers,
        timeout=30,
    )
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}", "message": resp.text[:500]}
    return resp.json()


# ---------------------------------------------------------------------------
# Chain ID mapping
# ---------------------------------------------------------------------------
CHAINS = {
    "eth": "1", "sol": "100278", "bnb": "56", "base": "8453",
    "arbitrum": "42161", "trx": "6", "ton": "100280",
    "suinet": "100281", "optimism": "10",
}

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "Bitget Wallet",
    instructions="On-chain data queries, token security audits, and swap quotes via Bitget Wallet ToB API. "
                 "Supports Ethereum, Solana, BNB Chain, Base, Arbitrum, Tron, TON, Sui, Optimism.",
)


@mcp.tool()
def token_info(chain: str, contract: str = "") -> dict:
    """Get detailed token information including price, market cap, supply, holders, and social links.

    Args:
        chain: Chain identifier (eth, sol, bnb, base, arbitrum, trx, ton, suinet, optimism)
        contract: Token contract address. Use empty string for native tokens (ETH, SOL, BNB, etc.)
    """
    result = _request("/bgw-pro/market/v3/coin/batchGetBaseInfo", {"list": [{"chain": chain, "contract": contract}]})
    if "data" in result and "list" in result["data"] and result["data"]["list"]:
        return result["data"]["list"][0]
    return result


@mcp.tool()
def token_price(chain: str, contract: str = "") -> dict:
    """Get the current price of a token.

    Args:
        chain: Chain identifier (eth, sol, bnb, base, arbitrum, trx, ton, suinet, optimism)
        contract: Token contract address. Use empty string for native tokens.
    """
    result = _request("/bgw-pro/market/v3/coin/batchGetBaseInfo", {"list": [{"chain": chain, "contract": contract}]})
    if "data" in result and "list" in result["data"] and result["data"]["list"]:
        d = result["data"]["list"][0]
        return {"symbol": d.get("symbol"), "name": d.get("name"), "price": d.get("price"), "chain": chain}
    return result


@mcp.tool()
def batch_token_info(tokens: list[dict]) -> dict:
    """Get info for multiple tokens in one call.

    Args:
        tokens: List of {"chain": "sol", "contract": "..."} objects.
    """
    return _request("/bgw-pro/market/v3/coin/batchGetBaseInfo", {"list": tokens})


@mcp.tool()
def kline(chain: str, contract: str, period: str = "1h", size: int = 24) -> dict:
    """Get K-line (candlestick) data for a token.

    Args:
        chain: Chain identifier
        contract: Token contract address
        period: Time period (1s, 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
        size: Number of candles to return (max 1440)
    """
    return _request("/bgw-pro/market/v3/coin/getKline", {
        "chain": chain, "contract": contract, "period": period, "size": size
    })


@mcp.tool()
def tx_info(chain: str, contract: str) -> dict:
    """Get token transaction statistics (5m/1h/4h/24h volume, buyers, sellers).

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/bgw-pro/market/v3/coin/getTxInfo", {"chain": chain, "contract": contract})


@mcp.tool()
def rankings(name: str = "topGainers") -> dict:
    """Get token rankings.

    Args:
        name: Ranking type — "topGainers" or "topLosers"
    """
    return _request("/bgw-pro/market/v3/topRank/detail", {"name": name})


@mcp.tool()
def liquidity(chain: str, contract: str) -> dict:
    """Get liquidity pool information for a token.

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/bgw-pro/market/v3/poolList", {"chain": chain, "contract": contract})


@mcp.tool()
def security_audit(chain: str, contract: str) -> dict:
    """Run a security audit on a token contract (honeypot detection, permission checks, blacklist).

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/bgw-pro/market/v3/coin/security/audits", {
        "list": [{"chain": chain, "contract": contract}], "source": "bg"
    })


@mcp.tool()
def swap_quote(
    from_chain: str,
    from_contract: str,
    to_contract: str,
    amount: str,
    to_chain: str = "",
    from_address: str = "",
) -> dict:
    """Get a swap quote with best route and estimated output.

    Args:
        from_chain: Source chain identifier
        from_contract: Source token contract (empty string for native token)
        to_contract: Destination token contract
        amount: Human-readable amount (e.g. "1" = 1 SOL, not lamports)
        to_chain: Destination chain (defaults to from_chain for same-chain swaps)
        from_address: Sender wallet address (optional, for more accurate quotes)
    """
    body: dict[str, Any] = {
        "fromChain": from_chain,
        "fromContract": from_contract,
        "toChain": to_chain or from_chain,
        "toContract": to_contract,
        "fromAmount": amount,
        "estimateGas": True,
    }
    if from_address:
        body["fromAddress"] = from_address
    return _request("/bgw-pro/swapx/pro/quote", body)


@mcp.tool()
def swap_calldata(
    from_chain: str,
    from_contract: str,
    to_contract: str,
    amount: str,
    from_address: str,
    to_address: str,
    market: str,
    to_chain: str = "",
    slippage: float | None = None,
) -> dict:
    """Generate unsigned transaction data for a swap (requires wallet signing to execute).

    Args:
        from_chain: Source chain identifier
        from_contract: Source token contract
        to_contract: Destination token contract
        amount: Human-readable amount
        from_address: Sender wallet address
        to_address: Recipient wallet address
        market: Market/aggregator from quote result
        to_chain: Destination chain (defaults to from_chain)
        slippage: Slippage tolerance percentage (optional)
    """
    body: dict[str, Any] = {
        "fromChain": from_chain,
        "fromContract": from_contract,
        "toChain": to_chain or from_chain,
        "toContract": to_contract,
        "fromAmount": amount,
        "fromAddress": from_address,
        "toAddress": to_address,
        "market": market,
    }
    if slippage is not None:
        body["slippage"] = slippage
    return _request("/bgw-pro/swapx/pro/swap", body)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
