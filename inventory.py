# finds inventory using product_id, then updates the inventory to 0 ("out of stock")

import requests
from termcolor import colored
from time import sleep

url = "https://YOURSHOPIFYSTORE.myshopify.com/admin/api/2022-10/inventory_levels/set.json"
headers = {
    "X-Shopify-Access-Token": "YOURACCESSTOKEN",
    "Content-Type": "application/json"
}

with open("ids.txt", "r") as f: # product ids
    product_ids = [line.strip() for line in f]

count = 0
total = 0

for product_id in product_ids:
    total += 1
    try:
        product_url = f"https://YOURSHOPIFYSTORE.myshopify.com/admin/api/2022-10/products/{product_id}.json"
        response = requests.get(product_url, headers=headers)
        product_details = response.json()
        inventory_item_id = product_details['product']['variants'][0]['inventory_item_id']

        payload = {"location_id": 11111, "inventory_item_id": inventory_item_id, "available": 0} # update location id 
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 429:
            print(colored("Rate limit exceeded, sleeping for 60 seconds","yellow"))
            sleep(60)
            with open("errors.txt","a") as f:
                f.write(f"{product_id}\n")

        elif response.status_code != 200:
            print(colored(f"Product ID: {product_id} | Inventory Update Error: {response.json()}", "red"))
            with open("errors.txt","a") as f:
                f.write(f"{product_id}\n")
        else:
            print(colored(f"Product ID: {product_id} | Inventory Update Successful", "green"))
            count += 1

    except Exception as e:
        print(colored(f"Product ID: {product_id} | Error: {e}","red"))
        with open("errors.txt","a") as f:
            f.write(f"{product_id}\n")

print(f"Program finished, successfully updated {count} out of {total} products")
