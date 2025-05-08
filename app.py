from flask import Flask, render_template, jsonify
import json
import pandas as pd
import google.generativeai as genai
import os

app = Flask(__name__)

# Load data
def load_data():
    with open('data/products.json', 'r') as f:
        products = json.load(f)
    with open('data/warehouses.json', 'r') as f:
        warehouses = json.load(f)
    with open('data/stores.json', 'r') as f:
        stores = json.load(f)
    return products, warehouses, stores

# Initialize Gemini
def init_gemini():
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    model = genai.GenerativeModel('gemini-pro')
    return model

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/warehouse-stats')
def warehouse_stats():
    products, warehouses, stores = load_data()
    
    # Calculate warehouse statistics
    warehouse_data = []
    for warehouse in warehouses:
        total_stock = sum(item['quantity'] for item in warehouse['stock'])
        unique_products = len(set(item['productId'] for item in warehouse['stock']))
        warehouse_data.append({
            'id': warehouse['id'],
            'country': warehouse['country'],
            'total_stock': total_stock,
            'unique_products': unique_products,
            'latitude': warehouse['latitude'],
            'longitude': warehouse['longitude']
        })
    
    return jsonify(warehouse_data)

@app.route('/api/product-distribution')
def product_distribution():
    products, warehouses, stores = load_data()
    
    # Calculate product distribution across warehouses
    product_data = {}
    for warehouse in warehouses:
        for item in warehouse['stock']:
            if item['productId'] not in product_data:
                product_data[item['productId']] = 0
            product_data[item['productId']] += item['quantity']
    
    # Convert to list format for visualization
    distribution_data = [{'productId': k, 'total_quantity': v} for k, v in product_data.items()]
    return jsonify(distribution_data)

@app.route('/api/optimization-insights')
def optimization_insights():
    products, warehouses, stores = load_data()
    
    # Prepare data for Gemini
    warehouse_summary = "\n".join([
        f"Warehouse {w['id']} in {w['country']} has {sum(item['quantity'] for item in w['stock'])} total items"
        for w in warehouses
    ])
    
    # Get insights from Gemini
    model = init_gemini()
    prompt = f"""Based on the following warehouse data, provide 3 specific recommendations for optimizing delivery:
    {warehouse_summary}
    
    Focus on:
    1. Geographic distribution
    2. Stock levels
    3. Potential bottlenecks
    """
    
    response = model.generate_content(prompt)
    return jsonify({'insights': response.text})

if __name__ == '__main__':
    app.run(debug=True) 