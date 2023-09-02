import sys
import json
import requests
import os.path
from pathlib import Path
import yfinance as yf
import pandas as pd
from datetime import datetime
from pprint import pprint#debug only

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

        if not country in ["united_states", "brazil"] : #supported countries
            raise TypeError("Unsupported country! - " + country)

        for required_country_key in ["asset_information", 'currency'] :

            if content.get(required_country_key) is None:
                raise TypeError("Required key not found!\ncountry -> " + country + "\nrequired key missing -> " + required_country_key)


        for ticker, asset_info in content['asset_information'].items() :

            for key in asset_info :

                if not key in ["average_price"] :   #supported asset info keys
                    raise TypeError("Unsupported key!\ncountry -> " + country + "\nticker -> " + ticker + "\nkey -> " + key)

        for required_currency_key in ["name", "symbol"] :

            if content['currency'].get(required_currency_key) is None:
                raise TypeError("Required key not found!\ncountry -> " + country + "\nrequired currency key missing -> " + required_currency_key)

        for currency_key in content['currency'] :

            if not currency_key in ["name", "symbol"] :  #supported currency info keys
                raise TypeError("Unsupported key!\ncountry -> " + country + "\ncurrency\nkey -> " + currency_key)

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
        assets[ticker]['average_annual_dividend'] = 0

        for dividend_date, value in stocks.tickers[ticker].dividends.items() :

            one_year_ago = datetime.now() - pd.DateOffset(years=1)

            if dividend_date.timestamp() > one_year_ago.timestamp() :
                assets[ticker]['payment_dates'].append(dividend_date)

            assets[ticker]['average_annual_dividend'] += value

        if assets[ticker]['average_annual_dividend'] == 0 :
            continue

        assets[ticker]['average_annual_dividend'] = round(assets[ticker]['average_annual_dividend'], 3)
        assets[ticker]['average_monthly_dividend'] = round(assets[ticker]['average_annual_dividend']/12, 3)


    return assets

def calculateExtraInformation(assets) :

    for ticker, asset_info in assets.items() :

        if not asset_info.get('average_price') is None :

            assets[ticker]['return'] = round(assets[ticker]['market_price'] - assets[ticker]['average_price'], 3)
            assets[ticker]['return_percentage'] = round((assets[ticker]['return']/assets[ticker]['average_price'])*100, 3)

            if assets[ticker]['return'] < 0 :
                    assets[ticker]['return_percentage'] = assets[ticker]['return_percentage']*-1

            if assets[ticker]['average_monthly_dividend'] > 0.0001:

                #considers the share gains or losses and dividends

                if assets[ticker]['average_price'] + assets[ticker]['return']*-1 < 0 :
                    assets[ticker]['payback_period_in_months'] = 0
                else :
                    assets[ticker]['payback_period_in_months'] = round((assets[ticker]['average_price'] + assets[ticker]['return']*-1) / assets[ticker]['average_monthly_dividend'], 3)

                if assets[ticker]['payback_period_in_months'] > 0 :
                    assets[ticker]['payback_period_in_years'] = round(assets[ticker]['payback_period_in_months']/12, 3)
                else :
                    assets[ticker]['payback_period_in_years'] = 0

                #considers dividends only

                assets[ticker]['dividend_only_payback_period_in_months'] = round(assets[ticker]['average_price'] / assets[ticker]['average_monthly_dividend'], 3)

                if assets[ticker]['dividend_only_payback_period_in_months'] > 0 :
                    assets[ticker]['dividend_only_payback_period_in_years'] = round(assets[ticker]['dividend_only_payback_period_in_months']/12 ,3)
                else :
                    assets[ticker]['dividend_only_payback_period_in_years'] = 0

        dividend_frequency = len(assets[ticker]['payment_dates'])

        if dividend_frequency == 0 :
            continue

        if dividend_frequency == 52 :
            assets[ticker]['dividend_frequency'] = 'Weekly'
        elif dividend_frequency == 26 :
            assets[ticker]['dividend_frequency'] = 'Biweekly'
        elif dividend_frequency == 12 :
            assets[ticker]['dividend_frequency'] = 'Monthly'
        elif dividend_frequency == 6 :
            assets[ticker]['dividend_frequency'] = 'Bimonthly'
        elif dividend_frequency == 4 :
            assets[ticker]['dividend_frequency'] = 'Quarterly'
        elif dividend_frequency == 3 :
            assets[ticker]['dividend_frequency'] = 'Trimesterly'
        elif dividend_frequency == 2 :
            assets[ticker]['dividend_frequency'] = 'Semiannually'
        elif dividend_frequency == 1 :
            assets[ticker]['dividend_frequency'] = 'Annually'


    pprint(assets)


def main():

    try:

        arguments = parseArguments(sys.argv)
        assets = getAssetsFromTemplate(arguments['template_path'])

    except Exception as ex:

        print("Something went wrong (1) ...\n"+ str(ex))
        sys.exit(0)

    try:

        american_assets = getAssetsAdditionalInformation(assets["united_states"]['asset_information'])
        brazilian_assets = getAssetsAdditionalInformation(assets["brazil"]['asset_information'])

    except Exception as ex:

        print("Something went wrong (2) ...\n"+ str(ex))
        sys.exit(0)

    try:

        american_assets = calculateExtraInformation(assets["united_states"]['asset_information'])
        brazilian_assets = calculateExtraInformation(assets["brazil"]['asset_information'])

    except Exception as ex:

        print("Something went wrong (3) ...\n"+ str(ex))
        sys.exit(0)

main()