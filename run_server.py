#!/usr/bin/env python3
"""
SynergyClone Server Çalıştırıcı - macOS
"""

from server import SynergyServer

if __name__ == "__main__":
    print("🍎 SynergyClone Server (macOS) GUI başlatılıyor...")
    server = SynergyServer()
    server.run() 