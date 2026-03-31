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
    instructions="On-chain data queries, token security audits, swap quotes, and Order Mode (gasless + cross-chain) "
                 "swaps via Bitget Wallet ToB API. "
                 "Supports Ethereum, Solana, BNB Chain, Base, Arbitrum, Tron, TON, Sui, Optimism, Polygon, Morph. "
                 "Order Mode enables gasless transactions (EIP-7702) and one-step cross-chain swaps. "
                 "Token analysis tools: search tokens by keyword, get detailed market info (price, mcap, FDV, liquidity, holders, "
                 "narratives), check developer history and rug status, view K-line charts with smart money/KOL/developer overlays, "
                 "analyze trading dynamics, transaction lists, holder distribution, and profit analysis. "
                 "Launchpad scanning: discover new tokens on launchpad platforms (pump.fun, etc.) with filters for market cap, "
                 "holders, liquidity, and bonding curve progress. "
                 "Smart money tracking: view top profitable addresses, profit/loss analysis per token, and track KOL/smart money "
                 "trading activity on K-line charts.",
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
def swap_send(chain: str, txs: list[dict]) -> dict:
    """Broadcast signed transactions via MEV-protected endpoint.

    Final step in swap flow: quote → calldata → sign → send.

    Args:
        chain: Chain name (e.g. sol, eth, bnb)
        txs: List of tx objects with id, chain, rawTx, from, nonce, provider(optional)
    """
    return _request("/bgw-pro/swapx/pro/send", {"chain": chain, "txs": txs})


# ---------------------------------------------------------------------------
# Token Analysis, Launchpad & Smart Money Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def search_tokens(keyword: str, chain: str = "", limit: int = 20, order_by: str = "") -> dict:
    """Search for tokens by keyword (name, symbol, or contract address).

    Args:
        keyword: Search keyword (token name, symbol, or contract address)
        chain: Filter by chain identifier (optional)
        limit: Maximum number of results (default 20)
        order_by: Sort order (e.g. "market_cap") (optional)
    """
    body: dict[str, Any] = {"keyword": keyword, "limit": limit}
    if chain:
        body["chain"] = chain
    if order_by:
        body["orderBy"] = order_by
    return _request("/bgw-pro/market/v3/coin/search", body)


@mcp.tool()
def coin_market_info(chain: str, contract: str) -> dict:
    """Get detailed market information for a token including price, market cap, FDV, liquidity, holders, price changes, pool list, and narratives.

    Args:
        chain: Chain identifier (eth, sol, bnb, base, arbitrum, trx, ton, suinet, optimism)
        contract: Token contract address
    """
    return _request("/bgw-pro/market/v3/coin/getMarketInfo", {"chain": chain, "contract": contract})


@mcp.tool()
def coin_dev(chain: str, contract: str, limit: int = 30, is_migrated: bool | None = None) -> dict:
    """Get the developer's historical projects with rug status. Useful for checking if a token's dev has a history of rugging.

    Args:
        chain: Chain identifier
        contract: Token contract address
        limit: Number of records to return (default 30)
        is_migrated: Filter by migration status (optional)
    """
    body: dict[str, Any] = {"chain": chain, "contract": contract, "limit": limit}
    if is_migrated is not None:
        body["isMigrated"] = is_migrated
    return _request("/bgw-pro/market/v3/coin/dev", body)


@mcp.tool()
def launchpad_tokens(
    chain: str = "sol",
    platforms: list[str] | None = None,
    stage: int | None = None,
    mc_min: int | None = None,
    mc_max: int | None = None,
    holder_min: int | None = None,
    holder_max: int | None = None,
    lp_min: int | None = None,
    lp_max: int | None = None,
    progress_min: float | None = None,
    progress_max: float | None = None,
    keywords: str = "",
    limit: int = 100,
) -> dict:
    """Get launchpad tokens (e.g. pump.fun) with various filters.

    Stage values: 0=new, 1=launching, 2=launched.

    Args:
        chain: Chain identifier (default "sol")
        platforms: Filter by launchpad platforms (optional)
        stage: Token stage — 0=new, 1=launching, 2=launched (optional)
        mc_min: Minimum market cap filter (optional)
        mc_max: Maximum market cap filter (optional)
        holder_min: Minimum holder count filter (optional)
        holder_max: Maximum holder count filter (optional)
        lp_min: Minimum liquidity filter (optional)
        lp_max: Maximum liquidity filter (optional)
        progress_min: Minimum bonding curve progress 0.0-1.0 (optional)
        progress_max: Maximum bonding curve progress 0.0-1.0 (optional)
        keywords: Search keywords (optional)
        limit: Maximum number of results (default 100)
    """
    body: dict[str, Any] = {"chain": chain, "limit": limit}
    if platforms is not None:
        body["platforms"] = platforms
    if stage is not None:
        body["stage"] = stage
    if mc_min is not None:
        body["mcMin"] = mc_min
    if mc_max is not None:
        body["mcMax"] = mc_max
    if holder_min is not None:
        body["holderMin"] = holder_min
    if holder_max is not None:
        body["holderMax"] = holder_max
    if lp_min is not None:
        body["lpMin"] = lp_min
    if lp_max is not None:
        body["lpMax"] = lp_max
    if progress_min is not None:
        body["progressMin"] = progress_min
    if progress_max is not None:
        body["progressMax"] = progress_max
    if keywords:
        body["keywords"] = keywords
    return _request("/bgw-pro/market/v3/launchpad/tokens", body)


