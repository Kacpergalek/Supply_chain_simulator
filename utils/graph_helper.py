import math

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

import math


def convert_speed(data: str | list | int | float | None, output_type: str = "float"):
    """
    Konwertuje różne formaty prędkości na km/h.
    Obsługuje: mph, knots, km/h, listy wartości, stringi z 'nan'.
    """
    
    # 1. Obsługa listy (np. ['50', '30'] lub "50;30")
    if isinstance(data, list):
        valid_speeds = []
        for item in data:
            # Rekurencyjne wywołanie dla każdego elementu listy
            val = convert_speed(item, output_type="float")
            if val is not None:
                valid_speeds.append(val)
        
        if not valid_speeds:
            return None
        # Zwracamy najniższą prędkość (najbezpieczniejszą dla routingu)
        result = min(valid_speeds)
        return int(result) if output_type == "int" else result

    # 2. Obsługa None i typów numerycznych
    if data is None:
        return None
    
    if isinstance(data, (int, float)):
        # Zakładamy, że czysta liczba to już km/h
        if math.isnan(data): return None
        return int(data) if output_type == "int" else float(data)

    # 3. Czyszczenie stringa
    data_str = str(data).strip().lower()
    
    # Obsługa "nan", "none", pustych oraz "signal" (częste w OSM)
    if data_str in ["nan", "none", "null", "", "signals"]:
        return None

    # Współczynniki konwersji
    MPH_TO_KMH = 1.60934
    KNOT_TO_KMH = 1.852

    try:
        value_kmh = 0.0
        
        # 4. Wykrywanie jednostek
        
        # Przypadek A: Mile na godzinę (mph)
        if "mph" in data_str:
            clean = data_str.replace("mph", "").strip()
            value_kmh = float(clean) * MPH_TO_KMH
            
        # Przypadek B: Węzły (knots / kn)
        elif "knots" in data_str or "kn" in data_str:
            clean = data_str.replace("knots", "").replace("kn", "").strip()
            value_kmh = float(clean) * KNOT_TO_KMH
            
        # Przypadek C: Kilometry na godzinę (km/h, kmh, kph)
        elif "km" in data_str or "kph" in data_str:
            # Usuwamy wszystko co nie jest liczbą (proste czyszczenie sufiksów)
            clean = data_str.replace("km/h", "").replace("kmh", "").replace("kph", "").strip()
            value_kmh = float(clean)
            
        # Przypadek E: Sama liczba (zakładamy km/h)
        else:
            value_kmh = float(data_str)

        # Finalny zwrot
        return int(value_kmh) if output_type == "int" else value_kmh

    except (ValueError, TypeError):
        # Jeśli mimo czyszczenia nie uda się zrobić float()
        return None