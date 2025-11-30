"""
NeoBot Tools - NeoOne API Entegrasyonu
Gerçek NeoOne sistemine bağlı tool fonksiyonları.
"""

import json
from .api_client import neoone_client

# Cache for customer groups (to avoid repeated API calls)
_customer_groups_cache = None

# --- Helper Functions ---

def _get_customer_groups_cached():
    """Müşteri gruplarını cache'den veya API'den al."""
    global _customer_groups_cache
    if _customer_groups_cache is None:
        _customer_groups_cache = neoone_client.get_customer_groups()
    return _customer_groups_cache

def _get_group_name(group_id: int) -> str:
    """Grup ID'sinden grup adını bul."""
    groups = _get_customer_groups_cached()
    for g in groups:
        if g.get("id") == group_id:
            return g.get("customerGroupName", f"Grup {group_id}")
    return f"Grup {group_id}"

# --- Tool Functions ---

def get_customer_groups():
    """
    Mevcut müşteri gruplarını listeler.
    """
    print("DEBUG: get_customer_groups çağrıldı (API).")
    try:
        groups = neoone_client.get_customer_groups()
        # Format for AI
        formatted = [{"id": g["id"], "name": g.get("customerGroupName", "")} for g in groups]
        return json.dumps(formatted, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: get_customer_groups failed: {e}")
        return json.dumps({"error": str(e)})

def get_product_groups():
    """
    Ürün gruplarını (kategorileri) listeler.
    """
    print("DEBUG: get_product_groups çağrıldı (API).")
    try:
        groups = neoone_client.get_product_groups()
        # Format for AI
        formatted = [{"id": g.get("id"), "name": g.get("name", g.get("productGroupName", ""))} for g in groups]
        return json.dumps(formatted, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: get_product_groups failed: {e}")
        return json.dumps({"error": str(e)})

def get_product_sales(start_date: str = None, end_date: str = None):
    """
    Ürün satış raporunu getirir.
    """
    print(f"DEBUG: get_product_sales çağrıldı. Başlangıç: {start_date}, Bitiş: {end_date}")
    try:
        sales = neoone_client.get_product_sales(start_date, end_date)
        return json.dumps(sales, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: get_product_sales failed: {e}")
        return json.dumps({"error": str(e)})

def search_product(query: str):
    """
    Ürün ismine göre arama yapar ve eşleşen ürünleri getirir.
    """
    print(f"DEBUG: search_product çağrıldı. Sorgu: {query}")
    try:
        all_products = neoone_client.get_product_sales()
        # Filter by name (case-insensitive)
        results = [
            {
                "id": p["productId"],
                "name": p["productName"],
                "code": p["productCode"],
                "category": p.get("productGroupName", ""),
                "total_sales": p.get("quantitySold", 0),
                "total_revenue": p.get("totalSales", 0)
            }
            for p in all_products 
            if query.lower() in p.get("productName", "").lower()
        ]
        # Remove duplicates by productId
        seen = set()
        unique_results = []
        for r in results:
            if r["id"] not in seen:
                seen.add(r["id"])
                unique_results.append(r)
        return json.dumps(unique_results, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: search_product failed: {e}")
        return json.dumps({"error": str(e)})

def get_top_bottom_products(limit: int = 3, order: str = "asc", customer_group_id: int = None):
    """
    Satış performansına göre sıralı ürünleri getirir.
    order='asc' -> En az satanlar (küçükten büyüğe)
    order='desc' -> En çok satanlar (büyükten küçüğe)
    """
    print(f"DEBUG: get_top_bottom_products çağrıldı. Limit: {limit}, Sıra: {order}, Grup: {customer_group_id}")
    try:
        all_products = neoone_client.get_product_sales()
        
        # Aggregate by product (sum quantities for same product)
        product_totals = {}
        for p in all_products:
            pid = p["productId"]
            # Skip bonus/bedelsiz products
            if "[BONUS]" in p.get("productName", "") or "[BEDELSİZ]" in p.get("productName", ""):
                continue
            
            if pid not in product_totals:
                product_totals[pid] = {
                    "id": pid,
                    "name": p["productName"],
                    "code": p["productCode"],
                    "category": p.get("productGroupName", ""),
                    "quantity_sold": 0,
                    "total_revenue": 0
                }
            product_totals[pid]["quantity_sold"] += p.get("quantitySold", 0)
            product_totals[pid]["total_revenue"] += p.get("totalSales", 0)
        
        products_list = list(product_totals.values())
        
        # Sort
        reverse = (order == "desc")
        sorted_products = sorted(products_list, key=lambda x: x["quantity_sold"], reverse=reverse)
        
        # Limit
        result = sorted_products[:limit]
        
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: get_top_bottom_products failed: {e}")
        return json.dumps({"error": str(e)})

def get_low_selling_products(threshold: int = 100, customer_group_id: int = None):
    """
    Satış adedi belirli bir eşiğin altında olan ürünleri getirir.
    """
    print(f"DEBUG: get_low_selling_products çağrıldı. Eşik: {threshold}, Grup: {customer_group_id}")
    try:
        all_products = neoone_client.get_product_sales()
        
        # Aggregate by product
        product_totals = {}
        for p in all_products:
            pid = p["productId"]
            # Skip bonus/bedelsiz products
            if "[BONUS]" in p.get("productName", "") or "[BEDELSİZ]" in p.get("productName", ""):
                continue
            
            if pid not in product_totals:
                product_totals[pid] = {
                    "id": pid,
                    "name": p["productName"],
                    "code": p["productCode"],
                    "category": p.get("productGroupName", ""),
                    "quantity_sold": 0
                }
            product_totals[pid]["quantity_sold"] += p.get("quantitySold", 0)
        
        # Filter below threshold
        low_selling = [p for p in product_totals.values() if p["quantity_sold"] < threshold]
        
        # Sort by quantity (lowest first)
        low_selling.sort(key=lambda x: x["quantity_sold"])
        
        return json.dumps(low_selling, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: get_low_selling_products failed: {e}")
        return json.dumps({"error": str(e)})

def get_product_sales_distribution(product_id: int = None, limit: int = 5, order: str = "asc"):
    """
    Ürün satış dağılımını grafik için getirir.
    - product_id verilmezse: En az/çok satan ürünlerin karşılaştırması
    - product_id verilirse: O ürünün birim bazlı dağılımı
    - order='asc': En az satanlar, order='desc': En çok satanlar
    """
    print(f"DEBUG: get_product_sales_distribution çağrıldı. Ürün: {product_id}, Limit: {limit}, Order: {order}")
    try:
        all_products = neoone_client.get_product_sales()
        
        # Eğer product_id verilmişse, o ürünün detayını göster
        if product_id is not None:
            product_sales = [p for p in all_products if p["productId"] == product_id]
            
            if not product_sales:
                return json.dumps({"error": "Ürün bulunamadı."})
            
            # Aggregate by unit of measure
            unit_totals = {}
            for p in product_sales:
                if "[BONUS]" in p.get("productName", "") or "[BEDELSİZ]" in p.get("productName", ""):
                    continue
                unit = p.get("unitOfMeasureName", "Birim")
                qty = p.get("quantitySold", 0)
                unit_totals[unit] = unit_totals.get(unit, 0) + qty
            
            distribution = [{"name": unit, "value": int(qty)} for unit, qty in unit_totals.items() if qty > 0]
            distribution.sort(key=lambda x: x["value"], reverse=True)
            
            if not distribution:
                return json.dumps({"error": "Bu ürün için satış verisi bulunamadı."})
            
            return json.dumps(distribution, ensure_ascii=False)
        
        # product_id yoksa: En az/çok satan ürünlerin karşılaştırması
        product_totals = {}
        for p in all_products:
            pid = p["productId"]
            if "[BONUS]" in p.get("productName", "") or "[BEDELSİZ]" in p.get("productName", ""):
                continue
            
            if pid not in product_totals:
                product_totals[pid] = {
                    "name": p["productName"],
                    "value": 0
                }
            product_totals[pid]["value"] += int(p.get("quantitySold", 0))
        
        products_list = list(product_totals.values())
        
        # Sıralama
        reverse = (order == "desc")
        products_list.sort(key=lambda x: x["value"], reverse=reverse)
        
        # Limit kadar al
        distribution = products_list[:limit]
        
        return json.dumps(distribution, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: get_product_sales_distribution failed: {e}")
        return json.dumps({"error": str(e)})

def create_discount(product_id: int, customer_group_id: int, discount_rate: int, duration_days: int, confirmed: bool = False):
    """
    Belirli bir ürün ve müşteri grubu için iskonto tanımlar.
    İskonto PASİF olarak oluşturulur, yönetici onayı ile aktif edilir.
    """
    print(f"DEBUG: create_discount çağrıldı. Ürün: {product_id}, Grup: {customer_group_id}, Oran: %{discount_rate}, Süre: {duration_days} gün, Onay: {confirmed}")
    
    if not confirmed:
        return json.dumps({"error": "İşlem kullanıcı tarafından onaylanmadı. Lütfen kullanıcıdan açıkça onay isteyin."})
    
    try:
        from datetime import datetime, timedelta
        
        # Calculate dates in ISO format
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)
        
        # API client'ı yeni formatla çağır
        result = neoone_client.create_discount(
            product_id=product_id,
            customer_group_id=customer_group_id,
            discount_percent=discount_rate,
            start_date=start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            end_date=end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        )
        
        # Add helpful message
        if result.get("success"):
            return json.dumps({
                "success": True,
                "message": f"İskonto başarıyla oluşturuldu (PASİF durumda). Yönetici onayı ile aktif edilecektir.",
                "data": result.get("data")
            }, ensure_ascii=False)
        else:
            return json.dumps(result, ensure_ascii=False)
            
    except Exception as e:
        print(f"ERROR: create_discount failed: {e}")
        return json.dumps({"error": str(e)})

def check_discount_performance(discount_id: int):
    """
    İskonto performansını kontrol eder.
    """
    print(f"DEBUG: check_discount_performance çağrıldı. ID: {discount_id}")
    try:
        discounts = neoone_client.get_discounts()
        discount = next((d for d in discounts if d.get("id") == discount_id), None)
        
        if not discount:
            return json.dumps({"error": "İskonto bulunamadı."})
        
        return json.dumps(discount, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: check_discount_performance failed: {e}")
        return json.dumps({"error": str(e)})

def get_active_discounts():
    """
    Aktif iskontoları listeler.
    """
    print("DEBUG: get_active_discounts çağrıldı.")
    try:
        discounts = neoone_client.get_active_discounts()
        return json.dumps(discounts, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: get_active_discounts failed: {e}")
        return json.dumps({"error": str(e)})

def get_customer_sales_performance(customer_group_name: str = None, city: str = None, 
                                    order_by: str = "revenue_desc", limit: int = 10):
    """
    Müşteri satış performansını getirir. Bölge ve ciro bazlı filtreleme yapılabilir.
    """
    print(f"DEBUG: get_customer_sales_performance çağrıldı. Grup: {customer_group_name}, Şehir: {city}, Sıralama: {order_by}, Limit: {limit}")
    try:
        customers = neoone_client.get_customer_sales_performance()
        
        # Filtrele
        if customer_group_name:
            customers = [c for c in customers if customer_group_name.lower() in c.get("customerGroupName", "").lower()]
        
        if city:
            customers = [c for c in customers if city.lower() in c.get("city", "").lower()]
        
        # Sırala
        reverse = (order_by == "revenue_desc")
        customers.sort(key=lambda x: x.get("totalRevenue", 0), reverse=reverse)
        
        # Limit uygula
        customers = customers[:limit]
        
        # Basitleştirilmiş çıktı
        result = [
            {
                "customer_id": c.get("customerId"),
                "customer_name": c.get("customerName"),
                "city": c.get("city"),
                "district": c.get("district"),
                "customer_group": c.get("customerGroupName"),
                "total_revenue": c.get("totalRevenue"),
                "order_count": c.get("orderCount")
            }
            for c in customers
        ]
        
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: get_customer_sales_performance failed: {e}")
        return json.dumps({"error": str(e)})

def create_bonus_discount(product_id: int, customer_group_id: int = None, customer_id: int = None,
                          buy_quantity: int = 2, bonus_quantity: int = 1, 
                          duration_days: int = 30, confirmed: bool = False):
    """
    X al Y bedava tipi kampanya oluşturur.
    customer_group_id: Müşteri grubu ID'si (tüm gruba uygulanır)
    customer_id: Belirli bir müşteri ID'si (tek müşteriye uygulanır)
    """
    print(f"DEBUG: create_bonus_discount çağrıldı. Ürün: {product_id}, Grup: {customer_group_id}, Müşteri: {customer_id}, Al: {buy_quantity}, Bedava: {bonus_quantity}, Süre: {duration_days} gün, Onay: {confirmed}")
    
    if not confirmed:
        return json.dumps({"error": "İşlem kullanıcı tarafından onaylanmadı. Lütfen kullanıcıdan açıkça onay isteyin."})
    
    try:
        from datetime import datetime, timedelta
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)
        
        result = neoone_client.create_bonus_discount(
            product_id=product_id,
            customer_group_id=customer_group_id,
            customer_id=customer_id,
            buy_quantity=buy_quantity,
            bonus_quantity=bonus_quantity,
            start_date=start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            end_date=end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        )
        
        if result.get("success"):
            return json.dumps({
                "success": True,
                "message": f"'{buy_quantity} al {bonus_quantity} bedava' kampanyası başarıyla oluşturuldu (PASİF durumda). Yönetici onayı ile aktif edilecektir.",
                "data": result.get("data")
            }, ensure_ascii=False)
        else:
            return json.dumps(result, ensure_ascii=False)
            
    except Exception as e:
        print(f"ERROR: create_bonus_discount failed: {e}")
        return json.dumps({"error": str(e)})

def get_cities_districts():
    """
    Sistemdeki şehir ve ilçeleri listeler.
    """
    print("DEBUG: get_cities_districts çağrıldı.")
    try:
        cities = neoone_client.get_cities()
        result = [{"id": c.get("id"), "name": c.get("name")} for c in cities]
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: get_cities_districts failed: {e}")
        return json.dumps({"error": str(e)})

# OpenAI Function Definitions (Schema)
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "search_product",
            "description": "Ürün ismine göre arama yapar. İskonto tanımlamadan önce ürünün ID'sini bulmak için kullanılır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Aranacak ürün ismi (örn: Mustela, Şampuan)."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_low_selling_products",
            "description": "Satış adetleri belirli bir eşiğin altında kalan ürünleri listeler. Düşük performanslı ürünleri bulmak için kullanılır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "integer",
                        "description": "Satış eşiği (adet). Bu sayının altında satış yapan ürünler listelenir. Varsayılan 100."
                    },
                    "customer_group_id": {
                        "type": "integer",
                        "description": "Analiz yapılacak müşteri grubu ID'si. Belirtilmezse tüm gruplardaki toplam satışa bakılır."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_bottom_products",
            "description": "En çok veya en az satan ürünleri sıralı şekilde getirir. 'En az satan 3 ürün' veya 'En çok satan 5 ürün' gibi sorgular için kullanılır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Kaç adet ürün getirileceği. Varsayılan 3."
                    },
                    "order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sıralama yönü. 'asc' = En az satanlar, 'desc' = En çok satanlar. Varsayılan 'asc'."
                    },
                    "customer_group_id": {
                        "type": "integer",
                        "description": "Analiz yapılacak müşteri grubu ID'si. Belirtilmezse toplam satışa bakılır."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_groups",
            "description": "Sistemdeki tanımlı müşteri gruplarını listeler.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_sales_distribution",
            "description": "Satış dağılımını grafik olarak göstermek için kullanılır. product_id verilmezse en az veya en çok satan ürünlerin karşılaştırmasını döner. 'En az satan ürünlerin grafiğini göster' veya 'satış dağılımını göster' gibi sorgular için kullanılır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Belirli bir ürünün detayını görmek için ürün ID'si. Verilmezse ürünler arası karşılaştırma yapılır."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Kaç ürün gösterileceği. Varsayılan 5."
                    },
                    "order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sıralama. 'asc' = En az satanlar, 'desc' = En çok satanlar. Varsayılan 'asc'."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_discount",
            "description": "Bir ürün ve müşteri grubu için yeni bir iskonto kampanyası oluşturur. İskonto PASİF olarak oluşturulur, yönetici onayı ile aktifleşir.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "İskonto yapılacak ürünün ID'si."
                    },
                    "customer_group_id": {
                        "type": "integer",
                        "description": "Hedef müşteri grubunun ID'si."
                    },
                    "discount_rate": {
                        "type": "integer",
                        "description": "Yüzde olarak iskonto oranı (örn: 10 = %10)."
                    },
                    "duration_days": {
                        "type": "integer",
                        "description": "İskontonun geçerli olacağı gün sayısı."
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Kullanıcının işlemi onaylayıp onaylamadığı. Kullanıcı 'evet' veya 'onaylıyorum' demeden true gönderilmemelidir."
                    }
                },
                "required": ["product_id", "customer_group_id", "discount_rate", "duration_days", "confirmed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_discount_performance",
            "description": "Var olan bir iskontonun detaylarını ve performans verilerini getirir.",
            "parameters": {
                "type": "object",
                "properties": {
                    "discount_id": {
                        "type": "integer",
                        "description": "Kontrol edilecek iskontonun ID'si."
                    }
                },
                "required": ["discount_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_discounts",
            "description": "Şu anda aktif olan tüm iskontoları listeler.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_sales_performance",
            "description": "Müşteri satış performansını getirir. Şehir, ilçe, müşteri grubu ve ciro bilgilerini içerir. Bölge bazlı analiz ve en az/çok ciro yapan müşterileri bulmak için kullanılır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_group_name": {
                        "type": "string",
                        "description": "Filtrelenecek müşteri grubu adı (örn: 'Plus Eczane', 'Eczane')"
                    },
                    "city": {
                        "type": "string",
                        "description": "Filtrelenecek şehir adı (örn: 'İstanbul')"
                    },
                    "order_by": {
                        "type": "string",
                        "enum": ["revenue_asc", "revenue_desc"],
                        "description": "Sıralama. 'revenue_asc' = En az ciro, 'revenue_desc' = En çok ciro"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Kaç müşteri getirileceği. Varsayılan 10."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_bonus_discount",
            "description": "X al Y bedava tipi kampanya oluşturur. Örneğin '2 kutu alana 1 kutu hediye' kampanyası. İskonto PASİF olarak oluşturulur. customer_group_id VEYA customer_id'den biri verilmelidir.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Kampanya yapılacak ürünün ID'si"
                    },
                    "customer_group_id": {
                        "type": "integer",
                        "description": "Hedef müşteri grubunun ID'si (tüm gruba uygulanır). get_customer_groups ile alınır."
                    },
                    "customer_id": {
                        "type": "integer",
                        "description": "Belirli bir müşterinin ID'si (tek müşteriye uygulanır). get_customer_sales_performance'dan alınır."
                    },
                    "buy_quantity": {
                        "type": "integer",
                        "description": "Satın alınması gereken minimum adet (örn: 2 al). Varsayılan 2."
                    },
                    "bonus_quantity": {
                        "type": "integer",
                        "description": "Hediye edilecek adet (örn: 1 bedava). Varsayılan 1."
                    },
                    "duration_days": {
                        "type": "integer",
                        "description": "Kampanyanın geçerli olacağı gün sayısı. Varsayılan 30."
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Kullanıcının işlemi onaylayıp onaylamadığı. 'evet' veya 'onaylıyorum' demeden true gönderilmemelidir."
                    }
                },
                "required": ["product_id", "confirmed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cities_districts",
            "description": "Sistemdeki şehir ve ilçeleri listeler. Bölge bazlı filtreleme için kullanılır.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_groups",
            "description": "Ürün gruplarını (kategorileri) listeler. Kullanıcı ürün kategorilerini veya gruplarını sorduğunda bu fonksiyon kullanılır.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# Function Dispatcher
available_functions = {
    "search_product": search_product,
    "get_low_selling_products": get_low_selling_products,
    "get_top_bottom_products": get_top_bottom_products,
    "get_customer_groups": get_customer_groups,
    "get_product_groups": get_product_groups,
    "get_product_sales_distribution": get_product_sales_distribution,
    "create_discount": create_discount,
    "check_discount_performance": check_discount_performance,
    "get_active_discounts": get_active_discounts,
    "get_customer_sales_performance": get_customer_sales_performance,
    "create_bonus_discount": create_bonus_discount,
    "get_cities_districts": get_cities_districts,
}

# Legacy: MOCK_PRODUCTS for /api/products endpoint (will be replaced later)
MOCK_PRODUCTS = []
