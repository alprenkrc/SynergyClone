# SynergyClone

🖱️ **Mouse ve klavye paylaşımı** - İki bilgisayar arasında tek mouse ve klavye kullanın!

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. Sunucu (Ana Bilgisayar)
```bash
python3 run_server.py
```

### 3. İstemci (Diğer Bilgisayar)
```bash
python3 run_client.py
```

## 📁 Proje Yapısı

```
SynergyClone/
├── server.py           # Ana sunucu uygulaması
├── client.py           # Ana istemci uygulaması  
├── run_server.py       # Sunucu başlatıcısı
├── run_client.py       # İstemci başlatıcısı
├── utils.py            # Yardımcı fonksiyonlar
├── input_handler.py    # Mouse/klavye işlemleri
├── requirements.txt    # Python bağımlılıkları
└── README.md          # Bu dosya
```

## 🎯 Nasıl Çalışır?

1. **Sunucu** ana bilgisayarda çalışır
2. **İstemci** diğer bilgisayarda çalışır ve sunucuya bağlanır
3. Mouse ekran kenarına geldiğinde **otomatik olarak diğer bilgisayara geçer**
4. **Klavye** ve **clipboard** da paylaşılır

## 🔧 Kurulum Adımları

### Ana Bilgisayar (Sunucu):
1. `python3 run_server.py` çalıştırın
2. **"Sunucuyu Başlat"** butonuna tıklayın
3. IP adresini not edin (örn: 192.168.1.100)

### Diğer Bilgisayar (İstemci):
1. `python3 run_client.py` çalıştırın  
2. Sunucu IP adresini girin
3. **"Bağlan"** butonuna tıklayın

## ⚠️ macOS Kullanıcıları

macOS'ta **Accessibility izinleri** gereklidir:

1. **System Settings** → **Privacy & Security** → **Accessibility**
2. **Terminal** veya **Python**'ı ekleyin
3. İzinleri **etkinleştirin**
4. Uygulamayı **yeniden başlatın**

**İzin vermezseniz:** Sadece WebSocket iletişimi çalışır (manuel clipboard paylaşımı)

## 🎮 Kullanım

### Mouse Geçişi:
- Mouse'u **ekran kenarına** götürün
- Otomatik olarak **diğer bilgisayara** geçer
- Geri dönmek için **diğer kenardan** gelin

### Klavye:
- Mouse hangi bilgisayardaysa **klavye de orada** çalışır

### Clipboard:
- **Otomatik:** Kopyala/yapıştır işlemleri senkronize olur
- **Manuel:** GUI'deki clipboard alanını kullanın

## 🔍 Sorun Giderme

### Bağlantı Sorunları:
- **Firewall:** Port 24800'ün açık olduğundan emin olun
- **IP Adresi:** Sunucuda gösterilen IP'yi kullanın
- **Ağ:** Aynı WiFi/ağda olduğunuzdan emin olun

### macOS "Illegal Hardware Instruction":
- **Çözüm:** Accessibility izinleri verin
- **Geçici:** Sadece WebSocket modu ile çalışır

### Windows İzinleri:
- **Admin hakları** gerekebilir
- **Antivirus** programını kontrol edin

## ✨ Özellikler

### ✅ Çalışan:
- 🖱️ Mouse paylaşımı ve geçişi
- ⌨️ Klavye paylaşımı  
- 📋 Clipboard senkronizasyonu
- 🖥️ Modern GUI arayüzü
- 🔄 Otomatik yeniden bağlanma
- 💓 Bağlantı durumu takibi

### 🔄 Geliştirme Aşamasında:
- 🎯 Daha akıllı ekran geçişi
- ⚙️ Özelleştirilebilir ayarlar
- 🔐 Şifre koruması

## 🛠️ Teknik Detaylar

- **Protokol:** WebSocket (ws://)
- **Port:** 24800 (varsayılan)
- **Platform:** Windows, macOS, Linux
- **Python:** 3.8+

## 📄 Lisans

Bu proje açık kaynak kodludur. Eğitim ve kişisel kullanım için serbesttir.

---

**💡 İpucu:** İlk kurulumda accessibility izinleri verin, sonra sorunsuz çalışır! 