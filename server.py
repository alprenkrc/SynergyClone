#!/usr/bin/env python3
"""
SynergyClone Server - Mouse ve keyboard paylaşımı için server
"""

import asyncio
import websockets
import json
import threading
import time
import platform
from input_handler import InputHandler

class SynergyServer:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.input_handler = InputHandler()
        self.controlling_local = True  # Başlangıçta local kontrolde
        self.screen_width = 1920  # Varsayılan değerler
        self.screen_height = 1080
        self.client_info = {}  # Client bilgileri
        self.running = True
        
    async def register_client(self, websocket, path):
        """Yeni client kaydı"""
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"✅ Client bağlandı: {client_addr}")
        
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            if client_addr in self.client_info:
                del self.client_info[client_addr]
            print(f"❌ Client ayrıldı: {client_addr}")

    async def send_to_clients(self, message):
        """Tüm clientlara mesaj gönder"""
        if self.clients:
            # Thread-safe mesaj gönderimi
            await asyncio.gather(
                *[self.safe_send(client, message) for client in self.clients.copy()],
                return_exceptions=True
            )

    async def safe_send(self, websocket, message):
        """Güvenli mesaj gönderimi"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            # Client bağlantısı kesilmiş, listeden çıkar
            self.clients.discard(websocket)
        except Exception as e:
            print(f"⚠️ Mesaj gönderme hatası: {e}")
            self.clients.discard(websocket)

    async def handle_client_message(self, websocket, message):
        """Client mesajlarını işle"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'client_info':
                # Client bilgilerini kaydet
                client_addr = websocket.remote_address
                self.client_info[client_addr] = data
                print(f"📱 Client bilgisi alındı: {data['screen_width']}x{data['screen_height']}")
                
            elif msg_type == 'control_returned':
                # Kontrol geri döndü
                self.controlling_local = True
                print("🔄 Kontrol server'a geri döndü")
                
        except json.JSONDecodeError:
            print(f"⚠️ Geçersiz JSON mesajı: {message}")
        except Exception as e:
            print(f"⚠️ Mesaj işleme hatası: {e}")

    def switch_to_client(self):
        """Manuel olarak client'a geç"""
        if not self.controlling_local:
            print("⚠️ Zaten client kontrolünde")
            return
            
        if not self.clients:
            print("⚠️ Bağlı client yok")
            return
            
        self.controlling_local = False
        print("🎮 Manuel olarak client'a geçildi")
        
        # Client'a kontrol mesajı gönder
        message = {
            'type': 'take_control',
            'reason': 'manual_switch'
        }
        
        # Asyncio loop'ta çalıştır
        asyncio.create_task(self.send_to_clients(message))

    def switch_to_local(self):
        """Manuel olarak local'e geç"""
        if self.controlling_local:
            print("⚠️ Zaten local kontrolünde")
            return
            
        self.controlling_local = True
        print("🎮 Manuel olarak local'e geçildi")
        
        # Client'a kontrol bırakma mesajı gönder
        message = {
            'type': 'release_control',
            'reason': 'manual_switch'
        }
        
        # Asyncio loop'ta çalıştır
        asyncio.create_task(self.send_to_clients(message))

    def start_manual_controls(self):
        """Manuel kontrol butonları"""
        def manual_control_thread():
            print("\n" + "="*50)
            print("🎮 MANUEL KONTROL BUTONLARI")
            print("="*50)
            print("1 - Windows'a geç (Client'a kontrol ver)")
            print("2 - macOS'a geç (Local kontrole dön)")
            print("3 - Durum göster")
            print("q - Çıkış")
            print("="*50)
            
            while self.running:
                try:
                    choice = input("\nSeçiminiz (1/2/3/q): ").strip().lower()
                    
                    if choice == '1':
                        print("🔄 Windows'a geçiliyor...")
                        self.switch_to_client()
                        
                    elif choice == '2':
                        print("🔄 macOS'a geçiliyor...")
                        self.switch_to_local()
                        
                    elif choice == '3':
                        status = "macOS (Local)" if self.controlling_local else "Windows (Client)"
                        client_count = len(self.clients)
                        print(f"📊 Durum: {status}")
                        print(f"🔗 Bağlı client sayısı: {client_count}")
                        
                        if self.client_info:
                            for addr, info in self.client_info.items():
                                print(f"   📱 {addr}: {info['screen_width']}x{info['screen_height']}")
                        
                    elif choice == 'q':
                        print("👋 Çıkılıyor...")
                        self.running = False
                        break
                        
                    else:
                        print("❌ Geçersiz seçim! (1/2/3/q)")
                        
                except KeyboardInterrupt:
                    print("\n👋 Çıkılıyor...")
                    self.running = False
                    break
                except Exception as e:
                    print(f"⚠️ Hata: {e}")
        
        # Manuel kontrol thread'ini başlat
        manual_thread = threading.Thread(target=manual_control_thread, daemon=True)
        manual_thread.start()

    def mouse_edge_detection(self):
        """Mouse kenar algılama"""
        def edge_detection_thread():
            last_pos = None
            edge_threshold = 5  # Kenardan kaç pixel uzakta algılansın
            
            while self.running:
                try:
                    if not self.controlling_local:
                        time.sleep(0.1)
                        continue
                    
                    # Mouse pozisyonunu al
                    current_pos = self.input_handler.get_mouse_position()
                    if current_pos is None:
                        time.sleep(0.1)
                        continue
                    
                    x, y = current_pos
                    
                    # Ekran boyutlarını al
                    screen_width, screen_height = self.input_handler.get_screen_size()
                    
                    # Kenar kontrolü
                    at_right_edge = x >= screen_width - edge_threshold
                    at_left_edge = x <= edge_threshold
                    at_top_edge = y <= edge_threshold
                    at_bottom_edge = y >= screen_height - edge_threshold
                    
                    # Eğer kenardaysa ve hareket ettiyse
                    if (at_right_edge or at_left_edge or at_top_edge or at_bottom_edge):
                        if last_pos and current_pos != last_pos:
                            print(f"🎯 Kenar algılandı: ({x}, {y}) - Ekran: {screen_width}x{screen_height}")
                            
                            # Client'a geç
                            if self.clients:
                                self.controlling_local = False
                                
                                # Koordinatları client ekranına dönüştür
                                if self.client_info:
                                    client_addr = list(self.client_info.keys())[0]
                                    client_screen = self.client_info[client_addr]
                                    
                                    # Kenar pozisyonuna göre client'taki pozisyonu hesapla
                                    if at_right_edge:
                                        client_x = 10  # Sol kenara
                                        client_y = int(y * client_screen['screen_height'] / screen_height)
                                    elif at_left_edge:
                                        client_x = client_screen['screen_width'] - 10  # Sağ kenara
                                        client_y = int(y * client_screen['screen_height'] / screen_height)
                                    elif at_top_edge:
                                        client_x = int(x * client_screen['screen_width'] / screen_width)
                                        client_y = client_screen['screen_height'] - 10  # Alt kenara
                                    else:  # at_bottom_edge
                                        client_x = int(x * client_screen['screen_width'] / screen_width)
                                        client_y = 10  # Üst kenara
                                    
                                    message = {
                                        'type': 'take_control',
                                        'mouse_x': client_x,
                                        'mouse_y': client_y,
                                        'reason': 'edge_detection'
                                    }
                                else:
                                    message = {
                                        'type': 'take_control',
                                        'reason': 'edge_detection'
                                    }
                                
                                # Asyncio loop'ta mesaj gönder
                                asyncio.create_task(self.send_to_clients(message))
                                print(f"📤 Client'a kontrol gönderildi")
                    
                    last_pos = current_pos
                    time.sleep(0.05)  # 50ms bekle
                    
                except Exception as e:
                    print(f"⚠️ Kenar algılama hatası: {e}")
                    time.sleep(1)
        
        # Kenar algılama thread'ini başlat
        edge_thread = threading.Thread(target=edge_detection_thread, daemon=True)
        edge_thread.start()

    async def start_server(self):
        """Server'ı başlat"""
        print(f"🚀 SynergyClone Server başlatılıyor...")
        print(f"📡 Adres: {self.host}:{self.port}")
        print(f"💻 Platform: {platform.system()}")
        
        # Input handler'ı başlat
        if not self.input_handler.start():
            print("❌ Input handler başlatılamadı!")
            return
        
        # Manuel kontrolleri başlat
        self.start_manual_controls()
        
        # Mouse kenar algılamayı başlat
        self.mouse_edge_detection()
        
        # WebSocket server'ı başlat
        async def handle_client(websocket, path):
            await asyncio.gather(
                self.register_client(websocket, path),
                self.handle_messages(websocket)
            )
        
        async with websockets.serve(handle_client, self.host, self.port):
            print("✅ Server başlatıldı! Clientların bağlanması bekleniyor...")
            
            # Server'ı çalışır durumda tut
            try:
                while self.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Server kapatılıyor...")
            finally:
                self.running = False
                self.input_handler.stop()

    async def handle_messages(self, websocket):
        """Client mesajlarını dinle"""
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"⚠️ Mesaj dinleme hatası: {e}")

if __name__ == "__main__":
    server = SynergyServer()
    asyncio.run(server.start_server()) 