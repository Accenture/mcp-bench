# import asyncio
# import aiohttp
# import json
# import random
# import time
# import re
# from datetime import datetime
# from typing import List, Dict, Optional, Any
# from bs4 import BeautifulSoup
# from fastmcp import FastMCP

# # MCP Server instance - HTTP mode için
# mcp = FastMCP("Gaming Trend Analytics")

# class SteamService:
#     def __init__(self):
#         self.base_url = 'https://api.steampowered.com'
#         self.store_url = 'https://store.steampowered.com'
#         self.last_request = 0
#         self.request_delay = 1.5  # Rate limiting
#         self.user_agents = [
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
#             'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
#         ]

#     def get_random_user_agent(self) -> str:
#         return random.choice(self.user_agents)

#     async def make_request(self, url: str, session: aiohttp.ClientSession, is_json: bool = False) -> str:
#         now = time.time()
#         time_since_last = now - self.last_request
        
#         if time_since_last < self.request_delay:
#             await asyncio.sleep(self.request_delay - time_since_last)
        
#         self.last_request = time.time()
        
#         headers = {
#             'User-Agent': self.get_random_user_agent(),
#             'Accept': 'application/json, text/plain, */*' if is_json else 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.9',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'DNT': '1',
#             'Connection': 'keep-alive',
#             'Upgrade-Insecure-Requests': '1' if not is_json else '0',
#         }
        
#         if is_json:
#             headers['X-Requested-With'] = 'XMLHttpRequest'
        
#         async with session.get(url, headers=headers, timeout=20) as response:
#             if is_json:
#                 return await response.json()
#             return await response.text()

#     async def get_trending_games(self) -> List[Dict[str, Any]]:
#         """Steam'den gerçek trending oyunları çeker - Featured & Recommended, New & Trending"""
#         async with aiohttp.ClientSession() as session:
#             games = []
            
#             # 1. Featured & Recommended oyunları çek
#             try:
#                 featured_games = await self._get_featured_games(session)
#                 games.extend(featured_games)
#             except Exception as e:
#                 print(f"Featured games error: {e}")
            
#             # 2. New & Trending oyunları çek
#             try:
#                 trending_games = await self._get_new_trending_games(session)
#                 games.extend(trending_games)
#             except Exception as e:
#                 print(f"New trending games error: {e}")
            
#             # 3. Popular New Releases çek
#             try:
#                 new_releases = await self._get_popular_new_releases(session)
#                 games.extend(new_releases)
#             except Exception as e:
#                 print(f"New releases error: {e}")
            
#             # 4. Eğer yeterli veri yoksa, Steam Charts'dan popüler oyunları çek
#             if len(games) < 5:
#                 try:
#                     popular_games = await self._get_steam_charts_popular(session)
#                     games.extend(popular_games)
#                 except Exception as e:
#                     print(f"Steam charts popular error: {e}")
            
#             # 5. Hala yeterli veri yoksa, Steam'in global stats'ından çek
#             if len(games) < 3:
#                 try:
#                     stats_games = await self._get_steam_global_stats(session)
#                     games.extend(stats_games)
#                 except Exception as e:
#                     print(f"Steam global stats error: {e}")
            
#             # Duplicate'ları temizle ve sınırla
#             seen_ids = set()
#             unique_games = []
#             for game in games:
#                 if game['id'] not in seen_ids and len(unique_games) < 25:
#                     seen_ids.add(game['id'])
#                     unique_games.append(game)
            
#             # Eğer hiç veri çekilemediyse hata fırlat
#             if not unique_games:
#                 raise Exception("No trending games data could be retrieved from any source")
            
#             return unique_games

#     async def _get_featured_games(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
#         """Steam ana sayfasından featured oyunları çeker"""
#         response_text = await self.make_request(f'{self.store_url}/?l=english', session)
#         soup = BeautifulSoup(response_text, 'html.parser')
#         games = []
        
#         # Featured carousel'dan oyunları çek
#         carousel_items = soup.select('.carousel_items .store_capsule, .featuredcapsule, .main_cluster_capsule')
        
#         for item in carousel_items[:10]:  # İlk 10 featured oyun
#             try:
#                 link = item.find('a')
#                 if not link or 'href' not in link.attrs:
#                     continue
                    
#                 href = link['href']
#                 app_id_match = re.search(r'/app/(\d+)/', href)
#                 if not app_id_match:
#                     continue
                    
#                 app_id = app_id_match.group(1)
                
#                 # Oyun adını çek
#                 title_elem = item.select_one('.store_capsule_title, .featuredcapsule_title')
#                 name = title_elem.text.strip() if title_elem else None
                
#                 if not name:
#                     # Alt attribute'dan dene
#                     img = item.find('img')
#                     if img and 'alt' in img.attrs:
#                         name = img['alt'].strip()
                
#                 # Fiyat bilgisini çek
#                 price_elem = item.select_one('.discount_final_price, .store_capsule_price')
#                 price = price_elem.text.strip() if price_elem else 'N/A'
                
#                 # İndirim bilgisini çek
#                 discount_elem = item.select_one('.discount_percent')
#                 discount = 0
#                 if discount_elem:
#                     discount_text = discount_elem.text.strip().replace('-', '').replace('%', '')
#                     try:
#                         discount = int(discount_text)
#                     except:
#                         discount = 0
                
#                 # Resim URL'sini çek
#                 img_elem = item.find('img')
#                 image = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None
                
#                 if name and app_id:
#                     games.append({
#                         'id': app_id,
#                         'name': name,
#                         'price': price,
#                         'discount': discount,
#                         'headerImage': image,
#                         'platform': 'Steam',
#                         'category': 'Featured',
#                         'isTrending': True,
#                         'source': 'featured'
#                     })
                    
#             except Exception as e:
#                 print(f"Error parsing featured game: {e}")
#                 continue
        
#         return games

#     async def _get_new_trending_games(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
#         """Steam'den New & Trending oyunları çeker"""
#         # Steam'in New & Trending API endpoint'i
#         url = f'{self.store_url}/search/results/?query&start=0&count=15&dynamic_data=&sort_by=_ASC&supportedlang=english&snr=1_7_7_popularnew_7&filter=popularnew&infinite=1'
        
#         data = await self.make_request(url, session, is_json=True)
        
#         if 'results_html' not in data:
#             raise Exception("No results_html in Steam trending response")
            
#         soup = BeautifulSoup(data['results_html'], 'html.parser')
#         games = []
        
#         for item in soup.select('.search_result_row'):
#             try:
#                 app_id = item.get('data-ds-appid')
#                 if not app_id:
#                     continue
                
#                 # Oyun adı
#                 title_elem = item.select_one('.title')
#                 name = title_elem.text.strip() if title_elem else None
                
#                 # Fiyat
#                 price_elem = item.select_one('.search_price')
#                 price = price_elem.text.strip() if price_elem else 'N/A'
                
#                 # Çıkış tarihi
#                 release_elem = item.select_one('.search_released')
#                 release_date = release_elem.text.strip() if release_elem else 'Unknown'
                
#                 # Review skoru
#                 review_elem = item.select_one('.search_review_summary')
#                 review_score = None
#                 if review_elem and 'data-tooltip-html' in review_elem.attrs:
#                     tooltip = review_elem['data-tooltip-html']
#                     # Review yüzdesini çıkar
#                     percentage_match = re.search(r'(\d+)%', tooltip)
#                     if percentage_match:
#                         review_score = f"{percentage_match.group(1)}%"
                
#                 # Resim
#                 img_elem = item.select_one('.search_capsule img')
#                 image = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None
                
#                 # Tag'ları çek
#                 tags = []
#                 tag_elems = item.select('.search_tag')
#                 for tag_elem in tag_elems:
#                     tag_text = tag_elem.text.strip()
#                     if tag_text:
#                         tags.append(tag_text)
                
#                 if name and app_id:
#                     games.append({
#                         'id': app_id,
#                         'name': name,
#                         'price': price,
#                         'headerImage': image,
#                         'platform': 'Steam',
#                         'releaseDate': release_date,
#                         'reviewScore': review_score,
#                         'tags': tags,
#                         'category': 'New & Trending',
#                         'isTrending': True,
#                         'source': 'new_trending'
#                     })
                    
#             except Exception as e:
#                 print(f"Error parsing trending game: {e}")
#                 continue
        
