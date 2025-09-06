# Esta son los mínimos campos estáticos requeridos para lógica operativa real

KRAKEN_MINIMO = {
    "kraken_sym_symbols": [
        "symbol_id", "symbol",       # Identificación
        "base", "quote", "taker",           # Par base-cotizado, # "taker" Info operativa y fee
    ],
    "kraken_sym_info": [
        "symbol_id", "symbol",       # Identificación
        "wsname", "altname",         # Alias Kraken
        "status", "ordermin", 
        "costmin"                   # Mínimos operativos   # Estado del símbolo
    ],
    "kraken_sym_precision": [
        "symbol_id", "symbol",       # Identificación
        "amount", "price"            # Precisión de cantidad y precio
    ],

}
 