#!/usr/bin/env python3
"""
SynergyClone Server - Ana bilgisayar uygulaması
Mouse ve klavye olaylarını yakalar ve bağlı istemcilere iletir.
"""

import asyncio
import websockets
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Dict, Set, Optional
import logging

from utils import (
    MessageType, Message, ScreenInfo, MouseEvent, KeyEvent,
    get_local_ip, ConfigManager
)
from input_handler import InputHandler, ScreenManager

class SynergyServer:
    def __init__(self):
        self.config_manager = ConfigManager("server_config.json")
        self.config = self.config_manager.load_config()
        
        # Server durumu
        self.running = False
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.server: Optional[websockets.WebSocketServer] = None
        
        # Input handler ve screen manager
        self.input_handler = InputHandler()
        self.screen_manager = ScreenManager()
        
        # Sunucu ekran bilgisi
        self.server_screen = self.screen_manager.get_primary_screen()
        
        # Client ekranları ve düzeni
        self.client_screens: Dict[str, ScreenInfo] = {}
        self.screen_layout = []  # Ekranların düzeni
        
        # Mouse tracking
        self.last_mouse_pos = (0, 0)
        self.current_screen = "server"  # Hangi ekranda mouse var
        self.mouse_moved_to_client = False
        
        # Callback'leri ayarla
        self._setup_input_callbacks()
        
        # GUI
        self.root = None
        self.status_label = None
        self.clients_listbox = None
        self.log_text = None
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_input_callbacks(self):
        """Input handler callback'lerini ayarlar."""
        self.input_handler.on_mouse_move = self._handle_mouse_move
        self.input_handler.on_mouse_click = self._handle_mouse_click
        self.input_handler.on_mouse_scroll = self._handle_mouse_scroll
        self.input_handler.on_key_press = self._handle_key_press
        self.input_handler.on_key_release = self._handle_key_release
    
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
            
            self.log(f"Sunucu başlatıldı: {host}:{port}")
            self.log(f"Yerel IP: {get_local_ip()}")
            
            # Input yakalamayı başlat (güvenli şekilde)
            try:
                self.input_handler.start_capture()
                self.log("Input yakalama başarıyla başlatıldı")
            except Exception as e:
                self.log(f"⚠️ Input yakalama başlatılamadı: {e}")
                self.log("⚠️ Sunucu temel WebSocket işlevselliği ile çalışacak")
                self.log("⚠️ macOS'ta Accessibility izinleri gerekli olabilir")
            
            # Server'ı sürekli çalıştır
            await self.server.wait_closed()
            
        except Exception as e:
            self.log(f"Sunucu başlatma hatası: {e}")
            raise
    
    async def stop_server(self):
        """Sunucuyu durdurur."""
        self.running = False
        
        # Input yakalamayı durdur (güvenli şekilde)
        try:
            self.input_handler.stop_capture()
        except Exception as e:
            self.log(f"Input yakalama durdurma hatası: {e}")
        
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
        
        self.log("Sunucu durduruldu")
    
    async def _handle_client(self, websocket, path):
        """Yeni istemci bağlantısını işler."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.clients[client_id] = websocket
        
        self.log(f"Yeni istemci bağlandı: {client_id}")
        self._update_clients_list()
        
        try:
            # Handshake mesajını bekle
            async for message in websocket:
                try:
                    msg = Message.from_json(message)
                    await self._process_client_message(client_id, msg)
                except json.JSONDecodeError:
                    self.log(f"Geçersiz mesaj formatı: {client_id}")
                except Exception as e:
                    self.log(f"Mesaj işleme hatası: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.log(f"İstemci bağlantısı kesildi: {client_id}")
        except Exception as e:
            self.log(f"İstemci işleme hatası: {e}")
        finally:
            # İstemciyi listeden çıkar
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.client_screens:
                del self.client_screens[client_id]
            
            self._update_clients_list()
            self.log(f"İstemci ayrıldı: {client_id}")
    
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
                'status': 'connected'
            })
            await self._send_message(client_id, response)
            
            self.log(f"Handshake tamamlandı: {client_id}")
            
        elif message.type == MessageType.HEARTBEAT:
            # Heartbeat yanıtı gönder
            response = Message(MessageType.HEARTBEAT)
            await self._send_message(client_id, response)
            
        elif message.type == MessageType.CLIPBOARD:
            # Clipboard içeriğini diğer istemcilere ilet
            clipboard_text = message.data.get('text', '')
            self.input_handler.set_clipboard_text(clipboard_text)
            
            # Diğer istemcilere de gönder
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
                self.log(f"Mesaj gönderme hatası ({client_id}): {e}")
    
    async def _broadcast_message(self, message: Message, exclude_client: str = None):
        """Tüm istemcilere mesaj gönderir."""
        for client_id in self.clients:
            if client_id != exclude_client:
                await self._send_message(client_id, message)
    
    def _handle_mouse_move(self, event: MouseEvent):
        """Mouse hareket olayını işler."""
        if not self.running or not self.clients:
            return
        
        self.last_mouse_pos = (event.x, event.y)
        
        # Eğer mouse sunucu ekranından çıktıysa istemciye gönder
        if self._should_forward_to_client(event.x, event.y):
            # Mouse'u hangi istemciye göndereceğimizi belirle
            target_client = self._get_target_client_for_position(event.x, event.y)
            
            if target_client and target_client != self.current_screen:
                self.current_screen = target_client
                self.input_handler.set_suppress_input(True)
                self.mouse_moved_to_client = True
                self.log(f"Mouse client'a geçti: {target_client}")
            
            # Mouse olayını istemciye gönder
            if target_client and target_client in self.clients:
                msg = Message(MessageType.MOUSE_MOVE, {
                    'x': event.x,
                    'y': event.y
                })
                asyncio.create_task(self._send_message(target_client, msg))
        else:
            # Mouse sunucu ekranına geri döndü
            if self.current_screen != "server":
                self.current_screen = "server"
                self.input_handler.set_suppress_input(False)
                self.mouse_moved_to_client = False
                self.log("Mouse sunucuya geri döndü")
    
    def _handle_mouse_click(self, event: MouseEvent):
        """Mouse tıklama olayını işler."""
        if not self.running or not self.clients or not self.mouse_moved_to_client:
            return
        
        msg = Message(MessageType.MOUSE_CLICK, {
            'x': event.x,
            'y': event.y,
            'button': event.button,
            'pressed': event.pressed
        })
        
        if self.current_screen != "server":
            asyncio.create_task(self._send_message(self.current_screen, msg))
    
    def _handle_mouse_scroll(self, event: MouseEvent):
        """Mouse scroll olayını işler."""
        if not self.running or not self.clients or not self.mouse_moved_to_client:
            return
        
        msg = Message(MessageType.MOUSE_SCROLL, {
            'x': event.x,
            'y': event.y,
            'scroll_x': event.scroll_x,
            'scroll_y': event.scroll_y
        })
        
        if self.current_screen != "server":
            asyncio.create_task(self._send_message(self.current_screen, msg))
    
    def _handle_key_press(self, event: KeyEvent):
        """Klavye tuşu basma olayını işler."""
        if not self.running or not self.clients or not self.mouse_moved_to_client:
            return
        
        msg = Message(MessageType.KEY_PRESS, {
            'key': event.key,
            'pressed': event.pressed
        })
        
        if self.current_screen != "server":
            asyncio.create_task(self._send_message(self.current_screen, msg))
    
    def _handle_key_release(self, event: KeyEvent):
        """Klavye tuşu bırakma olayını işler."""
        if not self.running or not self.clients or not self.mouse_moved_to_client:
            return
        
        msg = Message(MessageType.KEY_RELEASE, {
            'key': event.key,
            'pressed': event.pressed
        })
        
        if self.current_screen != "server":
            asyncio.create_task(self._send_message(self.current_screen, msg))
    
    def _should_forward_to_client(self, x: int, y: int) -> bool:
        """Mouse'un istemciye gönderilip gönderilmeyeceğini belirler."""
        # Basit mantık: mouse ekran sınırlarından çıkarsa istemciye gönder
        screen = self.server_screen
        
        # Sağ kenardan çıktı mı?
        if x >= screen.width - 5:
            return True
        
        # Sol kenardan çıktı mı?
        if x <= 5:
            return True
        
        return False
    
    def _get_target_client_for_position(self, x: int, y: int) -> Optional[str]:
        """Verilen pozisyon için hedef istemciyi belirler."""
        # Basit mantık: ilk bağlı istemciyi seç
        return list(self.clients.keys())[0] if self.clients else None
    
    def log(self, message: str):
        """Log mesajı ekler."""
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        # GUI log'a ekle
        if self.log_text:
            try:
                self.log_text.insert(tk.END, log_msg + "\n")
                self.log_text.see(tk.END)
            except:
                pass
    
    def _update_clients_list(self):
        """İstemci listesini günceller."""
        if self.clients_listbox:
            try:
                self.clients_listbox.delete(0, tk.END)
                for client_id in self.clients:
                    screen_info = self.client_screens.get(client_id, None)
                    display_text = client_id
                    if screen_info:
                        display_text += f" ({screen_info.width}x{screen_info.height})"
                    self.clients_listbox.insert(tk.END, display_text)
            except:
                pass
    
    def create_gui(self):
        """GUI oluşturur."""
        self.root = tk.Tk()
        self.root.title("SynergyClone Server")
        self.root.geometry("600x500")
        
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Sunucu bilgileri
        info_frame = ttk.LabelFrame(main_frame, text="Sunucu Bilgileri", padding="5")
        info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(info_frame, text=f"IP Adresi: {get_local_ip()}").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=f"Port: {self.config['server']['port']}").grid(row=1, column=0, sticky=tk.W)
        
        self.status_label = ttk.Label(info_frame, text="Durum: Durduruldu", foreground="red")
        self.status_label.grid(row=2, column=0, sticky=tk.W)
        
        # Kontrol butonları
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Sunucuyu Başlat", command=self._start_server_gui)
        self.start_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Sunucuyu Durdur", command=self._stop_server_gui, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(5, 0))
        
        # Bağlı istemciler
        clients_frame = ttk.LabelFrame(main_frame, text="Bağlı İstemciler", padding="5")
        clients_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.clients_listbox = tk.Listbox(clients_frame, height=5)
        self.clients_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        clients_scrollbar = ttk.Scrollbar(clients_frame, orient=tk.VERTICAL, command=self.clients_listbox.yview)
        clients_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.clients_listbox.configure(yscrollcommand=clients_scrollbar.set)
        
        # Log alanı
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10), padx=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=40)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        clients_frame.columnconfigure(0, weight=1)
        clients_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _start_server_gui(self):
        """GUI'den sunucuyu başlatır."""
        def start_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.start_server(
                    self.config['server']['host'],
                    self.config['server']['port']
                ))
            except Exception as e:
                self.log(f"Sunucu hatası: {e}")
            finally:
                loop.close()
        
        self.server_thread = threading.Thread(target=start_async, daemon=True)
        self.server_thread.start()
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Durum: Çalışıyor", foreground="green")
    
    def _stop_server_gui(self):
        """GUI'den sunucuyu durdurur."""
        if self.running:
            asyncio.create_task(self.stop_server())
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Durum: Durduruldu", foreground="red")
    
    def _on_closing(self):
        """Pencere kapatılırken çağrılır."""
        if self.running:
            self._stop_server_gui()
        self.root.destroy()
    
    def run(self):
        """Uygulamayı çalıştırır."""
        self.create_gui()
        self.root.mainloop()

def main():
    """Ana fonksiyon."""
    server = SynergyServer()
    server.run()

if __name__ == "__main__":
    main() 