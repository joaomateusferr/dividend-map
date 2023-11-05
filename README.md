# Installing dependencies

Run the script [install.sh](dependencies/install.sh) to install all the dependencies necessary to run this project.

# Understanding the template

The template is just a json file with specific formatting.

**country_name** is the name of the country as index of an associative object and within the object we must have the **asset_information**, **currency** and **export_asset_columns** fields, furthermore, it's worth remembering that the tamplete accepts multiple countries, the only difference is that multiple csv files will be generated as a result, one for each country.

```
{

    "united_states": {

        "asset_information": {
            ...
        },

        "currency": {
            ...
        },

        "export_asset_columns": [
            ...
        ]

    },

}
```

**asset_information** is an associative object indexed by the ticker of each asset.

```
...
"asset_information": {

        "IVV": {
            ...
        },

        "NOBL": {
            ...
        },

        "VNQ": {
            ...
        }

}
...
```

**asset_details** is the ticker of a particular asset as index of an associative object and within the object there are fields detailing the assets which are not mandatory but, their lack may prevent the calculation of some indicators.

```
...
"IVV": {
    "dividend_frequency" : "quarterly",
    "average_price": 426.88
},
...
```

Fields accepted:

**average_price**:

*Description*: Average price at which the shares of the asset were purchased.

*Affects export columns*: average_price, return, return_percentage, return_percentage, payback_period_in_months and payback_period_in_years.

**dividend_frequency**:

*Description*: Frequency with which the asset pays dividends, If this field does not exist on the asset_details and the asset pays dividends, the frequency will attempt to be calculated, however this may not be accurate as not all assets pay dividends regularly.

*Affects export columns*: dividend_frequency.

**currency** is an associative object which must contain the fields **name** and **symbol**

```
...
"currency": {
    "name": "dollar",
    "symbol": "$"
},
...
```