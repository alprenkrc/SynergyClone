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
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from input_handler import InputHandler

class SynergyClient:
    def __init__(self):
        self.server_host = '192.168.1.100'  # macOS server IP'sini buraya girin
        self.server_port = 8765
        self.websocket = None
        self.connected = False
        self.input_handler = InputHandler()
        self.controlling = False  # Bu client kontrol ediyor mu?
        self.running = True
        
        # Ekran bilgileri
        self.screen_width, self.screen_height = self.input_handler.get_screen_size()
        self.server_screen_width = 1920  # Varsayılan
        self.server_screen_height = 1080
        
        # GUI
        self.root = None
        self.status_label = None
        self.server_ip_entry = None
        self.server_port_entry = None
        self.log_text = None
        self.connect_button = None
        self.disconnect_button = None
        
        print(f"💻 Client Platform: {platform.system()}")
        print(f"📱 Client Ekran: {self.screen_width}x{self.screen_height}")

    def create_gui(self):
        """GUI oluştur"""
        self.root = tk.Tk()
        self.root.title("SynergyClone Client")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bağlantı ayarları
        connection_frame = ttk.LabelFrame(main_frame, text="Bağlantı Ayarları", padding="10")
        connection_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(connection_frame, text="Server IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.server_ip_entry = ttk.Entry(connection_frame, width=20)
        self.server_ip_entry.insert(0, self.server_host)
        self.server_ip_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(connection_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.server_port_entry = ttk.Entry(connection_frame, width=10)
        self.server_port_entry.insert(0, str(self.server_port))
        self.server_port_entry.grid(row=0, column=3)
        
        # Bağlantı butonları
        button_frame = ttk.Frame(connection_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
        self.connect_button = ttk.Button(button_frame, text="Bağlan", command=self._connect_gui)
        self.connect_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disconnect_button = ttk.Button(button_frame, text="Bağlantıyı Kes", command=self._disconnect_gui, state=tk.DISABLED)
        self.disconnect_button.pack(side=tk.LEFT)
        
        # Manuel kontrol butonları
        control_frame = ttk.LabelFrame(main_frame, text="Manuel Kontrol", padding="10")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        control_buttons_frame = ttk.Frame(control_frame)
        control_buttons_frame.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        ttk.Button(control_buttons_frame, text="Kontrolü Al", command=self._take_control_gui).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_buttons_frame, text="Kontrolü Geri Ver", command=self._release_control_gui).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_buttons_frame, text="Mouse Test", command=self._mouse_test_gui).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_buttons_frame, text="Durum", command=self._show_status_gui).pack(side=tk.LEFT)
        
        # Durum
        status_frame = ttk.LabelFrame(main_frame, text="Durum", padding="10")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Bağlı değil", foreground="red")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Log alanı
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        connection_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Kapanma eventi
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.log("🚀 SynergyClone Client başlatıldı")
        self.log(f"📱 Ekran çözünürlüğü: {self.screen_width}x{self.screen_height}")

    def log(self, message):
        """Log mesajı ekle"""
        if self.log_text:
            self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
            self.log_text.see(tk.END)
        print(message)

    def _connect_gui(self):
        """GUI'den bağlantı başlat"""
        self.server_host = self.server_ip_entry.get().strip()
        try:
            self.server_port = int(self.server_port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz port numarası!")
            return
        
        if not self.server_host:
            messagebox.showerror("Hata", "Server IP adresi boş olamaz!")
            return
        
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
        
        # Asyncio task başlat
        def connect_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.connect_to_server())
            except Exception as e:
                self.log(f"❌ Bağlantı hatası: {e}")
            finally:
                loop.close()
                # GUI'yi güncelle
                self.root.after(0, self._update_connection_status_disconnected)
        
        thread = threading.Thread(target=connect_async, daemon=True)
        thread.start()

    def _disconnect_gui(self):
        """GUI'den bağlantıyı kes"""
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
        self._update_connection_status_disconnected()

    def _take_control_gui(self):
        """GUI'den kontrolü al"""
        self.controlling = True
        self.start_edge_detection()
        self.log("🎮 Kontrol alındı (Manuel)")

    def _release_control_gui(self):
        """GUI'den kontrolü geri ver"""
        if self.websocket and self.controlling:
            asyncio.create_task(self.return_control())
        else:
            self.controlling = False
            self.log("🔄 Kontrol bırakıldı (Manuel)")

    def _mouse_test_gui(self):
        """GUI'den mouse testi"""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        success = self.input_handler.move_mouse(center_x, center_y)
        if success:
            self.log(f"✅ Mouse test başarılı: ({center_x}, {center_y})")
        else:
            self.log("❌ Mouse test başarısız")

    def _show_status_gui(self):
        """GUI'den durum göster"""
        status = "Kontrol ediyor" if self.controlling else "Beklemede"
        connection = "Bağlı" if self.connected else "Bağlı değil"
        self.log(f"📊 Durum: {status}")
        self.log(f"🔗 Bağlantı: {connection}")
        self.log(f"📱 Ekran: {self.screen_width}x{self.screen_height}")

    def _update_connection_status_connected(self):
        """Bağlantı durumunu güncelle - bağlı"""
        if self.status_label:
            self.status_label.config(text="Bağlı", foreground="green")

    def _update_connection_status_disconnected(self):
        """Bağlantı durumunu güncelle - bağlı değil"""
        if self.status_label:
            self.status_label.config(text="Bağlı değil", foreground="red")
        if self.connect_button:
            self.connect_button.config(state=tk.NORMAL)
        if self.disconnect_button:
            self.disconnect_button.config(state=tk.DISABLED)

    def _on_closing(self):
        """Pencere kapatılırken"""
        self.running = False
        if self.websocket:
            try:
                asyncio.create_task(self.websocket.close())
            except:
                pass
        self.root.destroy()

    async def connect_to_server(self):
        """Server'a bağlan"""
        try:
            self.log(f"🔗 Server'a bağlanılıyor: {self.server_host}:{self.server_port}")
            
            self.websocket = await websockets.connect(f"ws://{self.server_host}:{self.server_port}")
            self.connected = True
            
            self.log("✅ Server'a bağlandı!")
            self.root.after(0, self._update_connection_status_connected)
            
            # Client bilgilerini gönder
            await self.send_client_info()
            
            # Mesaj dinleme döngüsü
            await self.message_loop()
            
        except Exception as e:
            self.log(f"❌ Bağlantı hatası: {e}")
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
        self.log(f"📤 Client bilgisi gönderildi: {self.screen_width}x{self.screen_height}")

    async def message_loop(self):
        """Server'dan gelen mesajları dinle"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_server_message(data)
                except json.JSONDecodeError:
                    self.log(f"⚠️ Geçersiz JSON: {message}")
                except Exception as e:
                    self.log(f"⚠️ Mesaj işleme hatası: {e}")
        except websockets.exceptions.ConnectionClosed:
            self.log("❌ Server bağlantısı kesildi")
            self.connected = False
            self.root.after(0, self._update_connection_status_disconnected)

    async def handle_server_message(self, data):
        """Server mesajlarını işle"""
        msg_type = data.get('type')
        
        if msg_type == 'take_control':
            # Kontrol al
            self.controlling = True
            reason = data.get('reason', 'unknown')
            self.log(f"🎮 Kontrol alındı! Sebep: {reason}")
            
            # Eğer mouse pozisyonu belirtilmişse, mouse'u o pozisyona taşı
            if 'mouse_x' in data and 'mouse_y' in data:
                mouse_x = data['mouse_x']
                mouse_y = data['mouse_y']
                self.log(f"🖱️ Mouse pozisyonu ayarlanıyor: ({mouse_x}, {mouse_y})")
                
                # Mouse'u belirtilen pozisyona taşı
                success = self.input_handler.move_mouse(mouse_x, mouse_y)
                if success:
                    self.log(f"✅ Mouse başarıyla taşındı: ({mouse_x}, {mouse_y})")
                else:
                    self.log(f"❌ Mouse taşıma başarısız: ({mouse_x}, {mouse_y})")
            
            # Kenar algılama başlat
            self.start_edge_detection()
            
        elif msg_type == 'release_control':
            # Kontrol bırak
            self.controlling = False
            reason = data.get('reason', 'unknown')
            self.log(f"🔄 Kontrol bırakıldı! Sebep: {reason}")

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
                            self.log(f"🎯 Client kenar algılandı: ({x}, {y})")
                            
                            # Server'a kontrol geri ver
                            asyncio.create_task(self.return_control())
                            break
                    
                    last_pos = current_pos
                    time.sleep(0.05)
                    
                except Exception as e:
                    self.log(f"⚠️ Kenar algılama hatası: {e}")
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
            self.log("📤 Kontrol server'a geri verildi")
        except Exception as e:
            self.log(f"⚠️ Kontrol geri verme hatası: {e}")

    def run(self):
        """Client'ı çalıştır"""
        # Input handler'ı başlat
        if not self.input_handler.start():
            print("❌ Input handler başlatılamadı!")
            return
        
        # GUI oluştur ve çalıştır
        self.create_gui()
        self.root.mainloop()
        
        # Temizlik
        self.running = False
        self.input_handler.stop()

if __name__ == "__main__":
    client = SynergyClient()
    client.run() 