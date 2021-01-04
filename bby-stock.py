#!/usr/bin/python3

"""
Best Buy Canada Stock Checker

Checks stock status for specific SKUs on the Best Buy Canada Website.
The script looks availabilities both online and for pick-up in stores
nearby a specified postal code.
It then sends a notification to Slack using an Incoming Webhook.

All variables defined in the main function
"""

import sys
import json
import re
import requests
import argparse
import yaml
from datetime import datetime
from pathlib import Path

# Lookup prices
def price_lookup(sku, bbyca_offers_api_root, bbyca_offers_api_suffix, headers):
    price_request = requests.get(bbyca_offers_api_root + sku + bbyca_offers_api_suffix, headers=headers)
    price_result = json.loads(price_request.content)
    price = "$" + str(price_result[0]['salePrice'])
    if price_result[0]['isPreorderable']:
        preorder_status = "(:date: Preorder!)"
    else:
        preorder_status = ""
    return price, preorder_status

# Lookup availabilities
def availability_lookup(bbyca_api, data_sku, headers):
    r = requests.get(bbyca_api, params=data_sku, headers=headers)
    if '200' in str(r):
        result = json.loads(r.content)
        if result['availabilities'][0]['shipping']['purchasable']:
            purchasable_status = ">:money_with_wings:"
        else:
            purchasable_status = ">:red_circle:"
    else:
        print(r.content)
    return purchasable_status, result

# Build Slack message
def build_slack_message(slack_message, desc, purchasable_status, preorder_status, availability, price):
    slack_message_text = purchasable_status + "  " + desc + " - " + price + " " + preorder_status + "\n>*Shipping*: " + re.sub( r"([A-Z])", r" \1", availability['availabilities'][0]['shipping']['status']) + " \n>*Pick-up*: " + re.sub( r"([A-Z])", r" \1", availability['availabilities'][0]['pickup']['status'])
    print(slack_message_text)
    slack_message['blocks'].append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": slack_message_text
        }
    })
#    slack_message['blocks'].append({
#        "type": "divider"
#    })
    return slack_message

# Send Slack message
def post_slack_message(slack_message, webhook_url):
    slack_post = requests.post(
        webhook_url, data=json.dumps(slack_message),
        headers={'Content-Type': 'application/json'}
    )
    if slack_post.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (slack_post.status_code, slack_post.text)
        )


def main():

    # Config file option
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', 
        type=lambda p: Path(p).absolute(),
        help="Path to config file", 
        default=Path(__file__).absolute().parent / "stock_check.yml"
    )
    args = parser.parse_args()
    #print(args.config)

    # Read config file
    with open(args.config) as f:
        config = yaml.safe_load(f)

    postal_code = config['postal_code']

    # Best Buy Canada APIs URLs
    bbyca_api = "https://www.bestbuy.ca/ecomm-api/availability/products"
    bbyca_offers_api_root = "https://www.bestbuy.ca/api/offers/v1/products/"
    bbyca_offers_api_suffix = "/offers"

    # Slack Incoming Webhook (https://api.slack.com/messaging/webhooks)
    webhook_url = config['slack']['webhook_url']

    # Jedi mind trick because Best Buy does not appreciate "bots" walking through their Website.
    # "These aren't the droids you're looking for."
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }

    # Building blocks for the Slack message. (https://app.slack.com/block-kit-builder/) 
    slack_message = {
        "text": "Best Buy Canada Stock Checker",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Best Buy Stock Checker"
                }
            }
        ]
    }

    for key, sku in config['best_buy']['skus_list'].items():
        data_sku = {
            'postalCode': postal_code,
            'skus': sku['sku']
        }
        purchasable_status, availability = availability_lookup(bbyca_api, data_sku, headers)
        price, preorder_status = price_lookup(sku['sku'], bbyca_offers_api_root, bbyca_offers_api_suffix, headers)
        slack_message = build_slack_message(slack_message, sku['desc'], purchasable_status, preorder_status, availability, price)
    
    post_slack_message(slack_message, webhook_url)

if __name__ == "__main__":
    main()
