#!/usr/bin/env python3
"""
Bitget Wallet MCP Server — exposes Bitget Wallet API as MCP tools.
Uses the Skill internal API (copenapi.bgwapi.io) with SHA256 hash signing.
"""

import hashlib
import json
import os
import time
from typing import Any

import requests
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Config — override via env vars
# ---------------------------------------------------------------------------
BASE_URL = "https://copenapi.bgwapi.io"
WALLET_ID = os.environ.get("BGW_WALLET_ID", "")  # For Social Login Wallet users

# ---------------------------------------------------------------------------
# Signing & HTTP
# ---------------------------------------------------------------------------

def _make_sign(method: str, path: str, body_str: str, ts: str) -> str:
    """BKHmacAuth signature: SHA256(Method + Path + Body + Timestamp)."""
    message = method + path + body_str + ts
    digest = hashlib.sha256(message.encode("utf-8")).hexdigest()
    return "0x" + digest


def _request(path: str, body: dict | None = None) -> dict[str, Any]:
    """POST request with BKHmacAuth signing."""
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(body, separators=(",", ":"), ensure_ascii=False) if body else ""
    sign = _make_sign("POST", path, body_str, ts)
    token_val = WALLET_ID if WALLET_ID else "toc_agent"
    headers = {
        "Content-Type": "application/json",
        "channel": "toc_agent",
        "brand": "toc_agent",
        "clientversion": "10.0.0",
        "language": "en",
        "token": token_val,
        "X-SIGN": sign,
        "X-TIMESTAMP": ts,
    }
    resp = requests.post(
        BASE_URL + path,
        data=body_str or None,
        headers=headers,
        timeout=30,
    )
    if resp.status_code != 200:
        return {"status": -1, "error_code": resp.status_code, "msg": resp.text[:500]}
    return resp.json()


def _request_get(path_with_query: str) -> dict[str, Any]:
    """GET request with BKHmacAuth signing."""
    ts = str(int(time.time() * 1000))
    sign = _make_sign("GET", path_with_query, "", ts)
    token_val = WALLET_ID if WALLET_ID else "toc_agent"
    headers = {
        "channel": "toc_agent",
        "brand": "toc_agent",
        "clientversion": "10.0.0",
        "language": "en",
        "token": token_val,
        "X-SIGN": sign,
        "X-TIMESTAMP": ts,
    }
    resp = requests.get(BASE_URL + path_with_query, headers=headers, timeout=30)
    if resp.status_code != 200:
        return {"status": -1, "error_code": resp.status_code, "msg": resp.text[:500]}
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
    instructions=(
        "On-chain data queries, token security audits, swap operations, and balance lookups "
        "via Bitget Wallet API. "
        "Supports Ethereum, Solana, BNB Chain, Base, Arbitrum, Tron, TON, Sui, Optimism, Polygon, Morph. "
        "Swap flow: quote → confirm → make_order → (sign externally) → send → get_order_details. "
        "Pre-trade safety: use check_swap_token before swapping unknown tokens. "
        "Token analysis tools: search tokens by keyword, get detailed market info (price, mcap, FDV, liquidity, holders, "
        "narratives), check developer history and rug status, view K-line charts with smart money/KOL/developer overlays, "
        "analyze trading dynamics, transaction lists, holder distribution, and profit analysis. "
        "Launchpad scanning: discover new tokens on launchpad platforms (pump.fun, etc.) with filters for market cap, "
        "holders, liquidity, and bonding curve progress. "
        "Smart money tracking: view top profitable addresses, profit/loss analysis per token, and track KOL/smart money "
        "trading activity on K-line charts. "
        "RWA (Real World Asset) stock trading: discover available stocks (NVDA, TSLA, AAPL, etc.), get stock info, "
        "market status, K-line charts, order prices, trading config, and portfolio holdings on BNB/ETH chains. "
        "Smart money discovery: find top KOL and smart money addresses with performance filters (PnL, win rate, "
        "trade count) across chains. "
        "Balance: batch query token balances and USD values across chains."
    ),
)


