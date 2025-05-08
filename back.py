from typing import List, Dict, Tuple
import pandas as pd
import math
import json


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia en kilómetros entre dos puntos GPS usando la fórmula de Haversine.
    """
    R = 6371.0  # radio de la Tierra en km
    ?1, ?2 = math.radians(lat1), math.radians(lat2)
    ?? = math.radians(lat2 - lat1)
    ?? = math.radians(lon2 - lon1)

    a = math.sin(?? / 2) ** 2 + math.cos(?1) * math.cos(?2) * math.sin(?? / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def load_data(
    warehouses_json: List[dict],
    stores_json: List[dict],
    products_json: List[dict],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carga y normaliza los tres JSON en:
      - df_wh: almacenes
      - df_store: tiendas
      - df_prod: productos
      - df_wh_stock: filas (warehouse_id, productId, size, quantity)
      - df_store_demand: filas (store_id, productId, size, quantity)
    """
    df_wh = pd.DataFrame(warehouses_json)
    df_store = pd.DataFrame(stores_json)
    df_prod = pd.DataFrame(products_json)

    # Normalizar stock de almacenes
    wh_stock_records = []
    for wh in warehouses_json:
        for item in wh.get("stock", []):
            wh_stock_records.append({
                "warehouse_id": wh["id"],
                "productId": item["productId"],
                "size": item["size"],
                "quantity": item["quantity"],
            })
    df_wh_stock = pd.DataFrame(wh_stock_records)

    # Normalizar demanda de tiendas
    store_demand_records = []
    for st in stores_json:
        for item in st.get("demand", []):
            store_demand_records.append({
                "store_id": st["id"],
                "productId": item["productId"],
                "size": item["size"],
                "quantity": item["quantity"],
            })
    df_store_demand = pd.DataFrame(store_demand_records)

    return df_wh, df_store, df_prod, df_wh_stock, df_store_demand


def allocate_stock(
    df_wh: pd.DataFrame,
    df_store: pd.DataFrame,
    df_wh_stock: pd.DataFrame,
    df_store_demand: pd.DataFrame,
) -> Tuple[Dict[str, List[dict]], Dict[str, List[dict]]]:
    """
    Para cada tienda, recorre los almacenes de menor a mayor distancia y asigna stock
    hasta cubrir la demanda o agotar el inventario.

    Devuelve:
      - store_allocations: asignaciones por tienda
      - warehouse_allocations: asignaciones por almacén
    """
    # Calcular distancias
    dist_index = []
    for _, st in df_store.iterrows():
        for _, wh in df_wh.iterrows():
            d = haversine(st.latitude, st.longitude, wh.latitude, wh.longitude)
            dist_index.append({
                "store_id": st.id,
                "warehouse_id": wh.id,
                "distance": d
            })
    df_dist = pd.DataFrame(dist_index)

    store_allocations: Dict[str, List[dict]] = {sid: [] for sid in df_store["id"]}
    warehouse_allocations: Dict[str, List[dict]] = {wid: [] for wid in df_wh["id"]}

    # Estado mutable del stock
    wh_stock = { (row["warehouse_id"], row["productId"], row["size"]): row["quantity"]
                 for _, row in df_wh_stock.iterrows() }

    # Asignar por tienda y producto
    for _, st in df_store.iterrows():
        sid = st["id"]
        demands = df_store_demand[df_store_demand["store_id"] == sid]
        whs_sorted = (
            df_dist[df_dist["store_id"] == sid]
            .sort_values("distance")["warehouse_id"].tolist()
        )
        for _, dem in demands.iterrows():
            need = dem["quantity"]
            pid, size = dem["productId"], dem["size"]
            for wid in whs_sorted:
                if need <= 0:
                    break
                key = (wid, pid, size)
                avail = wh_stock.get(key, 0)
                if avail <= 0:
                    continue
                qty = min(avail, need)
                wh_stock[key] = avail - qty
                need -= qty
                store_allocations[sid].append({
                    "warehouse_id": wid,
                    "productId": pid,
                    "size": size,
                    "quantity": qty
                })
                warehouse_allocations[wid].append({
                    "store_id": sid,
                    "productId": pid,
                    "size": size,
                    "quantity": qty
                })
    return store_allocations, warehouse_allocations


def get_format_data():
    # Carga de datos desde archivos JSON
    with open("warehouses.json", "r", encoding="utf-8") as f:
        warehouses_json = json.load(f)
    with open("stores.json", "r", encoding="utf-8") as f:
        stores_json = json.load(f)
    with open("products.json", "r", encoding="utf-8") as f:
        products_json = json.load(f)

    df_wh, df_store, df_prod, df_wh_stock, df_store_demand = load_data(
        warehouses_json, stores_json, products_json
    )

    store_allocs, wh_allocs = allocate_stock(
        df_wh, df_store, df_wh_stock, df_store_demand
    )

    # Construir la salida en el formato solicitado, limitando los 10 primeros envíos por almacén
    output = {"almacenes": []}
    for wid in df_wh["id"]:
        almac = {"almacen": wid, "envíos": []}
        allocs = wh_allocs.get(wid, [])
        # Agrupar por tienda y producto
        by_store: Dict[str, Dict[str, set]] = {}
        for rec in allocs:
            store = rec["store_id"]
            pid = rec["productId"]
            size = rec["size"]
            by_store.setdefault(store, {}).setdefault(pid, set()).add(size)
        # Construir lista de envíos y limitar a 10 primeros
        envios = []
        for store, prods in by_store.items():
            envio = {"tienda": store, "productos": []}
            for pid, sizes in prods.items():
                envio["productos"].append({
                    "producto": pid,
                    "tallas": sorted(sizes)
                })
            envios.append(envio)
        almac["envíos"] = envios[:10]
        if almac["envíos"]:
            output["almacenes"].append(almac)

    # Imprimir JSON final
    return json.dumps(output, ensure_ascii=False, indent=2)

print(get_format_data())

