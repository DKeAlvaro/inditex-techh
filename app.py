from flask import Flask, render_template, jsonify, request
import json
import collections
from gemini_api import get_response, get_data_insights
import markdown

app = Flask(__name__)

# Load data
with open("data/warehouses.json", "r") as file:
    warehouses = json.load(file)
with open("data/products.json", "r") as file:
    products = json.load(file)
try:
    with open("data/stores.json", "r") as file:
        stores = json.load(file)
except:
    # Handle large file gracefully
    stores = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/basic_stats')
def basic_stats():
    return jsonify({
        'warehouse_count': len(warehouses),
        'product_count': len(products),
        'store_count': len(stores)
    })

@app.route('/api/brand_stats')
def brand_stats():
    brand_counts = collections.Counter([p["brandId"] for p in products])
    return jsonify({
        'brands': [{"name": brand, "count": count} for brand, count in brand_counts.most_common()]
    })

@app.route('/api/warehouse_countries')
def warehouse_countries():
    warehouse_countries = collections.Counter([w["country"] for w in warehouses])
    return jsonify({
        'countries': [{"name": country, "count": count} for country, count in warehouse_countries.most_common(10)]
    })

@app.route('/api/inventory_by_size')
def inventory_by_size():
    inventory_by_size = collections.defaultdict(int)
    
    for warehouse in warehouses:
        for item in warehouse["stock"]:
            inventory_by_size[item["size"]] += item["quantity"]
    
    return jsonify({
        'sizes': [{"size": size, "quantity": qty} for size, qty in sorted(inventory_by_size.items(), key=lambda x: x[1], reverse=True)]
    })

@app.route('/api/top_products')
def top_products():
    inventory_by_product = collections.defaultdict(int)
    
    for warehouse in warehouses:
        for item in warehouse["stock"]:
            inventory_by_product[item["productId"]] += item["quantity"]
    
    top_products = []
    for prod_id, qty in sorted(inventory_by_product.items(), key=lambda x: x[1], reverse=True)[:10]:
        top_products.append({"id": prod_id, "quantity": qty})
    
    return jsonify({'products': top_products})

@app.route('/api/ask_gemini', methods=['POST'])
def ask_gemini():
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "No se proporcionó ninguna pregunta"}), 400
    
    question = data['question']
    
    # Prepare data context for Gemini
    data_context = {
        "warehouses_count": len(warehouses),
        "products_count": len(products),
        "stores_count": len(stores),
        "warehouse_countries": list(set(w["country"] for w in warehouses)),
        "product_brands": list(set(p["brandId"] for p in products)),
    }
    
    # Get inventory by size info
    inventory_by_size = collections.defaultdict(int)
    for warehouse in warehouses:
        for item in warehouse["stock"]:
            inventory_by_size[item["size"]] += item["quantity"]
    
    data_context["inventory_by_size"] = [{"size": size, "quantity": qty} 
                                        for size, qty in sorted(inventory_by_size.items(), 
                                                              key=lambda x: x[1], reverse=True)]
    
    # Get top products info
    inventory_by_product = collections.defaultdict(int)
    for warehouse in warehouses:
        for item in warehouse["stock"]:
            inventory_by_product[item["productId"]] += item["quantity"]
    
    data_context["top_products"] = [{"id": prod_id, "quantity": qty} 
                                   for prod_id, qty in sorted(inventory_by_product.items(), 
                                                           key=lambda x: x[1], reverse=True)[:10]]
    
    # Get response from Gemini
    response = get_response(question, data_context)
    # Convert markdown to HTML
    html_response = markdown.markdown(response)
    return jsonify({"answer": html_response})

@app.route('/api/get_insights')
def get_insights():
    insights = get_data_insights(warehouses, products, stores)
    # Convert markdown to HTML
    html_insights = markdown.markdown(insights)
    return jsonify({"insights": html_insights})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 