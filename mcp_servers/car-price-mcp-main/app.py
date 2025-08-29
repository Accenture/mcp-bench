import requests
import json

def getCarBrands() -> str:
    """
    Get all car brands from FIPE API.
    """
    try:
        url = "https://parallelum.com.br/fipe/api/v1/carros/marcas"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return f"Error: Could not fetch car brands (Status: {response.status_code})"
        
        brands = response.json()
        
        if not brands:
            return "No car brands found"
        
        # Format brands information
        brands_info = "🚗 **Car Brands Available** 🚗\n\n"
        
        # Group brands by first letter for better organization
        brands_by_letter = {}
        for brand in brands:
            first_letter = brand['nome'][0].upper()
            if first_letter not in brands_by_letter:
                brands_by_letter[first_letter] = []
            brands_by_letter[first_letter].append(brand)
        
        # Show first 20 brands
        count = 0
        for letter in sorted(brands_by_letter.keys()):
            if count >= 20:
                break
            brands_info += f"**{letter}:**\n"
            for brand in brands_by_letter[letter][:5]:  # Max 5 per letter
                if count >= 20:
                    break
                brands_info += f"  • {brand['nome']} (Code: {brand['codigo']})\n"
                count += 1
            brands_info += "\n"
        
        brands_info += f"*Total: {len(brands)} brands available*\n"
        brands_info += "*Use searchCarPrice with brand name to get models and prices*"
        
        return brands_info
        
    except Exception as e:
        return f"Error fetching car brands: {str(e)}"

def searchCarPrice(query: str) -> str:
    """
    Search for car price by brand and model name.
    """
    try:
        # First get all brands
        brands_url = "https://parallelum.com.br/fipe/api/v1/carros/marcas"
        response = requests.get(brands_url, timeout=10)
        
        if response.status_code != 200:
            return f"Error: Could not fetch brands (Status: {response.status_code})"
        
        brands = response.json()
        
        # Search for brand by name (case insensitive)
        query_lower = query.lower()
        found_brand = None
        
        for brand in brands:
            if query_lower in brand['nome'].lower():
                found_brand = brand
                break
        
        if not found_brand:
            # If no brand found, show available brands
            brand_names = [brand['nome'] for brand in brands[:10]]
            return f"Brand '{query}' not found. Available brands include: {', '.join(brand_names)}..."
        
        # Get models for the found brand
        models_url = f"https://parallelum.com.br/fipe/api/v1/carros/marcas/{found_brand['codigo']}/modelos"
        response = requests.get(models_url, timeout=10)
        
        if response.status_code != 200:
            return f"Error: Could not fetch models for {found_brand['nome']} (Status: {response.status_code})"
        
        models_data = response.json()
        models = models_data.get("modelos", [])
        
        if not models:
            return f"No models found for {found_brand['nome']}"
        
        # Get price for first 3 models
        car_info = f"🚗 **{found_brand['nome']} Models & Prices** 🚗\n\n"
        
        for i, model in enumerate(models[:3]):  # Show first 3 models
            try:
                # Get years for this model
                years_url = f"https://parallelum.com.br/fipe/api/v1/carros/marcas/{found_brand['codigo']}/modelos/{model['codigo']}/anos"
                years_response = requests.get(years_url, timeout=10)
                
                if years_response.status_code == 200:
                    years = years_response.json()
                    if years:
                        # Get price for most recent year
                        latest_year = years[0]
                        price_url = f"https://parallelum.com.br/fipe/api/v1/carros/marcas/{found_brand['codigo']}/modelos/{model['codigo']}/anos/{latest_year['codigo']}"
                        price_response = requests.get(price_url, timeout=10)
                        
                        if price_response.status_code == 200:
                            price_data = price_response.json()
                            
                            car_info += f"**{i+1}. {model['nome']}**\n"
                            car_info += f"📅 **Year:** {price_data.get('AnoModelo', 'N/A')}\n"
                            car_info += f"⛽ **Fuel:** {price_data.get('Combustivel', 'N/A')}\n"
                            car_info += f"💰 **Price:** {price_data.get('Valor', 'N/A')}\n"
                            car_info += f"📊 **Reference:** {price_data.get('MesReferencia', 'N/A')}\n"
                            car_info += f"🔢 **FIPE Code:** {price_data.get('CodigoFipe', 'N/A')}\n\n"
                        else:
                            car_info += f"**{i+1}. {model['nome']}** - Price not available\n\n"
                    else:
                        car_info += f"**{i+1}. {model['nome']}** - No years available\n\n"
                else:
                    car_info += f"**{i+1}. {model['nome']}** - Years not available\n\n"
                    
            except Exception as model_error:
                car_info += f"**{i+1}. {model['nome']}** - Error: {str(model_error)}\n\n"
        
        if len(models) > 3:
            car_info += f"*...and {len(models)-3} more models available*\n"
        
        car_info += f"\n**Total Models:** {len(models)}\n"
        car_info += "*Prices are from FIPE (Brazilian vehicle price reference)*"
        
        return car_info
        
    except Exception as e:
        return f"Error searching for '{query}': {str(e)}"

def getCarsByType(vehicle_type: str) -> str:
    """
    Get vehicles by type (carros, motos, caminhoes).
    """
    try:
        # Map vehicle types
        type_mapping = {
            'car': 'carros',
            'cars': 'carros',
            'carro': 'carros',
            'carros': 'carros',
            'motorcycle': 'motos',
            'motorcycles': 'motos',
            'moto': 'motos',
            'motos': 'motos',
            'truck': 'caminhoes',
            'trucks': 'caminhoes',
            'caminhao': 'caminhoes',
            'caminhoes': 'caminhoes'
        }
        
        api_type = type_mapping.get(vehicle_type.lower(), 'carros')
        
        url = f"https://parallelum.com.br/fipe/api/v1/{api_type}/marcas"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return f"Error: Could not fetch {vehicle_type} brands (Status: {response.status_code})"
        
        brands = response.json()
        
        if not brands:
            return f"No {vehicle_type} brands found"
        
        # Format vehicle type info
        type_emoji = "🚗" if api_type == "carros" else "🏍️" if api_type == "motos" else "🚛"
        vehicles_info = f"{type_emoji} **{vehicle_type.title()} Brands** {type_emoji}\n\n"
        
        # Show first 15 brands
        for i, brand in enumerate(brands[:15], 1):
            vehicles_info += f"**{i}. {brand['nome']}** (Code: {brand['codigo']})\n"
        
        if len(brands) > 15:
            vehicles_info += f"\n*...and {len(brands)-15} more brands*\n"
        
        vehicles_info += f"\n**Total Brands:** {len(brands)}\n"
        vehicles_info += f"*Use searchCarPrice with brand name to get specific models and prices*"
        
        return vehicles_info
        
    except Exception as e:
        return f"Error fetching {vehicle_type} brands: {str(e)}"
