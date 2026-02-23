"""
Resolve a faixa horária atual baseada no horário de Brasília.
"""

from datetime import datetime, timezone, timedelta

# UTC-3 (Horário de Brasília)
BRT = timezone(timedelta(hours=-3))


def get_current_time_period() -> str:
    """
    Retorna a faixa horária atual para lookup na matriz.

    Faixas:
      MORNING_RUSH  → Seg-Sex  06:00-09:00
      EVENING_RUSH  → Seg-Sex  17:00-20:00
      NIGHT         → Todos    21:00-05:59
      WEEKEND       → Sáb-Dom  06:00-20:59
      NORMAL        → Seg-Sex  09:00-17:00 e 20:00-21:00
    """
    now = datetime.now(BRT)
    hour = now.hour
    weekday = now.weekday()  # 0=Mon, 6=Sun

    # Noite (21h-06h) — vale para todos os dias
    if hour >= 21 or hour < 6:
        return "NIGHT"

    # Fim de semana (06h-21h)
    if weekday >= 5:  # Sábado ou Domingo
        return "WEEKEND"

    # Dias úteis
    if 6 <= hour < 9:
        return "MORNING_RUSH"
    if 17 <= hour < 20:
        return "EVENING_RUSH"

    return "NORMAL"
