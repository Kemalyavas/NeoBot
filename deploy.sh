#!/bin/bash
# ================================================
# NeoBI Production Deployment Script
# Sunucu: neobicb.neocortexbe.com -> Port 6000
# ================================================

set -e  # Hata olursa dur

echo "🚀 NeoBI Kurulum Başlıyor..."

# 1. Gerekli paketleri kur
echo "📦 Sistem paketleri kontrol ediliyor..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm git

# 2. Node.js versiyonunu kontrol et (en az 16 olmalı)
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "⚠️ Node.js 16+ gerekli. Güncelleniyor..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# 3. Proje klasörüne git
cd ~

# 4. Eğer repo varsa güncelle, yoksa klonla
if [ -d "NeoBot" ]; then
    echo "📁 Mevcut repo güncelleniyor..."
    cd NeoBot
    git pull origin main
else
    echo "📥 Repo klonlanıyor..."
    git clone https://github.com/Kemalyavas/NeoBot.git
    cd NeoBot
fi

# 5. Backend kurulumu
echo "🐍 Backend kuruluyor..."
cd backend

# Virtual environment oluştur
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları kur
pip install --upgrade pip
pip install -r requirements.txt

# .env dosyası oluştur (eğer yoksa)
if [ ! -f ".env" ]; then
    echo "⚠️ .env dosyası bulunamadı!"
    echo ""
    echo "Lütfen .env dosyasını manuel oluşturun:"
    echo "   nano .env"
    echo ""
    echo "İçeriği:"
    echo "   OPENAI_API_KEY=<API_KEY_BURAYA>"
    echo "   ASSISTANT_ID=asst_wIXnI16IvhhPbFbanBZHl64G"
    echo "   NEOONE_API_URL=https://test.neoone.com.tr/api/v1"
    echo "   NEOONE_EMAIL=<EMAIL_BURAYA>"
    echo "   NEOONE_PASSWORD=<PASSWORD_BURAYA>"
    echo ""
    echo "Devam etmek için .env dosyasını oluşturun ve scripti tekrar çalıştırın."
    exit 1
else
    echo "✅ .env dosyası mevcut"
fi

# 6. Frontend build
echo "⚛️ Frontend build alınıyor..."
cd ../frontend
npm install
npm run build

echo "✅ Frontend build tamamlandı (dist klasörü oluştu)"

# 7. Backend'e geri dön
cd ../backend
source venv/bin/activate

echo ""
echo "================================================"
echo "✅ KURULUM TAMAMLANDI!"
echo "================================================"
echo ""
echo "🚀 Sunucuyu başlatmak için:"
echo "   cd ~/NeoBot/backend"
echo "   source venv/bin/activate"
echo "   uvicorn main:app --host 0.0.0.0 --port 6000"
echo ""
echo "🌐 Erişim: https://neobicb.neocortexbe.com"
echo ""
echo "💡 Arkaplanda çalıştırmak için:"
echo "   nohup uvicorn main:app --host 0.0.0.0 --port 6000 > neobi.log 2>&1 &"
echo ""
