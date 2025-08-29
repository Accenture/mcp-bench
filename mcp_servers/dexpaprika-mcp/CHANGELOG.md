# Changelog

All notable changes to the DexPaprika MCP Server will be documented in this file.

## [1.1.0] - 2025-01-27

### ⚠️ BREAKING CHANGES

#### API Deprecation - Global Pools Endpoint Removed
- **REMOVED**: `getTopPools` function that used the deprecated global `/pools` endpoint
- The global `/pools` endpoint has been permanently removed and now returns `410 Gone`
- All pool queries now require a specific network to improve performance and provide more relevant results

### 🔄 Migration Guide

#### For users who were using `getTopPools`:

**Before (v1.0.x):**
```javascript
// This will no longer work
getTopPools({ page: 0, limit: 10, sort: 'desc', orderBy: 'volume_usd' })
```

**After (v1.1.0):**
```javascript
// Use network-specific queries instead
getNetworkPools({ network: 'ethereum', page: 0, limit: 10, sort: 'desc', orderBy: 'volume_usd' })
getNetworkPools({ network: 'solana', page: 0, limit: 10, sort: 'desc', orderBy: 'volume_usd' })
```

### ✨ Added

- **Enhanced Error Handling**: Added specific error handling for `410 Gone` responses with helpful migration messages
- **Improved Function Descriptions**: All functions now include better guidance on parameter usage
- **New Parameter Support**: Added `reorder` parameter to `getTokenPools` function
- **Better Documentation**: Enhanced parameter descriptions with references to helper functions (e.g., "use getNetworks to see all available networks")
- **Network Guidance**: All network-dependent functions now reference `getNetworks` for discovering valid network IDs

### 🔧 Changed

- **Version**: Updated from 1.0.5 to 1.1.0 to reflect breaking changes
- **Primary Pool Method**: `getNetworkPools` is now highlighted as the primary method for pool data retrieval
- **Parameter Limits**: Updated limit descriptions to reflect API maximum of 100 items per page
- **OHLCV Documentation**: Improved parameter descriptions for better clarity on supported formats
- **Transaction Pagination**: Enhanced documentation for both page-based and cursor-based pagination options

### 🛠️ Technical Improvements

- **Better Error Messages**: More descriptive error messages that guide users toward correct usage patterns
- **Consistent Parameter Descriptions**: Standardized network parameter descriptions across all functions
- **Enhanced Type Safety**: Maintained strong typing with Zod schemas while improving usability

### 📝 Notes

- This update aligns with DexPaprika API v1.3.0 changes
- The API is now considered stable (no longer in beta)
- No API key is required for any endpoints
- All existing network-specific endpoints remain unchanged and fully functional

## [1.0.5] - Previous Release

### 🔧 Changed
- Updated dependencies
- Minor bug fixes and improvements

## [1.0.4] - Previous Release

### ✨ Added
- Initial stable release with full DexPaprika API coverage
- Support for networks, DEXes, pools, tokens, and search functionality
- OHLCV data retrieval for price analysis
- Transaction history access
- Comprehensive error handling and rate limiting support

---

## Migration Support

If you need help migrating from v1.0.x to v1.1.0, please:

1. **Replace all `getTopPools` calls** with `getNetworkPools` calls specifying the desired network
2. **Use `getNetworks`** first to discover available networks if you need to query multiple networks
3. **Update any error handling** to account for the new `410 Gone` error messages
4. **Consider the performance benefits** of network-specific queries for your use case

For additional support, please refer to the [DexPaprika API documentation](https://docs.dexpaprika.com/) or open an issue in this repository. 