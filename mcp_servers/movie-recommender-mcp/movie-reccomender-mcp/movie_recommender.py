import requests

def getMovieSuggestions(keyword: str) -> str:
    """
    Get movie suggestions from TMDb API based on keyword.
    """
    API_KEY = "c6fae702c36224d5f01778d394772520"  # Gerçek key ile değiştirilebilir
    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={keyword}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if not data.get("results"):
            return "Film bulunamadı."

        suggestions = []
        for movie in data["results"][:3]:
            title = movie.get("title", "Bilinmiyor")
            overview = movie.get("overview", "Açıklama yok.")
            suggestions.append(f"🎬 {title}\n{overview}")

        return "\n\n".join(suggestions)
    else:
        return "API isteği başarısız oldu."
