"""
Dados de seed — Bases e Ambulâncias do SAMU Salvador.

10 bases distribuídas estrategicamente pela cidade.
12 ambulâncias (Brotas e Pituba recebem 2 cada — áreas de alta demanda).
"""

BASES = [
    {
        "code": "BASE-01",
        "name": "Base Central - Brotas",
        "address": "Av. Dom João VI, s/n, Brotas, Salvador-BA",
        "neighborhood": "Brotas",
        "latitude": -12.9866,
        "longitude": -38.5033,
    },
    {
        "code": "BASE-02",
        "name": "Base Itapagipe",
        "address": "Av. Beira Mar, s/n, Ribeira, Salvador-BA",
        "neighborhood": "Itapagipe",
        "latitude": -12.9267,
        "longitude": -38.5059,
    },
    {
        "code": "BASE-03",
        "name": "Base Cabula",
        "address": "Rua Silveira Martins, s/n, Cabula, Salvador-BA",
        "neighborhood": "Cabula",
        "latitude": -12.9558,
        "longitude": -38.4712,
    },
    {
        "code": "BASE-04",
        "name": "Base Pituba",
        "address": "Av. Manoel Dias da Silva, s/n, Pituba, Salvador-BA",
        "neighborhood": "Pituba",
        "latitude": -12.9889,
        "longitude": -38.4532,
    },
    {
        "code": "BASE-05",
        "name": "Base Itapuã",
        "address": "Rua das Alamedas, s/n, Itapuã, Salvador-BA",
        "neighborhood": "Itapuã",
        "latitude": -12.9456,
        "longitude": -38.3711,
    },
    {
        "code": "BASE-06",
        "name": "Base Pau da Lima",
        "address": "Rua Jayme Vieira Lima, s/n, Pau da Lima, Salvador-BA",
        "neighborhood": "Pau da Lima",
        "latitude": -12.9367,
        "longitude": -38.4214,
    },
    {
        "code": "BASE-07",
        "name": "Base Cajazeiras",
        "address": "Estrada do Coqueiro Grande, s/n, Cajazeiras, Salvador-BA",
        "neighborhood": "Cajazeiras",
        "latitude": -12.8912,
        "longitude": -38.4178,
    },
    {
        "code": "BASE-08",
        "name": "Base Subúrbio - Periperi",
        "address": "Rua da Travessia, s/n, Periperi, Salvador-BA",
        "neighborhood": "Periperi",
        "latitude": -12.8745,
        "longitude": -38.4912,
    },
    {
        "code": "BASE-09",
        "name": "Base Barra",
        "address": "Av. Oceânica, s/n, Barra, Salvador-BA",
        "neighborhood": "Barra",
        "latitude": -13.0044,
        "longitude": -38.5312,
    },
    {
        "code": "BASE-10",
        "name": "Base Liberdade",
        "address": "Rua Lima e Silva, s/n, Liberdade, Salvador-BA",
        "neighborhood": "Liberdade",
        "latitude": -12.9480,
        "longitude": -38.4960,
    },
]

# 12 ambulâncias — Brotas (BASE-01) e Pituba (BASE-04) recebem 2
AMBULANCES = [
    {"code": "AMB-01", "ambulance_type": "USB", "base_code": "BASE-01"},
    {"code": "AMB-02", "ambulance_type": "USA", "base_code": "BASE-01"},  # 2ª em Brotas
    {"code": "AMB-03", "ambulance_type": "USB", "base_code": "BASE-02"},
    {"code": "AMB-04", "ambulance_type": "USB", "base_code": "BASE-03"},
    {"code": "AMB-05", "ambulance_type": "USB", "base_code": "BASE-04"},
    {"code": "AMB-06", "ambulance_type": "USA", "base_code": "BASE-04"},  # 2ª em Pituba
    {"code": "AMB-07", "ambulance_type": "USB", "base_code": "BASE-05"},
    {"code": "AMB-08", "ambulance_type": "USB", "base_code": "BASE-06"},
    {"code": "AMB-09", "ambulance_type": "USB", "base_code": "BASE-07"},
    {"code": "AMB-10", "ambulance_type": "USB", "base_code": "BASE-08"},
    {"code": "AMB-11", "ambulance_type": "USB", "base_code": "BASE-09"},
    {"code": "AMB-12", "ambulance_type": "USA", "base_code": "BASE-10"},
]
