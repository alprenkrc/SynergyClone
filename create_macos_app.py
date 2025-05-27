#!/usr/bin/env python3
"""
macOS .app bundle oluşturucu
SynergyClone Server'ı macOS uygulaması haline getirir
"""

import os
import shutil
import stat
import plistlib
from pathlib import Path

def create_app_bundle():
    """SynergyClone Server için .app bundle oluşturur."""
    
    # App bundle yapısı
    app_name = "SynergyClone Server"
    app_bundle = f"{app_name}.app"
    
    # Mevcut bundle'ı temizle
    if os.path.exists(app_bundle):
        shutil.rmtree(app_bundle)
    
    # Bundle dizin yapısını oluştur
    contents_dir = os.path.join(app_bundle, "Contents")
    macos_dir = os.path.join(contents_dir, "MacOS")
    resources_dir = os.path.join(contents_dir, "Resources")
    
    os.makedirs(macos_dir)
    os.makedirs(resources_dir)
    
    # Info.plist oluştur
    info_plist = {
        'CFBundleName': app_name,
        'CFBundleDisplayName': app_name,
        'CFBundleIdentifier': 'com.synergyClone.server',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleExecutable': 'SynergyClone_Server',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'SYNC',
        'LSMinimumSystemVersion': '10.15.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,  # GUI uygulaması olarak göster
        'NSAppleEventsUsageDescription': 'SynergyClone mouse ve klavye olaylarını yakalamak için Apple Events kullanır.',
        'NSSystemAdministrationUsageDescription': 'SynergyClone sistem seviyesinde input yakalama için yönetici izinleri gerektirir.',
        # Accessibility izni için açıklama
        'NSAccessibilityUsageDescription': 'SynergyClone mouse ve klavye olaylarını yakalamak ve diğer bilgisayarlara iletmek için accessibility izinlerine ihtiyaç duyar.',
    }
    
    info_plist_path = os.path.join(contents_dir, "Info.plist")
    with open(info_plist_path, 'wb') as f:
        plistlib.dump(info_plist, f)
    
    # Executable script oluştur
    executable_content = f'''#!/usr/bin/env python3
import os
import sys

# Bundle içindeki Python dosyalarının yolunu ekle
bundle_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
resources_dir = os.path.join(bundle_dir, "Resources")
sys.path.insert(0, resources_dir)

# Ana server'ı çalıştır
if __name__ == "__main__":
    import server
    server.main()
'''
    
    executable_path = os.path.join(macos_dir, "SynergyClone_Server")
    with open(executable_path, 'w') as f:
        f.write(executable_content)
    
    # Executable izinleri ver
    st = os.stat(executable_path)
    os.chmod(executable_path, st.st_mode | stat.S_IEXEC)
    
    # Python dosyalarını Resources'a kopyala
    python_files = [
        'server.py',
        'client.py', 
        'utils.py',
        'input_handler.py',
        'run_server.py',
        'run_client.py'
    ]
    
    for file in python_files:
        if os.path.exists(file):
            shutil.copy2(file, resources_dir)
    
    # requirements.txt'yi de kopyala
    if os.path.exists('requirements.txt'):
        shutil.copy2('requirements.txt', resources_dir)
    
    print(f"✅ {app_bundle} başarıyla oluşturuldu!")
    print(f"📁 Konum: {os.path.abspath(app_bundle)}")
    print()
    print("🔧 Kullanım:")
    print(f"1. {app_bundle}'ı Applications klasörüne taşıyın")
    print("2. Uygulamayı çalıştırın")
    print("3. macOS accessibility izni isteyecek - 'Open System Preferences' tıklayın")
    print("4. Privacy & Security > Accessibility'de SynergyClone Server'ı etkinleştirin")
    print("5. Uygulamayı yeniden başlatın")
    
    return app_bundle

if __name__ == "__main__":
    create_app_bundle() 