@mcp.tool()
def simple_kline(
    chain: str,
    contract: str,
    period: str = "5m",
    size: int | None = None,
    user_address: str = "",
    is_show_kol: bool = True,
    is_show_smart_money: bool = True,
    is_show_developer: bool = True,
) -> dict:
    """Get simplified K-line data with smart money, KOL, and developer trading overlays.

    Args:
        chain: Chain identifier
        contract: Token contract address
        period: Time period (1s, 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
        size: Number of candles to return (optional)
        user_address: User address to highlight on chart (optional)
        is_show_kol: Show KOL trading activity overlay (default True)
        is_show_smart_money: Show smart money trading activity overlay (default True)
        is_show_developer: Show developer trading activity overlay (default True)
    """
    body: dict[str, Any] = {
        "chain": chain,
        "contract": contract,
        "period": period,
        "isShowKol": is_show_kol,
        "isShowSmartMoney": is_show_smart_money,
        "isShowDeveloper": is_show_developer,
    }
    if size is not None:
        body["size"] = size
    if user_address:
        body["userAddress"] = user_address
    return _request("/bgw-pro/market/v2/coin/SimpleKline", body)


@mcp.tool()
def trading_dynamics(chain: str, contract: str) -> dict:
    """Get trading dynamics for a token (buy/sell pressure, whale activity, etc.).

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/bgw-pro/market/v2/coin/GetTradingDynamics", {"chain": chain, "contract": contract})


@mcp.tool()
def transaction_list(
    chain: str,
    contract: str,
    page: int = 1,
    size: int = 20,
    side: str = "",
    only_barrage: bool = False,
    period: str = "",
    txnfrom_tags: list[str] | None = None,
) -> dict:
    """Get recent transactions for a token with filtering options.

    Args:
        chain: Chain identifier
        contract: Token contract address
        page: Page number (default 1)
        size: Page size (default 20)
        side: Filter by side — "buy" or "sell" (optional)
        only_barrage: Show only large/notable transactions (default False)
        period: Time period filter (optional)
        txnfrom_tags: Filter by sender tags, e.g. ["smart_money", "kol"] (optional)
    """
    body: dict[str, Any] = {
        "chain": chain,
        "contract": contract,
        "page": page,
        "size": size,
        "onlyBarrage": only_barrage,
    }
    if side:
        body["side"] = side
    if period:
        body["period"] = period
    if txnfrom_tags is not None:
        body["txnfromTags"] = txnfrom_tags
    return _request("/bgw-pro/market/v2/coin/TransactionList", body)


@mcp.tool()
def holders_info(
    chain: str,
    contract: str,
    sort: str = "holding_desc",
    special_holder_key: str = "",
    address_tags: list[str] | None = None,
) -> dict:
    """Get holder distribution and top holders for a token.

    Args:
        chain: Chain identifier
        contract: Token contract address
        sort: Sort order (default "holding_desc")
        special_holder_key: Filter by special holder type (optional)
        address_tags: Filter by address tags (optional)
    """
    body: dict[str, Any] = {"chain": chain, "contract": contract, "sort": sort}
    if special_holder_key:
        body["specialHolderKey"] = special_holder_key
    if address_tags is not None:
        body["addressTags"] = address_tags
    return _request("/bgw-pro/market/v2/GetHoldersInfo", body)


@mcp.tool()
def profit_address_analysis(chain: str, contract: str) -> dict:
    """Get profit/loss analysis of addresses holding a token (distribution of profitable vs losing addresses).

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/bgw-pro/market/v2/coin/GetProfitAddressAnalysis", {"chain": chain, "contract": contract})


@mcp.tool()
def top_profit(chain: str, contract: str) -> dict:
    """Get top profitable addresses for a token (who made the most money trading this token).

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/bgw-pro/market/v2/coin/GetTopProfit", {"chain": chain, "contract": contract})


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