#         if not games:
#             raise Exception("No trending games found in Steam response")
        
#         return games

#     async def _get_popular_new_releases(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
#         """Steam'den Popular New Releases çeker"""
#         # Popular New Releases endpoint
#         url = f'{self.store_url}/search/results/?query&start=0&count=10&dynamic_data=&sort_by=Released_DESC&supportedlang=english&filter=popularnew&infinite=1'
        
#         data = await self.make_request(url, session, is_json=True)
        
#         if 'results_html' not in data:
#             raise Exception("No results_html in Steam new releases response")
            
#         soup = BeautifulSoup(data['results_html'], 'html.parser')
#         games = []
        
#         for item in soup.select('.search_result_row'):
#             try:
#                 app_id = item.get('data-ds-appid')
#                 if not app_id:
#                     continue
                
#                 title_elem = item.select_one('.title')
#                 name = title_elem.text.strip() if title_elem else None
                
#                 price_elem = item.select_one('.search_price')
#                 price = price_elem.text.strip() if price_elem else 'N/A'
                
#                 release_elem = item.select_one('.search_released')
#                 release_date = release_elem.text.strip() if release_elem else 'Unknown'
                
#                 img_elem = item.select_one('.search_capsule img')
#                 image = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None
                
#                 if name and app_id:
#                     games.append({
#                         'id': app_id,
#                         'name': name,
#                         'price': price,
#                         'headerImage': image,
#                         'platform': 'Steam',
#                         'releaseDate': release_date,
#                         'category': 'Popular New Release',
#                         'isTrending': True,
#                         'source': 'new_releases'
#                     })
                    
#             except Exception as e:
#                 print(f"Error parsing new release: {e}")
#                 continue
        
#         return games

#     async def _get_steam_charts_popular(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
#         """SteamCharts'dan popüler oyunları çeker"""
#         response_text = await self.make_request('https://steamcharts.com/', session)
#         soup = BeautifulSoup(response_text, 'html.parser')
#         games = []
        
#         table = soup.find('table', class_='common-table')
#         if not table:
#             raise Exception("Could not find SteamCharts table")
        
#         rows = table.select('tbody tr')[:10]  # İlk 10 oyun
        
#         for index, row in enumerate(rows):
#             try:
#                 cells = row.select('td')
#                 if len(cells) < 4:
#                     continue
                
#                 # Oyun adı ve link
#                 name_cell = cells[1]
#                 name_link = name_cell.find('a')
#                 name = name_link.text.strip() if name_link else name_cell.text.strip()
                
#                 # App ID'yi link'ten çıkar
#                 app_id = f"chart_{index}"
#                 if name_link and 'href' in name_link.attrs:
#                     href = name_link['href']
#                     app_id_match = re.search(r'/app/(\d+)', href)
#                     if app_id_match:
#                         app_id = app_id_match.group(1)
                
#                 # Mevcut oyuncu sayısı
#                 current_text = cells[2].text.strip().replace(',', '')
#                 current_players = 0
#                 if current_text.isdigit():
#                     current_players = int(current_text)
                
#                 if name and name != 'Game' and current_players > 0:
#                     games.append({
#                         'id': app_id,
#                         'name': name,
#                         'currentPlayers': current_players,
#                         'platform': 'Steam',
#                         'category': 'Popular',
#                         'isTrending': True,
#                         'source': 'steamcharts'
#                     })
                    
#             except Exception as e:
#                 print(f"Error parsing SteamCharts row: {e}")
#                 continue
        
#         if not games:
#             raise Exception("No games found in SteamCharts")
        
#         return games

#     async def _get_steam_global_stats(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
#         """Steam'in global stats sayfasından oyunları çeker"""
#         response_text = await self.make_request(f'{self.store_url}/stats/', session)
#         soup = BeautifulSoup(response_text, 'html.parser')
#         games = []
        
#         # Steam stats sayfasından oyunları çek
#         stat_rows = soup.select('.player_count_row')
        
#         for index, row in enumerate(stat_rows[:10]):
#             try:
#                 name_elem = row.select_one('.gameLink')
#                 if not name_elem:
#                     continue
                    
#                 name = name_elem.text.strip()
                
#                 # App ID'yi link'ten çıkar
#                 app_id = f"stats_{index}"
#                 if 'href' in name_elem.attrs:
#                     href = name_elem['href']
#                     app_id_match = re.search(r'/app/(\d+)', href)
#                     if app_id_match:
#                         app_id = app_id_match.group(1)
                
#                 # Player count
#                 count_elem = row.select_one('.currentServers')
#                 current_players = 0
#                 if count_elem:
#                     count_text = count_elem.text.strip().replace(',', '')
#                     if count_text.isdigit():
#                         current_players = int(count_text)
                
#                 if name and current_players > 0:
#                     games.append({
#                         'id': app_id,
#                         'name': name,
#                         'currentPlayers': current_players,
#                         'platform': 'Steam',
#                         'category': 'Popular',
#                         'isTrending': True,
#                         'source': 'steam_global_stats'
#                     })
                    
#             except Exception as e:
#                 print(f"Error parsing Steam stats row: {e}")
#                 continue
        
#         if not games:
#             raise Exception("No games found in Steam global stats")
        
#         return games

#     async def get_top_sellers(self) -> List[Dict[str, Any]]:
#         """Steam'den gerçek top seller oyunları çeker"""
#         async with aiohttp.ClientSession() as session:
#             # Steam Top Sellers API
#             url = f'{self.store_url}/search/results/?query&start=0&count=20&dynamic_data=&sort_by=_ASC&supportedlang=english&filter=topsellers&infinite=1'
            
#             data = await self.make_request(url, session, is_json=True)
            
#             if 'results_html' not in data:
#                 raise Exception("No results_html in Steam top sellers response")
                
#             soup = BeautifulSoup(data['results_html'], 'html.parser')
#             games = []
            
#             for index, item in enumerate(soup.select('.search_result_row')):
#                 try:
#                     app_id = item.get('data-ds-appid')
#                     if not app_id:
#                         continue
                    
#                     title_elem = item.select_one('.title')
#                     name = title_elem.text.strip() if title_elem else None
                    
#                     price_elem = item.select_one('.search_price')
#                     price = price_elem.text.strip() if price_elem else 'N/A'
                    
#                     # İndirim bilgisi
#                     discount_elem = item.select_one('.search_discount span')
#                     discount = 0
#                     if discount_elem:
#                         discount_text = discount_elem.text.strip().replace('-', '').replace('%', '')
#                         try:
#                             discount = int(discount_text)
#                         except:
#                             discount = 0
                    
#                     # Review bilgisi
#                     review_elem = item.select_one('.search_review_summary')
#                     review_score = None
#                     review_count = None
#                     if review_elem and 'data-tooltip-html' in review_elem.attrs:
#                         tooltip = review_elem['data-tooltip-html']
#                         percentage_match = re.search(r'(\d+)%', tooltip)
#                         count_match = re.search(r'([\d,]+)\s+user reviews', tooltip)
#                         if percentage_match:
#                             review_score = f"{percentage_match.group(1)}%"
#                         if count_match:
#                             review_count = count_match.group(1)
                    
#                     release_elem = item.select_one('.search_released')
#                     release_date = release_elem.text.strip() if release_elem else 'Unknown'
                    
#                     img_elem = item.select_one('.search_capsule img')
#                     image = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None
                    
#                     # Tag'ları çek
#                     tags = []
#                     tag_elems = item.select('.search_tag')
#                     for tag_elem in tag_elems:
#                         tag_text = tag_elem.text.strip()
#                         if tag_text:
#                             tags.append(tag_text)
                    
#                     if name and app_id:
#                         games.append({
#                             'id': app_id,
#                             'name': name,
#                             'price': price,
#                             'discount': discount,
#                             'headerImage': image,
#                             'platform': 'Steam',
#                             'releaseDate': release_date,
#                             'reviewScore': review_score,
#                             'reviewCount': review_count,
#                             'tags': tags,
#                             'rank': index + 1,
#                             'isTopSeller': True
#                         })
                        
#                 except Exception as e:
#                     print(f"Error parsing top seller: {e}")
#                     continue
            
#             if not games:
#                 raise Exception("No top sellers found in Steam response")
            
#             return games

