import sys
import json
import requests
import os.path
from pathlib import Path
import yfinance as yf

SUPPORTED_COUNTRIES = ["united_states", "brazil"]
SUPPORTED_KEYS = ["average_price"]

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

        #add checks on required fields (currencies) here

        for ticker, asset_info in content['asset_information'].items() :

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

def getAssetsAdditionalInformation(assets) :

    tickers = list(assets.keys())

    delimiter = " "
    tickers_string = delimiter.join(map(str, tickers))
    stocks = yf.Tickers(tickers_string)

    for ticker, asset_info in assets.items() :

        assets[ticker]['market_price'] = round(stocks.tickers[ticker].fast_info['lastPrice'], 3)
        assets[ticker]['payment_dates']  = []
        assets[ticker]['average_annual_dividend_per_share'] = 0

        for date, value in stocks.tickers[ticker].dividends.items() :

            assets[ticker]['payment_dates'].append(date)
            assets[ticker]['average_annual_dividend_per_share'] += value

        assets[ticker]['average_annual_dividend_per_share'] = round(assets[ticker]['average_annual_dividend_per_share'], 3)
        assets[ticker]['average_monthly_dividend_per_share'] = round(assets[ticker]['average_annual_dividend_per_share']/12, 3)


    return assets

def main():

    try:

        arguments = parseArguments(sys.argv)
        assets = getAssetsFromTemplate(arguments['template_path'])

    except Exception as ex:

        print("Something went wrong (1) ...\n"+ str(ex))
        sys.exit(0)

    try:

        american_assets = getAssetsAdditionalInformation(assets["united_states"]['asset_information'])
        print(american_assets)
        brazilian_assets = getAssetsAdditionalInformation(assets["brazil"]['asset_information'])
        print(brazilian_assets)

    except Exception as ex:

        print("Something went wrong (2) ...\n"+ str(ex))
        sys.exit(0)

main()