# ---------------------------------------------------------------------------
# Market Data Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def token_info(chain: str, contract: str = "") -> dict:
    """Get detailed token information including price, market cap, supply, holders, and social links.

    Args:
        chain: Chain identifier (eth, sol, bnb, base, arbitrum, trx, ton, suinet, optimism)
        contract: Token contract address. Use empty string for native tokens (ETH, SOL, BNB, etc.)
    """
    result = _request("/market/v3/coin/batchGetBaseInfo", {"list": [{"chain": chain, "contract": contract}]})
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
    result = _request("/market/v3/coin/batchGetBaseInfo", {"list": [{"chain": chain, "contract": contract}]})
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
    return _request("/market/v3/coin/batchGetBaseInfo", {"list": tokens})


@mcp.tool()
def kline(chain: str, contract: str, period: str = "1h", size: int = 24) -> dict:
    """Get K-line (candlestick) data for a token.

    Args:
        chain: Chain identifier
        contract: Token contract address
        period: Time period (1s, 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
        size: Number of candles to return (max 1440)
    """
    return _request("/market/v3/coin/getKline", {
        "chain": chain, "contract": contract, "period": period, "size": size
    })


@mcp.tool()
def tx_info(chain: str, contract: str) -> dict:
    """Get token transaction statistics (5m/1h/4h/24h volume, buyers, sellers).

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/market/v3/coin/getTxInfo", {"chain": chain, "contract": contract})


@mcp.tool()
def batch_tx_info(tokens: list[dict]) -> dict:
    """Batch get transaction statistics for multiple tokens.

    Args:
        tokens: List of {"chain": "sol", "contract": "..."} objects (max 100).
    """
    return _request("/market/v3/coin/batchGetTxInfo", {"list": tokens})


@mcp.tool()
def historical_coins(create_time: str, limit: int = 10) -> dict:
    """Get token list by timestamp (paginated). Useful for discovering new tokens.

    Args:
        create_time: Timestamp string (e.g. "2025-06-17 06:55:28")
        limit: Number of records to return (default 10)
    """
    return _request("/market/v3/historical-coins", {"createTime": create_time, "limit": limit})


@mcp.tool()
def rankings(name: str = "topGainers") -> dict:
    """Get token rankings.

    Args:
        name: Ranking type — "topGainers" or "topLosers"
    """
    return _request("/market/v3/topRank/detail", {"name": name})


@mcp.tool()
def liquidity(chain: str, contract: str) -> dict:
    """Get liquidity pool information for a token.

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/market/v3/poolList", {"chain": chain, "contract": contract})


@mcp.tool()
def security_audit(chain: str, contract: str) -> dict:
    """Run a security audit on a token contract (honeypot detection, permission checks, blacklist).

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/market/v3/coin/security/audits", {
        "list": [{"chain": chain, "contract": contract}], "source": "bg"
    })


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
    return _request("/market/v3/coin/search", body)


@mcp.tool()
def search_tokens_v2(keyword: str, chain: str = "") -> dict:
    """Search tokens by keyword using v2 API (broader results including DEX tokens).

    Args:
        keyword: Search keyword (token name, symbol, or contract address)
        chain: Filter by chain (optional)
    """
    body: dict[str, Any] = {"keyword": keyword}
    if chain:
        body["chain"] = chain
    return _request("/market/v2/search/tokens", body)


@mcp.tool()
def coin_market_info(chain: str, contract: str) -> dict:
    """Get detailed market information for a token including price, market cap, FDV, liquidity, holders, price changes, pool list, and narratives.

    Args:
        chain: Chain identifier (eth, sol, bnb, base, arbitrum, trx, ton, suinet, optimism)
        contract: Token contract address
    """
    return _request("/market/v3/coin/getMarketInfo", {"chain": chain, "contract": contract})


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
    return _request("/market/v3/coin/dev", body)


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
    return _request("/market/v3/launchpad/tokens", body)


# ---------------------------------------------------------------------------
# Token Analysis Tools (v2)
# ---------------------------------------------------------------------------

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
    return _request("/market/v2/coin/SimpleKline", body)


@mcp.tool()
def trading_dynamics(chain: str, contract: str) -> dict:
    """Get trading dynamics for a token (buy/sell pressure, whale activity, etc.).

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/market/v2/coin/GetTradingDynamics", {"chain": chain, "contract": contract})


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
    return _request("/market/v2/coin/TransactionList", body)


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
    return _request("/market/v2/GetHoldersInfo", body)


