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
    "suinet": "100281", "optimism": "10", "matic": "137",
    "morph": "morph",
}

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "Bitget Wallet",
    instructions="On-chain data queries, token security audits, swap quotes, reverse quotes, and Order Mode (gasless + cross-chain) "
                 "swaps via Bitget Wallet ToB API. "
                 "Supports Ethereum, Solana, BNB Chain, Base, Arbitrum, Tron, TON, Sui, Optimism, Polygon, Morph. "
                 "Order Mode enables gasless transactions (EIP-7702) and one-step cross-chain swaps. "
                 "Reverse quote (swapr) supports exactIn and minAmountOut modes — use minAmountOut when the user "
                 "specifies desired output amount instead of input amount.",
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
def batch_tx_info(tokens: list[dict]) -> dict:
    """Batch get transaction statistics for multiple tokens.

    Args:
        tokens: List of {"chain": "sol", "contract": "..."} objects (max 100).
    """
    return _request("/bgw-pro/market/v3/coin/batchGetTxInfo", {"list": tokens})


@mcp.tool()
def historical_coins(create_time: str, limit: int = 10) -> dict:
    """Get token list by timestamp (paginated). Useful for discovering new tokens.

    Args:
        create_time: Timestamp string (e.g. "2025-06-17 06:55:28")
        limit: Number of records to return (default 10)
    """
    return _request("/bgw-pro/market/v3/historical-coins", {"createTime": create_time, "limit": limit})