#     async def get_current_player_stats(self) -> List[Dict[str, Any]]:
#         """SteamCharts'dan gerçek player istatistiklerini çeker"""
#         async with aiohttp.ClientSession() as session:
#             try:
#                 # SteamCharts ana sayfası
#                 response_text = await self.make_request('https://steamcharts.com/', session)
#                 soup = BeautifulSoup(response_text, 'html.parser')
#                 games = []
                
#                 # Ana tablo satırlarını bul
#                 table = soup.find('table', class_='common-table')
#                 if not table:
#                     # Alternatif olarak Steam'in kendi stats sayfasını dene
#                     return await self._get_steam_stats_alternative(session)
                
#                 rows = table.select('tbody tr')[:20]  # İlk 20 oyun
                
#                 for index, row in enumerate(rows):
#                     try:
#                         cells = row.select('td')
#                         if len(cells) < 4:
#                             continue
                        
#                         # Rank
#                         rank_text = cells[0].text.strip()
#                         rank = int(rank_text) if rank_text.isdigit() else index + 1
                        
#                         # Oyun adı ve link
#                         name_cell = cells[1]
#                         name_link = name_cell.find('a')
#                         name = name_link.text.strip() if name_link else name_cell.text.strip()
                        
#                         # App ID'yi link'ten çıkar
#                         app_id = f"chart_{index}"
#                         if name_link and 'href' in name_link.attrs:
#                             href = name_link['href']
#                             app_id_match = re.search(r'/app/(\d+)', href)
#                             if app_id_match:
#                                 app_id = app_id_match.group(1)
                        
#                         # Mevcut oyuncu sayısı
#                         current_text = cells[2].text.strip().replace(',', '')
#                         current_players = 0
#                         if current_text.isdigit():
#                             current_players = int(current_text)
                        
#                         # Peak oyuncu sayısı
#                         peak_text = cells[3].text.strip().replace(',', '')
#                         peak_players = 0
#                         if peak_text.isdigit():
#                             peak_players = int(peak_text)
                        
#                         # 24 saat değişim (varsa)
#                         change_24h = None
#                         if len(cells) > 4:
#                             change_text = cells[4].text.strip()
#                             if change_text and change_text != '-':
#                                 change_24h = change_text
                        
#                         if name and name != 'Game' and current_players > 0:
#                             games.append({
#                                 'id': app_id,
#                                 'name': name,
#                                 'currentPlayers': current_players,
#                                 'peakPlayers': peak_players,
#                                 'change24h': change_24h,
#                                 'rank': rank,
#                                 'platform': 'Steam',
#                                 'isPopular': True,
#                                 'lastUpdated': datetime.now().isoformat()
#                             })
                            
#                     except Exception as e:
#                         print(f"Error parsing player stats row: {e}")
#                         continue
                
#                 if not games:
#                     # SteamCharts'dan veri alınamazsa alternatif dene
#                     return await self._get_steam_stats_alternative(session)
                
#                 return games
                
#             except Exception as e:
#                 print(f"SteamCharts error: {e}")
#                 return await self._get_steam_stats_alternative(session)

#     async def _get_steam_stats_alternative(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
#         """Steam'in kendi most played sayfasından veri çeker"""
#         response_text = await self.make_request(f'{self.store_url}/stats/', session)
#         soup = BeautifulSoup(response_text, 'html.parser')
#         games = []
        
#         # Steam stats sayfasından oyunları çek
#         stat_rows = soup.select('.player_count_row')
        
#         for index, row in enumerate(stat_rows[:15]):
#             try:
#                 name_elem = row.select_one('.gameLink')
#                 if not name_elem:
#                     continue
                    
#                 name = name_elem.text.strip()
                
#                 # App ID'yi link'ten çıkar
#                 app_id = f"stats_{index}"
#                 if 'href' in name_elem.attrs:
#                     href = name_elem['href']
#                     app_id_match = re.search(r'/app/(\d+)', href)
#                     if app_id_match:
#                         app_id = app_id_match.group(1)
                
#                 # Player count
#                 count_elem = row.select_one('.currentServers')
#                 current_players = 0
#                 if count_elem:
#                     count_text = count_elem.text.strip().replace(',', '')
#                     if count_text.isdigit():
#                         current_players = int(count_text)
                
#                 if name and current_players > 0:
#                     games.append({
#                         'id': app_id,
#                         'name': name,
#                         'currentPlayers': current_players,
#                         'rank': index + 1,
#                         'platform': 'Steam',
#                         'isPopular': True,
#                         'source': 'steam_stats'
#                     })
                    
#             except Exception as e:
#                 print(f"Error parsing Steam stats row: {e}")
#                 continue
        
#         if not games:
#             raise Exception("No player statistics could be retrieved from any Steam source")
        
#         return games


# class EpicGamesService:
#     def __init__(self):
#         self.base_url = 'https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions'

#     async def get_free_games(self) -> List[Dict[str, Any]]:
#         async with aiohttp.ClientSession() as session:
#             url = f"{self.base_url}?locale=en-US&country=US&allowCountries=US"
#             headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#             }
            
#             async with session.get(url, headers=headers, timeout=15) as response:
#                 data = await response.json()
                
#                 games = data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
                
#                 if not games:
#                     raise Exception("No games found in Epic Games response")
                
#                 filtered_games = []
#                 for game in games:
#                     promotions = game.get('promotions', {})
#                     has_current_promo = promotions.get('promotionalOffers', [])
#                     has_upcoming_promo = promotions.get('upcomingPromotionalOffers', [])
                    
#                     if has_current_promo or has_upcoming_promo:
#                         price_info = game.get('price', {}).get('totalPrice', {}).get('fmtPrice', {})
                        
#                         promotion_end_date = None
#                         if has_current_promo:
#                             promo_offers = has_current_promo[0].get('promotionalOffers', [])
#                             if promo_offers:
#                                 promotion_end_date = promo_offers[0].get('endDate')
                        
#                         filtered_games.append({
#                             'id': game.get('id'),
#                             'name': game.get('title'),
#                             'description': game.get('description'),
#                             'price': price_info.get('originalPrice', 'Free'),
#                             'discountPrice': price_info.get('discountPrice', 'Free'),
#                             'platform': 'Epic Games',
#                             'developer': game.get('developer'),
#                             'publisher': game.get('publisher'),
#                             'releaseDate': game.get('releaseDate'),
#                             'tags': [tag.get('name') for tag in game.get('tags', [])],
#                             'images': [{'type': img.get('type'), 'url': img.get('url')} 
#                                       for img in game.get('keyImages', [])],
#                             'isFree': game.get('price', {}).get('totalPrice', {}).get('originalPrice') == 0,
#                             'promotionEndDate': promotion_end_date,
#                             'upcoming': len(has_upcoming_promo) > 0
#                         })
                
#                 if not filtered_games:
#                     raise Exception("No free games with promotions found")
                
#                 return filtered_games[:15]

#     async def get_trending_games(self) -> List[Dict[str, Any]]:
#         """Epic Games Store'dan trending oyunları çeker (Epic'in public API'si sınırlı olduğu için web scraping)"""
#         async with aiohttp.ClientSession() as session:
#             headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#             }
            
#             # Epic Games Store ana sayfasından featured oyunları çek
#             async with session.get('https://store.epicgames.com/en-US/', headers=headers, timeout=15) as response:
#                 html = await response.text()
#                 soup = BeautifulSoup(html, 'html.parser')
                
#                 games = []
                
#                 # Epic'in featured game card'larını bul
#                 game_cards = soup.select('[data-testid*="offer"], .css-1myhtyb, .css-1jx3eyg')
                
#                 for index, card in enumerate(game_cards[:10]):
#                     try:
#                         # Oyun adını bul
#                         name_elem = card.select_one('h3, [data-testid="offer-title"], .css-2ucwu')
#                         name = name_elem.text.strip() if name_elem else None
                        
#                         # Fiyat bilgisini bul
#                         price_elem = card.select_one('[data-testid="price"], .css-119zqif')
#                         price = price_elem.text.strip() if price_elem else 'N/A'
                        
#                         # Link'i bul
#                         link_elem = card.find('a')
#                         game_url = None
#                         if link_elem and 'href' in link_elem.attrs:
#                             game_url = link_elem['href']
                        
#                         # Resim URL'sini bul
#                         img_elem = card.find('img')
#                         image = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None
                        
