#!/usr/bin/env python3
"""
Windows Mouse Test - Mouse simülasyonunu test eder
"""

import time
import platform
import ctypes
import sys

def is_admin():
    """Yönetici hakları kontrolü"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def test_windows_api():
    """Windows API ile mouse testi"""
    if platform.system() != "Windows":
        print("❌ Bu test sadece Windows'ta çalışır")
        return False
    
    try:
        import ctypes
        print("✅ ctypes import başarılı")
        
        # Yönetici hakları kontrolü
        if not is_admin():
            print("⚠️ Yönetici hakları YOK - bu sorun olabilir")
        else:
            print("✅ Yönetici hakları mevcut")
        
        # DPI awareness ayarla
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            print("✅ DPI awareness ayarlandı")
        except Exception as e:
            print(f"⚠️ DPI awareness ayarlanamadı: {e}")
        
        # Ekran çözünürlüğünü al
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        print(f"📱 Ekran çözünürlüğü: {width}x{height}")
        
        # Mevcut mouse pozisyonunu al
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        point = POINT()
        result = ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        if not result:
            print("❌ GetCursorPos başarısız")
            return False
        print(f"🖱️ Mevcut mouse pozisyonu: ({point.x}, {point.y})")
        
        # Mouse'u hareket ettir
        test_x = width // 2
        test_y = height // 2
        
        print(f"🎯 Mouse'u ({test_x}, {test_y}) pozisyonuna hareket ettiriliyor...")
        
        # SetCursorPos dene
        result = ctypes.windll.user32.SetCursorPos(test_x, test_y)
        print(f"SetCursorPos sonucu: {result}")
        
        if result:
            print("✅ SetCursorPos başarılı!")
            
            # 1 saniye bekle
            time.sleep(1)
            
            # Tekrar pozisyonu kontrol et
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            print(f"🖱️ Yeni mouse pozisyonu: ({point.x}, {point.y})")
            
            if abs(point.x - test_x) < 10 and abs(point.y - test_y) < 10:
                print("✅ Mouse pozisyonu doğru!")
                return True
            else:
                print(f"❌ Mouse pozisyonu yanlış! Beklenen: ({test_x}, {test_y}), Gerçek: ({point.x}, {point.y})")
                return False
        else:
            # Hata kodunu al
            error_code = ctypes.windll.kernel32.GetLastError()
            print(f"❌ SetCursorPos başarısız! Hata kodu: {error_code}")
            return False
            
    except Exception as e:
        print(f"❌ Windows API hatası: {e}")
        return False

def test_pynput():
    """Pynput ile mouse testi"""
    try:
        from pynput import mouse
        print("✅ pynput import başarılı")
        
        controller = mouse.Controller()
        
        # Mevcut pozisyon
        pos = controller.position
        print(f"🖱️ Pynput mevcut pozisyon: {pos}")
        
        # Mouse'u hareket ettir
        test_x = pos[0] + 50  # Daha küçük hareket
        test_y = pos[1] + 50
        
        print(f"🎯 Pynput ile ({test_x}, {test_y}) pozisyonuna hareket ettiriliyor...")
        
        try:
            controller.position = (test_x, test_y)
            print("✅ Pynput position set başarılı")
        except Exception as e:
            print(f"❌ Pynput position set hatası: {e}")
            return False
        
        time.sleep(1)
        
        new_pos = controller.position
        print(f"🖱️ Pynput yeni pozisyon: {new_pos}")
        
        if abs(new_pos[0] - test_x) < 10 and abs(new_pos[1] - test_y) < 10:
            print("✅ Pynput mouse hareketi başarılı!")
            return True
        else:
            print(f"❌ Pynput mouse hareketi başarısız! Beklenen: ({test_x}, {test_y}), Gerçek: {new_pos}")
            return False
            
    except Exception as e:
        print(f"❌ Pynput hatası: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Windows Mouse Simülasyon Testi")
    print("=" * 40)
    
    # Yönetici hakları uyarısı
    if not is_admin():
        print("⚠️ UYARI: Yönetici hakları olmadan çalışıyorsunuz!")
        print("💡 Daha iyi sonuçlar için 'Yönetici olarak çalıştır' kullanın")
        print()
    
    print("\n1️⃣ Windows API Testi:")
    api_result = test_windows_api()
    
    print("\n2️⃣ Pynput Testi:")
    pynput_result = test_pynput()
    
    print("\n📊 Sonuçlar:")
    print(f"Windows API: {'✅ Başarılı' if api_result else '❌ Başarısız'}")
    print(f"Pynput: {'✅ Başarılı' if pynput_result else '❌ Başarısız'}")
    
    if not api_result and not pynput_result:
        print("\n⚠️ Öneriler:")
        print("1. ✅ Uygulamayı 'Yönetici olarak çalıştır'")
        print("2. Windows Defender Real-time protection'ı geçici olarak kapatın")
        print("3. UAC ayarlarını düşürün")
        print("4. Developer Mode'u açın")
        print("5. Antivirus programını geçici olarak devre dışı bırakın")
    elif api_result or pynput_result:
        print("\n✅ En az bir yöntem çalışıyor - SynergyClone çalışmalı!") 