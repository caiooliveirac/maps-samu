"""
Dados de seed — Bases e Ambulâncias do SAMU Salvador.

10 bases reais do SAMU 192 Salvador.
12 ambulâncias USA (Unidade de Suporte Avançado).
Pau Miúdo e Boca do Rio recebem 2 cada.
Coordenadas capturadas diretamente no mapa (tiles CARTO/OSM).
"""

BASES = [
    {
        "code": "BASE-CC",
        "name": "Base Cabula",
        "address": "Cabula, Salvador-BA",
        "neighborhood": "Cabula",
        "latitude": -12.959085368755753,
        "longitude": -38.452475666999824,
    },
    {
        "code": "BASE-PM",
        "name": "Base Pau Miúdo",
        "address": "Pau Miúdo, Salvador-BA",
        "neighborhood": "Pau Miúdo",
        "latitude": -12.95905922981074,
        "longitude": -38.48783791065217,
    },
    {
        "code": "BASE-CZ",
        "name": "Base Cajazeiras",
        "address": "Cajazeiras, Salvador-BA",
        "neighborhood": "Cajazeiras",
        "latitude": -12.89830491875039,
        "longitude": -38.38994264602661,
    },
    {
        "code": "BASE-PP",
        "name": "Base Periperi",
        "address": "Periperi, Salvador-BA",
        "neighborhood": "Periperi",
        "latitude": -12.86804250862112,
        "longitude": -38.47256004810334,
    },
    {
        "code": "BASE-SM",
        "name": "Base San Martin",
        "address": "San Martin, Salvador-BA",
        "neighborhood": "San Martin",
        "latitude": -12.94683635856308,
        "longitude": -38.4812879562378,
    },
    {
        "code": "BASE-CN",
        "name": "Base Centenário",
        "address": "Centenário, Salvador-BA",
        "neighborhood": "Centenário",
        "latitude": -12.99081602269466,
        "longitude": -38.51138234138489,
    },
    {
        "code": "BASE-BR",
        "name": "Base Boca do Rio",
        "address": "Boca do Rio, Salvador-BA",
        "neighborhood": "Boca do Rio",
        "latitude": -12.983680899095727,
        "longitude": -38.438683748245246,
    },
    {
        "code": "BASE-IT",
        "name": "Base Itapoã",
        "address": "Itapoã, Salvador-BA",
        "neighborhood": "Itapoã",
        "latitude": -12.92447500417301,
        "longitude": -38.35114717483521,
    },
    {
        "code": "BASE-CB",
        "name": "Base Cidade Baixa",
        "address": "Cidade Baixa, Salvador-BA",
        "neighborhood": "Cidade Baixa",
        "latitude": -12.935104347757715,
        "longitude": -38.50652754306794,
    },
    {
        "code": "BASE-PR",
        "name": "Base Paralela",
        "address": "Paralela, Salvador-BA",
        "neighborhood": "Paralela",
        "latitude": -12.937347274850167,
        "longitude": -38.39782297611237,
    },
]

# 12 ambulâncias USA (Suporte Avançado) — Pau Miúdo e Boca do Rio recebem 2
AMBULANCES = [
    {"code": "CC70", "ambulance_type": "USA", "base_code": "BASE-CC"},
    {"code": "PM04", "ambulance_type": "USA", "base_code": "BASE-PM"},
    {"code": "PM40", "ambulance_type": "USA", "base_code": "BASE-PM"},
    {"code": "CZ50", "ambulance_type": "USA", "base_code": "BASE-CZ"},
    {"code": "PP20", "ambulance_type": "USA", "base_code": "BASE-PP"},
    {"code": "SM01", "ambulance_type": "USA", "base_code": "BASE-SM"},
    {"code": "CN10", "ambulance_type": "USA", "base_code": "BASE-CN"},
    {"code": "BR60", "ambulance_type": "USA", "base_code": "BASE-BR"},
    {"code": "BR05", "ambulance_type": "USA", "base_code": "BASE-BR"},
    {"code": "IT30", "ambulance_type": "USA", "base_code": "BASE-IT"},
    {"code": "CB02", "ambulance_type": "USA", "base_code": "BASE-CB"},
    {"code": "PR03", "ambulance_type": "USA", "base_code": "BASE-PR"},
]
