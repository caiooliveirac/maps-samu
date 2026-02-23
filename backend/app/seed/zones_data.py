"""
Zonas de Salvador — bairros e sub-bairros.

Bairros grandes como Cajazeiras, Brotas, Cabula e Liberdade
são divididos em sub-zonas para precisão no cálculo de tempo.

center_lat/center_lng = ponto central de referência da zona.
radius_m = raio aproximado para matching por proximidade.
"""

ZONES = [
    # ── Centro Histórico / Cidade Alta ──
    {"name": "Pelourinho", "parent": "Centro Histórico", "lat": -12.9714, "lng": -38.5124, "radius": 400},
    {"name": "Comércio", "parent": "Centro Histórico", "lat": -12.9682, "lng": -38.5169, "radius": 500},
    {"name": "Barris", "parent": "Centro", "lat": -12.9800, "lng": -38.5100, "radius": 500},
    {"name": "Nazaré", "parent": "Centro", "lat": -12.9756, "lng": -38.5095, "radius": 400},
    {"name": "Saúde", "parent": "Centro", "lat": -12.9730, "lng": -38.5060, "radius": 400},

    # ── Barra / Ondina ──
    {"name": "Barra Centro", "parent": "Barra", "lat": -13.0044, "lng": -38.5312, "radius": 500},
    {"name": "Barra Avenida", "parent": "Barra", "lat": -13.0012, "lng": -38.5280, "radius": 500},
    {"name": "Ondina", "parent": "Ondina", "lat": -13.0060, "lng": -38.5190, "radius": 500},
    {"name": "Graça", "parent": "Graça", "lat": -12.9960, "lng": -38.5190, "radius": 500},
    {"name": "Vitória", "parent": "Vitória", "lat": -12.9930, "lng": -38.5220, "radius": 400},
    {"name": "Canela", "parent": "Canela", "lat": -12.9910, "lng": -38.5170, "radius": 400},

    # ── Brotas (subdividido) ──
    {"name": "Brotas Centro", "parent": "Brotas", "lat": -12.9866, "lng": -38.5033, "radius": 500},
    {"name": "Brotas - Acupe", "parent": "Brotas", "lat": -12.9810, "lng": -38.4970, "radius": 500},
    {"name": "Brotas - Campinas", "parent": "Brotas", "lat": -12.9890, "lng": -38.4980, "radius": 500},
    {"name": "Engenho Velho de Brotas", "parent": "Brotas", "lat": -12.9830, "lng": -38.5010, "radius": 500},
    {"name": "Federação", "parent": "Federação", "lat": -12.9940, "lng": -38.5080, "radius": 600},

    # ── Liberdade (subdividido) ──
    {"name": "Liberdade Centro", "parent": "Liberdade", "lat": -12.9480, "lng": -38.4960, "radius": 500},
    {"name": "IAPI", "parent": "Liberdade", "lat": -12.9510, "lng": -38.4930, "radius": 500},
    {"name": "Curuzu", "parent": "Liberdade", "lat": -12.9500, "lng": -38.4985, "radius": 400},
    {"name": "Lapinha", "parent": "Liberdade", "lat": -12.9550, "lng": -38.5020, "radius": 400},
    {"name": "Sieiro", "parent": "Liberdade", "lat": -12.9460, "lng": -38.4940, "radius": 400},

    # ── Itapagipe / Cidade Baixa ──
    {"name": "Ribeira", "parent": "Itapagipe", "lat": -12.9267, "lng": -38.5059, "radius": 500},
    {"name": "Bonfim", "parent": "Itapagipe", "lat": -12.9280, "lng": -38.5090, "radius": 500},
    {"name": "Calçada", "parent": "Itapagipe", "lat": -12.9400, "lng": -38.5070, "radius": 500},
    {"name": "Mares", "parent": "Itapagipe", "lat": -12.9380, "lng": -38.5100, "radius": 400},
    {"name": "Roma", "parent": "Itapagipe", "lat": -12.9350, "lng": -38.5060, "radius": 400},

    # ── Cabula (subdividido) ──
    {"name": "Cabula Centro", "parent": "Cabula", "lat": -12.9558, "lng": -38.4712, "radius": 600},
    {"name": "Cabula VI", "parent": "Cabula", "lat": -12.9530, "lng": -38.4680, "radius": 500},
    {"name": "Saboeiro", "parent": "Cabula", "lat": -12.9600, "lng": -38.4650, "radius": 500},
    {"name": "Pernambués", "parent": "Cabula", "lat": -12.9650, "lng": -38.4700, "radius": 600},
    {"name": "Narandiba", "parent": "Cabula", "lat": -12.9580, "lng": -38.4760, "radius": 500},
    {"name": "Tancredo Neves", "parent": "Cabula", "lat": -12.9690, "lng": -38.4600, "radius": 600},
    {"name": "Engomadeira", "parent": "Cabula", "lat": -12.9510, "lng": -38.4640, "radius": 400},

    # ── Pituba / Costa Azul / Stiep ──
    {"name": "Pituba Centro", "parent": "Pituba", "lat": -12.9889, "lng": -38.4532, "radius": 500},
    {"name": "Costa Azul", "parent": "Pituba", "lat": -12.9900, "lng": -38.4470, "radius": 500},
    {"name": "Stiep", "parent": "Pituba", "lat": -12.9850, "lng": -38.4480, "radius": 500},
    {"name": "Caminho das Árvores", "parent": "Pituba", "lat": -12.9830, "lng": -38.4540, "radius": 500},
    {"name": "Iguatemi", "parent": "Pituba", "lat": -12.9800, "lng": -38.4580, "radius": 500},
    {"name": "Imbuí", "parent": "Imbuí", "lat": -12.9720, "lng": -38.4410, "radius": 500},
    {"name": "Boca do Rio", "parent": "Boca do Rio", "lat": -12.9730, "lng": -38.4300, "radius": 600},

    # ── Itapuã / Praia do Flamengo ──
    {"name": "Itapuã Centro", "parent": "Itapuã", "lat": -12.9456, "lng": -38.3711, "radius": 600},
    {"name": "Praia do Flamengo", "parent": "Itapuã", "lat": -12.9500, "lng": -38.3600, "radius": 600},
    {"name": "Stella Maris", "parent": "Itapuã", "lat": -12.9380, "lng": -38.3550, "radius": 600},
    {"name": "Patamares", "parent": "Patamares", "lat": -12.9580, "lng": -38.3900, "radius": 600},
    {"name": "Piatã", "parent": "Piatã", "lat": -12.9520, "lng": -38.4000, "radius": 500},
    {"name": "Jardim dos Namorados", "parent": "Pituba", "lat": -12.9650, "lng": -38.4200, "radius": 500},

    # ── Pau da Lima / São Marcos ──
    {"name": "Pau da Lima Centro", "parent": "Pau da Lima", "lat": -12.9367, "lng": -38.4214, "radius": 600},
    {"name": "São Marcos", "parent": "São Marcos", "lat": -12.9300, "lng": -38.4100, "radius": 500},
    {"name": "Castelo Branco", "parent": "Pau da Lima", "lat": -12.9250, "lng": -38.4300, "radius": 500},
    {"name": "Sete de Abril", "parent": "Pau da Lima", "lat": -12.9400, "lng": -38.4150, "radius": 500},
    {"name": "Nova Brasília", "parent": "Pau da Lima", "lat": -12.9350, "lng": -38.4250, "radius": 500},
    {"name": "Sussuarana", "parent": "Sussuarana", "lat": -12.9300, "lng": -38.4450, "radius": 600},

    # ── Cajazeiras (subdividido — bairro grande) ──
    {"name": "Cajazeiras I-III", "parent": "Cajazeiras", "lat": -12.8912, "lng": -38.4178, "radius": 500},
    {"name": "Cajazeiras IV-V", "parent": "Cajazeiras", "lat": -12.8870, "lng": -38.4200, "radius": 500},
    {"name": "Cajazeiras VI-VIII", "parent": "Cajazeiras", "lat": -12.8830, "lng": -38.4150, "radius": 500},
    {"name": "Cajazeiras IX-XI", "parent": "Cajazeiras", "lat": -12.8800, "lng": -38.4120, "radius": 500},
    {"name": "Fazenda Grande", "parent": "Cajazeiras", "lat": -12.8950, "lng": -38.4100, "radius": 600},
    {"name": "Boca da Mata", "parent": "Cajazeiras", "lat": -12.8880, "lng": -38.4250, "radius": 500},

    # ── Subúrbio Ferroviário ──
    {"name": "Periperi", "parent": "Subúrbio", "lat": -12.8745, "lng": -38.4912, "radius": 600},
    {"name": "Paripe", "parent": "Subúrbio", "lat": -12.8650, "lng": -38.4950, "radius": 600},
    {"name": "Plataforma", "parent": "Subúrbio", "lat": -12.8900, "lng": -38.4980, "radius": 500},
    {"name": "São Tomé de Paripe", "parent": "Subúrbio", "lat": -12.8580, "lng": -38.5000, "radius": 500},
    {"name": "Coutos", "parent": "Subúrbio", "lat": -12.8700, "lng": -38.4870, "radius": 500},
    {"name": "Fazenda Coutos", "parent": "Subúrbio", "lat": -12.8680, "lng": -38.4800, "radius": 500},

    # ── São Caetano / Valéria ──
    {"name": "São Caetano", "parent": "São Caetano", "lat": -12.9200, "lng": -38.4780, "radius": 600},
    {"name": "Valéria", "parent": "Valéria", "lat": -12.9050, "lng": -38.4500, "radius": 700},
    {"name": "Pirajá", "parent": "Pirajá", "lat": -12.9100, "lng": -38.4650, "radius": 600},

    # ── Paralela / Mussurunga ──
    {"name": "Paralela - CAB", "parent": "Paralela", "lat": -12.9700, "lng": -38.4500, "radius": 600},
    {"name": "Mussurunga", "parent": "Mussurunga", "lat": -12.9200, "lng": -38.3900, "radius": 600},
    {"name": "São Cristóvão", "parent": "São Cristóvão", "lat": -12.9150, "lng": -38.4050, "radius": 500},

    # ── Rio Vermelho / Amaralina ──
    {"name": "Rio Vermelho", "parent": "Rio Vermelho", "lat": -13.0100, "lng": -38.5020, "radius": 500},
    {"name": "Amaralina", "parent": "Amaralina", "lat": -13.0050, "lng": -38.4900, "radius": 500},
    {"name": "Nordeste de Amaralina", "parent": "Amaralina", "lat": -12.9980, "lng": -38.4840, "radius": 500},
    {"name": "Santa Cruz", "parent": "Rio Vermelho", "lat": -13.0080, "lng": -38.4960, "radius": 400},
]
