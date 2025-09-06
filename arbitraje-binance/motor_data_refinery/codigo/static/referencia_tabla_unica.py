# app/codigo/static/referencia_tabla_unica.py
schema_unificado = {
    "sym_symbols": [
        "symbol_id", "symbol", "base", "quote", "type", "spot", "swap", "future", "option", "active", "taker", "maker"
    ],
    "sym_info": [
        "symbol_id", "symbol", "info_status", "info_isSpotTradingAllowed"
    ],
    "sym_precision": [
        "symbol_id", "symbol", "precision_amount", "precision_price"
    ],
}
