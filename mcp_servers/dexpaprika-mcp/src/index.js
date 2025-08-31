import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import fetch from 'node-fetch';
import { z } from 'zod';

// Base URL for DexPaprika API
const API_BASE_URL = 'https://api.dexpaprika.com';

// Helper function to fetch data from DexPaprika API
async function fetchFromAPI(endpoint) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
      if (response.status === 410) {
        throw new Error(
          'This endpoint has been permanently removed. Please use network-specific endpoints instead. ' +
          'For example, use /networks/{network}/pools instead of /pools. ' +
          'Get available networks first using the getNetworks function.'
        );
      }
      if (response.status === 429) {
        throw new Error(
          'Rate limit exceeded. You have reached the maximum number of requests allowed for the free tier. ' +
          'To increase your rate limits and access additional features, please consider upgrading to a paid plan at https://docs.dexpaprika.com/'
        );
      }
      throw new Error(`API request failed with status ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching from API: ${error.message}`);
    throw error;
  }
}

// Helper to format response for MCP
function formatMcpResponse(data) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(data)
      }
    ]
  };
}

// MCP server instance
const server = new McpServer({
  name: 'dexpaprika-mcp',
  version: '1.1.0',
  description: 'MCP server for accessing DexPaprika API data for decentralized exchanges and tokens',
});

/* 
 * IMPORTANT FOR AI ASSISTANTS:
 * 
 * WORKFLOW FOR GETTING POOL DATA:
 * 1. ALWAYS call getNetworks() first to see available networks
 * 2. Use getNetworkPools() to get pools on specific networks (there is NO global pools function)
 * 3. For cross-network searches, use search() function
 * 
 * KEY FUNCTIONS:
 * - getNetworks: REQUIRED first step, returns valid network IDs
 * - getNetworkPools: PRIMARY pool function (replaces any "getTopPools" concept)
 * - search: Cross-network search when network is unknown
 * 
 * THERE IS NO "getTopPools" or "getAllPools" function - always use network-specific queries!
 */

// getNetworks
server.tool(
  'getNetworks',
  'REQUIRED FIRST STEP: Get all supported blockchain networks. Always call this first to see available networks before using any network-specific functions. Returns network IDs like "ethereum", "solana", etc.',
  {},
  async () => {
    const data = await fetchFromAPI('/networks');
    return formatMcpResponse(data);
  }
);

// getNetworkDexes
server.tool(
  'getNetworkDexes',
  'Get available DEXes on a specific network. First call getNetworks to see valid network IDs.',
  {
    network: z.string().describe('Network ID from getNetworks (e.g., "ethereum", "solana")'),
    page: z.number().optional().default(0).describe('Page number for pagination'),
    limit: z.number().optional().default(10).describe('Number of items per page')
  },
  async ({ network, page, limit }) => {
    const data = await fetchFromAPI(`/networks/${network}/dexes?page=${page}&limit=${limit}`);
    return formatMcpResponse(data);
  }
);

// getNetworkPools - This is now the primary way to get pools
server.tool(
  'getNetworkPools',
  'PRIMARY POOL FUNCTION: Get top liquidity pools on a specific network. This is the MAIN way to get pool data - there is NO global pools function. Use this instead of any "getTopPools" or "getAllPools" concepts.',
  {
    network: z.string().describe('Network ID from getNetworks (required) - e.g., "ethereum", "solana"'),
    page: z.number().optional().default(0).describe('Page number for pagination'),
    limit: z.number().optional().default(10).describe('Number of items per page (max 100)'),
    sort: z.enum(['asc', 'desc']).optional().default('desc').describe('Sort order'),
    orderBy: z.enum(['volume_usd', 'price_usd', 'transactions', 'last_price_change_usd_24h', 'created_at']).optional().default('volume_usd').describe('Field to order by')
  },
  async ({ network, page, limit, sort, orderBy }) => {
    const data = await fetchFromAPI(`/networks/${network}/pools?page=${page}&limit=${limit}&sort=${sort}&order_by=${orderBy}`);
    return formatMcpResponse(data);
  }
);

// getDexPools
server.tool(
  'getDexPools',
  'Get pools from a specific DEX on a network. First use getNetworks, then getNetworkDexes to find valid DEX IDs.',
  {
    network: z.string().describe('Network ID from getNetworks (e.g., "ethereum", "solana")'),
    dex: z.string().describe('DEX identifier from getNetworkDexes (e.g., "uniswap_v3")'),
    page: z.number().optional().default(0).describe('Page number for pagination'),
    limit: z.number().optional().default(10).describe('Number of items per page (max 100)'),
    sort: z.enum(['asc', 'desc']).optional().default('desc').describe('Sort order'),
    orderBy: z.enum(['volume_usd', 'price_usd', 'transactions', 'last_price_change_usd_24h', 'created_at']).optional().default('volume_usd').describe('Field to order by')
  },
  async ({ network, dex, page, limit, sort, orderBy }) => {
    const data = await fetchFromAPI(`/networks/${network}/dexes/${dex}/pools?page=${page}&limit=${limit}&sort=${sort}&order_by=${orderBy}`);
    return formatMcpResponse(data);
  }
);

// getPoolDetails
server.tool(
  'getPoolDetails',
  'Get detailed information about a specific pool. Requires network ID from getNetworks and a pool address.',
  {
    network: z.string().describe('Network ID from getNetworks (e.g., "ethereum", "solana")'),
    poolAddress: z.string().describe('Pool address or identifier'),
    inversed: z.boolean().optional().default(false).describe('Whether to invert the price ratio')
  },
  async ({ network, poolAddress, inversed }) => {
    const data = await fetchFromAPI(`/networks/${network}/pools/${poolAddress}?inversed=${inversed}`);
    return formatMcpResponse(data);
  }
);

