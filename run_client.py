#!/usr/bin/env python3
"""
SynergyClone Client Çalıştırıcı - Windows
"""

from client import SynergyClient
import asyncio

if __name__ == "__main__":
    print("🪟 SynergyClone Client (Windows) başlatılıyor...")
    
    # macOS server IP'sini buraya girin
    SERVER_IP = "192.168.1.100"  # macOS'un IP adresi
    SERVER_PORT = 8765
    
    client = SynergyClient(SERVER_IP, SERVER_PORT)
    asyncio.run(client.start_client()) 