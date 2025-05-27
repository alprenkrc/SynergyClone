#!/usr/bin/env python3
"""
SynergyClone Server Starter Script - Simple Version
Input capture olmadan sadece WebSocket sunucusu çalıştırır.
"""

import asyncio
import websockets
import json
import time
from typing import Dict, Optional
import signal
import sys

from utils import (
    MessageType, Message, ScreenInfo, get_local_ip, ConfigManager
)

class SimpleSynergyServer:
    def __init__(self):
        self.config_manager = ConfigManager("server_config.json")
        self.config = self.config_manager.load_config()
        
        # Server durumu
        self.running = False
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.server: Optional[websockets.WebSocketServer] = None
        
        # Sunucu ekran bilgisi (varsayılan)
        self.server_screen = ScreenInfo(width=1920, height=1080, name="Server")
        self.client_screens: Dict[str, ScreenInfo] = {}
        
        # Signal handler
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Shutdown signal handler"""
        print("\n🛑 Sunucu kapatılıyor...")
        self.running = False
        sys.exit(0)
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 24800):
        """WebSocket sunucusunu başlatır."""
        try:
            self.server = await websockets.serve(
                self._handle_client,
                host,
                port,
                ping_interval=30,
                ping_timeout=10
            )
            self.running = True
            
            self.log(f"🚀 Sunucu başlatıldı: {host}:{port}")
            self.log(f"🌐 Yerel IP: {get_local_ip()}")
            self.log("📡 WebSocket-only mode - Input capture devre dışı")
            self.log("✅ Sunucu çalışıyor. Çıkmak için Ctrl+C kullanın.")
            
            # Server'ı sürekli çalıştır
            await self.server.wait_closed()
            
        except Exception as e:
            self.log(f"❌ Sunucu başlatma hatası: {e}")
            raise
    
    async def stop_server(self):
        """Sunucuyu durdurur."""
        self.running = False
        
        # Tüm istemcileri bilgilendir
        disconnect_msg = Message(MessageType.DISCONNECT)
        await self._broadcast_message(disconnect_msg)
        
        # Bağlantıları kapat
        for client_id, websocket in self.clients.copy().items():
            try:
                await websocket.close()
            except:
                pass
        
        self.clients.clear()
        
        # Sunucuyu kapat
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        self.log("🛑 Sunucu durduruldu")
    
    async def _handle_client(self, websocket, path):
        """Yeni istemci bağlantısını işler."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.clients[client_id] = websocket
        
        self.log(f"🔗 Yeni istemci bağlandı: {client_id}")
        
        try:
            async for message in websocket:
                try:
                    msg = Message.from_json(message)
                    await self._process_client_message(client_id, msg)
                except json.JSONDecodeError:
                    self.log(f"❌ Geçersiz mesaj formatı: {client_id}")
                except Exception as e:
                    self.log(f"❌ Mesaj işleme hatası: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.log(f"🔌 İstemci bağlantısı kesildi: {client_id}")
        except Exception as e:
            self.log(f"❌ İstemci işleme hatası: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.client_screens:
                del self.client_screens[client_id]
            
            self.log(f"👋 İstemci ayrıldı: {client_id}")
    
    async def _process_client_message(self, client_id: str, message: Message):
        """İstemciden gelen mesajları işler."""
        if message.type == MessageType.HANDSHAKE:
            # İstemci ekran bilgilerini al
            screen_data = message.data.get('screen_info', {})
            screen = ScreenInfo(
                width=screen_data.get('width', 1920),
                height=screen_data.get('height', 1080),
                name=screen_data.get('name', f"Client-{client_id}")
            )
            self.client_screens[client_id] = screen
            
            # Handshake yanıtını gönder
            response = Message(MessageType.HANDSHAKE, {
                'server_screen': {
                    'width': self.server_screen.width,
                    'height': self.server_screen.height,
                    'name': self.server_screen.name
                },
                'status': 'connected',
                'input_capture_available': False
            })
            await self._send_message(client_id, response)
            
            self.log(f"🤝 Handshake tamamlandı: {client_id}")
            
        elif message.type == MessageType.HEARTBEAT:
            # Heartbeat yanıtı gönder
            response = Message(MessageType.HEARTBEAT, {
                'timestamp': time.time()
            })
            await self._send_message(client_id, response)
            
        elif message.type == MessageType.CLIPBOARD:
            # Clipboard mesajlarını diğer istemcilere ilet
            clipboard_text = message.data.get('text', '')
            self.log(f"📋 Clipboard: {clipboard_text[:50]}...")
            
            for other_client_id in self.clients:
                if other_client_id != client_id:
                    await self._send_message(other_client_id, message)
        
        elif message.type in [MessageType.MOUSE_MOVE, MessageType.MOUSE_CLICK, 
                             MessageType.MOUSE_SCROLL, MessageType.KEY_PRESS, 
                             MessageType.KEY_RELEASE]:
            # Input mesajlarını diğer istemcilere ilet
            self.log(f"🎯 {message.type.value} mesajı alındı")
            
            for other_client_id in self.clients:
                if other_client_id != client_id:
                    await self._send_message(other_client_id, message)
    
    async def _send_message(self, client_id: str, message: Message):
        """Belirli bir istemciye mesaj gönderir."""
        if client_id in self.clients:
            try:
                websocket = self.clients[client_id]
                await websocket.send(message.to_json())
            except Exception as e:
                self.log(f"❌ Mesaj gönderme hatası ({client_id}): {e}")
    
    async def _broadcast_message(self, message: Message, exclude_client: str = None):
        """Tüm istemcilere mesaj gönderir."""
        for client_id in self.clients:
            if client_id != exclude_client:
                await self._send_message(client_id, message)
    
    def log(self, message: str):
        """Log mesajı ekler."""
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
    
    def run(self):
        """Uygulamayı çalıştırır."""
        try:
            asyncio.run(self.start_server(
                self.config['server']['host'],
                self.config['server']['port']
            ))
        except KeyboardInterrupt:
            print("\n🛑 Sunucu durduruldu")
        except Exception as e:
            print(f"❌ Sunucu hatası: {e}")

def main():
    """Ana fonksiyon."""
    print("🚀 SynergyClone Server (Simple Mode) başlatılıyor...")
    print("📡 WebSocket-only mode - Input capture devre dışı")
    print("🖥️ İstemciler arası mesaj iletimi için kullanın")
    print("-" * 50)
    
    server = SimpleSynergyServer()
    server.run()

if __name__ == "__main__":
    main() 