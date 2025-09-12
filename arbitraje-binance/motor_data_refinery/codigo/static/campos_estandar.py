"""
Definición de campos estándar y mapeos por exchange.

Dominus: ajusta los mapeos por exchange según equivalencias reales.
El objetivo es producir una tabla/CSV con nombres de campos estables
que el motor realtime y módulos posteriores puedan consumir
independientemente del exchange.

Convención del mapeo:
- MAPPING[exchange_id][source_key] = target_field
- source_key usa claves aplanadas tipo: 'precision_price', 'limits_amount_min', etc.

Campos objetivo sugeridos (mínimos para spot):
- symbol, base, quote, active
- fee_maker, fee_taker
- price_precision, amount_precision
- min_price, min_amount

Puedes ampliar TARGET_FIELDS si querés estandarizar más columnas.
"""

from __future__ import annotations
from typing import Dict, List

# Campos objetivo a producir en la salida estandarizada
TARGET_FIELDS: List[str] = [
    "symbol",
    "base",
    "quote",
    "active",
    "fee_maker",
    "fee_taker",
    "price_precision",
    "amount_precision",
    "min_price",
    "min_amount",
]

# Mapeos por exchange (INICIAL / editable por Dominus)
# Nota: las claves de la izquierda son las claves crudas APLANADAS provenientes de CCXT
#       (ej.: 'precision_price', 'limits_price_min', 'maker', 'taker').
MAPPING: Dict[str, Dict[str, str]] = {
    # Binance
    "binance": {
        "symbol": "symbol",
        "base": "base",
        "quote": "quote",
        "active": "active",
        "maker": "fee_maker",
        "taker": "fee_taker",
        "precision_price": "price_precision",
        "precision_amount": "amount_precision",
        "limits_price_min": "min_price",
        "limits_amount_min": "min_amount",
    },

    # Kraken (plantilla — revisar claves reales del flatten para Kraken)
    "kraken": {
        "symbol": "symbol",
        "base": "base",
        "quote": "quote",
        "active": "active",
        "maker": "fee_maker",
        "taker": "fee_taker",
        "precision_price": "price_precision",
        "precision_amount": "amount_precision",
        "limits_price_min": "min_price",
        "limits_amount_min": "min_amount",
    },
}

