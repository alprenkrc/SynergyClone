#!/usr/bin/env python3
"""
SynergyClone Server Çalıştırıcı - macOS
"""

from server import SynergyServer
import asyncio

if __name__ == "__main__":
    print("🍎 SynergyClone Server (macOS) başlatılıyor...")
    server = SynergyServer()
    asyncio.run(server.start_server()) 