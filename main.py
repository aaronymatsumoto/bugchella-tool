import requests
import json
import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import time

# Load credentials from config.json file
def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
        return config

def get_access_token(base_url, client_id, client_secret):
    url = f"{base_url}/v1/auth/token"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "clientId": client_id,
        "clientSecret": client_secret
    }
    response = requests.post(url, json=payload, headers=headers)
    #print(response.text)
    response.raise_for_status()
    token_data = response.json()
    access_token = token_data.get("access_token")  # or check the actual key name
    #print("Access Token:", access_token)
    return access_token

def make_headers(config, base_url):
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    token = get_access_token(base_url, client_id, client_secret)
    return {
        "Authorization": f"Bearer {token}",
        "tenantId": config["tenant_id"]
    }

def get_customers(base_url, config):
    all_customers = []
    seen_ids = set()
    page = 0
    limit = 100
    while True:
        url = f"{base_url}/v1/customers"
        params = {
            "page": page,
            "limit": limit,
            #"include_inactive": True
        }
        headers = make_headers(config, base_url)
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        customers = data.get("items", [])
        new_customers = []
        for customer in customers:
            customer_id = customer.get("id")
            if customer_id not in seen_ids:
                seen_ids.add(customer_id)
                new_customers.append(customer)
        all_customers.extend(new_customers)

        if len(customers) < limit:
            break  # No more data
        page += 1
    return all_customers

def fetch_customer_if_no_properties(base_url, config, customer):
    headers = make_headers(config, base_url)
    customer_id = customer["id"]
    name = customer["name"]
    url = f"{base_url}/v1/customers/{customer_id}/properties"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data.get("totalCount", 0) == 0:
        return name  # This customer has no properties

def get_customers_no_properties(base_url, config, max_workers=20):
    customers = get_customers(base_url, config)
    customer_names_without_props = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_customer_if_no_properties, base_url, config, customer)
            for customer in customers
        ]
        for future in as_completed(futures):
            name = future.result()
            if name:
                customer_names_without_props.append(name)
    return customer_names_without_props

def fetch_properties(base_url, config, customer):
    max_retries = 1
    customer_id = customer["id"]
    url = f"{base_url}/v1/customers/{customer_id}/properties"
    headers = make_headers(config, base_url)
    params = {
        "include_addresses": True
    }
    for attempt in range(max_retries + 1):
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 401:
            if attempt == max_retries:
                response.raise_for_status()
            print(f"Auth token expired while fetching properties for customer {customer_id}. Refreshing token...")
            headers = make_headers(config, base_url)  # refresh token
            continue
        response.raise_for_status()
        break

    data = response.json()
    properties = data.get("items", [])
    return properties


def get_properties(base_url, config, max_workers=10):
    customers = get_customers(base_url, config)
    properties = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_properties, base_url, config, customer)
            for customer in customers
        ]
        for future in as_completed(futures):
            result = future.result()
            if result:
                properties.extend(result)
    return properties

def get_properties_more_than_two_address(properties):
    results = []
    for p in properties:
        if len(p.get("addresses", [])) > 2:
            results.append(p["companyName"])
    return results

def save_list_to_csv(data_list, filename="output.csv"):
    # get the folder where the script is running
    folder = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(folder, filename)

    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Write each item as a row
        for item in data_list:
            writer.writerow([item])
    print(f"Data saved to {filepath}")

def save_customers_to_csv(data_list, filename="output.csv"):
    # get the folder where the script is running
    folder = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(folder, filename)

    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Name", "ID", "isactive", "status"])
        # Write each item as a row
        for c in data_list:
            writer.writerow([c.get("name", ""), c.get("id", ""), c.get("isActive", ""), c.get("status", "")])
    print(f"Data saved to {filepath}")


def main():
    base_url = "https://public-api.live.buildops.com"
    parser = argparse.ArgumentParser(description="CLI to fetch BuildOps customers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: get_customers
    subparsers.add_parser("get_customers", help="List all customers")

    # Subcommand: get_customers_no_properties
    subparsers.add_parser("get_customers_no_properties", help="List Customers with no properties")

    # Subcommand: get_properties
    subparsers.add_parser("get_properties", help="List properties")

    # Subcommand: get_properties_with_more_than_two_address
    subparsers.add_parser("get_properties_more_than_two_address", help="List properties with more than 2 addresses")

    subparsers.add_parser("test")

    args = parser.parse_args()

    # Load config
    config = load_config()
    tenant = config["tenant_id"]
    headers = make_headers(config, base_url)

    # Run selected command
    if args.command == "get_customers":
        customer_list = get_customers(base_url, config)
        print(f"Number of Customers: {len(customer_list)}")
        # = [c['name'] for c in customer_list]
        save_customers_to_csv(customer_list, filename="customers.csv")
    elif args.command == "get_customers_no_properties":
        customer_list = get_customers_no_properties(base_url, config)
        print(f"Number of Customers No Properties: {len(customer_list)}")
        save_list_to_csv(customer_list, filename="customer_list_no_properties.csv")
    elif args.command == "get_properties":
        properties = get_properties(base_url, config)
        print(f"Number of Properties: {len(properties)}")
        save_list_to_csv(properties, filename="property_list.csv")
    elif args.command == "get_properties_more_than_two_address":
        properties = get_properties(base_url, config)
        property_list = get_properties_more_than_two_address(properties)
        print(f"Number of Properties with more than 2 Addresses: {len(property_list)}")
        save_list_to_csv(property_list, filename="property_list_more_than_two_address.csv")
    elif args.command == "test":
        #testing "LIVPTCHK1" showing UI no property
        #url = f"{base_url}/v1/customers/4fe5664c-3996-43e1-8afd-fa3e1b9a4d20/properties"
        #testing "LIVE_6.67C1" API showing no property, UI has 2
        #url = f"{base_url}/v1/customers/3387b669-8569-4b19-b2ef-26bc7200fb85/properties"
        """
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(data)
        """

if __name__ == "__main__":
    main()
