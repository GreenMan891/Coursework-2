from datetime import datetime


def formatDateForProvider(dateObj, providerName):
    if providerName == "idk":
        return dateObj.strftime("%y%m%d")
    return dateObj.strftime("%d/%m/%Y")  # national nail


def cleanPrice(priceStr):
    if not priceStr or priceStr.lower() == "n/a":
        return None
    try:
        return float(str(priceStr).replace('£', '').replace('$', '').replace(',', '').strip())
    except ValueError:
        return None
