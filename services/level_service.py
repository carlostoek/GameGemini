# services/level_service.py

# Define los niveles y rangos aquí. Puedes adaptar los nombres y puntos.
LEVELS = [
    {"name": "Suscriptor Íntimo", "min_points": 0, "max_points": 99},
    {"name": "Conocedor Apasionado", "min_points": 100, "max_points": 499},
    {"name": "Maestro del Deseo", "min_points": 500, "max_points": 999},
    {"name": "Leyenda VIP", "min_points": 1000, "max_points": 1999},
    {"name": "Ícono VIP", "min_points": 2000, "max_points": 3499},
    {"name": "Leyenda Suprema", "min_points": 3500, "max_points": float("inf")},
]

async def get_level_by_points(points: int):
    for level in LEVELS:
        if level["min_points"] <= points <= level["max_points"]:
            return level["name"]
    return LEVELS[0]["name"]

async def get_progress_to_next_level(points: int):
    """
    Devuelve (nivel actual, puntos actuales, puntos requeridos para el siguiente nivel, % de avance).
    """
    for idx, level in enumerate(LEVELS):
        if level["min_points"] <= points <= level["max_points"]:
            next_level = LEVELS[idx + 1] if idx + 1 < len(LEVELS) else None
            points_to_next = (next_level["min_points"] - points) if next_level else 0
            percent = (
                100
                if not next_level
                else int(100 * (points - level["min_points"]) / (next_level["min_points"] - level["min_points"]))
            )
            return {
                "current_level": level["name"],
                "current_points": points,
                "next_level": next_level["name"] if next_level else None,
                "points_to_next": points_to_next,
                "percent": percent,
            }
    # Fallback (por si acaso)
    return {
        "current_level": LEVELS[0]["name"],
        "current_points": points,
        "next_level": LEVELS[1]["name"],
        "points_to_next": LEVELS[1]["min_points"] - points,
        "percent": 0,
    }
