#!/usr/bin/python3

"""
Best Buy Canada Stock Checker

Checks stock status for specific SKUs on the Best Buy Canada Website.
The script looks availabilities both online and for pick-up in stores
nearby a specified postal code.
It then sends a notification to Slack using an Incoming Webhook.

Adjust the stock_check.yml file according to your needs
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
        preorder_status = True
    else:
        preorder_status = False
    return price, preorder_status

# Lookup availabilities
def availability_lookup(bbyca_api, data_sku, headers):
    r = requests.get(bbyca_api, params=data_sku, headers=headers)
    if '200' in str(r):
        result = json.loads(r.content)
        if result['availabilities'][0]['shipping']['purchasable']:
            purchasable_status = True
        else:
            purchasable_status = False
    else:
        print(r.content)
    return purchasable_status, result

# Build Slack message
def build_slack_message(slack_message, desc, purchasable_status, preorder_status, availability, price):
    if purchasable_status:
        purchasable_icon = ":money_with_wings:"
    else:
        purchasable_icon = ":red_circle:"
    
    if preorder_status:
        preorder_message = "(:date: Preorder!)"
    else:
        preorder_message = ""
    slack_message_text = ">" + purchasable_icon + "  " + desc + " - " + price + " " + preorder_message + "\n>*Shipping*: " + re.sub( r"([A-Z])", r" \1", availability['availabilities'][0]['shipping']['status']) + " \n>*Pick-up*: " + re.sub( r"([A-Z])", r" \1", availability['availabilities'][0]['pickup']['status'])
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
    parser.add_argument('-a', '--alert', help="Alert mode; Send notification only if in stock or preorder", action="store_true")
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

    send_notification = False
    for key, sku in config['best_buy']['skus_list'].items():
        data_sku = {
            'postalCode': postal_code,
            'skus': sku['sku']
        }
        purchasable_status, availability = availability_lookup(bbyca_api, data_sku, headers)
        price, preorder_status = price_lookup(sku['sku'], bbyca_offers_api_root, bbyca_offers_api_suffix, headers)
        slack_message = build_slack_message(slack_message, sku['desc'], purchasable_status, preorder_status, availability, price)
        if purchasable_status or preorder_status:
            send_notification = True

    if args.alert:
        if send_notification:
            post_slack_message(slack_message, webhook_url)
    else:
        post_slack_message(slack_message, webhook_url)

if __name__ == "__main__":
    main()
