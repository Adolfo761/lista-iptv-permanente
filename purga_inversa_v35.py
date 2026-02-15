import re
import os

FILE_TV = "playlist.m3u"
FILE_VOD = "vod.m3u"
OUT_TV = "playlist_v35.m3u"
OUT_VOD = "vod_v35.m3u"

# 1. PATRONES DE SERIES Y PELÍCULAS (Que no deben estar en TV)
# Busca: S01E01, (2024), [SubsEspanol], etc.
PATRON_VOD = re.compile(r'(S\d+\s*E\d+|TEMPORADA|CAP[IÍ]TULO|\(\d{4}\)|\[.*?\])', re.IGNORECASE)

# 2. PALABRAS CLAVE DE ADULTOS (Sacadas de tus fotos y generales)
KEYWORDS_ADULT = [
    "CORY CHASE", "BAISE-MOI", "EVIL ANGEL", "LARA DURO", "PORN", "XXX", "SEX", 
    "KAMA SUTRA", "EROTIC", "ADULT", "18+", "NSFW", "UNCENSORED", "BRAZZERS",
    "REALITY KINGS", "MOFOS", "BANG BROS", "XVIDEOS", "PRIVATE"
]

def parse_m3u(filename):
    if not os.path.exists(filename): return []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if not content.startswith("#EXTM3U"): content = "#EXTM3U\n" + content
    return re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)

def main():
    print("🚀 INICIANDO PURGA INVERSA V35 (LIMPIEZA DE TV)...")
    
    items_tv = parse_m3u(FILE_TV)
    items_vod = parse_m3u(FILE_VOD)
    
    print(f"📦 Canales TV Antes: {len(items_tv)}")
    
    clean_tv = []
    transferred_to_vod = []
    
    count_adults = 0
    count_series = 0
    count_movies = 0

    for entry in items_tv:
        lines = entry.strip().split('\n')
        extinf = lines[0]
        url = lines[1] if len(lines) > 1 else ""
        name = extinf.split(',')[-1].strip()
        name_upper = name.upper()
        
        # --- DETECCIÓN DE INTRUSOS ---
        
        # 1. ES ADULTO? (Cory Chase, Baise-moi, etc)
        if any(k in name_upper for k in KEYWORDS_ADULT):
            # Mover a VOD -> ZONA ADULTOS
            new_group = "ZONA ADULTOS (+18) 🔞"
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')
            
            transferred_to_vod.append(f"{extinf}\n{url}")
            count_adults += 1
            continue

        # 2. ES SERIE? (Star Trek S1 E1, Astra S1 E3)
        match_serie = re.search(r'(.*?)\s*(?:S\d+|TEMPORADA|CAP[IÍ]TULO)', name, re.IGNORECASE)
        if match_serie:
            # Mover a VOD -> SERIE: NOMBRE
            nombre_serie = match_serie.group(1).strip(' -:|')
            new_group = f"SERIE: {nombre_serie.upper()}" if len(nombre_serie) > 2 else "SERIE: VARIAS"
            
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')

            transferred_to_vod.append(f"{extinf}\n{url}")
            count_series += 1
            continue

        # 3. ES PELÍCULA? (Tiene Año entre parentesis)
        if re.search(r'\(\d{4}\)', name):
            # Mover a VOD -> PELICULAS: GENERAL
            new_group = "PELICULAS: GENERAL"
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')
                
            transferred_to_vod.append(f"{extinf}\n{url}")
            count_movies += 1
            continue

        # SI PASA TODOS LOS FILTROS -> ES UN CANAL REAL
        clean_tv.append(entry)

    # UNIR LO NUEVO AL VOD EXISTENTE
    final_vod = items_vod + transferred_to_vod

    # GUARDAR RESULTADOS
    with open(OUT_TV, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in clean_tv: f.write(item.strip() + "\n")

    with open(OUT_VOD, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in final_vod: f.write(item.strip() + "\n")

    print(f"✅ ¡PURGA COMPLETADA!")
    print(f"   📺 Canales Legítimos restantes: {len(clean_tv)}")
    print(f"   🗑️ BASURA SACADA DE TV:")
    print(f"      - Adultos infiltrados: {count_adults}")
    print(f"      - Series infiltradas: {count_series}")
    print(f"      - Películas infiltradas: {count_movies}")
    print(f"   📦 Todo esto se movió a vod.m3u")

if __name__ == "__main__":
    main()
