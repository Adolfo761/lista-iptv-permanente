import re
import os

FILE_VOD = "vod.m3u"
FILE_TV = "playlist.m3u"
OUT_VOD = "vod_v32.m3u"
OUT_TV = "playlist_v32.m3u"

# --- REGLAS DE CLASIFICACIÓN BASADAS EN TUS CAPTURAS ---
# Si el nombre empieza con o contiene estas palabras, se va a la carpeta asignada.

REGLAS_MIGRACION = [
    # 1. CINE PREMIUM (HBO, TNT, AXN, GOLDEN, ETC.)
    ({"keywords": ["CINE -", "HBO", "MAX", "TNT", "AXN", "GOLDEN", "CINEMAX", "STAR CHANNEL", "UNIVERSAL", "STUDIO UNIVERSAL", "SPACE", "PARAMOUNT", "SONY", "AMC", "LIFETIME", "A&E", "E!", "TELEMUNDO", "DHE", "SYFY", "FILM & ARTS", "EUROPA EUROPA", "EL GOURMET", "FOOD NETWORK", "DISTRITO COMEDIA", "DE PELICULA", "TCM", "FX"], "folder": "TV: 🎬 CINE PREMIUM"}),
    
    # 2. DOCUMENTALES (Vi un "DOC-" en las fotos)
    ({"keywords": ["DOC-", "DISCOVERY", "HISTORY", "ANIMAL PLANET", "NAT GEO", "H&H", "ID INVESTIGATION", "TLC"], "folder": "TV: 🦁 DOCUMENTALES"}),
    
    # 3. SERIES 24/7 (Friends, Big Bang, etc.)
    ({"keywords": ["24/7", "SERIES COMEDIAS", "SERIES NARCOS", "SERIES RETRO", "SERIES ACCION"], "folder": "TV: 📺 SERIES 24/7"}),
    
    # 4. DEPORTES (Si se coló alguno)
    ({"keywords": ["ESPN", "FOX SPORTS", "TUDN", "WIN+", "DAZN", "NBA", "MLB", "UFC"], "folder": "TV: ⚽ DEPORTES"}),
    
    # 5. NOTICIAS INTERNACIONALES (Vi unos iconos de mundos)
    ({"keywords": ["PELICULAS: 🌎", "NOTICIAS", "CNN", "BBC", "TELEDIARIO"], "folder": "TV: 🌍 INTERNACIONAL"} )
]

# Patrón de protección para NO mover películas reales (que tienen año)
PATRON_PELICULA_REAL = re.compile(r'\(\d{4}\)', re.IGNORECASE)

def parse_m3u(filename):
    if not os.path.exists(filename): return []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if not content.startswith("#EXTM3U"): content = "#EXTM3U\n" + content
    return re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)

def main():
    print("🚀 INICIANDO RESCATE DE CANALES V32...")
    
    items_vod = parse_m3u(FILE_VOD)
    items_tv = parse_m3u(FILE_TV)
    
    print(f"📦 VOD Inicial: {len(items_vod)}")
    print(f"📦 TV Inicial: {len(items_tv)}")

    moved_count = 0
    new_vod_list = []
    
    # Procesar VOD
    for entry in items_vod:
        lines = entry.strip().split('\n')
        extinf = lines[0]
        url = lines[1] if len(lines) > 1 else ""
        name = extinf.split(',')[-1].strip()
        name_upper = name.upper()
        
        # ¿Es una película real con Año (2023)? -> SE QUEDA EN VOD
        if PATRON_PELICULA_REAL.search(name):
            new_vod_list.append(entry)
            continue
            
        # ¿Es un canal que debemos rescatar?
        encontrado = False
        for regla in REGLAS_MIGRACION:
            # Verificamos si cumple alguna keyword
            if any(k in name_upper for k in regla["keywords"]):
                
                # ¡ES UN CANAL! Lo movemos a TV
                new_group = regla["folder"]
                
                # Limpiamos el nombre (quitamos "CINE -" o "DOC-" para que se vea limpio en la lista)
                # Opcional: Si prefieres dejar el nombre original, comenta estas lineas
                clean_name = name.replace("CINE - ", "").replace("DOC-", "").strip()
                
                # Reconstruimos el EXTINF
                if 'group-title="' in extinf:
                    extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
                else:
                    extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')
                
                # Actualizamos el nombre visible
                parts = extinf.split(',')
                extinf = ",".join(parts[:-1]) + "," + clean_name
                
                items_tv.append(f"{extinf}\n{url}")
                moved_count += 1
                encontrado = True
                break # Ya lo encontramos, pasamos al siguiente
        
        if not encontrado:
            # Si no encaja en ninguna regla de TV, se queda en VOD (puede ser una peli sin año o basura)
            new_vod_list.append(entry)

    # ORDENAR LA LISTA DE TV (Importante para que las nuevas carpetas queden bien ubicadas)
    print("📊 Organizando y ordenando lista de TV...")
    items_tv.sort(key=lambda x: (x.split('group-title="')[1].split('"')[0] if 'group-title="' in x else "ZZZ", x.split(',')[-1]))

    # GUARDAR
    with open(OUT_VOD, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in new_vod_list: f.write(item.strip() + "\n")

    with open(OUT_TV, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in items_tv: f.write(item.strip() + "\n")

    print(f"✅ ¡OPERACIÓN COMPLETADA!")
    print(f"   🚑 Canales Rescatados y Movidos a TV: {moved_count}")
    print(f"   📺 Tamaño final Lista TV: {len(items_tv)}")
    print(f"   📼 Tamaño final Lista VOD: {len(new_vod_list)}")

if __name__ == "__main__":
    main()
