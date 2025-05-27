#!/usr/bin/env python3
"""
SynergyClone Client Starter Script
İstemci uygulamasını başlatmak için kullanılır.
"""

import sys
import os

# Projenin ana dizinini Python path'e ekle
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

try:
    from client import main
    
    if __name__ == "__main__":
        print("SynergyClone Client başlatılıyor...")
        print("Diğer bilgisayarlarda mouse ve klavye olaylarını almak için kullanın.")
        print("-" * 50)
        main()
        
except ImportError as e:
    print(f"Import hatası: {e}")
    print("Gerekli bağımlılıkları yüklediğinizden emin olun:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
    sys.exit(1) 