import math

import unicodedata

def haversine_coordinates(lat1, lon1, lat2, lon2, metric : str):
    if metric == "length":
        R = 6371  # promień Ziemi

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c * 1000

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    d_lon = lon2 - lon1
    d_lat = lat2 - lat1
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(d_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return 6371 * c


def convert_speed(data: str | list | int | float | None, output_type: str = "float"):
    """
    Konwertuje różne formaty prędkości na km/h.
    Obsługuje: mph, knots, km/h, listy wartości, stringi z 'nan'.
    """
    
    if isinstance(data, list):
        valid_speeds = []
        for item in data:
            # Rekurencyjne wywołanie dla każdego elementu listy
            val = convert_speed(item, output_type="float")
            if val is not None:
                valid_speeds.append(val)
        
        if not valid_speeds:
            return None
        result = min(valid_speeds)
        return int(result) if output_type == "int" else result

    if data is None:
        return None
    
    if isinstance(data, (int, float)):
        if math.isnan(data): return None
        return int(data) if output_type == "int" else float(data)

    data_str = str(data).strip().lower()
    
    if data_str in ["nan", "none", "null", "", "signals"]:
        return None

    MPH_TO_KMH = 1.60934
    KNOT_TO_KMH = 1.852

    try:
        value_kmh = 0.0

        if "mph" in data_str:
            clean = data_str.replace("mph", "").strip()
            value_kmh = float(clean) * MPH_TO_KMH
            
        elif "knots" in data_str or "kn" in data_str:
            clean = data_str.replace("knots", "").replace("kn", "").strip()
            value_kmh = float(clean) * KNOT_TO_KMH
            
        elif "km" in data_str or "kph" in data_str:
            # Usuwamy wszystko co nie jest liczbą (proste czyszczenie sufiksów)
            clean = data_str.replace("km/h", "").replace("kmh", "").replace("kph", "").strip()
            value_kmh = float(clean)
            
        else:
            value_kmh = float(data_str)

        return int(value_kmh) if output_type == "int" else value_kmh

    except (ValueError, TypeError):
        return None


def normalize_country(country: str) -> str:
    country = country.replace("ł", "l").replace("Ł", "L")

    normalized = unicodedata.normalize('NFKD', country)

    # 3. Odfiltrowanie znaków diakrytycznych (ogonków, kresek)
    ascii_text = "".join([c for c in normalized if not unicodedata.combining(c)])

    return (
        ascii_text
        .lower()
        .strip()
        .replace(" ", "_")
        .replace(",", "")
    )