#                         if name:
#                             games.append({
#                                 'id': f'epic_{index}',
#                                 'name': name,
#                                 'price': price,
#                                 'platform': 'Epic Games',
#                                 'gameUrl': game_url,
#                                 'headerImage': image,
#                                 'category': 'Featured',
#                                 'trending': True
#                             })
                            
#                     except Exception as e:
#                         print(f"Error parsing Epic game card: {e}")
#                         continue
                
#                 if not games:
#                     raise Exception("No trending games found on Epic Games Store")
                
#                 return games


# # Service instances
# steam_service = SteamService()
# epic_service = EpicGamesService()

# # MCP Tools (aynı kalıyor)

# @mcp.tool()
# async def get_steam_trending_games() -> dict:
#     """Get real trending games from Steam platform with live data from multiple sources."""
#     try:
#         games = await steam_service.get_trending_games()
#         return {
#             'success': True,
#             'platform': 'Steam',
#             'type': 'Trending Games',
#             'count': len(games),
#             'data': games,
#             'sources': ['featured', 'new_trending', 'new_releases', 'steamcharts', 'steam_stats'],
#             'timestamp': datetime.now().isoformat()
#         }
#     except Exception as e:
#         return {
#             'success': False,
#             'error': 'Failed to fetch Steam trending games',
#             'message': str(e)
#         }

# @mcp.tool()
# async def get_steam_top_sellers() -> dict:
#     """Get real top selling games from Steam platform with live sales data."""
#     try:
#         games = await steam_service.get_top_sellers()
#         return {
#             'success': True,
#             'platform': 'Steam',
#             'type': 'Top Sellers',
#             'count': len(games),
#             'data': games,
#             'timestamp': datetime.now().isoformat()
#         }
#     except Exception as e:
#         return {
#             'success': False,
#             'error': 'Failed to fetch Steam top sellers',
#             'message': str(e)
#         }

# @mcp.tool()
# async def get_steam_most_played() -> dict:
#     """Get real-time most played games from Steam with live player statistics from SteamCharts."""
#     try:
#         games = await steam_service.get_current_player_stats()
#         return {
#             'success': True,
#             'platform': 'Steam',
#             'type': 'Most Played Games (Live Stats)',
#             'count': len(games),
#             'data': games,
#             'source': 'SteamCharts + Steam Stats',
#             'timestamp': datetime.now().isoformat()
#         }
#     except Exception as e:
#         return {
#             'success': False,
#             'error': 'Failed to fetch Steam player statistics',
#             'message': str(e)
#         }

# @mcp.tool()
# async def get_epic_free_games() -> dict:
#     """Get current and upcoming free games from Epic Games Store with real promotion data."""
#     try:
#         games = await epic_service.get_free_games()
#         return {
#             'success': True,
#             'platform': 'Epic Games',
#             'type': 'Free Games',
#             'count': len(games),
#             'data': games,
#             'timestamp': datetime.now().isoformat()
#         }
#     except Exception as e:
#         return {
#             'success': False,
#             'error': 'Failed to fetch Epic Games free games',
#             'message': str(e)
#         }

# @mcp.tool()
# async def get_epic_trending_games() -> dict:
#     """Get trending games from Epic Games Store."""
#     try:
#         games = await epic_service.get_trending_games()
#         return {
#             'success': True,
#             'platform': 'Epic Games',
#             'type': 'Trending Games',
#             'count': len(games),
#             'data': games,
#             'timestamp': datetime.now().isoformat()
#         }
#     except Exception as e:
#         return {
#             'success': False,
#             'error': 'Failed to fetch Epic Games trending games',
#             'message': str(e)
#         }

# @mcp.tool()
# async def get_all_trending_games() -> dict:
#     """Get comprehensive real-time gaming data from all platforms (Steam and Epic Games)."""
#     results = {
#         'success': True,
#         'timestamp': datetime.now().isoformat(),
#         'data': {
#             'steam': {
#                 'trending': [],
#                 'topSellers': [],
#                 'mostPlayed': []
#             },
#             'epic': {
#                 'free': [],
#                 'trending': []
#             }
#         },
#         'errors': []
#     }
    
#     # Gather all data concurrently
#     tasks = [
#         steam_service.get_trending_games(),
#         steam_service.get_top_sellers(),
#         steam_service.get_current_player_stats(),
#         epic_service.get_free_games(),
#         epic_service.get_trending_games()
#     ]
    
#     try:
#         steam_trending, steam_top_sellers, steam_popular, epic_free, epic_trending = await asyncio.gather(
#             *tasks, return_exceptions=True
#         )
        
#         # Process results
#         if isinstance(steam_trending, Exception):
#             results['errors'].append(f"Steam trending: {str(steam_trending)}")
#         else:
#             results['data']['steam']['trending'] = steam_trending
            
#         if isinstance(steam_top_sellers, Exception):
#             results['errors'].append(f"Steam top sellers: {str(steam_top_sellers)}")
#         else:
#             results['data']['steam']['topSellers'] = steam_top_sellers
            
#         if isinstance(steam_popular, Exception):
#             results['errors'].append(f"Steam popular: {str(steam_popular)}")
#         else:
#             results['data']['steam']['mostPlayed'] = steam_popular
            
#         if isinstance(epic_free, Exception):
#             results['errors'].append(f"Epic free games: {str(epic_free)}")
#         else:
#             results['data']['epic']['free'] = epic_free
            
#         if isinstance(epic_trending, Exception):
#             results['errors'].append(f"Epic trending: {str(epic_trending)}")
#         else:
#             results['data']['epic']['trending'] = epic_trending
            
#     except Exception as e:
#         results['success'] = False
#         results['errors'].append(f"General error: {str(e)}")
    
#     return results

# @mcp.tool()
# async def get_api_health() -> dict:
#     """Check the health status of the Gaming Trend Analytics API."""
#     return {
#         'status': 'healthy',
#         'timestamp': datetime.now().isoformat(),
#         'version': '2.0.0',
#         'description': 'Gaming Trend Analytics MCP Server - Real-time Steam & Epic Games data',
#         'features': [
#             'Real-time Steam trending games from multiple sources',
#             'Live Steam top sellers with detailed metadata',
#             'Live player statistics from SteamCharts',
#             'Epic Games free games with promotions',
#             'Epic Games trending games',
#             'Comprehensive multi-platform data aggregation',
#             'No mock data - all real-time sources'
#         ],
#         'available_tools': [
#             'get_steam_trending_games',
#             'get_steam_top_sellers', 
#             'get_steam_most_played',
#             'get_epic_free_games',
#             'get_epic_trending_games',
#             'get_all_trending_games'
#         ]
#     }

# app.py
import asyncio
import aiohttp
import json
import random
import time
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup

