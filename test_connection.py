#!/usr/bin/env python3
"""
WebSocket bağlantı testi
"""

import asyncio
import websockets
import json

async def test_connection():
    try:
        print("🔗 Sunucuya bağlanmaya çalışılıyor...")
        websocket = await websockets.connect('ws://127.0.0.1:24800')
        print('✅ Sunucuya bağlandı!')
        
        # Test mesajı gönder
        test_msg = {'type': 'test', 'message': 'Test bağlantısı'}
        await websocket.send(json.dumps(test_msg))
        print('📤 Test mesajı gönderildi')
        
        # Yanıt bekle (timeout ile)
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f'📥 Sunucudan yanıt: {response}')
        except asyncio.TimeoutError:
            print('⏰ Sunucudan yanıt gelmedi (timeout)')
        
        await websocket.close()
        print('✅ Bağlantı test edildi ve kapatıldı')
        
    except ConnectionRefusedError:
        print('❌ Sunucuya bağlanılamadı - Sunucu çalışmıyor olabilir')
    except Exception as e:
        print(f'❌ Bağlantı hatası: {e}')

if __name__ == "__main__":
    asyncio.run(test_connection()) 