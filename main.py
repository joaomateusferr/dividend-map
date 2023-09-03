import sys
import json
import requests
import math
import csv
import os.path
from pathlib import Path
import yfinance as yf
import pandas as pd
from datetime import datetime
from pprint import pprint   #debug only

REQUIRED_COUNTRY_KEY = ['asset_information', 'export_asset_columns', 'currency']
REQUIRED_CURRENCY_KEYS = ['name', 'symbol']
REQUIRED_EXPORT_ASSET_COLUMNS = ['ticker']

SUPPORTED_COUNTRIES = ['united_states', 'brazil']
SUPPORTED_ASSET_INFO_KEYS = ['average_price', 'dividend_frequency']
SUPPORTED_CURRENCY_KEYS = ['name', 'symbol']
SUPPORTED_EXPORT_ASSET_COLUMNS = ['ticker', 'market_price', 'average_price', 'return', 'return_percentage', 'dividend_frequency', 'average_annual_dividend', 'average_monthly_dividend', 'magic_number', 'payback_period_in_months', 'dividend_only_payback_period_in_months', 'payback_period_in_years', 'dividend_only_payback_period_in_years']

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

        if not country in SUPPORTED_COUNTRIES:
            raise TypeError("Unsupported country! - " + country)

        for required_country_key in REQUIRED_COUNTRY_KEY :

            if content.get(required_country_key) is None:
                raise TypeError("Required key not found!\ncountry -> " + country + "\nrequired key missing -> " + required_country_key)


        for ticker, asset_info in content['asset_information'].items() :

            for key in asset_info :

                if not key in SUPPORTED_ASSET_INFO_KEYS :
                    raise TypeError("Unsupported key!\ncountry -> " + country + "\nticker -> " + ticker + "\nkey -> " + key)

        for required_currency_key in REQUIRED_CURRENCY_KEYS:

            if content['currency'].get(required_currency_key) is None:
                raise TypeError("Required key not found!\ncountry -> " + country + "\nrequired currency key missing -> " + required_currency_key)

        for currency_key in content['currency'] :

            if not currency_key in SUPPORTED_CURRENCY_KEYS:
                raise TypeError("Unsupported key!\ncountry -> " + country + "\ncurrency\nkey -> " + currency_key)

        missing_required_export_asset_column = None

        for required_export_asset_column in REQUIRED_EXPORT_ASSET_COLUMNS:

            if required_export_asset_column not in content['export_asset_columns']:
                missing_required_export_asset_column = required_export_asset_column
                break

        if not missing_required_export_asset_column is None :
            raise TypeError("Required key not found!\ncountry -> " + country + "\nrequired export asset column missing -> " + missing_required_export_asset_column)

        for export_asset_column in content['export_asset_columns'] :

            if not export_asset_column in SUPPORTED_EXPORT_ASSET_COLUMNS:
                raise TypeError("Unsupported key!\ncountry -> " + country + "\nexport asset column\nkey -> " + export_asset_column)

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

            if not asset_info.get('average_monthly_dividend') is None and assets[ticker]['average_monthly_dividend'] > 0.0001:

                #magic number

                assets[ticker]['magic_number'] = math.ceil(assets[ticker]['market_price']/assets[ticker]['average_monthly_dividend'])

                #payback period considers the share gains or losses and dividends

                if assets[ticker]['average_price'] + assets[ticker]['return']*-1 < 0 :
                    assets[ticker]['payback_period_in_months'] = 0
                else :
                    assets[ticker]['payback_period_in_months'] = round((assets[ticker]['average_price'] + assets[ticker]['return']*-1) / assets[ticker]['average_monthly_dividend'], 3)

                if assets[ticker]['payback_period_in_months'] > 0 :
                    assets[ticker]['payback_period_in_years'] = round(assets[ticker]['payback_period_in_months']/12, 3)
                else :
                    assets[ticker]['payback_period_in_years'] = 0

                #dividend only payback period considers dividends only

                assets[ticker]['dividend_only_payback_period_in_months'] = round(assets[ticker]['average_price'] / assets[ticker]['average_monthly_dividend'], 3)

                if assets[ticker]['dividend_only_payback_period_in_months'] > 0 :
                    assets[ticker]['dividend_only_payback_period_in_years'] = round(assets[ticker]['dividend_only_payback_period_in_months']/12 ,3)
                else :
                    assets[ticker]['dividend_only_payback_period_in_years'] = 0

        dividend_frequency = len(assets[ticker]['payment_dates'])

        if dividend_frequency == 0 :
            continue

        #not all assets have regular dividend payments if the dividend_frequency exists in asset form the template use it otherwise, try to calculate it manually
        if not asset_info.get('dividend_frequency') is None :
            continue

        if dividend_frequency == 52 :
            assets[ticker]['dividend_frequency'] = 'weekly'
        elif dividend_frequency == 26 :
            assets[ticker]['dividend_frequency'] = 'biweekly'
        elif dividend_frequency == 12 :
            assets[ticker]['dividend_frequency'] = 'monthly'
        elif dividend_frequency == 6 :
            assets[ticker]['dividend_frequency'] = 'bimonthly'
        elif dividend_frequency == 4 :
            assets[ticker]['dividend_frequency'] = 'quarterly'
        elif dividend_frequency == 3 :
            assets[ticker]['dividend_frequency'] = 'trimesterly'
        elif dividend_frequency == 2 :
            assets[ticker]['dividend_frequency'] = 'semiannually'
        elif dividend_frequency == 1 :
            assets[ticker]['dividend_frequency'] = 'annually'


    return assets

def formatCSVData(export_asset_columns, assets) :

    csv_data = []
    csv_data.append(export_asset_columns)

    for ticker, asset_info in assets.items() :

        row = []

        for export_asset_column in export_asset_columns:

            if export_asset_column == 'ticker' :
                row.append(ticker)
                continue

            if not asset_info.get(export_asset_column) is None:
                row.append(asset_info.get(export_asset_column))
            else :
                row.append('-')

        csv_data.append(row)

    return csv_data

def createCSV(export_path, csv_data) :

    for country, data in csv_data.items() :

        with open(export_path + '/' +country+'.csv', mode='w', newline='') as file:

            writer = csv.writer(file)

            for row in data:
                writer.writerow(row)

def main():

    try:

        arguments = parseArguments(sys.argv)
        assets = getAssetsFromTemplate(arguments['template_path'])

    except Exception as ex:

        print("Something went wrong when trying to get template information ...\n"+ str(ex))
        sys.exit(0)

    try:

        for country, content in assets.items() :
            assets[country]['asset_information'] = getAssetsAdditionalInformation(content['asset_information'])

    except Exception as ex:

        print("Something went wrong when trying to get asset information from the yahoo finance api ...\n"+ str(ex))
        sys.exit(0)

    try:

        for country, content in assets.items() :
            assets[country]['asset_information']  = calculateExtraInformation(content['asset_information'])

    except Exception as ex:

        print("Something went wrong when trying to calculate extra information about assets ...\n"+ str(ex))
        sys.exit(0)

    csv_data = {}

    try:

        for country, content in assets.items() :
            csv_data[country] = {}
            csv_data[country] = formatCSVData(content['export_asset_columns'], content['asset_information'])

    except Exception as ex:

        print("Something went wrong when formatting the csv ...\n"+ str(ex))
        sys.exit(0)

    try:

        createCSV(arguments['export_path'], csv_data)

    except Exception as ex:

        print("Something went wrong when creating the csv ...\n"+ str(ex))
        sys.exit(0)


main()