# --- SteamService class ---
class SteamService:
    def __init__(self):
        self.base_url = "https://api.steampowered.com"
        self.store_url = "https://store.steampowered.com"
        self.last_request = 0
        self.request_delay = 1.5  # Rate limiting
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        ]
        print(f"[{datetime.now()}] SteamService initialized.")

    def get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)

    async def make_request(
        self, url: str, session: aiohttp.ClientSession, is_json: bool = False
    ) -> Any:
        now = time.time()
        time_since_last = now - self.last_request

        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)

        self.last_request = time.time()

        headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "application/json, text/plain, */*"
            if is_json
            else "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1" if not is_json else "0",
        }

        if is_json:
            headers["X-Requested-With"] = "XMLHttpRequest"

        # print(f"[{datetime.now()}] Making request to: {url}")
        async with session.get(url, headers=headers, timeout=20) as response:
            response.raise_for_status()  # Raise an exception for HTTP errors
            if is_json:
                return await response.json()
            return await response.text()

    async def get_trending_games(self) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            games = []
            sources_attempted = []

            try:
                sources_attempted.append("featured_home")
                featured_games = await self._get_featured_games(session)
                games.extend(featured_games)
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: Featured games error: {e}"
                )

            try:
                sources_attempted.append("new_trending_api")
                trending_games = await self._get_new_trending_games(session)
                games.extend(trending_games)
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: New trending games error: {e}"
                )

            try:
                sources_attempted.append("popular_new_releases_api")
                new_releases = await self._get_popular_new_releases(session)
                games.extend(new_releases)
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: New releases error: {e}"
                )

            if len(games) < 5: # Try more sources if initial results are sparse
                try:
                    sources_attempted.append("steamcharts_top")
                    popular_games = await self._get_steam_charts_popular(
                        session
                    )
                    games.extend(popular_games)
                except Exception as e:
                    print(
                        f"[{datetime.now()}] SteamService: Steam charts popular error: {e}"
                    )

            if len(games) < 3: # One last attempt if still very few games
                try:
                    sources_attempted.append("steam_global_stats_page")
                    stats_games = await self._get_steam_global_stats(session)
                    games.extend(stats_games)
                except Exception as e:
                    print(
                        f"[{datetime.now()}] SteamService: Steam global stats error: {e}"
                    )

            seen_ids = set()
            unique_games = []
            for game in games:
                game_id = game.get("id")
                # Ensure game_id is a string for the set
                if game_id and str(game_id) not in seen_ids and len(unique_games) < 25 :
                    seen_ids.add(str(game_id))
                    unique_games.append(game)

            if not unique_games:
                print(
                    f"[{datetime.now()}] SteamService: No trending games data could be retrieved from any source. Sources attempted: {sources_attempted}"
                )
            return unique_games

    async def _get_featured_games(
        self, session: aiohttp.ClientSession
    ) -> List[Dict[str, Any]]:
        response_text = await self.make_request(
            f"{self.store_url}/?l=english&cc=US", session
        )
        soup = BeautifulSoup(response_text, "lxml")
        games = []
        carousel_items = soup.select(
            ".carousel_items .store_capsule, .featuredcapsule, .main_cluster_capsule, .home_area_spotlight, .discovery_queue_spotlight"
        )

        for item in carousel_items[:10]:
            try:
                link = item.find("a", href=True)
                if not link:
                    continue

                href = link["href"]
                app_id_match = re.search(r"/app/(\d+)/", href)
                app_id = None
                if app_id_match:
                    app_id = app_id_match.group(1)
                else:
                    data_appid = item.get("data-ds-appid") or item.get(
                        "data-ds-bundleid"
                    )
                    if data_appid and data_appid.isdigit():
                        app_id = data_appid
                    else: # Try to get from URL if it's a bundle or sub
                        id_match_alt = re.search(r'/(bundle|sub)/(\d+)', href)
                        if id_match_alt:
                            app_id = f"{id_match_alt.group(1)}_{id_match_alt.group(2)}"


                if not app_id:
                    continue

                title_elem = item.select_one(
                    ".store_capsule_name, .featuredcapsule_title, .focus_title, .home_area_spotlight_name, .dq_title"
                )
                name = title_elem.text.strip() if title_elem else None

                if not name:
                    img = item.find("img", alt=True)
                    if img:
                        name = img["alt"].strip()

                price_elem = item.select_one(
                    ".discount_final_price, .store_capsule_price .price, .focus_price, .home_area_spotlight_price, .dq_price .discount_final_price"
                )
                price = price_elem.text.strip() if price_elem else "N/A"

                discount_elem = item.select_one(".discount_pct, .discount_percent")
                discount = 0
                if discount_elem:
                    discount_text = (
                        discount_elem.text.strip().replace("-", "").replace("%", "")
                    )
                    try:
                        discount = int(discount_text)
                    except ValueError:
                        discount = 0

                img_elem = item.find("img", src=True)
                image = img_elem["src"] if img_elem else None

                if name and app_id:
                    games.append(
                        {
                            "id": app_id,
                            "name": name,
                            "price": price,
                            "discount": discount,
                            "headerImage": image,
                            "platform": "Steam",
                            "category": "Featured",
                            "isTrending": True,
                            "source": "featured_home",
                            "url": href
                        }
                    )
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: Error parsing featured game: {e}"
                )
                continue
        return games

    async def _get_new_trending_games(
        self, session: aiohttp.ClientSession
    ) -> List[Dict[str, Any]]:
        url = f"{self.store_url}/search/results/?query&start=0&count=15&dynamic_data=&sort_by=_ASC&supportedlang=english&snr=1_7_7_popularnew_7&filter=popularnew&infinite=1"
        try:
            data = await self.make_request(url, session, is_json=True)
        except Exception as e:
            print(
                f"[{datetime.now()}] SteamService: Failed to fetch new_trending JSON: {e}"
            )
            return []

        if "results_html" not in data:
            print(
                f"[{datetime.now()}] SteamService: No results_html in Steam new_trending response"
            )
            return []

        soup = BeautifulSoup(data["results_html"], "lxml")
        games = []
        for item in soup.select("a.search_result_row"):
            try:
                app_id = item.get("data-ds-appid")
                if not app_id:
                    continue

                name = item.select_one(".title").text.strip()
                price = (
                    item.select_one(".search_price").text.strip()
                    if item.select_one(".search_price")
                    else "N/A"
                )
                release_date = (
                    item.select_one(".search_released").text.strip()
                    if item.select_one(".search_released")
                    else "Unknown"
                )
                review_score = None
                review_summary_span = item.select_one(".search_review_summary span")
                if review_summary_span and 'data-tooltip-html' in review_summary_span.attrs:
                    tooltip_html = review_summary_span['data-tooltip-html']
                    match = re.search(r"(\d+)% of the", tooltip_html)
                    if match:
                        review_score = f"{match.group(1)}%"

                image = (
                    item.select_one(".search_capsule img")["src"]
                    if item.select_one(".search_capsule img")
                    else None
                )
                tags = [
                    tag.text.strip()
                    for tag in item.select(".search_tag")
                    if tag.text.strip()
                ]

                if name and app_id:
                    games.append(
                        {
                            "id": app_id,
                            "name": name,
                            "price": price,
                            "headerImage": image,
                            "platform": "Steam",
                            "releaseDate": release_date,
                            "reviewScore": review_score,
                            "tags": tags,
                            "category": "New & Trending",
                            "isTrending": True,
                            "source": "new_trending_api",
                            "url": item.get('href')
                        }
                    )
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: Error parsing new_trending game: {e}"
                )
                continue
        return games

    async def _get_popular_new_releases(
        self, session: aiohttp.ClientSession
    ) -> List[Dict[str, Any]]:
        url = f"{self.store_url}/search/results/?query&start=0&count=10&dynamic_data=&sort_by=Released_DESC&supportedlang=english&filter=popularnew&infinite=1"
        try:
            data = await self.make_request(url, session, is_json=True)
        except Exception as e:
            print(
                f"[{datetime.now()}] SteamService: Failed to fetch popular_new_releases JSON: {e}"
            )
            return []

        if "results_html" not in data:
            print(
                f"[{datetime.now()}] SteamService: No results_html in Steam popular_new_releases response"
            )
            return []

        soup = BeautifulSoup(data["results_html"], "lxml")
        games = []
        for item in soup.select("a.search_result_row"):
            try:
                app_id = item.get("data-ds-appid")
                if not app_id:
                    continue
                name = item.select_one(".title").text.strip()
                price = (
                    item.select_one(".search_price").text.strip()
                    if item.select_one(".search_price")
                    else "N/A"
                )
                release_date = (
                    item.select_one(".search_released").text.strip()
                    if item.select_one(".search_released")
                    else "Unknown"
                )
                image = (
                    item.select_one(".search_capsule img")["src"]
                    if item.select_one(".search_capsule img")
                    else None
                )
                if name and app_id:
                    games.append(
                        {
                            "id": app_id,
                            "name": name,
                            "price": price,
                            "headerImage": image,
                            "platform": "Steam",
                            "releaseDate": release_date,
                            "category": "Popular New Release",
                            "isTrending": True,
                            "source": "popular_new_releases_api",
                            "url": item.get('href')
                        }
                    )
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: Error parsing popular_new_release: {e}"
                )
                continue
        return games

    async def _get_steam_charts_popular(
        self, session: aiohttp.ClientSession
    ) -> List[Dict[str, Any]]:
        try:
            response_text = await self.make_request(
                "https://steamcharts.com/", session
            )
        except Exception as e:
            print(
                f"[{datetime.now()}] SteamService: Failed to fetch SteamCharts page: {e}"
            )
            return []

        soup = BeautifulSoup(response_text, "lxml")
        games = []
        table = soup.find("table", id="top-games")
        if not table:
            print(
                f"[{datetime.now()}] SteamService: Could not find SteamCharts table"
            )
            return []

        for row in table.select("tbody tr")[:10]:
            try:
                cells = row.select("td")
                if len(cells) < 3:
                    continue
                name_link = cells[1].find("a", href=True)
                name = name_link.text.strip() if name_link else cells[1].text.strip()
                app_id = None
                if name_link:
                    match = re.search(r"/app/(\d+)", name_link["href"])
                    if match: app_id = match.group(1)
                if not app_id: app_id = f"chart_{name.replace(' ', '_').lower()}"


                current_players = int(cells[2].text.strip().replace(",", ""))
                if name.lower() != "game" and current_players > 0:
                    games.append(
                        {
                            "id": app_id,
                            "name": name,
                            "currentPlayers": current_players,
                            "platform": "Steam",
                            "category": "Popular (SteamCharts)",
                            "isTrending": True,
                            "source": "steamcharts_top",
                            "url": name_link['href'] if name_link else None
                        }
                    )
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: Error parsing SteamCharts row: {e}"
                )
                continue
        return games

    async def _get_steam_global_stats(
        self, session: aiohttp.ClientSession
    ) -> List[Dict[str, Any]]:
        try:
            response_text = await self.make_request(
                f"{self.store_url}/stats/Steam-Game-and-Player-Statistics?l=english",
                session,
            )
        except Exception as e:
            print(
                f"[{datetime.now()}] SteamService: Failed to fetch Steam global stats page: {e}"
            )
            return []

        soup = BeautifulSoup(response_text, "lxml")
        games = []
        for row in soup.select(".player_count_row")[:10]:
            try:
                name_link = row.select_one("a.gameLink")
                if not name_link:
                    continue
                name = name_link.text.strip()
                app_id = None
                match = re.search(r"/app/(\d+)", name_link["href"])
                if match: app_id = match.group(1)
                if not app_id: app_id = f"stats_{name.replace(' ', '_').lower()}"


                current_players_cell = row.select_one("span.currentServers")
                current_players = (
                    int(current_players_cell.text.strip().replace(",", ""))
                    if current_players_cell
                    else 0
                )
                if name and current_players > 0:
                    games.append(
                        {
                            "id": app_id,
                            "name": name,
                            "currentPlayers": current_players,
                            "platform": "Steam",
                            "category": "Popular (Global Stats)",
                            "isTrending": True,
                            "source": "steam_global_stats_page",
                            "url": name_link['href'] if name_link else None
                        }
                    )
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: Error parsing Steam global stats row: {e}"
                )
                continue
        return games

    async def get_top_sellers(self) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            url = f"{self.store_url}/search/results/?query&start=0&count=20&dynamic_data=&sort_by=_ASC&supportedlang=english&filter=topsellers&infinite=1"
            try:
                data = await self.make_request(url, session, is_json=True)
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: Failed to fetch top_sellers JSON: {e}"
                )
                return []

            if "results_html" not in data:
                print(
                    f"[{datetime.now()}] SteamService: No results_html in Steam top_sellers response"
                )
                return []

            soup = BeautifulSoup(data["results_html"], "lxml")
            games = []
            for index, item in enumerate(soup.select("a.search_result_row")):
                try:
                    app_id = item.get("data-ds-appid")
                    if not app_id:
                        continue
                    name = item.select_one(".title").text.strip()
                    price_text = (
                        item.select_one(".search_price").text.strip()
                        if item.select_one(".search_price")
                        else "N/A"
                    )
                    discount = 0
                    discount_span = item.select_one(".search_discount span")
                    if discount_span and discount_span.text.strip():
                        try:
                            discount = int(discount_span.text.strip().replace("-","").replace("%",""))
                        except ValueError:
                            pass # discount remains 0

                    review_score, review_count = None, None
                    review_summary_span = item.select_one(".search_review_summary span")
                    if review_summary_span and 'data-tooltip-html' in review_summary_span.attrs:
                        tooltip_html = review_summary_span['data-tooltip-html']
                        score_match = re.search(r"(\d+)% of the", tooltip_html)
                        if score_match: review_score = f"{score_match.group(1)}%"
                        count_match = re.search(r"([\d,]+) user reviews", tooltip_html)
                        if count_match: review_count = count_match.group(1).replace(",", "")


                    release_date = (
                        item.select_one(".search_released").text.strip()
                        if item.select_one(".search_released")
                        else "Unknown"
                    )
                    image = (
                        item.select_one(".search_capsule img")["src"]
                        if item.select_one(".search_capsule img")
                        else None
                    )
                    tags = [
                        tag.text.strip()
                        for tag in item.select(".search_tag")
                        if tag.text.strip()
                    ]
                    if name and app_id:
                        games.append(
                            {
                                "id": app_id,
                                "name": name,
                                "price": price_text,
                                "discount": discount,
                                "headerImage": image,
                                "platform": "Steam",
                                "releaseDate": release_date,
                                "reviewScore": review_score,
                                "reviewCount": review_count,
                                "tags": tags,
                                "rank": index + 1,
                                "isTopSeller": True,
                                "source": "top_sellers_api",
                                "url": item.get('href')
                            }
                        )
                except Exception as e:
                    print(
                        f"[{datetime.now()}] SteamService: Error parsing top_seller: {e}"
                    )
                    continue
            return games

    async def get_current_player_stats(self) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            games_steamcharts = []
            try:
                response_text = await self.make_request(
                    "https://steamcharts.com/", session
                )
                soup = BeautifulSoup(response_text, "lxml")
                table = soup.find("table", id="top-games")
                if table:
                    for index, row in enumerate(table.select("tbody tr")[:20]):
                        try:
                            cells = row.select("td")
                            if len(cells) < 4:
                                continue
                            rank = int(cells[0].text.strip())
                            name_link = cells[1].find("a", href=True)
                            name = name_link.text.strip() if name_link else cells[1].text.strip()

                            app_id = None
                            if name_link:
                                match = re.search(r"/app/(\d+)", name_link["href"])
                                if match: app_id = match.group(1)
                            if not app_id: app_id = f"chart_{name.replace(' ', '_').lower()}"


                            current_players = int(
                                cells[2].text.strip().replace(",", "")
                            )
                            peak_players = int(
                                cells[3].text.strip().replace(",", "")
                            )
                            change_24h = (
                                cells[4].text.strip()
                                if len(cells) > 4 and cells[4].text.strip() != "-"
                                else None
                            )
                            if name.lower() != "game" and current_players > 0:
                                games_steamcharts.append(
                                    {
                                        "id": app_id,
                                        "name": name,
                                        "currentPlayers": current_players,
                                        "peakPlayers": peak_players,
                                        "change24h": change_24h,
                                        "rank": rank,
                                        "platform": "Steam",
                                        "isPopular": True,
                                        "source": "steamcharts_live",
                                        "lastUpdated": datetime.now().isoformat(),
                                        "url": name_link['href'] if name_link else None
                                    }
                                )
                        except Exception as e:
                            print(
                                f"[{datetime.now()}] SteamService: Error parsing SteamCharts player stats row: {e}"
                            )
                            continue
                else:
                    print(
                        f"[{datetime.now()}] SteamService: SteamCharts table not found."
                    )
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: SteamCharts request error: {e}"
                )

            if not games_steamcharts:
                print(
                    f"[{datetime.now()}] SteamService: SteamCharts failed or no data, trying Steam stats page."
                )
                return await self._get_steam_stats_alternative(session)
            return games_steamcharts

    async def _get_steam_stats_alternative(
        self, session: aiohttp.ClientSession
    ) -> List[Dict[str, Any]]:
        try:
            response_text = await self.make_request(
                f"{self.store_url}/stats/Steam-Game-and-Player-Statistics?l=english",
                session,
            )
        except Exception as e:
            print(
                f"[{datetime.now()}] SteamService: Failed to fetch Steam stats alternative page: {e}"
            )
            return []

        soup = BeautifulSoup(response_text, "lxml")
        games = []
        for index, row in enumerate(soup.select(".player_count_row")[:15]):
            try:
                name_link = row.select_one("a.gameLink")
                if not name_link:
                    continue
                name = name_link.text.strip()
                app_id = None
                match = re.search(r"/app/(\d+)", name_link["href"])
                if match: app_id = match.group(1)
                if not app_id: app_id = f"stats_alt_{name.replace(' ', '_').lower()}"

                current_players_cell = row.select_one("span.currentServers")
                current_players = (
                    int(current_players_cell.text.strip().replace(",", ""))
                    if current_players_cell
                    else 0
                )
                if name and current_players > 0:
                    games.append(
                        {
                            "id": app_id,
                            "name": name,
                            "currentPlayers": current_players,
                            "rank": index + 1,
                            "platform": "Steam",
                            "isPopular": True,
                            "source": "steam_stats_page_alt",
                            "lastUpdated": datetime.now().isoformat(),
                            "url": name_link['href'] if name_link else None
                        }
                    )
            except Exception as e:
                print(
                    f"[{datetime.now()}] SteamService: Error parsing Steam stats alternative row: {e}"
                )
                continue
        return games


