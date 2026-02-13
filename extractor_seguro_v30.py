import re
import os

FILE_VOD = "vod.m3u"
FILE_TV = "playlist.m3u"
OUT_VOD = "vod_v30.m3u"
OUT_TV = "playlist_v30.m3u"

# PALABRAS CLAVE BLINDADAS (Basadas en tus capturas)
KEYWORDS_ADULTOS = [
    "XXX", "PORNO", "ADULT", "PLAYBOY", "VENUS", "SEXY", "HOT", "EROTIC", "HENTAI", 
    "PRIVATE", "REDLIGHT", "BRAZZERS", "BLACKED", "BANGBROS", "CAM SODA", "AV TAXI",
    "BABES", "TEAMSKEET", "CUM4K", "DEEPER", "REALITY KINGS", "MOFOS", "NAUGHTY",
    "FAKE HUB", "PENTHOUSE", "HUSTLER", "VIXEN", "TUSHY", "BLACK4K", "21 NATURALS",
    "21 SEXTREME", "BABY DOLL", "ROXIE SINNER", "ADERES QUIN", "ERIN EVERHEART"
]

CATEGORIAS_TV = {
    "DEPORTES": ["ESPN", "FOX SPORTS", "SPORT", "DEPORTE", "FUTBOL", "SOCCER", "NBA", "MLB", "NFL", "UFC", "TUDN", "DAZN"],
    "INFANTILES": ["DISNEY", "NICK", "CARTOON", "KIDS", "JUNIOR", "BOOMERANG", "TOONCAST", "DISCOVERY KIDS", "NAT GEO KIDS"],
    "CINE": ["HBO", "CINEMAX", "TNT", "STAR", "CINEMA", "CINE", "PELICULA", "AMC", "AXN", "FX", "GOLDEN", "PARAMOUNT", "SPACE"],
    "NOTICIAS": ["NOTICIA", "NEWS", "CNN", "BBC", "TELEDIARIO", "24H", "WEATHER", "AL JAZEERA"],
    "DOCUMENTALES": ["DISCOVERY", "HISTORY", "NAT GEO", "ANIMAL PLANET", "INVESTIGATION", "H&H"],
    "MUSICA": ["MTV", "VH1", "HTV", "MUSIC", "KARAOKE"]
}

# Patrón para identificar VOD REAL (Películas y Series que se deben quedar en VOD)
PATRON_VOD_REAL = re.compile(r'\(\d{4}\)|S\d+|E\d+|TEMPORADA|CAP[IÍ]TULO|EPISODIO|\d+x\d+', re.IGNORECASE)

def parse_m3u(filename):
    if not os.path.exists(filename): return []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if not content.startswith("#EXTM3U"): content = "#EXTM3U\n" + content
    return re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)

def main():
    print("🚀 INICIANDO EXTRACCIÓN SEGURA V30...")
    
    items_vod = parse_m3u(FILE_VOD)
    items_tv = parse_m3u(FILE_TV)
    
    new_vod_list = []
    moved_to_adults = 0
    moved_to_tv = 0
    
    # Procesar VOD
    for entry in items_vod:
        lines = entry.strip().split('\n')
        extinf = lines[0]
        url = lines[1] if len(lines) > 1 else ""
        name = extinf.split(',')[-1].strip().upper()
        
        # 1. DETECCIÓN DE ADULTOS (PRIORIDAD MÁXIMA)
        if any(k in name for k in KEYWORDS_ADULTOS):
            # Se queda en VOD, pero nos aseguramos que vaya a la carpeta correcta
            new_group = "ZONA ADULTOS (+18) 🔞"
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')
            new_vod_list.append(f"{extinf}\n{url}")
            moved_to_adults += 1
            continue

        # 2. ¿ES UNA PELÍCULA O SERIE DE VERDAD? (Año, Temporada)
        if PATRON_VOD_REAL.search(name):
            # Se queda en VOD tal cual
            new_vod_list.append(entry)
            continue

        # 3. SI LLEGAMOS AQUÍ, PODRÍA SER UN CANAL EN VIVO... PERO CON CUIDADO
        found_category = None
        new_group_tv = "TV: 📺 VARIOS" # Default seguro

        for cat, keywords in CATEGORIAS_TV.items():
            if any(k in name for k in keywords):
                found_category = cat
                # EMOJIS
                emoji = "📺"
                if cat == "DEPORTES": emoji = "⚽"
                elif cat == "INFANTILES": emoji = "🦄"
                elif cat == "CINE": emoji = "🎬"
                elif cat == "NOTICIAS": emoji = "🌍"
                elif cat == "DOCUMENTALES": emoji = "🦁"
                elif cat == "MUSICA": emoji = "🎵"
                
                new_group_tv = f"TV: {emoji} {cat}"
                break
        
        # Corrección de "TV: TV:" (Si el script anterior la lió o el original venía mal)
        # Aquí forzamos el nombre limpio.
        
        if found_category:
            # Es un canal reconocido (ESPN, HBO...), lo movemos a TV
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group_tv}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group_tv}"')
            items_tv.append(f"{extinf}\n{url}")
            moved_to_tv += 1
        else:
            # Si NO tiene año, NO tiene temporada y NO es un canal conocido...
            # Probablemente sea un clip basura o algo raro. MEJOR DEJARLO EN VOD "OTROS"
            # Para no ensuciar la lista de TV.
            new_group = "VOD: OTROS / SIN CLASIFICAR"
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')
            new_vod_list.append(f"{extinf}\n{url}")

    # ORDENAR TV (Limpiando dobles prefijos por si acaso)
    final_tv_items = []
    for item in items_tv:
        # Limpieza final de "TV: TV:"
        item = item.replace('group-title="TV: TV:', 'group-title="TV:')
        final_tv_items.append(item)

    final_tv_items.sort(key=lambda x: x.split(',')[0]) # Ordenar alfabéticamente

    # GUARDAR
    with open(OUT_VOD, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in new_vod_list: f.write(item.strip() + "\n")

    with open(OUT_TV, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in final_tv_items: f.write(item.strip() + "\n")

    print(f"✅ ¡AUDITORÍA BLINDADA COMPLETADA!")
    print(f"   🔞 Clips adultos detectados y asegurados en VOD: {moved_to_adults}")
    print(f"   📺 Canales reales movidos a TV: {moved_to_tv}")
    print(f"   📼 Se mantienen en VOD: {len(new_vod_list)}")

if __name__ == "__main__":
    main()
