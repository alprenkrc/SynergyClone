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
import tkinter as tk
from tkinter import ttk, scrolledtext
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
        
        # GUI
        self.root = None
        self.status_label = None
        self.client_count_label = None
        self.log_text = None
        self.start_button = None
        self.stop_button = None
        
    def create_gui(self):
        """GUI oluştur"""
        self.root = tk.Tk()
        self.root.title("SynergyClone Server")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Server ayarları
        server_frame = ttk.LabelFrame(main_frame, text="Server Ayarları", padding="10")
        server_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Gerçek IP adresini al
        real_ip = self.get_local_ip()
        ttk.Label(server_frame, text=f"Server IP: {real_ip}:{self.port}").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(server_frame, text=f"Platform: {platform.system()}").grid(row=1, column=0, sticky=tk.W)
        
        # Server kontrol butonları
        button_frame = ttk.Frame(server_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0))
        
        self.start_button = ttk.Button(button_frame, text="Server Başlat", command=self._start_server_gui)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Server Durdur", command=self._stop_server_gui, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Manuel kontrol butonları
        control_frame = ttk.LabelFrame(main_frame, text="Manuel Kontrol", padding="10")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        control_buttons_frame = ttk.Frame(control_frame)
        control_buttons_frame.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        ttk.Button(control_buttons_frame, text="Windows'a Geç", command=self._switch_to_client_gui).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_buttons_frame, text="macOS'a Geç", command=self._switch_to_local_gui).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_buttons_frame, text="Durum Göster", command=self._show_status_gui).pack(side=tk.LEFT)
        
        # Durum bilgileri
        status_frame = ttk.LabelFrame(main_frame, text="Durum", padding="10")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Server durduruldu", foreground="red")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.client_count_label = ttk.Label(status_frame, text="Bağlı client: 0")
        self.client_count_label.grid(row=1, column=0, sticky=tk.W)
        
        # Log alanı
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Kapanma eventi
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.log("🚀 SynergyClone Server GUI başlatıldı")
        self.log(f"📱 Server IP: {real_ip}:{self.port}")

    def get_local_ip(self):
        """Gerçek local IP adresini al"""
        try:
            import socket
            # Google DNS'e bağlanmaya çalışarak local IP'yi al
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                # Alternatif yöntem
                import socket
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                if ip.startswith("127."):
                    # localhost ise, network interface'leri kontrol et
                    import subprocess
                    if platform.system() == "Darwin":  # macOS
                        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if 'inet ' in line and '127.0.0.1' not in line and 'inet 169.254' not in line:
                                parts = line.strip().split()
                                for i, part in enumerate(parts):
                                    if part == 'inet' and i + 1 < len(parts):
                                        return parts[i + 1]
                return ip
            except Exception:
                return "localhost"

    def log(self, message):
        """Log mesajı ekle"""
        if self.log_text:
            self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
            self.log_text.see(tk.END)
        print(message)

    def _start_server_gui(self):
        """GUI'den server başlat"""
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Server başlatılıyor...", foreground="orange")
        
        # Asyncio task başlat
        def start_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.start_server())
            except Exception as e:
                self.log(f"❌ Server hatası: {e}")
            finally:
                loop.close()
                # GUI'yi güncelle
                self.root.after(0, self._update_server_status_stopped)
        
        thread = threading.Thread(target=start_async, daemon=True)
        thread.start()

    def _stop_server_gui(self):
        """GUI'den server durdur"""
        self.running = False
        self._update_server_status_stopped()

    def _switch_to_client_gui(self):
        """GUI'den Windows'a geç"""
        self.switch_to_client()

    def _switch_to_local_gui(self):
        """GUI'den macOS'a geç"""
        self.switch_to_local()

    def _show_status_gui(self):
        """GUI'den durum göster"""
        status = "macOS (Local)" if self.controlling_local else "Windows (Client)"
        client_count = len(self.clients)
        self.log(f"📊 Durum: {status}")
        self.log(f"🔗 Bağlı client sayısı: {client_count}")
        
        if self.client_info:
            for addr, info in self.client_info.items():
                self.log(f"   📱 {addr}: {info['screen_width']}x{info['screen_height']}")

    def _update_server_status_running(self):
        """Server durumunu güncelle - çalışıyor"""
        if self.status_label:
            self.status_label.config(text="Server çalışıyor", foreground="green")

    def _update_server_status_stopped(self):
        """Server durumunu güncelle - durduruldu"""
        if self.status_label:
            self.status_label.config(text="Server durduruldu", foreground="red")
        if self.start_button:
            self.start_button.config(state=tk.NORMAL)
        if self.stop_button:
            self.stop_button.config(state=tk.DISABLED)

    def _update_client_count(self):
        """Client sayısını güncelle"""
        if self.client_count_label:
            count = len(self.clients)
            self.client_count_label.config(text=f"Bağlı client: {count}")

    def _on_closing(self):
        """Pencere kapatılırken"""
        self.running = False
        self.root.destroy()

    async def register_client(self, websocket, path):
        """Yeni client kaydı"""
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        self.log(f"✅ Client bağlandı: {client_addr}")
        self.root.after(0, self._update_client_count)
        
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            if client_addr in self.client_info:
                del self.client_info[client_addr]
            self.log(f"❌ Client ayrıldı: {client_addr}")
            self.root.after(0, self._update_client_count)

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
            self.log(f"⚠️ Mesaj gönderme hatası: {e}")
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
                self.log(f"📱 Client bilgisi alındı: {data['screen_width']}x{data['screen_height']}")
                
            elif msg_type == 'control_returned':
                # Kontrol geri döndü
                self.controlling_local = True
                self.log("🔄 Kontrol server'a geri döndü")
                
        except json.JSONDecodeError:
            self.log(f"⚠️ Geçersiz JSON mesajı: {message}")
        except Exception as e:
            self.log(f"⚠️ Mesaj işleme hatası: {e}")

    def switch_to_client(self):
        """Manuel olarak client'a geç"""
        if not self.controlling_local:
            self.log("⚠️ Zaten client kontrolünde")
            return
            
        if not self.clients:
            self.log("⚠️ Bağlı client yok")
            return
            
        self.controlling_local = False
        self.log("🎮 Manuel olarak client'a geçildi")
        
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
            self.log("⚠️ Zaten local kontrolünde")
            return
            
        self.controlling_local = True
        self.log("🎮 Manuel olarak local'e geçildi")
        
        # Client'a kontrol bırakma mesajı gönder
        message = {
            'type': 'release_control',
            'reason': 'manual_switch'
        }
        
        # Asyncio loop'ta çalıştır
        asyncio.create_task(self.send_to_clients(message))

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
                            self.log(f"🎯 Kenar algılandı: ({x}, {y}) - Ekran: {screen_width}x{screen_height}")
                            
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
                                self.log(f"📤 Client'a kontrol gönderildi")
                    
                    last_pos = current_pos
                    time.sleep(0.05)  # 50ms bekle
                    
                except Exception as e:
                    self.log(f"⚠️ Kenar algılama hatası: {e}")
                    time.sleep(1)
        
        # Kenar algılama thread'ini başlat
        edge_thread = threading.Thread(target=edge_detection_thread, daemon=True)
        edge_thread.start()

    async def start_server(self):
        """Server'ı başlat"""
        self.log(f"🚀 SynergyClone Server başlatılıyor...")
        self.log(f"📡 Adres: {self.host}:{self.port}")
        self.log(f"💻 Platform: {platform.system()}")
        
        # Input handler'ı başlat
        if not self.input_handler.start():
            self.log("❌ Input handler başlatılamadı!")
            return
        
        # Mouse kenar algılamayı başlat
        self.mouse_edge_detection()
        
        # WebSocket server'ı başlat
        async def handle_client(websocket, path):
            await asyncio.gather(
                self.register_client(websocket, path),
                self.handle_messages(websocket)
            )
        
        async with websockets.serve(handle_client, self.host, self.port):
            self.log("✅ Server başlatıldı! Clientların bağlanması bekleniyor...")
            self.root.after(0, self._update_server_status_running)
            
            # Server'ı çalışır durumda tut
            try:
                while self.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                self.log("\n👋 Server kapatılıyor...")
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
            self.log(f"⚠️ Mesaj dinleme hatası: {e}")

    def run(self):
        """Server'ı çalıştır"""
        # GUI oluştur ve çalıştır
        self.create_gui()
        self.root.mainloop()
        
        # Temizlik
        self.running = False

if __name__ == "__main__":
    server = SynergyServer()
    server.run() 