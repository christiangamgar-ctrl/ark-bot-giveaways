# ─────────────────────────────────────────────
#  CONFIGURACIÓN GENERAL DEL BOT
# ─────────────────────────────────────────────

# Tu link de PayPal para comprar llaves
PAYPAL_LINK = "https://www.paypal.com/paypalme/ArkStarLegacy"

# Precio de cada llave en euros
KEY_PRICE_EUR = 10

# ID del rol de admin (cámbialo por el tuyo)
# Los miembros con este rol podrán usar comandos de admin
ADMIN_ROLE_NAME = "Admin"  # O usa ADMIN_ROLE_ID = 123456789

# ─────────────────────────────────────────────
#  PREMIOS DE GIVEAWAY
# ─────────────────────────────────────────────
GIVEAWAY_PRIZES = [
    "10 Credits",
    "20 Credits",
    "30 Credits",
    "40 Credits",
    "50 Credits",
    "1x ASC",
    "2x ASC",
    "Full Tribe ASC",
]

# ─────────────────────────────────────────────
#  CONTENIDO MYSTERY BOX (con probabilidades)
# ─────────────────────────────────────────────
# Cada entrada: ("nombre del premio", peso_probabilidad)
# Mayor peso = más probable. Private Map tiene el menor peso.
MYSTERY_BOX_PRIZES = [
    ("2 Dino Colors",           15),
    ("2 OC Blueprints",         15),
    ("Variety Pack 10",         10),
    ("Variety Pack 20",         8),
    ("Variety Pack 50",         5),
    ("Breeding Pack 10",        10),
    ("Breeding Pack 15",        8),
    ("Breeding Pack 25",        6),
    ("Breeding Pack 40",        4),
    ("Breeding Pack 60",        3),
    ("Ammo Pack 15",            10),
    ("Ammo Pack 25",            7),
    ("Ammo Pack 40",            5),
    ("Ascension Pack 6",        8),
    ("Ascension Pack 15",       5),
    ("Ascension Pack 20",       3),
    ("Blueprints Pack 10",      8),
    ("Blueprints Pack 25",      5),
    ("Blueprints Pack 60",      3),
    ("Turret Pack 10",          8),
    ("Turret Pack 25",          5),
    ("Turret Pack 50",          3),
    ("Base Pack 10",            8),
    ("Base Pack 20",            6),
    ("Base Pack 40",            4),
    ("Base Pack 60",            2),
    ("Private Map 12h",         2),
    ("Private Map 24h",         1),
    ("Private Map 48h",         1),
]
