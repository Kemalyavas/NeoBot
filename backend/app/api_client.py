"""
NeoOne API Client
Gerçek NeoOne sistemine bağlantı için HTTP istemcisi.
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Token doğrulama cache'i (token -> (is_valid, expiry_time))
_token_validation_cache = {}
TOKEN_CACHE_DURATION = timedelta(minutes=10)  # 10 dakika cache

class NeoOneClient:
    """NeoOne API ile iletişim kuran istemci sınıfı."""
    
    def __init__(self):
        self.base_url = os.getenv("NEOONE_API_URL", "https://test.neoone.com.tr/api/v1")
        self.email = os.getenv("NEOONE_EMAIL")
        self.password = os.getenv("NEOONE_PASSWORD")
        self._token = None
        self._token_expiry = None
    
    def _get_token(self) -> str:
        """Token al veya cache'den döndür."""
        # Token hala geçerliyse cache'den dön
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token
        
        # Yeni token al
        response = requests.post(
            f"{self.base_url}/Auth/login",
            json={"email": self.email, "password": self.password},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        data = response.json()
        self._token = data.get("token")
        # Token'ı 55 dakika geçerli say (güvenlik marjı)
        self._token_expiry = datetime.now() + timedelta(minutes=55)
        
        print(f"DEBUG: Yeni token alındı")
        return self._token
    
    def _headers(self) -> dict:
        """Authorization header'ı ile request headers döndür."""
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json"
        }
    
    # ==================== TOKEN VALIDATION ====================
    
    def validate_user_token(self, user_token: str) -> bool:
        """
        Kullanıcının NeoOne token'ının geçerli olup olmadığını kontrol eder.
        Cache kullanarak gereksiz API çağrılarını önler.
        """
        global _token_validation_cache
        
        # Cache'de var mı ve hala geçerli mi kontrol et
        if user_token in _token_validation_cache:
            is_valid, expiry = _token_validation_cache[user_token]
            if datetime.now() < expiry:
                print(f"DEBUG: Token validation from cache: {is_valid}")
                return is_valid
        
        # Cache'de yok veya süresi dolmuş, API'ye sor
        try:
            response = requests.get(
                f"{self.base_url}/Users",
                headers={
                    "Authorization": f"Bearer {user_token}",
                    "Content-Type": "application/json"
                },
                timeout=5  # 5 saniye timeout
            )
            
            is_valid = response.status_code == 200
            
            # Cache'e kaydet
            _token_validation_cache[user_token] = (is_valid, datetime.now() + TOKEN_CACHE_DURATION)
            
            print(f"DEBUG: Token validation API call: {is_valid} (status: {response.status_code})")
            return is_valid
            
        except Exception as e:
            print(f"ERROR: Token validation failed: {e}")
            # Hata durumunda false dön ama cache'leme
            return False
    
    # ==================== CUSTOMER GROUPS ====================
    
    def get_customer_groups(self) -> list:
        """Müşteri gruplarını getirir."""
        response = requests.get(
            f"{self.base_url}/CustomerGroups",
            headers=self._headers()
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            return data.get("data", [])
        return []
    
    # ==================== CUSTOMERS ====================
    
    def get_customers(self) -> list:
        """Tüm müşterileri getirir."""
        response = requests.get(
            f"{self.base_url}/Customers",
            headers=self._headers()
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            return data.get("data", [])
        # Bazen direkt liste dönebilir
        if isinstance(data, list):
            return data
        return []
    
    # ==================== PRODUCT GROUPS (KATEGORİLER) ====================
    
    def get_product_groups(self) -> list:
        """Ürün gruplarını (kategorileri) getirir."""
        response = requests.get(
            f"{self.base_url}/ProductGroups",
            headers=self._headers()
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            return data.get("data", [])
        return []
    
    # ==================== PRODUCT SALES ====================
    
    def get_product_sales(self, start_date: str = None, end_date: str = None) -> list:
        """
        Ürün satış raporunu getirir.
        
        Args:
            start_date: Başlangıç tarihi (YYYY-MM-DD)
            end_date: Bitiş tarihi (YYYY-MM-DD)
        """
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        
        response = requests.get(
            f"{self.base_url}/orders/reports/product-sales",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            return data.get("data", {}).get("data", [])
        return []
    
    # ==================== DISCOUNTS ====================
    
    def create_discount(self, product_id: int, customer_group_id: int, discount_percent: int, 
                        start_date: str, end_date: str, name: str = None) -> dict:
        """
        Yeni iskonto oluşturur.
        
        Args:
            product_id: Ürün ID
            customer_group_id: Müşteri grubu ID
            discount_percent: Yüzde iskonto oranı
            start_date: Başlangıç tarihi (ISO format)
            end_date: Bitiş tarihi (ISO format)
            name: İskonto adı (opsiyonel)
        """
        # İskonto adı oluştur
        if not name:
            name = f"Bot İskonto - {product_id} - {customer_group_id}"
        
        discount_data = {
            "name": name,
            "type": "Total",
            "startDate": start_date,
            "endDate": end_date,
            "discountPercent": discount_percent,
            "discountAmount": 0,
            "priority": 1,
            "allowOverlap": True,
            "isActive": False,  # Bot tarafından oluşturulan iskontolar PASİF başlar
            "discountTargets": [
                {
                    "customerGroupId": customer_group_id
                }
            ],
            "discountProducts": [
                {
                    "productId": product_id,
                    "discountPercent": discount_percent,
                    "discountAmount": 0
                }
            ]
        }
        
        print(f"DEBUG: Discount API'ye gönderilen veri: {discount_data}")
        
        response = requests.post(
            f"{self.base_url}/Discounts",
            headers=self._headers(),
            json=discount_data
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_discounts(self) -> list:
        """Mevcut iskontoları getirir."""
        response = requests.get(
            f"{self.base_url}/Discounts",
            headers=self._headers()
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            return data.get("data", [])
        return []
    
    def get_active_discounts(self) -> list:
        """Aktif iskontoları getirir."""
        response = requests.get(
            f"{self.base_url}/Discounts/active",
            headers=self._headers()
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            return data.get("data", [])
        return []
    
    # ==================== CUSTOMER REPORTS ====================
    
    def get_customer_sales_performance(self) -> list:
        """Müşteri satış performans raporunu getirir."""
        response = requests.get(
            f"{self.base_url}/customers/reports/sales-performance",
            headers=self._headers()
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            return data.get("data", {}).get("data", [])
        return []
    
    # ==================== CITIES ====================
    
    def get_cities(self) -> list:
        """Şehirleri getirir."""
        response = requests.get(
            f"{self.base_url}/Cities",
            headers=self._headers()
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            return data.get("data", [])
        return []
    
    # ==================== BONUS DISCOUNT ====================
    
    def create_bonus_discount(self, product_id: int, customer_group_id: int = None,
                               customer_id: int = None,
                               buy_quantity: int = 2, bonus_quantity: int = 1,
                               start_date: str = None, end_date: str = None, 
                               name: str = None) -> dict:
        """
        X al Y bedava tipi kampanya oluşturur.
        customer_group_id veya customer_id'den biri verilmelidir.
        """
        if not name:
            name = f"Bot Kampanya - {product_id} - {buy_quantity}+{bonus_quantity}"
        
        # Target belirleme
        target = {}
        if customer_id:
            target["customerId"] = customer_id
        elif customer_group_id:
            target["customerGroupId"] = customer_group_id
        
        discount_data = {
            "name": name,
            "type": "BonusProduct",
            "startDate": start_date,
            "endDate": end_date,
            "discountPercent": 0,
            "discountAmount": 0,
            "priority": 1,
            "allowOverlap": False,
            "isActive": False,  # Bot tarafından oluşturulan kampanyalar PASİF başlar
            "discountTargets": [target],
            "discountProducts": [],
            "discountBonusProducts": [
                {
                    "buyProductId": product_id,
                    "bonusProductId": product_id,
                    "minQuantity": buy_quantity,
                    "bonusQuantity": bonus_quantity,
                    "maxQuantity": buy_quantity + 100
                }
            ]
        }
        
        print(f"DEBUG: Bonus Discount API'ye gönderilen veri: {discount_data}")
        
        response = requests.post(
            f"{self.base_url}/Discounts",
            headers=self._headers(),
            json=discount_data
        )
        response.raise_for_status()
        
        return response.json()


# Singleton instance
neoone_client = NeoOneClient()