@mcp.tool()
def rankings(name: str = "topGainers") -> dict:
    """Get token rankings.

    Args:
        name: Ranking type — "topGainers", "topLosers", or "hotpicks"
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
    from_symbol: str = "",
    to_symbol: str = "",
) -> dict:
    """Get a swap quote with best route and estimated output.

    Args:
        from_chain: Source chain identifier
        from_contract: Source token contract (empty string for native token)
        to_contract: Destination token contract
        amount: IMPORTANT: Human-readable amount, NOT smallest units.
               "0.1" = 0.1 USDT, "1" = 1 SOL. Do NOT pass wei/lamports/raw values.
        to_chain: Destination chain (defaults to from_chain for same-chain swaps)
        from_address: Sender wallet address (optional, for more accurate quotes)
        from_symbol: Source token symbol (optional, helps with routing)
        to_symbol: Destination token symbol (optional, helps with routing)
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
    if from_symbol:
        body["fromSymbol"] = from_symbol
    if to_symbol:
        body["toSymbol"] = to_symbol
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
    deadline: int | None = None,
    from_symbol: str = "",
    to_symbol: str = "",
) -> dict:
    """Generate unsigned transaction data for a swap (requires wallet signing to execute).

    Args:
        from_chain: Source chain identifier
        from_contract: Source token contract
        to_contract: Destination token contract
        amount: IMPORTANT: Human-readable amount, NOT smallest units.
               "0.1" = 0.1 USDT, "1" = 1 SOL. Do NOT pass wei/lamports/raw values.
        from_address: Sender wallet address
        to_address: Recipient wallet address
        market: Market/aggregator from quote result
        to_chain: Destination chain (defaults to from_chain)
        slippage: Slippage tolerance percentage (optional)
        deadline: Transaction deadline in seconds (optional, default: API default 600s).
                 Controls how long the transaction remains valid on-chain.
                 Recommended: 300s for safety against sandwich attacks.
        from_symbol: Source token symbol (optional)
        to_symbol: Destination token symbol (optional)
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
    if deadline is not None:
        body["deadline"] = deadline
    if from_symbol:
        body["fromSymbol"] = from_symbol
    if to_symbol:
        body["toSymbol"] = to_symbol
    return _request("/bgw-pro/swapx/pro/swap", body)


@mcp.tool()
def swap_reverse_quote(
    from_chain: str,
    from_contract: str,
    to_contract: str,
    amount: str,
    request_mode: str,
    from_address: str,
    to_address: str,
    fee_rate: float,
    slippage: str | None = None,
    deadline: int | None = None,
    executor_address: str = "",
) -> dict:
    """Get a reverse quote that combines quote + tx building in one call.

    Supports two modes:
    - exactIn: User specifies input amount → system calculates output
    - minAmountOut: User specifies desired minimum output → system calculates required input

    Use minAmountOut when the user says something like "I want at least 10 USDC".

    Args:
        from_chain: Chain identifier (eth, sol, bnb, base, arbitrum, matic, morph)
        from_contract: Source token contract (empty string for native token)
        to_contract: Destination token contract
        amount: IMPORTANT: Human-readable amount, NOT smallest units.
               In exactIn mode this is the input amount.
               In minAmountOut mode this is the desired minimum output.
        request_mode: "exactIn" or "minAmountOut"
        from_address: Sender wallet address
        to_address: Recipient wallet address
        fee_rate: Fee rate as decimal ratio (0.05 = 5%). Must be >= 0. Pass 0 for no fee.
        slippage: Slippage percentage as string (optional, default "0.5")
        deadline: Transaction deadline in seconds (optional, default 600)
        executor_address: If tx sender differs from from_address (optional)
    """
    body: dict[str, Any] = {
        "fromChain": from_chain,
        "fromContract": from_contract,
        "toContract": to_contract,
        "amount": amount,
        "requestMode": request_mode,
        "fromAddress": from_address,
        "toAddress": to_address,
        "feeRate": fee_rate,
    }
    if slippage is not None:
        body["slippage"] = slippage
    if deadline is not None:
        body["deadline"] = deadline
    if executor_address:
        body["executorAddress"] = executor_address
    return _request("/bgw-pro/swapx/pro/swapr", body)


@mcp.tool()
def swap_send(chain: str, txs: list[dict]) -> dict:
    """Broadcast signed transactions via MEV-protected endpoint.

    Final step in swap flow: quote → calldata → sign → send.

    Args:
        chain: Chain name (e.g. sol, eth, bnb)
        txs: List of tx objects with id, chain, rawTx, from, nonce, provider(optional)
    """
    return _request("/bgw-pro/swapx/pro/send", {"chain": chain, "txs": txs})


# ---------------------------------------------------------------------------
# Order Mode — Gasless & Cross-Chain Swaps
# ---------------------------------------------------------------------------

@mcp.tool()
def order_quote(
    from_chain: str,
    from_contract: str,
    to_contract: str,
    amount: str,
    from_address: str,
    to_chain: str = "",
    to_address: str = "",
    fee_rate: str = "",
) -> dict:
    """Get an order-mode swap quote with cross-chain and gasless support.

    Order Mode enables gasless transactions (EIP-7702) and one-step cross-chain swaps.
    Use this instead of swap_quote when you need gasless or cross-chain capabilities.

    Args:
        from_chain: Source chain (eth, sol, bnb, base, arbitrum, matic, morph)
        from_contract: Source token contract address
        to_contract: Destination token contract address
        amount: Human-readable amount (e.g. "10" for 10 USDC)
        from_address: Sender wallet address
        to_chain: Destination chain (defaults to from_chain for same-chain)
        to_address: Recipient address (REQUIRED for cross-chain to non-EVM chains like Solana)
        fee_rate: Optional B2B fee rate for partner commission
    """
    body: dict[str, Any] = {
        "fromChain": from_chain,
        "fromContract": from_contract,
        "fromAmount": amount,
        "toChain": to_chain or from_chain,
        "toContract": to_contract,
        "fromAddress": from_address,
    }
    if to_address:
        body["toAddress"] = to_address
    if fee_rate:
        body["feeRate"] = fee_rate
    return _request("/bgw-pro/swapx/order/getSwapPrice", body)


@mcp.tool()
def order_create(
    from_chain: str,
    from_contract: str,
    to_contract: str,
    amount: str,
    from_address: str,
    to_address: str,
    market: str,
    to_chain: str = "",
    slippage: float | None = None,
    fee_rate: str = "",
    feature: str = "",
) -> dict:
    """Create an order and receive unsigned transaction/signature data.

    Returns either `signatures` (gasless via EIP-7702) or `txs` (normal transactions).
    - signatures array → gasless mode, sign each hash with wallet key
    - txs array → normal mode, sign and broadcast each transaction

    Args:
        from_chain: Source chain
        from_contract: Source token contract
        to_contract: Destination token contract
        amount: Human-readable amount
        from_address: Sender wallet address
        to_address: Recipient wallet address (use target chain format for cross-chain)
        market: Market/aggregator from order_quote result
        to_chain: Destination chain (defaults to from_chain)
        slippage: Slippage tolerance percentage
        fee_rate: Optional B2B fee rate
        feature: Optional feature flag (e.g. "no_gas" for gasless mode)
    """
    body: dict[str, Any] = {
        "fromChain": from_chain,
        "fromContract": from_contract,
        "fromAmount": amount,
        "toChain": to_chain or from_chain,
        "toContract": to_contract,
        "fromAddress": from_address,
        "toAddress": to_address,
        "market": market,
    }
    if slippage is not None:
        body["slippage"] = str(slippage)
    if fee_rate:
        body["feeRate"] = fee_rate
    if feature:
        body["feature"] = feature
    return _request("/bgw-pro/swapx/order/makeSwapOrder", body)


@mcp.tool()
def order_submit(order_id: str, signed_txs: list[str]) -> dict:
    """Submit signed transactions for an order.

    After signing the data from order_create, submit the signatures here.
    For gasless (EIP-7702): submit hex-encoded signatures (0x-prefixed).
    For normal txs: submit serialized signed transactions.

    Args:
        order_id: Order ID from order_create
        signed_txs: List of signed transaction data strings
    """
    return _request("/bgw-pro/swapx/order/submitSwapOrder", {
        "orderId": order_id,
        "signedTxs": signed_txs,
    })


@mcp.tool()
def order_status(order_id: str) -> dict:
    """Query order lifecycle status.

    Status flow: init → processing → success | failed | refunding → refunded

    Returns order details including fromChain, toChain, fromAmount, toAmount,
    receiveAmount (actual amount received on success), and transaction hashes.

    Args:
        order_id: Order ID to query
    """
    return _request("/bgw-pro/swapx/order/getSwapOrder", {"orderId": order_id})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
