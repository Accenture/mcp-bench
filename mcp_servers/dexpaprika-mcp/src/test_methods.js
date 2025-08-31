#!/usr/bin/env node

import fetch from 'node-fetch';

// Base URL for DexPaprika API
const API_BASE_URL = 'https://api.dexpaprika.com';

// Helper function to fetch data from DexPaprika API
async function fetchFromAPI(endpoint) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
      if (response.status === 410) {
        throw new Error(`Endpoint has been permanently removed: ${endpoint}. Use network-specific endpoints instead.`);
      }
      throw new Error(`API request failed with status ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching from API: ${error.message}`);
    throw error;
  }
}

// Test function to run a specific API endpoint and display the result
async function testEndpoint(name, endpoint) {
  console.log(`\n-------- Testing ${name} --------`);
  try {
    const data = await fetchFromAPI(endpoint);
    console.log('Response structure:', JSON.stringify(data, null, 2).substring(0, 500) + '...');
    console.log('Response type:', typeof data);
    if (Array.isArray(data)) {
      console.log('Is Array: true');
    } else if (typeof data === 'object') {
      console.log('Object keys:', Object.keys(data));
    }
    console.log(`${name} test: SUCCESS`);
  } catch (error) {
    console.error(`${name} test: FAILED`, error);
  }
}

async function runTests() {
  console.log('Starting DexPaprika API endpoint tests (v1.1.0)...');
  console.log('Note: The global /pools endpoint has been removed as of v1.1.0');
  
  // Test each endpoint
  await testEndpoint('getNetworks', '/networks');
  await testEndpoint('getNetworkDexes', '/networks/ethereum/dexes');
  await testEndpoint('getNetworkPools (Ethereum)', '/networks/ethereum/pools');
  await testEndpoint('getNetworkPools (Solana)', '/networks/solana/pools');
  await testEndpoint('getDexPools', '/networks/ethereum/dexes/uniswap_v3/pools');
  await testEndpoint('getPoolDetails', '/networks/ethereum/pools/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640');
  await testEndpoint('getTokenDetails', '/networks/ethereum/tokens/0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48');
  await testEndpoint('search', '/search?query=ethereum');
  await testEndpoint('getStats', '/stats');
  
  console.log('\nAll tests completed! All endpoints are using the network-specific approach.');
}

runTests().catch(error => {
  console.error('Test failed with error:', error);
  process.exit(1);
}); 