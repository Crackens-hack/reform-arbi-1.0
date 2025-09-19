# Auto-generado: estructura completa deducida desde CCXT.
# Exchange origen: binance
# Origen del generador: app/codigo/1_generar_schemas.py

schema = {
    "id": "str",
    "lowercaseId": "str",
    "symbol": "str",
    "base": "str",
    "quote": "str",
    "settle": "None",
    "baseId": "str",
    "quoteId": "str",
    "settleId": "None",
    "type": "str",
    "spot": "bool",
    "margin": "bool",
    "swap": "bool",
    "future": "bool",
    "option": "bool",
    "index": "None",
    "active": "bool",
    "contract": "bool",
    "linear": "None",
    "inverse": "None",
    "subType": "None",
    "taker": "float",
    "maker": "float",
    "contractSize": "None",
    "expiry": "None",
    "expiryDatetime": "None",
    "strike": "None",
    "optionType": "None",
    "precision": {
        "amount": "float",
        "price": "float",
        "cost": "None",
        "base": "float",
        "quote": "float"
    },
    "limits": {
        "leverage": {
            "min": "None",
            "max": "None"
        },
        "amount": {
            "min": "float",
            "max": "float"
        },
        "price": {
            "min": "float",
            "max": "float"
        },
        "cost": {
            "min": "float",
            "max": "float"
        },
        "market": {
            "min": "float",
            "max": "float"
        }
    },
    "marginModes": {
        "cross": "bool",
        "isolated": "bool"
    },
    "created": "None",
    "info": {
        "symbol": "str",
        "status": "str",
        "baseAsset": "str",
        "baseAssetPrecision": "str",
        "quoteAsset": "str",
        "quotePrecision": "str",
        "quoteAssetPrecision": "str",
        "baseCommissionPrecision": "str",
        "quoteCommissionPrecision": "str",
        "orderTypes": "[str]",
        "icebergAllowed": "bool",
        "ocoAllowed": "bool",
        "otoAllowed": "bool",
        "quoteOrderQtyMarketAllowed": "bool",
        "allowTrailingStop": "bool",
        "cancelReplaceAllowed": "bool",
        "amendAllowed": "bool",
        "pegInstructionsAllowed": "bool",
        "isSpotTradingAllowed": "bool",
        "isMarginTradingAllowed": "bool",
        "filters": "[any]",
        "permissions": "[[any, any]]",
        "permissionSets": "[any]",
        "defaultSelfTradePreventionMode": "str",
        "allowedSelfTradePreventionModes": "[str]",
        "pair": "str",
        "contractType": "str",
        "deliveryDate": "str",
        "onboardDate": "str",
        "maintMarginPercent": "str",
        "requiredMarginPercent": "str",
        "marginAsset": "str",
        "pricePrecision": "str",
        "quantityPrecision": "str",
        "underlyingType": "str",
        "underlyingSubType": "[str]",
        "triggerProtect": "str",
        "liquidationFee": "str",
        "marketTakeBound": "str",
        "maxMoveOrderLimit": "str",
        "timeInForce": "[str]",
        "contractStatus": "str",
        "contractSize": "str",
        "equalQtyPrecision": "str"
    },
    "tierBased": "bool",
    "percentage": "bool",
    "feeSide": "str"
}