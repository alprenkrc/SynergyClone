#!/usr/bin/env python3
"""
SynergyClone Setup Script
Gerekli izinleri ayarlar ve bağımlılıkları kontrol eder.
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Python sürümünü kontrol eder."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("⚠️  Python 3.8+ gerekli. Mevcut sürüm:", sys.version)
        return False
    print("✅ Python sürümü uygun:", sys.version.split()[0])
    return True

def install_dependencies():
    """Bağımlılıkları yükler."""
    print("📦 Bağımlılıklar yükleniyor...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Bağımlılıklar başarıyla yüklendi!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Bağımlılık yükleme hatası: {e}")
        return False

def check_permissions():
    """Gerekli izinleri kontrol eder."""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        print("🔒 macOS üzerinde Accessibility izinleri gerekli!")
        print("   System Preferences > Security & Privacy > Accessibility")
        print("   Terminal ve Python'a izin verin.")
    elif system == "windows":  # Windows
        print("🔒 Windows üzerinde yönetici izinleri gerekebilir!")
        print("   Input simulation için admin hakları gerekli olabilir.")
    else:  # Linux
        print("🔒 Linux üzerinde X11 izinleri kontrol ediliyor...")
    
    return True

def make_executable():
    """Script dosyalarını çalıştırılabilir yapar."""
    scripts = ["run_server.py", "run_client.py"]
    for script in scripts:
        if os.path.exists(script):
            try:
                os.chmod(script, 0o755)
                print(f"✅ {script} çalıştırılabilir yapıldı")
            except Exception as e:
                print(f"⚠️  {script} izin hatası: {e}")

def create_desktop_shortcuts():
    """Masaüstü kısayolları oluşturur (isteğe bağlı)."""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        print("💡 macOS'te Automator ile uygulama oluşturabilirsiniz")
    elif system == "windows":  # Windows
        print("💡 Windows'ta .bat dosyaları oluşturabilirsiniz")
    else:  # Linux
        print("💡 Linux'ta .desktop dosyaları oluşturabilirsiniz")

def main():
    """Ana kurulum fonksiyonu."""
    print("🚀 SynergyClone Kurulum")
    print("=" * 40)
    
    # Python sürüm kontrolü
    if not check_python_version():
        sys.exit(1)
    
    # İzin kontrolü
    check_permissions()
    
    # Bağımlılık yükleme
    if not install_dependencies():
        sys.exit(1)
    
    # Executable yapma
    make_executable()
    
    # Kısayol önerileri
    create_desktop_shortcuts()
    
    print("\n🎉 Kurulum tamamlandı!")
    print("\n📖 Kullanım:")
    print("   Sunucu (ana bilgisayar): python run_server.py")
    print("   İstemci (diğer bilgisayar): python run_client.py")
    print("\n💡 İpuçları:")
    print("   • Sunucuyu önce başlatın")
    print("   • İstemcide sunucu IP adresini girin")
    print("   • Mouse'u ekran kenarına götürerek geçiş yapın")
    print("   • macOS'te Accessibility izinlerini verin")

if __name__ == "__main__":
    main() 