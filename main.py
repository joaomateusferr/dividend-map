import sys
import json
import os.path
from pathlib import Path

SUPPORTED_COUNTRIES = ["united_states", "brazil"]
REQUIRED_KEYS = ["ticker"]
SUPPORTED_KEYS = ["ticker", "average_price"]

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

        item = 1

        for asset in content :

            for required_key in REQUIRED_KEYS :
                
                if asset.get(required_key) is None:
                    raise TypeError("Required key not found!\ncountry -> " + country + "\nitem -> " + str(item) + "\nrequired key missing -> " + required_key)


            for key in asset :

                if not key in SUPPORTED_KEYS :
                    raise TypeError("Unsupported key!\ncountry -> " + country + "\nitem -> " + str(item) + "\nkey -> " + key)
            
            item += 1

def getAssetsFromTemplate(template_path) :

    template_file = open(template_path, "r")
    template_string = template_file.read()

    try: 
        assets = json.loads(template_string)
    except Exception as ex:
        raise TypeError("Invalid Json!")

    validateTemplate(assets)
    

    return assets

def main():

    try:

        arguments = parseArguments(sys.argv)
        assets = getAssetsFromTemplate(arguments['template_path'])

    except Exception as ex:
        print("Something went wrong ...\n"+ str(ex))
        sys.exit(0)

    print(str(assets))

main()