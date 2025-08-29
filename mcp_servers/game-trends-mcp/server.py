# server.py
from fastmcp import FastMCP
from datetime import datetime # get_api_health için eklendi

# Global placeholder for the app instance
_app_instance = None

def _get_app_instance():
    """
    GameAnalyticsApp örneğini tembel yükler (lazily initializes) ve döndürür.
    Bu fonksiyon, bir araç ilk kez çağrıldığında app örneğini oluşturur.
    """
    global _app_instance
    if _app_instance is None:
        # app modülünü ve GameAnalyticsApp sınıfını burada import ediyoruz
        # böylece başlangıçta yüklenmemiş oluyorlar.
        from app import GameAnalyticsApp # app.py dosyasından GameAnalyticsApp import ediliyor
        print(f"[{datetime.now()}] Initializing GameAnalyticsApp instance...")
        _app_instance = GameAnalyticsApp()
    return _app_instance

# MCP Server instance
mcp = FastMCP("Gaming Trend Analytics")

# MCP Tools
# Her araç fonksiyonu artık _get_app_instance() çağırarak app örneğini alacak.

@mcp.tool()
async def get_steam_trending_games() -> dict:
    """Get real trending games from Steam platform with live data from multiple sources."""
    app = _get_app_instance()
    return await app.get_steam_trending_games()

@mcp.tool()
async def get_steam_top_sellers() -> dict:
    """Get real top selling games from Steam platform with live sales data."""
    app = _get_app_instance()
    return await app.get_steam_top_sellers()

@mcp.tool()
async def get_steam_most_played() -> dict:
    """Get real-time most played games from Steam with live player statistics from SteamCharts."""
    app = _get_app_instance()
    return await app.get_steam_most_played()

@mcp.tool()
async def get_epic_free_games() -> dict:
    """Get current and upcoming free games from Epic Games Store with real promotion data."""
    app = _get_app_instance()
    return await app.get_epic_free_games()

@mcp.tool()
async def get_epic_trending_games() -> dict:
    """Get trending games from Epic Games Store."""
    app = _get_app_instance()
    return await app.get_epic_trending_games()

@mcp.tool()
async def get_all_trending_games() -> dict:
    """Get comprehensive real-time gaming data from all platforms (Steam and Epic Games)."""
    app = _get_app_instance()
    return await app.get_all_trending_games()

@mcp.tool()
async def get_api_health() -> dict:
    """Check the health status of the Gaming Trend Analytics API."""
    app = _get_app_instance()
    # GameAnalyticsApp örneği üzerinden get_api_health çağrılıyor
    return app.get_api_health()


if __name__ == "__main__":
    print(f"[{datetime.now()}] MCP Server (server.py) starting in STDIO mode...")
    # FastMCP araç kaydı, dekoratörler işlendiğinde (modül yükleme zamanında) gerçekleşir.
    # Bu kısım hızlı olmalıdır. GameAnalyticsApp'in asıl başlatılması ertelenmiştir.
    mcp.run()
    print(f"[{datetime.now()}] MCP Server (server.py) finished.")