# SynergyClone

Mouse ve klavye paylaşımı için açık kaynak çözüm. Birden fazla bilgisayar arasında mouse ve klavyeyi paylaşmanızı sağlar.

## 🚀 Hızlı Başlangıç

### Gereksinimler

```bash
pip install -r requirements.txt
```

### Sunucu Başlatma

**Önerilen (Basit Mod):**
```bash
python3 run_server_simple.py
```

**Tam Özellikli (GUI ile):**
```bash
python3 run_server.py
```

### İstemci Başlatma

```bash
python3 run_client.py
```

## 📁 Proje Yapısı

### Ana Dosyalar
- `server.py` - Ana sunucu uygulaması (GUI ile)
- `client.py` - Ana istemci uygulaması
- `run_server_simple.py` - Basit sunucu (input capture olmadan)
- `utils.py` - Yardımcı fonksiyonlar ve sınıflar
- `input_handler.py` - Mouse/klavye yakalama ve simülasyon

### Başlatıcılar
- `run_server.py` - GUI sunucu başlatıcısı
- `run_client.py` - İstemci başlatıcısı

### Test Dosyaları
- `test_connection.py` - Sunucu bağlantı testi
- `simple_test.py` - Basit test scripti

### Alternatif Versiyonlar
- `server_simple.py` - Basit sunucu implementasyonu
- `client_simple.py` - Basit istemci implementasyonu

## 🔧 Kullanım

### 1. Sunucu Kurulumu (Ana Bilgisayar)

Ana bilgisayarda sunucuyu başlatın:

```bash
# Basit mod (önerilen)
python3 run_server_simple.py

# veya GUI ile
python3 run_server.py
```

Sunucu başladığında şu bilgileri göreceksiniz:
- IP adresi (örn: 192.168.1.100)
- Port (varsayılan: 24800)

### 2. İstemci Kurulumu (Diğer Bilgisayarlar)

Diğer bilgisayarlarda istemciyi başlatın:

```bash
python3 run_client.py
```

İstemci başladığında:
1. Sunucu IP adresini girin
2. Bağlan butonuna tıklayın

### 3. Bağlantı Testi

Sunucunun çalışıp çalışmadığını test etmek için:

```bash
python3 test_connection.py
```

## ⚠️ macOS Kullanıcıları İçin

macOS'ta input capture için Accessibility izinleri gereklidir:

1. **System Settings** > **Privacy & Security** > **Accessibility**
2. **Terminal** veya **Python** uygulamasını ekleyin
3. İzinleri etkinleştirin

Eğer izin vermek istemiyorsanız, `run_server_simple.py` kullanın - bu input capture olmadan çalışır.

## 🔍 Sorun Giderme

### Bağlantı Sorunları

1. **Sunucu çalışıyor mu?**
   ```bash
   python3 test_connection.py
   ```

2. **Firewall kontrolü**
   - Port 24800'ün açık olduğundan emin olun

3. **IP adresi kontrolü**
   - Sunucu başladığında gösterilen IP adresini kullanın

### macOS "Illegal Hardware Instruction" Hatası

Bu hata accessibility izinleri ile ilgilidir. Çözümler:

1. **Basit modu kullanın:**
   ```bash
   python3 run_server_simple.py
   ```

2. **Accessibility izinleri verin:**
   - System Settings > Privacy & Security > Accessibility
   - Terminal'i ekleyin ve etkinleştirin

## 📋 Özellikler

### Çalışan Özellikler
- ✅ WebSocket tabanlı iletişim
- ✅ Çoklu istemci desteği
- ✅ Handshake protokolü
- ✅ Heartbeat sistemi
- ✅ Clipboard paylaşımı (mesaj düzeyinde)
- ✅ GUI arayüzü
- ✅ Basit mod (input capture olmadan)

### Geliştirme Aşamasında
- 🔄 Mouse/klavye yakalama (macOS izinleri gerekli)
- 🔄 Ekranlar arası geçiş
- 🔄 Otomatik bağlantı

## 🛠️ Geliştirme

### Kod Yapısı

- **Server**: WebSocket sunucusu, istemci yönetimi
- **Client**: WebSocket istemcisi, input simülasyonu
- **Utils**: Mesaj protokolü, yardımcı fonksiyonlar
- **Input Handler**: Platform-specific input yakalama

### Mesaj Protokolü

```json
{
  "type": "message_type",
  "data": {...},
  "timestamp": "..."
}
```

Mesaj tipleri:
- `handshake` - Bağlantı kurma
- `heartbeat` - Canlılık kontrolü
- `mouse_move` - Mouse hareketi
- `mouse_click` - Mouse tıklama
- `key_press` - Klavye basma
- `clipboard` - Clipboard paylaşımı

## 📄 Lisans

Bu proje açık kaynak kodludur. Kendi sorumluluğunuzda kullanın.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun
3. Değişikliklerinizi commit edin
4. Pull request gönderin

---

**Not**: Bu proje eğitim amaçlıdır. Üretim ortamında kullanmadan önce güvenlik testleri yapın. 