// getTokenDetails
server.tool(
  'getTokenDetails',
  'Get detailed information about a specific token on a network. First use getNetworks to get valid network IDs.',
  {
    network: z.string().describe('Network ID from getNetworks (e.g., "ethereum", "solana")'),
    tokenAddress: z.string().describe('Token address or identifier')
  },
  async ({ network, tokenAddress }) => {
    const data = await fetchFromAPI(`/networks/${network}/tokens/${tokenAddress}`);
    return formatMcpResponse(data);
  }
);

// getTokenPools
server.tool(
  'getTokenPools',
  'Get liquidity pools containing a specific token on a network. Great for finding where a token is traded.',
  {
    network: z.string().describe('Network ID from getNetworks (e.g., "ethereum", "solana")'),
    tokenAddress: z.string().describe('Token address or identifier'),
    page: z.number().optional().default(0).describe('Page number for pagination'),
    limit: z.number().optional().default(10).describe('Number of items per page (max 100)'),
    sort: z.enum(['asc', 'desc']).optional().default('desc').describe('Sort order'),
    orderBy: z.enum(['volume_usd', 'price_usd', 'transactions', 'last_price_change_usd_24h', 'created_at']).optional().default('volume_usd').describe('Field to order by'),
    reorder: z.boolean().optional().describe('If true, reorders the pool so that the specified token becomes the primary token for all metrics'),
    address: z.string().optional().describe('Filter pools that contain this additional token address')
  },
  async ({ network, tokenAddress, page, limit, sort, orderBy, reorder, address }) => {
    let endpoint = `/networks/${network}/tokens/${tokenAddress}/pools?page=${page}&limit=${limit}&sort=${sort}&order_by=${orderBy}`;
    if (reorder !== undefined) {
      endpoint += `&reorder=${reorder}`;
    }
    if (address) {
      endpoint += `&address=${encodeURIComponent(address)}`;
    }
    const data = await fetchFromAPI(endpoint);
    return formatMcpResponse(data);
  }
);

// getPoolOHLCV
server.tool(
  'getPoolOHLCV',
  'Get historical price data (OHLCV) for a pool - essential for price analysis, backtesting, and visualization. Requires network and pool address.',
  {
    network: z.string().describe('Network ID from getNetworks (e.g., "ethereum", "solana")'),
    poolAddress: z.string().describe('Pool address or identifier'),
    start: z.string().describe('Start time for historical data (Unix timestamp, RFC3339 timestamp, or yyyy-mm-dd format)'),
    end: z.string().optional().describe('End time for historical data (max 1 year from start)'),
    limit: z.number().optional().default(1).describe('Number of data points to retrieve (max 366) - adjust for different analysis needs'),
    interval: z.string().optional().default('24h').describe('Interval granularity: 1m, 5m, 10m, 15m, 30m, 1h, 6h, 12h, 24h'),
    inversed: z.boolean().optional().default(false).describe('Whether to invert the price ratio for alternative pair perspective (e.g., ETH/USDC vs USDC/ETH)')
  },
  async ({ network, poolAddress, start, end, limit, interval, inversed }) => {
    let endpoint = `/networks/${network}/pools/${poolAddress}/ohlcv?start=${encodeURIComponent(start)}&interval=${interval}&limit=${limit}&inversed=${inversed}`;
    if (end) {
      endpoint += `&end=${encodeURIComponent(end)}`;
    }
    const data = await fetchFromAPI(endpoint);
    return formatMcpResponse(data);
  }
);

// getPoolTransactions
server.tool(
  'getPoolTransactions',
  'Get recent transactions for a specific pool. Shows swaps, adds, removes. Requires network and pool address.',
  {
    network: z.string().describe('Network ID from getNetworks (e.g., "ethereum", "solana")'),
    poolAddress: z.string().describe('Pool address or identifier'),
    page: z.number().optional().default(0).describe('Page number for pagination (up to 100 pages)'),
    limit: z.number().optional().default(10).describe('Number of items per page (max 100)'),
    cursor: z.string().optional().describe('Transaction ID used for cursor-based pagination')
  },
  async ({ network, poolAddress, page, limit, cursor }) => {
    let endpoint = `/networks/${network}/pools/${poolAddress}/transactions?page=${page}&limit=${limit}`;
    if (cursor) {
      endpoint += `&cursor=${encodeURIComponent(cursor)}`;
    }
    const data = await fetchFromAPI(endpoint);
    return formatMcpResponse(data);
  }
);

// search
server.tool(
  'search',
  'Search across ALL networks for tokens, pools, and DEXes by name, symbol, or address. Good starting point when you don\'t know the specific network.',
  {
    query: z.string().describe('Search term (e.g., "uniswap", "bitcoin", or a token address)')
  },
  async ({ query }) => {
    if (!query.trim()) {
      throw new Error('Search query cannot be empty');
    }
    const sanitizedQuery = encodeURIComponent(query.trim());
    const data = await fetchFromAPI(`/search?query=${sanitizedQuery}`);
    return formatMcpResponse(data);
  }
);

// getStats
server.tool(
  'getStats',
  'Get high-level statistics about the DexPaprika ecosystem: total networks, DEXes, pools, and tokens available.',
  {},
  async () => {
    const data = await fetchFromAPI('/stats');
    return formatMcpResponse(data);
  }
);

// Start the server
async function main() {
  try {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('DexPaprika MCP server is running...');
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

main(); 