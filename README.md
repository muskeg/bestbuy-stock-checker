# bestbuy-stock-checker
Lookup SKUs at Best Buy **Canada** and get Slack notifications when they're available online or for pick-up nearby.

![Stock Checker Slack Message](https://i.imgur.com/7CfRXls.png)

## Requirements
The script is made for **Python3** and uses:
* PyYAML: https://pyyaml.org/wiki/PyYAMLDocumentation
* requests: https://requests.readthedocs.io/en/master/user/install/

## Config file
The configuration file (default: stock_check.yml) is a yaml file containing all user-specific required information.

```yaml
# Your postal code (no spaces), for nearby stores status
postal_code: "H0H0H0"

slack:
  # Slack Incoming Webhook (https://api.slack.com/messaging/webhooks)
  webhook_url: "https://hooks.slack.com/services/XXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXX"

best_buy:
  # The products SKUs. You can find them shown as "Web Code" on the product's page
  # Add your own description for the product
  # (Slack's markdown supported: https://api.slack.com/reference/surfaces/formatting)
  skus_list:
    item1:
      desc: "*Big-arse TV* :tv:"
      sku: "14471417"
    item2:
      desc: "*Karaoke system* :microphone:"
      sku: "12893288"
    item3:
      desc: "*Hello Kitty eau de toilette* :scream_cat::toilet:"
      sku: "12920503"
```
### Postal Code
The postal code is required to check if the item is available for local order and pickup. Additionally, the API call fails if it's not provided so if you don't need it, leave Santa Claus' postal code as-is.

### Slack
That section only contains the url to your incoming message webhook. You can easily setup an app on your workspace to get that webhook by following Slack's documentation here: https://api.slack.com/messaging/webhooks

### Best Buy
That section contain a list of items with your own description and the items' [SKUs](https://en.wikipedia.org/wiki/Stock_keeping_unit). Since we're using Slack's messaging, the description value supports markdown formatting. Refer to Slacks messages formatting documentation for more information: https://api.slack.com/reference/surfaces/formatting

The list can contain any number of items but keep in mind that every item requires 2 API calls, proportionally increasing execution time.

## Usage
Using the bot is simple. You can run it with or without an optional `--config` flag allowing you to specify the path to your config file. The flag supports both relative and absolute paths.

Example:
```bash
raph@surface:~$ python3 bby-stock.py --help
usage: bby-stock.py [-h] [-c CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to config file
```
## TO-DO
* Currently the robot sends a message at every execution. I'm planning to add a flag to send message only when an item is purchasable. 
* Add a "no Slack" flag to skip sending the message to Slack and instead just print to console

