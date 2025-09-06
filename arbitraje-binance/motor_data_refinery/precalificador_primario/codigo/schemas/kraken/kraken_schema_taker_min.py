# kraken_schema_taker_min.py

schema = {
    "symbol_id": "str",  # agregado manualmente
    "symbol": "str",
    "base": "str",
    "quote": "str",
    "taker": "float",

    "precision": {
        "amount": "float",
        "price": "float"
    },

    "info": {
        "wsname": "str",
        "altname": "str",
        "status": "str",
        "ordermin": "str",
        "costmin": "str"
    }
}
