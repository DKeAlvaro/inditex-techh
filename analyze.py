import pandas as pd
import json
import collections
import matplotlib.pyplot as plt
import numpy as np
from prettytable import PrettyTable

# Load data files
with open("data/warehouses.json", "r") as file:
    warehouses = json.load(file)
with open("data/products.json", "r") as file:
    products = json.load(file)
with open("data/stores.json", "r") as file:
    stores = json.load(file)
with open("data/shipments.json", "r") as file:
    shipments = json.load(file)


print("\n----- BASIC STATISTICS -----")
print(f"Number of warehouses: {len(warehouses)}")
print(f"Number of products: {len(products)}")
print(f"Number of stores: {len(stores)}")

# Create product lookup dictionary
product_dict = {p["id"]: p for p in products}
brand_counts = collections.Counter([p["brandId"] for p in products])

print("\n----- PRODUCT STATISTICS -----")
print("Products by brand:")
for brand, count in brand_counts.most_common():
    print(f"  {brand}: {count}")

# Warehouse statistics
print("\n----- WAREHOUSE STATISTICS -----")
warehouse_countries = collections.Counter([w["country"] for w in warehouses])
print("Warehouses by country:")
for country, count in warehouse_countries.most_common(10):
    print(f"  {country}: {count}")

# Product distribution in warehouses
for i in range(len(warehouses)):
    warehouse = warehouses[i]
    product_ids = set()
    total_items = 0
    size_counts = collections.Counter()
    
    for item in warehouse["stock"]:
        product_ids.add(item["productId"])
        total_items += item["quantity"]
        size_counts[item["size"]] += 1
    
    print(f"\nWarehouse '{warehouse['id']}' (Country: {warehouse['country']}):")
    print(f"  Number of unique product IDs: {len(product_ids)}")
    print(f"  Total item quantity: {total_items}")
    print(f"  Most common sizes stocked: {', '.join([s for s, _ in size_counts.most_common(3)])}")

# Calculate total inventory by product 
print("\n----- INVENTORY STATISTICS -----")
inventory_by_product = collections.defaultdict(int)
inventory_by_size = collections.defaultdict(int)

for warehouse in warehouses:
    for item in warehouse["stock"]:
        inventory_by_product[item["productId"]] += item["quantity"]
        inventory_by_size[item["size"]] += item["quantity"]

print("Top 10 products by inventory quantity:")
for prod_id, qty in sorted(inventory_by_product.items(), key=lambda x: x[1], reverse=True)[:10]:
    brand = product_dict.get(prod_id, {}).get("brandId", "unknown")
    print(f"  {prod_id} (Brand: {brand}): {qty}")

print("\n----- ITEMS BY SIZE -----")
size_table = PrettyTable()
size_table.field_names = ["Size", "Quantity", "Percentage"]
total_quantity = sum(inventory_by_size.values())

for size, qty in sorted(inventory_by_size.items(), key=lambda x: x[1], reverse=True):
    percentage = (qty / total_quantity) * 100
    size_table.add_row([size, qty, f"{percentage:.2f}%"])

print(size_table)

# Additional statistics about stores if file is not too large
if len(stores) <= 1000:  # Only analyze if reasonable size
    store_countries = collections.Counter([s.get("country", "Unknown") for s in stores])
    print("\n----- STORE STATISTICS -----")
    print("Top 10 countries by store count:")
    for country, count in store_countries.most_common(10):
        print(f"  {country}: {count}")

