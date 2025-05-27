#!/usr/bin/env python3
"""
SynergyClone Client - Windows bilgisayar uygulaması
"""

import asyncio
import websockets
import json
import threading
import time
import platform
from input_handler import InputHandler

class SynergyClient:
    def __init__(self, server_host='192.168.1.100', server_port=8765):
        self.server_host = server_host
        self.server_port = server_port
        self.websocket = None
        self.connected = False
        self.input_handler = InputHandler()
        self.controlling = False  # Bu client kontrol ediyor mu?
        self.running = True
        
        # Ekran bilgileri
        self.screen_width, self.screen_height = self.input_handler.get_screen_size()
        self.server_screen_width = 1920  # Varsayılan
        self.server_screen_height = 1080
        
        print(f"💻 Client Platform: {platform.system()}")
        print(f"📱 Client Ekran: {self.screen_width}x{self.screen_height}")

    async def connect_to_server(self):
        """Server'a bağlan"""
        try:
            print(f"🔗 Server'a bağlanılıyor: {self.server_host}:{self.server_port}")
            
            self.websocket = await websockets.connect(f"ws://{self.server_host}:{self.server_port}")
            self.connected = True
            
            print("✅ Server'a bağlandı!")
            
            # Client bilgilerini gönder
            await self.send_client_info()
            
            # Mesaj dinleme döngüsü
            await self.message_loop()
            
        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            self.connected = False

    async def send_client_info(self):
        """Client bilgilerini server'a gönder"""
        if not self.websocket:
            return
            
        message = {
            'type': 'client_info',
            'screen_width': self.screen_width,
            'screen_height': self.screen_height,
            'platform': platform.system()
        }
        
        await self.websocket.send(json.dumps(message))
        print(f"📤 Client bilgisi gönderildi: {self.screen_width}x{self.screen_height}")

    async def message_loop(self):
        """Server'dan gelen mesajları dinle"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_server_message(data)
                except json.JSONDecodeError:
                    print(f"⚠️ Geçersiz JSON: {message}")
                except Exception as e:
                    print(f"⚠️ Mesaj işleme hatası: {e}")
        except websockets.exceptions.ConnectionClosed:
            print("❌ Server bağlantısı kesildi")
            self.connected = False

    async def handle_server_message(self, data):
        """Server mesajlarını işle"""
        msg_type = data.get('type')
        
        if msg_type == 'take_control':
            # Kontrol al
            self.controlling = True
            reason = data.get('reason', 'unknown')
            print(f"🎮 Kontrol alındı! Sebep: {reason}")
            
            # Eğer mouse pozisyonu belirtilmişse, mouse'u o pozisyona taşı
            if 'mouse_x' in data and 'mouse_y' in data:
                mouse_x = data['mouse_x']
                mouse_y = data['mouse_y']
                print(f"🖱️ Mouse pozisyonu ayarlanıyor: ({mouse_x}, {mouse_y})")
                
                # Mouse'u belirtilen pozisyona taşı
                success = self.input_handler.move_mouse(mouse_x, mouse_y)
                if success:
                    print(f"✅ Mouse başarıyla taşındı: ({mouse_x}, {mouse_y})")
                else:
                    print(f"❌ Mouse taşıma başarısız: ({mouse_x}, {mouse_y})")
            
            # Kenar algılama başlat
            self.start_edge_detection()
            
        elif msg_type == 'release_control':
            # Kontrol bırak
            self.controlling = False
            reason = data.get('reason', 'unknown')
            print(f"🔄 Kontrol bırakıldı! Sebep: {reason}")
            
        elif msg_type == 'mouse_move':
            if self.controlling:
                x = data.get('x', 0)
                y = data.get('y', 0)
                
                # Koordinat dönüşümü (server ekranından client ekranına)
                client_x = int(x * self.screen_width / self.server_screen_width)
                client_y = int(y * self.screen_height / self.server_screen_height)
                
                print(f"🖱️ Mouse hareket: Server({x},{y}) -> Client({client_x},{client_y})")
                self.input_handler.move_mouse(client_x, client_y)
                
        elif msg_type == 'mouse_click':
            if self.controlling:
                button = data.get('button', 'left')
                action = data.get('action', 'click')
                x = data.get('x', 0)
                y = data.get('y', 0)
                
                # Koordinat dönüşümü
                client_x = int(x * self.screen_width / self.server_screen_width)
                client_y = int(y * self.screen_height / self.server_screen_height)
                
                print(f"🖱️ Mouse {action}: {button} at ({client_x},{client_y})")
                self.input_handler.click_mouse(client_x, client_y, button, action)
                
        elif msg_type == 'mouse_scroll':
            if self.controlling:
                x = data.get('x', 0)
                y = data.get('y', 0)
                dx = data.get('dx', 0)
                dy = data.get('dy', 0)
                
                print(f"🖱️ Mouse scroll: ({dx},{dy}) at ({x},{y})")
                self.input_handler.scroll_mouse(x, y, dx, dy)

    def start_edge_detection(self):
        """Kenar algılama başlat"""
        def edge_detection_thread():
            last_pos = None
            edge_threshold = 5
            
            while self.controlling and self.running:
                try:
                    # Mouse pozisyonunu al
                    current_pos = self.input_handler.get_mouse_position()
                    if current_pos is None:
                        time.sleep(0.1)
                        continue
                    
                    x, y = current_pos
                    
                    # Kenar kontrolü
                    at_left_edge = x <= edge_threshold
                    at_right_edge = x >= self.screen_width - edge_threshold
                    at_top_edge = y <= edge_threshold
                    at_bottom_edge = y >= self.screen_height - edge_threshold
                    
                    # Eğer kenardaysa ve hareket ettiyse
                    if (at_left_edge or at_right_edge or at_top_edge or at_bottom_edge):
                        if last_pos and current_pos != last_pos:
                            print(f"🎯 Client kenar algılandı: ({x}, {y})")
                            
                            # Server'a kontrol geri ver
                            asyncio.create_task(self.return_control())
                            break
                    
                    last_pos = current_pos
                    time.sleep(0.05)
                    
                except Exception as e:
                    print(f"⚠️ Kenar algılama hatası: {e}")
                    time.sleep(1)
        
        # Thread başlat
        edge_thread = threading.Thread(target=edge_detection_thread, daemon=True)
        edge_thread.start()

    async def return_control(self):
        """Kontrolü server'a geri ver"""
        if not self.websocket or not self.controlling:
            return
            
        self.controlling = False
        
        message = {
            'type': 'control_returned',
            'reason': 'edge_detection'
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print("📤 Kontrol server'a geri verildi")
        except Exception as e:
            print(f"⚠️ Kontrol geri verme hatası: {e}")

    def start_manual_controls(self):
        """Manuel kontrol butonları"""
        def manual_control_thread():
            print("\n" + "="*50)
            print("🎮 MANUEL KONTROL BUTONLARI (CLIENT)")
            print("="*50)
            print("1 - Kontrolü al (Test)")
            print("2 - Kontrolü geri ver")
            print("3 - Durum göster")
            print("4 - Mouse test (Windows API)")
            print("q - Çıkış")
            print("="*50)
            
            while self.running:
                try:
                    choice = input("\nSeçiminiz (1/2/3/4/q): ").strip().lower()
                    
                    if choice == '1':
                        print("🎮 Kontrol alınıyor...")
                        self.controlling = True
                        self.start_edge_detection()
                        
                    elif choice == '2':
                        print("🔄 Kontrol geri veriliyor...")
                        asyncio.create_task(self.return_control())
                        
                    elif choice == '3':
                        status = "Kontrol ediyor" if self.controlling else "Beklemede"
                        connection = "Bağlı" if self.connected else "Bağlı değil"
                        print(f"📊 Durum: {status}")
                        print(f"🔗 Bağlantı: {connection}")
                        print(f"📱 Ekran: {self.screen_width}x{self.screen_height}")
                        
                    elif choice == '4':
                        print("🧪 Windows API mouse testi...")
                        # Mouse'u ekranın ortasına taşı
                        center_x = self.screen_width // 2
                        center_y = self.screen_height // 2
                        success = self.input_handler.move_mouse(center_x, center_y)
                        if success:
                            print(f"✅ Mouse başarıyla taşındı: ({center_x}, {center_y})")
                        else:
                            print(f"❌ Mouse taşıma başarısız")
                        
                    elif choice == 'q':
                        print("👋 Çıkılıyor...")
                        self.running = False
                        break
                        
                    else:
                        print("❌ Geçersiz seçim! (1/2/3/4/q)")
                        
                except KeyboardInterrupt:
                    print("\n👋 Çıkılıyor...")
                    self.running = False
                    break
                except Exception as e:
                    print(f"⚠️ Hata: {e}")
        
        # Manuel kontrol thread'ini başlat
        manual_thread = threading.Thread(target=manual_control_thread, daemon=True)
        manual_thread.start()

    async def start_client(self):
        """Client'ı başlat"""
        print(f"🚀 SynergyClone Client başlatılıyor...")
        print(f"🎯 Server: {self.server_host}:{self.server_port}")
        
        # Input handler'ı başlat
        if not self.input_handler.start():
            print("❌ Input handler başlatılamadı!")
            return
        
        # Manuel kontrolleri başlat
        self.start_manual_controls()
        
        try:
            # Server'a bağlan
            await self.connect_to_server()
        except KeyboardInterrupt:
            print("\n👋 Client kapatılıyor...")
        finally:
            self.running = False
            self.input_handler.stop()
            if self.websocket:
                await self.websocket.close()

if __name__ == "__main__":
    # Server IP'sini buradan değiştirebilirsiniz
    SERVER_IP = "192.168.1.100"  # macOS'un IP adresi
    SERVER_PORT = 8765
    
    client = SynergyClient(SERVER_IP, SERVER_PORT)
    asyncio.run(client.start_client()) 