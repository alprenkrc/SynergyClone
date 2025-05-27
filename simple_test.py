#!/usr/bin/env python3
"""
Basit test dosyası - bağımlılıkları ve temel fonksiyonları test eder
"""

import sys
import platform
import tkinter as tk

def test_imports():
    """Temel import'ları test eder."""
    print("🧪 Kütüphane testleri...")
    
    try:
        import websockets
        print("✅ websockets yüklü")
    except ImportError:
        print("❌ websockets eksik")
    
    try:
        from pynput import mouse, keyboard
        print("✅ pynput yüklü")
    except ImportError:
        print("❌ pynput eksik")
    
    try:
        import tkinter as tk
        print("✅ tkinter yüklü")
    except ImportError:
        print("❌ tkinter eksik")

def test_screen_info():
    """Ekran bilgilerini test eder."""
    print("\n📺 Ekran bilgisi testi...")
    try:
        root = tk.Tk()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        print(f"✅ Ekran çözünürlüğü: {width}x{height}")
        root.destroy()
    except Exception as e:
        print(f"❌ Ekran bilgisi hatası: {e}")

def test_basic_gui():
    """Basit GUI testi."""
    print("\n🖼️ GUI testi...")
    try:
        root = tk.Tk()
        root.title("SynergyClone Test")
        root.geometry("300x200")
        
        label = tk.Label(root, text="Test başarılı!\nSynergyClone çalışır durumda.")
        label.pack(expand=True)
        
        button = tk.Button(root, text="Kapat", command=root.destroy)
        button.pack(pady=10)
        
        print("✅ GUI penceresi açıldı")
        root.mainloop()
        
    except Exception as e:
        print(f"❌ GUI hatası: {e}")

def main():
    """Ana test fonksiyonu."""
    print("🚀 SynergyClone Basit Test")
    print("=" * 40)
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")
    print("-" * 40)
    
    test_imports()
    test_screen_info()
    
    print("\n💡 GUI testini başlatmak için 'Enter' tuşuna basın...")
    input()
    test_basic_gui()
    
    print("\n🎉 Testler tamamlandı!")

if __name__ == "__main__":
    main() 