# --- EpicGamesService class ---
class EpicGamesService:
    def __init__(self):
        self.base_url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        self.store_browse_url = "https://store.epicgames.com/en-US/browse"
        print(f"[{datetime.now()}] EpicGamesService initialized.")


    async def get_free_games(self) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}?locale=en-US&country=US&allowCountries=US"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
            try:
                async with session.get(
                    url, headers=headers, timeout=15
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            except Exception as e:
                print(
                    f"[{datetime.now()}] EpicGamesService: Failed to fetch Epic free games: {e}"
                )
                return []

            games_data = (
                data.get("data", {})
                .get("Catalog", {})
                .get("searchStore", {})
                .get("elements", [])
            )
            if not games_data:
                print(
                    f"[{datetime.now()}] EpicGamesService: No games found in Epic Games free games API response"
                )
                return []

            filtered_games = []
            for game in games_data:
                try:
                    promotions = game.get("promotions", {})
                    current_promos = promotions.get("promotionalOffers", [])
                    upcoming_promos = promotions.get(
                        "upcomingPromotionalOffers", []
                    )

                    is_free_now, promotion_details = False, None
                    if current_promos and current_promos[0].get(
                        "promotionalOffers"
                    ):
                        offer = current_promos[0]["promotionalOffers"][0]
                        if (
                            offer.get("discountSetting", {}).get(
                                "discountPercentage"
                            )
                            == 0
                            and offer.get("endDate")
                        ):
                            is_free_now = True
                            promotion_details = {
                                "startDate": offer.get("startDate"),
                                "endDate": offer.get("endDate"),
                                "type": "current",
                            }

                    is_upcoming_free, upcoming_promotion_details = False, None
                    if not is_free_now and upcoming_promos and upcoming_promos[0].get("promotionalOffers"):
                        offer = upcoming_promos[0]["promotionalOffers"][0]
                        if (
                            offer.get("discountSetting", {}).get(
                                "discountPercentage"
                            )
                            == 0
                            and offer.get("endDate")
                        ):
                            is_upcoming_free = True
                            upcoming_promotion_details = {
                                "startDate": offer.get("startDate"),
                                "endDate": offer.get("endDate"),
                                "type": "upcoming",
                            }
                    
                    if not is_free_now and not is_upcoming_free:
                        continue

                    price_info = game.get("price", {}).get("totalPrice", {})
                    discount_price = price_info.get("discountPrice", 0)
                    if not (discount_price == 0 and (is_free_now or is_upcoming_free)):
                        continue


                    product_slug = game.get("productSlug") or (game.get("offerMappings", [{}])[0].get("pageSlug") if game.get("offerMappings") else None)
                    game_url = f"https://store.epicgames.com/en-US/p/{product_slug}" if product_slug else None
                    if not game_url and game.get('catalogNs',{}).get('mappings'): # Fallback for URL from mappings
                        for mapping in game['catalogNs']['mappings']:
                            if mapping.get('pageType') == 'productHome':
                                game_url = f"https://store.epicgames.com/en-US/p/{mapping.get('pageSlug')}"
                                if not product_slug: product_slug = mapping.get('pageSlug')
                                break


                    filtered_games.append(
                        {
                            "id": game.get("id"),
                            "namespace": game.get("namespace"),
                            "name": game.get("title"),
                            "description": game.get("description"),
                            "originalPrice": price_info.get("fmtPrice", {}).get(
                                "originalPrice", "N/A"
                            ),
                            "discountPrice": price_info.get("fmtPrice", {}).get(
                                "discountPrice", "Free"
                            ),
                            "platform": "Epic Games",
                            "developer": game.get("developerDisplayName"),
                            "publisher": game.get("publisherDisplayName"),
                            "releaseDate": game.get("releaseDate")
                            or game.get("effectiveDate"),
                            "tags": [
                                tag.get("name")
                                for tag in game.get("tags", [])
                                if tag.get("name")
                            ],
                            "images": [
                                {"type": img.get("type"), "url": img.get("url")}
                                for img in game.get("keyImages", [])
                                if img.get("url")
                            ],
                            "isFreeNow": is_free_now,
                            "isUpcomingFree": is_upcoming_free,
                            "promotionDetails": promotion_details
                            if is_free_now
                            else upcoming_promotion_details,
                            "productSlug": product_slug,
                            "url": game_url,
                            "source": "epic_free_games_api"
                        }
                    )
                except Exception as e:
                    print(
                        f"[{datetime.now()}] EpicGamesService: Error processing one Epic free game: {e} - Game: {game.get('title')}"
                    )
                    continue
            if not filtered_games:
                print(
                    f"[{datetime.now()}] EpicGamesService: No free games with active/upcoming promotions found after filtering."
                )
            return filtered_games[:15]

    async def get_trending_games(self) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            html = None
            try:
                async with session.get(
                    f"{self.store_browse_url}?sortBy=trending&sortDir=DESC&count=20",
                    headers=headers,
                    timeout=20,
                ) as response:
                    response.raise_for_status()
                    html = await response.text()
            except Exception as e:
                print(
                    f"[{datetime.now()}] EpicGamesService: Failed to fetch Epic trending browse page: {e}. Falling back to main page."
                )
                try:
                    async with session.get(
                        "https://store.epicgames.com/en-US/",
                        headers=headers,
                        timeout=15,
                    ) as response_main:
                        response_main.raise_for_status()
                        html = await response_main.text()
                except Exception as e_main:
                    print(
                        f"[{datetime.now()}] EpicGamesService: Failed to fetch Epic main page for trending: {e_main}"
                    )
                    return []
            
            if not html: return []

            soup = BeautifulSoup(html, "lxml")
            games = []
            seen_names_or_urls = set()

            # Common selectors for game cards on Epic Store
            # These might need frequent updates due to website changes
            card_selectors = [
                'div[data-testid^="offer-card-"]',
                'article[data-testid^="offer-card-"]',
                '.css-1myhtyb', # Generic card class often used
                '.css-1jx3eyg', # Another generic card class
                'div[role="group"] > div[data-component="DiscoverCard"]', # For discover sections
                'section[data-testid="section-wrapper"] li[data-testid="list-item"]' # For list items in sections
            ]

            game_cards = []
            for selector in card_selectors:
                game_cards.extend(soup.select(selector))
                if len(game_cards) > 20 : break # Stop if we have enough candidates

            for index, card in enumerate(game_cards[:25]): # Process up to 25 candidates
                try:
                    name, price, game_url, image = None, "N/A", None, None

                    # Try to find a link first, as it's a good anchor
                    link_elem = card.find("a", href=True)
                    if link_elem:
                        href_val = link_elem["href"]
                        if href_val.startswith("/"):
                            game_url = f"https://store.epicgames.com{href_val}"
                        elif href_val.startswith("http"):
                            game_url = href_val
                        
                        # Extract name from link's inner text or aria-label
                        name_candidate_elems = link_elem.select('span[data-testid="offer-title-info-title"], div[data-testid="truncate-text-title"], .css-2ucwu, .css-uahz85, span[aria-label]')
                        for elem in name_candidate_elems:
                            if elem.text.strip(): name = elem.text.strip(); break
                        if not name and link_elem.get('aria-label'): name = link_elem.get('aria-label')
                        if not name and link_elem.text.strip(): name = link_elem.text.strip()


                    # If name not found via link, try broader card search
                    if not name:
                        name_elems = card.select('span[data-testid="offer-title-info-title"], div[data-testid="truncate-text-title"], .css-2ucwu, .css-uahz85, h3')
                        for elem in name_elems:
                            if elem.text.strip(): name = elem.text.strip(); break
                    
                    # Image alt text as fallback for name
                    if not name:
                        img_alt_elem = card.select_one("img[alt]")
                        if img_alt_elem and img_alt_elem["alt"].strip():
                            name = img_alt_elem["alt"].strip().replace("Cover art for ", "").replace("Box art for ", "")

                    if not name: continue # Skip if no name found

                    # Deduplication based on name or URL
                    dedup_key = game_url if game_url else name.lower()
                    if dedup_key in seen_names_or_urls: continue
                    seen_names_or_urls.add(dedup_key)

                    price_elems = card.select('span[data-testid="offer-price"], .css-119zqif, .css-4f2d21, div[data-testid="purchase-price-items"] span')
                    for elem in price_elems:
                        if elem.text.strip(): price = elem.text.strip(); break
                    
                    img_elem = card.select_one("img[src]")
                    if img_elem: image = img_elem["src"]

                    game_id = f"epic_trend_{index}"
                    if game_url:
                        match = re.search(r"/(?:p|store)/([^/?]+)", game_url)
                        if match: game_id = match.group(1)
                    elif name:
                        game_id = f"epic_trend_{name.lower().replace(' ', '_').replace(':','')}"


                    games.append(
                        {
                            "id": game_id,
                            "name": name,
                            "price": price,
                            "platform": "Epic Games",
                            "url": game_url,
                            "headerImage": image,
                            "category": "Trending/Featured",
                            "isTrending": True,
                            "source": "epic_store_scrape"
                        }
                    )
                    if len(games) >= 10: break # Limit to 10 distinct games
                except Exception as e:
                    print(
                        f"[{datetime.now()}] EpicGamesService: Error parsing Epic game card: {e}"
                    )
                    continue
            if not games:
                print(
                    f"[{datetime.now()}] EpicGamesService: No trending games found on Epic Games Store via scraping."
                )
            return games


# --- The GameAnalyticsApp class that server.py expects ---
class GameAnalyticsApp:
    def __init__(self):
        print(f"[{datetime.now()}] GameAnalyticsApp: Initializing services...")
        self.steam_service = SteamService()
        self.epic_service = EpicGamesService()
        self.initialization_time = datetime.now()
        print(f"[{datetime.now()}] GameAnalyticsApp: Services initialized.")

    async def get_steam_trending_games(self) -> dict:
        print(
            f"[{datetime.now()}] GameAnalyticsApp: Calling steam_service.get_trending_games"
        )
        try:
            games = await self.steam_service.get_trending_games()
            return {
                "success": True,
                "platform": "Steam",
                "type": "Trending Games",
                "count": len(games),
                "data": games,
                "sources_consulted": [ # This is illustrative; actual sources are in game items
                    "featured_home",
                    "new_trending_api",
                    "popular_new_releases_api",
                    "steamcharts_top",
                    "steam_global_stats_page",
                ],
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(
                f"[{datetime.now()}] GameAnalyticsApp: Error in get_steam_trending_games: {e}"
            )
            return {
                "success": False,
                "error": "Failed to fetch Steam trending games",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_steam_top_sellers(self) -> dict:
        print(
            f"[{datetime.now()}] GameAnalyticsApp: Calling steam_service.get_top_sellers"
        )
        try:
            games = await self.steam_service.get_top_sellers()
            return {
                "success": True,
                "platform": "Steam",
                "type": "Top Sellers",
                "count": len(games),
                "data": games,
                "source_type": "top_sellers_api", # Illustrative
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(
                f"[{datetime.now()}] GameAnalyticsApp: Error in get_steam_top_sellers: {e}"
            )
            return {
                "success": False,
                "error": "Failed to fetch Steam top sellers",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_steam_most_played(self) -> dict:
        print(
            f"[{datetime.now()}] GameAnalyticsApp: Calling steam_service.get_current_player_stats"
        )
        try:
            games = await self.steam_service.get_current_player_stats()
            return {
                "success": True,
                "platform": "Steam",
                "type": "Most Played Games (Live Stats)",
                "count": len(games),
                "data": games,
                "sources_consulted": ["steamcharts_live", "steam_stats_page_alt"], # Illustrative
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(
                f"[{datetime.now()}] GameAnalyticsApp: Error in get_steam_most_played: {e}"
            )
            return {
                "success": False,
                "error": "Failed to fetch Steam player statistics",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_epic_free_games(self) -> dict:
        print(
            f"[{datetime.now()}] GameAnalyticsApp: Calling epic_service.get_free_games"
        )
        try:
            games = await self.epic_service.get_free_games()
            return {
                "success": True,
                "platform": "Epic Games",
                "type": "Free Games",
                "count": len(games),
                "data": games,
                "source_type": "epic_free_games_api", # Illustrative
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(
                f"[{datetime.now()}] GameAnalyticsApp: Error in get_epic_free_games: {e}"
            )
            return {
                "success": False,
                "error": "Failed to fetch Epic Games free games",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_epic_trending_games(self) -> dict:
        print(
            f"[{datetime.now()}] GameAnalyticsApp: Calling epic_service.get_trending_games"
        )
        try:
            games = await self.epic_service.get_trending_games()
            return {
                "success": True,
                "platform": "Epic Games",
                "type": "Trending Games",
                "count": len(games),
                "data": games,
                "source_type": "epic_store_scrape", # Illustrative
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(
                f"[{datetime.now()}] GameAnalyticsApp: Error in get_epic_trending_games: {e}"
            )
            return {
                "success": False,
                "error": "Failed to fetch Epic Games trending games",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_all_trending_games(self) -> dict:
        print(
            f"[{datetime.now()}] GameAnalyticsApp: Calling get_all_trending_games"
        )
        results_template = {
            "success": False, "data": [], "error": None, "message": None, "count": 0, "platform": None, "type": None
        }
        
        steam_trending_res, steam_top_sellers_res, steam_most_played_res, epic_free_res, epic_trending_res = await asyncio.gather(
            self.get_steam_trending_games(),
            self.get_steam_top_sellers(),
            self.get_steam_most_played(),
            self.get_epic_free_games(),
            self.get_epic_trending_games(),
            return_exceptions=True,
        )
        
        all_data = {}
        partial_failures = False

        def process_result(result, platform, type_name):
            nonlocal partial_failures
            if isinstance(result, Exception):
                partial_failures = True
                entry = {**results_template, "platform": platform, "type": type_name}
                entry["error"] = f"Task for {platform} {type_name} failed with exception"
                entry["message"] = str(result)
                return entry
            if not result.get('success'):
                partial_failures = True
            return result

        all_data['steam_trending'] = process_result(steam_trending_res, "Steam", "Trending Games")
        all_data['steam_top_sellers'] = process_result(steam_top_sellers_res, "Steam", "Top Sellers")
        all_data['steam_most_played'] = process_result(steam_most_played_res, "Steam", "Most Played Games")
        all_data['epic_free_games'] = process_result(epic_free_res, "Epic Games", "Free Games")
        all_data['epic_trending_games'] = process_result(epic_trending_res, "Epic Games", "Trending Games")

        overall_success = not partial_failures
        
        if partial_failures:
            print(
                f"[{datetime.now()}] GameAnalyticsApp: get_all_trending_games completed with partial failures."
            )
        else:
            print(
                f"[{datetime.now()}] GameAnalyticsApp: get_all_trending_games completed successfully."
            )

        return {
            "success": overall_success,
            "timestamp": datetime.now().isoformat(),
            "data": all_data,
            "partial_failures_occurred": partial_failures
        }


    def get_api_health(self) -> dict:  # This can be synchronous
        print(f"[{datetime.now()}] GameAnalyticsApp: Calling get_api_health")
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "app_initialization_time": self.initialization_time.isoformat(),
            "version": "2.2.1", # Version bump
            "description": "Gaming Trend Analytics - GameAnalyticsApp Instance",
            "services_status": {
                "steam_service": "initialized"
                if hasattr(self, "steam_service")
                else "not_initialized",
                "epic_service": "initialized"
                if hasattr(self, "epic_service")
                else "not_initialized",
            },
            "notes": "Health check for the GameAnalyticsApp instance. All tool logic is delegated from server.py to this app instance.",
        }

# No MCP instance or tool definitions here. This file is imported by server.py.