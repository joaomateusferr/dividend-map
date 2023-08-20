import sys
import json
import requests
import os.path
from pathlib import Path

SUPPORTED_COUNTRIES = ["united_states", "brazil"]
SUPPORTED_KEYS = ["average_price"]

BR_API_BASE_URL = "https://brapi.dev/api"

def parseArguments(system_arguments) :

    if len(system_arguments) == 1 :
        raise TypeError("empty arguments!")

    arguments = {}

    template_path = Path(system_arguments[1])

    if not template_path.exists() :
        raise TypeError("Template file does not exist!")

    if not template_path.is_file() :
        raise TypeError("Template path does not lead to a file!")

    filename = os.path.basename(system_arguments[1])
    extension = filename.split(".")[-1]

    if extension != "json" :
        raise TypeError("Invalid template extension! (not json)")

    arguments['template_path'] = system_arguments[1]

    if len(system_arguments) == 2 :
        template_path_string = os.path.dirname(system_arguments[1])
        arguments['export_path'] = template_path_string
        print("Export path not provided, setting it to same as the template (" + template_path_string + ")")
        return arguments

    export_path = Path(system_arguments[2])

    if not export_path.exists() :
        raise TypeError("Export path does not exist!")

    if not export_path.is_dir() :
        raise TypeError("Export path it's not a directory!")

    arguments['export_path'] = system_arguments[2]

    return arguments

def validateTemplate(assets) :

    for country, content in assets.items() :

        if not country in SUPPORTED_COUNTRIES :
            raise TypeError("Unsupported country! - " + country)

        for ticker, asset_info in content.items() :

            for key in asset_info :

                if not key in SUPPORTED_KEYS :
                    raise TypeError("Unsupported key!\ncountry -> " + country + "\nticker -> " + ticker + "\nkey -> " + key)

def getAssetsFromTemplate(template_path) :

    template_file = open(template_path, "r")
    template_string = template_file.read()

    try:
        assets = json.loads(template_string)
    except Exception as ex:
        raise TypeError("Invalid Json!")

    validateTemplate(assets)

    return assets

def getBrazilianAssetsInformationsFromBrApi(tickers_string) :

    request_url = BR_API_BASE_URL + "/quote/"+ tickers_string +'?range=1y&interval=1m&fundamental=false&dividends=true'

    session = requests.session()
    session.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    response = session.get(request_url)

    if response.status_code != 200 :
        raise TypeError("Br api response code -> " + str(response.status_code))

    result = response.json()

    assets_informations = {}

    for asset_info in result["results"] :

        if not asset_info.get('error') is None:
            print("There was an error getting information from " + asset_info["symbol"] + " ignoring it...")
            continue

        if not asset_info["dividendsData"]["cashDividends"] :
            print("There is no dividend data for " + asset_info["symbol"] + " ignoring it...")
            continue

        year_dividends = 0

        for cash_dividends in asset_info["dividendsData"]["cashDividends"] :
            year_dividends += cash_dividends["rate"]


        assets_informations[asset_info["symbol"]] = {
            "market_price" : asset_info['regularMarketPrice'],
            "dividends_per_share_by_year" : round(year_dividends, 3)
        }

    return assets_informations

def getBrazilianAssetsInformations(brazilian_assets) :

    tickers = list(brazilian_assets.keys())

    delimiter = "%2C"
    tickers_string = delimiter.join(map(str, tickers))

    brazilian_assets_informations = getBrazilianAssetsInformationsFromBrApi(tickers_string)

    for ticker, asset_info in brazilian_assets_informations.items() :
        brazilian_assets_informations[ticker] = brazilian_assets_informations[ticker] | brazilian_assets[ticker]
        brazilian_assets_informations[ticker]["dividends_per_share_by_month"] = round(brazilian_assets_informations[ticker]["dividends_per_share_by_year"]/12, 3)

    return brazilian_assets_informations

def main():

    try:

        arguments = parseArguments(sys.argv)
        assets = getAssetsFromTemplate(arguments['template_path'])

    except Exception as ex:

        print("Something went wrong (1) ...\n"+ str(ex))
        sys.exit(0)

    try:

        brazilian_assets_informations = getBrazilianAssetsInformations(assets["brazil"])

    except Exception as ex:

        print("Something went wrong (2) ...\n"+ str(ex))
        sys.exit(0)

main()