@mcp.tool()
def profit_address_analysis(chain: str, contract: str) -> dict:
    """Get profit/loss analysis of addresses holding a token (distribution of profitable vs losing addresses).

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/market/v2/coin/GetProfitAddressAnalysis", {"chain": chain, "contract": contract})


@mcp.tool()
def top_profit(chain: str, contract: str) -> dict:
    """Get top profitable addresses for a token (who made the most money trading this token).

    Args:
        chain: Chain identifier
        contract: Token contract address
    """
    return _request("/market/v2/coin/GetTopProfit", {"chain": chain, "contract": contract})


@mcp.tool()
def smart_money_addresses(
    group_ids: list[int] | None = None,
    data_period: str = "7d",
    sort_field: str = "pnl_usd",
    sort_order: str = "desc",
    param_filters: dict | None = None,
    page: int = 1,
    limit: int = 30,
) -> dict:
    """Find KOL and smart money addresses with performance filters.

    Args:
        group_ids: Role filter — [0]=all, [1]=smart money, [2]=KOL (default all)
        data_period: Statistics window — "24h", "7d" (default), "30d"
        sort_field: Sort by — "pnl_usd" (default), "win_rate", "trade_count", "last_activity_time"
        sort_order: "desc" (default) or "asc"
        param_filters: Filter map. Keys: chain (values list), pnl_usd (min/max), win_rate (min/max 0-100), trade_count (min/max).
                       Example: {"chain": {"values": ["sol"]}, "win_rate": {"min": 70, "max": 100}}
        page: Page number (default 1)
        limit: Page size, max 30 (default 30)
    """
    body: dict[str, Any] = {
        "data_period": data_period,
        "sort_field": sort_field,
        "sort_order": sort_order,
        "page": page,
        "limit": limit,
    }
    if group_ids is not None:
        body["recommend_group_ids"] = group_ids
    if param_filters is not None:
        body["param_filters"] = param_filters
    return _request("/market/v2/monitor/recommend-group/address/list", body)


# ---------------------------------------------------------------------------
# RWA (Real World Asset) Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def rwa_ticker_list(chain: str, user_address: str = "", keyword: str = "") -> dict:
    """Get available RWA stock tickers. Optionally include user balance.

    Args:
        chain: Chain — "bnb" or "eth"
        user_address: User wallet address (optional, to include balance info)
        keyword: Search keyword for stock name or contract (optional)
    """
    body: dict[str, Any] = {"chain": chain}
    if user_address:
        body["user_address"] = user_address
    if keyword:
        body["key_word"] = keyword
    return _request("/market/v2/rwa/GetUserTickerSelector", body)


@mcp.tool()
def rwa_config(address_list: list[dict]) -> dict:
    """Get RWA trading config: supported stablecoins, slippage, amount limits, gas info.

    Args:
        address_list: List of {"chain": "bnb", "address": "0x..."} objects for each chain
    """
    return _request("/swap-go/rwa/getConfig", {"addressList": address_list})


@mcp.tool()
def rwa_stock_info(ticker: str) -> dict:
    """Get RWA stock info: market status, trading limits, chain assets, description.

    Args:
        ticker: Stock ticker (e.g. "NVDAon", "TSLAon", "AAPLon")
    """
    import urllib.parse
    path = f"/market/v2/rwa/StockInfo?ticker={urllib.parse.quote(ticker)}"
    return _request_get(path)


@mcp.tool()
def rwa_order_price(
    ticker: str,
    chain: str,
    side: str,
    tx_coin_contract: str,
    user_address: str,
) -> dict:
    """Get display buy/sell price for an RWA stock (pre-trade display, not actual quote).

    Args:
        ticker: Stock ticker (e.g. "NVDAon")
        chain: Chain — "bnb" or "eth"
        side: "buy" or "sell"
        tx_coin_contract: Stablecoin contract from rwa_config (fromTokenList/toTokenList)
        user_address: User wallet address
    """
    return _request("/market/v2/rwa/StockOrderPrice", {
        "ticker": ticker,
        "chain": chain,
        "side": side,
        "tx_coin_contract": tx_coin_contract,
        "user_address": user_address,
    })


@mcp.tool()
def rwa_kline(chain: str, contract: str, period: str = "1d", size: int | None = None) -> dict:
    """Get K-line data for an RWA stock.

    Args:
        chain: Use "rwa" for RWA stocks
        contract: Stock ticker (e.g. "NVDAon")
        period: Time period (e.g. "1d", "1h")
        size: Number of candles (optional)
    """
    body: dict[str, Any] = {"chain": chain, "contract": contract, "period": period}
    if size is not None:
        body["size"] = size
    return _request("/market/v2/coin/Kline", body)


@mcp.tool()
def rwa_my_holdings(user_address: str) -> dict:
    """Get user's RWA stock holdings.

    Args:
        user_address: User wallet address
    """
    return _request("/market/v2/rwa/GetMyHoldings", {"user_address": user_address})


# ---------------------------------------------------------------------------
# Swap Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def swap_quote(
    from_address: str,
    from_chain: str,
    from_symbol: str,
    from_contract: str,
    from_amount: str,
    to_chain: str,
    to_symbol: str,
    to_contract: str,
    to_address: str = "",
    tab_type: str = "swap",
    slippage: str = "",
) -> dict:
    """Get a swap quote with best route and estimated output.

    This is step 1 of the swap flow: quote → confirm → make_order → (sign) → send.

    Args:
        from_address: Sender wallet address
        from_chain: Source chain identifier (eth, sol, bnb, base, arbitrum, etc.)
        from_symbol: Source token symbol (e.g. "ETH", "SOL", "USDT")
        from_contract: Source token contract address (empty string for native tokens)
        from_amount: Human-readable amount, NOT smallest units.
                    "0.1" = 0.1 USDT, "1" = 1 SOL. Do NOT pass wei/lamports/raw values.
        to_chain: Destination chain identifier
        to_symbol: Destination token symbol
        to_contract: Destination token contract address
        to_address: Recipient wallet address (defaults to from_address if empty)
        tab_type: Swap type — "swap" for same-chain, "bridge" for cross-chain (default "swap")
        slippage: Slippage tolerance as string, e.g. "0.5" for 0.5% (default "" for auto)
    """
    body: dict[str, Any] = {
        "fromAddress": from_address,
        "fromChain": from_chain,
        "fromSymbol": from_symbol,
        "fromContract": from_contract,
        "fromAmount": from_amount,
        "toChain": to_chain or from_chain,
        "toSymbol": to_symbol,
        "toContract": to_contract or "",
        "tab_type": tab_type,
        "publicKey": "",
        "slippage": slippage,
        "toAddress": to_address or from_address,
        "requestId": str(int(time.time() * 1000)),
    }
    return _request("/swap-go/swapx/quote", body)


@mcp.tool()
def swap_confirm(
    from_chain: str,
    from_symbol: str,
    from_contract: str,
    from_amount: str,
    from_address: str,
    to_chain: str,
    to_symbol: str,
    to_contract: str,
    to_address: str,
    market: str,
    protocol: str,
    slippage: str,
    gas_level: str = "average",
    features: list[str] | None = None,
    last_out_amount: str = "",
    recommend_slippage: str = "",
) -> dict:
    """Confirm a swap quote (2nd quote step). Uses market/protocol from initial quote result.

    This is step 2 of the swap flow: quote → confirm → make_order → (sign) → send.

    Args:
        from_chain: Source chain identifier
        from_symbol: Source token symbol
        from_contract: Source token contract (empty string for native token)
        from_amount: Human-readable amount, NOT smallest units.
        from_address: Sender wallet address
        to_chain: Destination chain identifier
        to_symbol: Destination token symbol
        to_contract: Destination token contract
        to_address: Recipient wallet address
        market: Market ID from quote result (quoteResults[].market.id)
        protocol: Protocol from quote result (quoteResults[].market.protocol)
        slippage: Slippage tolerance as string, e.g. "0.5" for 0.5%
        gas_level: Gas level — "average" or "fast" (default "average")
        features: Gas payment mode — ["user_gas"] (user pays gas) or ["no_gas"] (gasless).
                  Default ["user_gas"]. Use ["no_gas"] only when native balance is insufficient.
        last_out_amount: Last quoted output amount (optional, for refresh)
        recommend_slippage: Recommended slippage from quote (optional, defaults to slippage)
    """
    body: dict[str, Any] = {
        "fromChain": from_chain,
        "fromSymbol": from_symbol,
        "fromContract": from_contract,
        "fromAmount": from_amount,
        "fromAddress": from_address,
        "toChain": to_chain,
        "toSymbol": to_symbol,
        "toContract": to_contract or "",
        "toAddress": to_address,
        "market": market,
        "slippage": slippage,
        "gasLevel": gas_level,
        "features": features or ["user_gas"],
        "protocol": protocol,
        "recommendSlippage": recommend_slippage or slippage,
        "lastOutAmount": last_out_amount,
        "mevProtection": {
            "chain": from_chain,
            "mevFee": "0",
            "amountMin": from_amount,
            "mevTarget": True,
            "mode": "smart",
        },
    }
    return _request("/swap-go/swapx/confirm", body)


@mcp.tool()
def swap_make_order(
    order_id: str,
    from_chain: str,
    from_contract: str,
    from_symbol: str,
    from_address: str,
    to_chain: str,
    to_contract: str,
    to_symbol: str,
    to_address: str,
    from_amount: str,
    slippage: str,
    market: str,
    protocol: str,
    source: str = "agent",
) -> dict:
    """Create a swap order and receive unsigned transactions to sign.

    This is step 3 of the swap flow: quote → confirm → make_order → (sign) → send.
    Returns unsigned transaction data (data.txs) that must be signed by the wallet.

    Args:
        order_id: Order ID from confirm result (data.orderId)
        from_chain: Source chain identifier
        from_contract: Source token contract (empty string for native token)
        from_symbol: Source token symbol
        from_address: Sender wallet address
        to_chain: Destination chain identifier
        to_contract: Destination token contract
        to_symbol: Destination token symbol
        to_address: Recipient wallet address
        from_amount: Human-readable amount
        slippage: Slippage tolerance as string
        market: Market ID from confirm result
        protocol: Protocol from confirm result
        source: Source identifier (default "agent")
    """
    body: dict[str, Any] = {
        "orderId": order_id,
        "fromChain": from_chain,
        "fromContract": from_contract,
        "fromSymbol": from_symbol,
        "fromAddress": from_address,
        "toChain": to_chain,
        "toContract": to_contract or "",
        "toSymbol": to_symbol,
        "toAddress": to_address,
        "fromAmount": from_amount,
        "slippage": slippage,
        "market": market,
        "protocol": protocol,
        "source": source,
    }
    return _request("/swap-go/swapx/makeOrder", body)


@mcp.tool()
def swap_send(order_id: str, txs: list[dict]) -> dict:
    """Submit signed transactions for a swap order.

    This is the final step of the swap flow: quote → confirm → make_order → (sign) → send.

    Args:
        order_id: Order ID from swap_make_order result
        txs: List of signed transaction objects
    """
    return _request("/swap-go/swapx/send", {"orderId": order_id, "txs": txs})


@mcp.tool()
def swap_get_order_details(order_id: str) -> dict:
    """Query swap order status and details.

    Status flow: init → processing → success | failed | refunding → refunded

    Args:
        order_id: Order ID to query
    """
    return _request("/swap-go/swapx/getOrderDetails", {"orderId": order_id})


@mcp.tool()
def check_swap_token(token_list: list[dict]) -> dict:
    """Pre-trade risk check for tokens before swapping.

    Use this to check if a token is safe to trade (honeypot, tax, blacklist, etc.)
    before initiating a swap.

    Args:
        token_list: List of token objects, each with {"chain": "...", "contract": "...", "symbol": "..."}.
                    The body key sent to the API is "list", not "tokens".
    """
    return _request("/swap-go/swapx/checkSwapToken", {"list": token_list})


@mcp.tool()
def get_token_list(chain: str) -> dict:
    """Get popular/recommended tokens for a specific chain.

    Useful for discovering commonly traded tokens on a chain.

    Args:
        chain: Chain identifier (eth, sol, bnb, base, arbitrum, trx, ton, suinet, optimism)
    """
    return _request("/swap-go/swapx/getTokenList", {"chain": chain, "isAllNetWork": 1})


# ---------------------------------------------------------------------------
# Balance Tool
# ---------------------------------------------------------------------------

@mcp.tool()
def balance(wallets: list[dict], currency: str = "usd") -> dict:
    """Batch query token balances and USD values across chains.

    Args:
        wallets: List of wallet objects, each with:
                 - chain: Chain identifier (eth, sol, bnb, etc.)
                 - address: Wallet address to query
                 - contract: List of contract address strings. Use [""] for native token only,
                            or ["", "0xcontract..."] for native + specific tokens.
        currency: Currency for USD conversion (default "usd")
    """
    return _request("/user/wallet/batchV2", {
        "list": wallets,
        "nocache": True,
        "appointCurrency": currency,
        "noreport": True,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
