#!/usr/bin/env python3
"""
Windows Mouse Test - Mouse simülasyonunu test eder
"""

import time
import platform

def test_windows_api():
    """Windows API ile mouse testi"""
    if platform.system() != "Windows":
        print("❌ Bu test sadece Windows'ta çalışır")
        return False
    
    try:
        import ctypes
        print("✅ ctypes import başarılı")
        
        # DPI awareness ayarla
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            print("✅ DPI awareness ayarlandı")
        except:
            print("⚠️ DPI awareness ayarlanamadı")
        
        # Ekran çözünürlüğünü al
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        print(f"📱 Ekran çözünürlüğü: {width}x{height}")
        
        # Mevcut mouse pozisyonunu al
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        point = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        print(f"🖱️ Mevcut mouse pozisyonu: ({point.x}, {point.y})")
        
        # Mouse'u hareket ettir
        test_x = width // 2
        test_y = height // 2
        
        print(f"🎯 Mouse'u ({test_x}, {test_y}) pozisyonuna hareket ettiriliyor...")
        result = ctypes.windll.user32.SetCursorPos(test_x, test_y)
        
        if result:
            print("✅ Mouse hareketi başarılı!")
            
            # 2 saniye bekle
            time.sleep(2)
            
            # Tekrar pozisyonu kontrol et
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            print(f"🖱️ Yeni mouse pozisyonu: ({point.x}, {point.y})")
            
            if abs(point.x - test_x) < 5 and abs(point.y - test_y) < 5:
                print("✅ Mouse pozisyonu doğru!")
                return True
            else:
                print("❌ Mouse pozisyonu yanlış!")
                return False
        else:
            print("❌ Mouse hareketi başarısız!")
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
        test_x = pos[0] + 100
        test_y = pos[1] + 100
        
        print(f"🎯 Pynput ile ({test_x}, {test_y}) pozisyonuna hareket ettiriliyor...")
        controller.position = (test_x, test_y)
        
        time.sleep(1)
        
        new_pos = controller.position
        print(f"🖱️ Pynput yeni pozisyon: {new_pos}")
        
        if abs(new_pos[0] - test_x) < 5 and abs(new_pos[1] - test_y) < 5:
            print("✅ Pynput mouse hareketi başarılı!")
            return True
        else:
            print("❌ Pynput mouse hareketi başarısız!")
            return False
            
    except Exception as e:
        print(f"❌ Pynput hatası: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Windows Mouse Simülasyon Testi")
    print("=" * 40)
    
    print("\n1️⃣ Windows API Testi:")
    api_result = test_windows_api()
    
    print("\n2️⃣ Pynput Testi:")
    pynput_result = test_pynput()
    
    print("\n📊 Sonuçlar:")
    print(f"Windows API: {'✅ Başarılı' if api_result else '❌ Başarısız'}")
    print(f"Pynput: {'✅ Başarılı' if pynput_result else '❌ Başarısız'}")
    
    if not api_result and not pynput_result:
        print("\n⚠️ Öneriler:")
        print("1. Uygulamayı 'Yönetici olarak çalıştır'")
        print("2. Antivirus/Windows Defender'ı geçici olarak devre dışı bırakın")
        print("3. Windows güvenlik ayarlarını kontrol edin") 