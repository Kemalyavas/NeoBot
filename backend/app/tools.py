import json
import random

# --- Mock Database ---
MOCK_PRODUCTS = [
    {"id": "p_101", "name": "Çikolatalı Gofret", "category": "Atıştırmalık", "sales_last_month": {"g_1": 800, "g_2": 300, "g_3": 100, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_102", "name": "Organik Yulaf Ezmesi", "category": "Kahvaltılık", "sales_last_month": {"g_1": 2, "g_2": 3, "g_3": 0, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_103", "name": "Premium Filtre Kahve", "category": "İçecek", "sales_last_month": {"g_1": 1, "g_2": 5, "g_3": 2, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_104", "name": "Zeytinyağlı Sabun", "category": "Kozmetik", "sales_last_month": {"g_1": 1, "g_2": 2, "g_3": 0, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_105", "name": "Enerji İçeceği", "category": "İçecek", "sales_last_month": {"g_1": 50, "g_2": 200, "g_3": 600, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_106", "name": "Siyah Çay 1kg", "category": "İçecek", "sales_last_month": {"g_1": 1500, "g_2": 800, "g_3": 200, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_107", "name": "Bulaşık Deterjanı 750ml", "category": "Temizlik", "sales_last_month": {"g_1": 50, "g_2": 350, "g_3": 50, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_108", "name": "Kağıt Havlu 6'lı", "category": "Temizlik", "sales_last_month": {"g_1": 2, "g_2": 8, "g_3": 2, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_109", "name": "Ayçiçek Yağı 5L", "category": "Gıda", "sales_last_month": {"g_1": 50, "g_2": 200, "g_3": 50, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_110", "name": "Makarna (Burgu)", "category": "Gıda", "sales_last_month": {"g_1": 600, "g_2": 800, "g_3": 100, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_111", "name": "Diş Macunu", "category": "Kozmetik", "sales_last_month": {"g_1": 5, "g_2": 15, "g_3": 5, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_112", "name": "Şampuan 500ml", "category": "Kozmetik", "sales_last_month": {"g_1": 10, "g_2": 25, "g_3": 5, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_113", "name": "Meyve Suyu (Şeftali)", "category": "İçecek", "sales_last_month": {"g_1": 200, "g_2": 300, "g_3": 100, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_114", "name": "Tuzlu Fıstık", "category": "Atıştırmalık", "sales_last_month": {"g_1": 3, "g_2": 4, "g_3": 2, "g_4": 0, "g_5": 0, "g_6": 0}},
    {"id": "p_115", "name": "Bebek Bezi (4 Numara)", "category": "Bebek Bakım", "sales_last_month": {"g_1": 20, "g_2": 100, "g_3": 30, "g_4": 0, "g_5": 0, "g_6": 0}},
]

MOCK_CUSTOMER_GROUPS = [
    {"id": "g_1", "name": "Bakkallar"},
    {"id": "g_2", "name": "Süpermarketler"},
    {"id": "g_3", "name": "Benzin İstasyonları"},
    {"id": "g_4", "name": "Online Pazaryerleri"},
    {"id": "g_5", "name": "Toptancılar"},
    {"id": "g_6", "name": "Oteller & Restoranlar (HoReCa)"},
]

MOCK_DISCOUNTS = []

# --- Tool Functions ---

def get_low_selling_products(threshold: int = 10, group_id: str = None):
    """
    Satış adedi belirli bir eşiğin altında olan ürünleri getirir.
    Eğer group_id verilirse sadece o gruptaki satışlara bakar.
    """
    print(f"DEBUG: get_low_selling_products çağrıldı. Eşik: {threshold}, Grup: {group_id}")
    
    low_selling = []
    for p in MOCK_PRODUCTS:
        sales_data = p['sales_last_month']
        
        if group_id:
            # Belirli bir grup için kontrol et
            sales = sales_data.get(group_id, 0)
        else:
            # Toplam satışa bak
            sales = sum(sales_data.values())
            
        if sales < threshold:
            # Sonuç objesini hazırla (sadece ilgili satış bilgisini dön)
            product_info = p.copy()
            product_info['sales_last_month'] = sales # Tek bir sayıya indirge
            low_selling.append(product_info)
            
    return json.dumps(low_selling)

def get_customer_groups():
    """
    Mevcut müşteri gruplarını listeler.
    """
    print("DEBUG: get_customer_groups çağrıldı.")
    return json.dumps(MOCK_CUSTOMER_GROUPS)

def create_discount(product_id: str, group_id: str, discount_rate: int, duration_days: int):
    """
    Belirli bir ürün ve müşteri grubu için iskonto tanımlar.
    """
    print(f"DEBUG: create_discount çağrıldı. Ürün: {product_id}, Grup: {group_id}, Oran: %{discount_rate}, Süre: {duration_days} gün")
    
    # Ürün ve grup kontrolü (Mock)
    product = next((p for p in MOCK_PRODUCTS if p['id'] == product_id), None)
    group = next((g for g in MOCK_CUSTOMER_GROUPS if g['id'] == group_id), None)
    
    if not product:
        return json.dumps({"error": "Ürün bulunamadı."})
    if not group:
        return json.dumps({"error": "Müşteri grubu bulunamadı."})

    discount_id = f"dsc_{random.randint(1000, 9999)}"
    new_discount = {
        "id": discount_id,
        "product_name": product['name'],
        "group_name": group['name'],
        "rate": discount_rate,
        "duration": duration_days,
        "status": "Active"
    }
    MOCK_DISCOUNTS.append(new_discount)
    
    return json.dumps({
        "status": "success",
        "message": "İskonto başarıyla tanımlandı.",
        "discount_details": new_discount
    })

def check_discount_performance(discount_id: str):
    """
    Tanımlı bir iskontonun performansını kontrol eder.
    """
    print(f"DEBUG: check_discount_performance çağrıldı. ID: {discount_id}")
    # Mock logic: Rastgele bir performans sonucu dönelim
    return json.dumps({
        "discount_id": discount_id,
        "usage_count": random.randint(0, 5), # Düşük kullanım simülasyonu
        "revenue_generated": random.randint(0, 1000),
        "comment": "İskonto tanımlı ama kullanım düşük görünüyor."
    })

def search_product(query: str):
    """
    Ürün ismine göre arama yapar ve eşleşen ürünleri getirir.
    """
    print(f"DEBUG: search_product çağrıldı. Sorgu: {query}")
    results = [p for p in MOCK_PRODUCTS if query.lower() in p['name'].lower()]
    return json.dumps(results)

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
                        "description": "Aranacak ürün ismi (örn: Sabun)."
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
            "description": "Son ayda satış adetleri belirli bir eşiğin altında kalan ürünleri listeler. Analiz için kullanılır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "integer",
                        "description": "Satış eşiği. Varsayılan 10.",
                        "default": 10
                    },
                    "group_id": {
                        "type": "string",
                        "description": "Analiz yapılacak müşteri grubu ID'si (örn: g_1). Eğer belirtilmezse genel toplama bakılır."
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
            "description": "Sistemdeki tanımlı müşteri gruplarını (örn: Bakkallar, Marketler) listeler.",
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
            "name": "create_discount",
            "description": "Bir ürün ve müşteri grubu için yeni bir iskonto kampanyası oluşturur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "İskonto yapılacak ürünün ID'si (örn: p_102)."
                    },
                    "group_id": {
                        "type": "string",
                        "description": "Hedef müşteri grubunun ID'si (örn: g_1)."
                    },
                    "discount_rate": {
                        "type": "integer",
                        "description": "Yüzde olarak iskonto oranı (örn: 10)."
                    },
                    "duration_days": {
                        "type": "integer",
                        "description": "İskontonun geçerli olacağı gün sayısı."
                    }
                },
                "required": ["product_id", "group_id", "discount_rate", "duration_days"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_discount_performance",
            "description": "Var olan bir iskontonun performans verilerini (kullanım, ciro) getirir.",
            "parameters": {
                "type": "object",
                "properties": {
                    "discount_id": {
                        "type": "string",
                        "description": "Kontrol edilecek iskontonun ID'si."
                    }
                },
                "required": ["discount_id"]
            }
        }
    }
]

# Function Dispatcher
available_functions = {
    "get_low_selling_products": get_low_selling_products,
    "get_customer_groups": get_customer_groups,
    "create_discount": create_discount,
    "check_discount_performance": check_discount_performance,
    "search_product": search_product,
}
