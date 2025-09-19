schema = {
    "symbol": "str", "base": "str", "quote": "str",

    "type": "str", "spot": "bool",
    "swap": "bool", "future": "bool", "option": "bool",
    "active": "bool",

    "taker": "float", "maker": "float",

    "precision": {
        "amount": "float",
        "price": "float",
    },

    "info": {
        "status": "str",
        "isSpotTradingAllowed": "bool",
    }
}
