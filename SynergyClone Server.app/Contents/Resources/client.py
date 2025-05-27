#!/usr/bin/env python3
"""
SynergyClone Client - İstemci bilgisayar uygulaması
Sunucudan gelen mouse ve klavye olaylarını alır ve simüle eder.
"""

import asyncio
import websockets
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Optional
import logging

from utils import (
    MessageType, Message, ScreenInfo, MouseEvent, KeyEvent,
    ConfigManager, validate_ip_address, validate_port
)
from input_handler import InputHandler, ScreenManager

class SynergyClient:
    def __init__(self):
        self.config_manager = ConfigManager("client_config.json")
        self.config = self.config_manager.load_config()
        
        # Client durumu
        self.connected = False
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Input handler ve screen manager
        self.input_handler = InputHandler()
        self.screen_manager = ScreenManager()
        
        # İstemci ekran bilgisi
        self.client_screen = self.screen_manager.get_primary_screen()
        
        # Sunucu ekran bilgisi
        self.server_screen: Optional[ScreenInfo] = None
        
        # Heartbeat
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.heartbeat_interval = 30  # saniye
        
        # GUI
        self.root = None
        self.status_label = None
        self.server_ip_entry = None
        self.server_port_entry = None
        self.log_text = None
        
        # Connection tracking
        self.auto_reconnect = True
        self.connection_task: Optional[asyncio.Task] = None
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def connect_to_server(self, host: str, port: int):
        """Sunucuya bağlanır."""
        try:
            self.log(f"Sunucuya bağlanılıyor: {host}:{port}")
            
            # WebSocket bağlantısı kur
            self.websocket = await websockets.connect(
                f"ws://{host}:{port}",
                ping_interval=30,
                ping_timeout=10
            )
            
            self.connected = True
            self.reconnect_attempts = 0
            
            self.log("Sunucuya bağlandı!")
            
            # Handshake gönder
            await self._send_handshake()
            
            # Heartbeat başlat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Mesaj dinleme döngüsü
            await self._message_loop()
            
        except websockets.exceptions.ConnectionClosed:
            self.log("Sunucu bağlantısı kesildi")
        except websockets.exceptions.InvalidURI:
            self.log("Geçersiz sunucu adresi")
        except ConnectionRefusedError:
            self.log("Sunucuya bağlanılamadı - bağlantı reddedildi")
        except Exception as e:
            self.log(f"Bağlantı hatası: {e}")
        finally:
            self.connected = False
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            
            # Otomatik yeniden bağlanma
            if self.auto_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                self.log(f"Yeniden bağlanma denemesi {self.reconnect_attempts}/{self.max_reconnect_attempts}")
                await asyncio.sleep(5)  # 5 saniye bekle
                await self.connect_to_server(host, port)
    
    async def disconnect(self):
        """Sunucudan bağlantıyı keser."""
        self.auto_reconnect = False
        self.connected = False
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        if self.websocket:
            try:
                # Disconnect mesajı gönder
                disconnect_msg = Message(MessageType.DISCONNECT)
                await self.websocket.send(disconnect_msg.to_json())
                await self.websocket.close()
            except:
                pass
            finally:
                self.websocket = None
        
        self.log("Sunucudan bağlantı kesildi")
    
    async def _send_handshake(self):
        """Handshake mesajını gönderir."""
        if not self.websocket:
            return
        
        handshake_msg = Message(MessageType.HANDSHAKE, {
            'screen_info': {
                'width': self.client_screen.width,
                'height': self.client_screen.height,
                'name': self.client_screen.name
            },
            'client_info': {
                'platform': self.input_handler.platform,
                'version': '1.0.0'
            }
        })
        
        await self.websocket.send(handshake_msg.to_json())
        self.log("Handshake gönderildi")
    
    async def _heartbeat_loop(self):
        """Heartbeat döngüsü."""
        try:
            while self.connected and self.websocket:
                heartbeat_msg = Message(MessageType.HEARTBEAT)
                await self.websocket.send(heartbeat_msg.to_json())
                await asyncio.sleep(self.heartbeat_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log(f"Heartbeat hatası: {e}")
    
    async def _message_loop(self):
        """Sunucudan gelen mesajları dinler."""
        try:
            async for message in self.websocket:
                try:
                    msg = Message.from_json(message)
                    await self._process_server_message(msg)
                except json.JSONDecodeError:
                    self.log("Geçersiz mesaj formatı")
                except Exception as e:
                    self.log(f"Mesaj işleme hatası: {e}")
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def _process_server_message(self, message: Message):
        """Sunucudan gelen mesajları işler."""
        if message.type == MessageType.HANDSHAKE:
            # Sunucu bilgilerini al
            server_data = message.data.get('server_screen', {})
            self.server_screen = ScreenInfo(
                width=server_data.get('width', 1920),
                height=server_data.get('height', 1080),
                name=server_data.get('name', "Server")
            )
            
            status = message.data.get('status', 'unknown')
            self.log(f"Handshake tamamlandı - Durum: {status}")
            
            # GUI durumunu güncelle - handshake başarılı olduğunda bağlı olarak işaretle
            if status == 'connected':
                self.root.after(0, self._update_connection_status_connected)
            
        elif message.type == MessageType.MOUSE_MOVE:
            # Mouse hareket olayını simüle et
            x = message.data.get('x', 0)
            y = message.data.get('y', 0)
            self.input_handler.simulate_mouse_move(x, y)
            
        elif message.type == MessageType.MOUSE_CLICK:
            # Mouse tıklama olayını simüle et
            x = message.data.get('x', 0)
            y = message.data.get('y', 0)
            button = message.data.get('button', 'left')
            pressed = message.data.get('pressed', True)
            self.input_handler.simulate_mouse_click(x, y, button, pressed)
            
        elif message.type == MessageType.MOUSE_SCROLL:
            # Mouse scroll olayını simüle et
            x = message.data.get('x', 0)
            y = message.data.get('y', 0)
            scroll_x = message.data.get('scroll_x', 0)
            scroll_y = message.data.get('scroll_y', 0)
            self.input_handler.simulate_mouse_scroll(x, y, scroll_x, scroll_y)
            
        elif message.type == MessageType.KEY_PRESS:
            # Klavye tuşu basma olayını simüle et
            key = message.data.get('key', '')
            pressed = message.data.get('pressed', True)
            self.input_handler.simulate_key_press(key, pressed)
            
        elif message.type == MessageType.KEY_RELEASE:
            # Klavye tuşu bırakma olayını simüle et
            key = message.data.get('key', '')
            self.input_handler.simulate_key_press(key, False)
            
        elif message.type == MessageType.CLIPBOARD:
            # Clipboard içeriğini al ve yerel clipboard'a kopyala
            clipboard_text = message.data.get('text', '')
            if clipboard_text:
                self.input_handler.set_clipboard_text(clipboard_text)
                self.log(f"Clipboard güncellendi: {clipboard_text[:50]}...")
                
        elif message.type == MessageType.HEARTBEAT:
            # Heartbeat yanıtı - bağlantı canlı
            pass
            
        elif message.type == MessageType.DISCONNECT:
            # Sunucu bağlantıyı kesti
            self.log("Sunucu bağlantıyı kesti")
            await self.disconnect()
    
    async def send_clipboard(self, text: str):
        """Clipboard içeriğini sunucuya gönderir."""
        if not self.connected or not self.websocket:
            return
        
        clipboard_msg = Message(MessageType.CLIPBOARD, {'text': text})
        try:
            await self.websocket.send(clipboard_msg.to_json())
        except Exception as e:
            self.log(f"Clipboard gönderme hatası: {e}")
    
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
    
    def create_gui(self):
        """GUI oluşturur."""
        self.root = tk.Tk()
        self.root.title("SynergyClone Client")
        self.root.geometry("500x400")
        
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bağlantı ayarları
        connection_frame = ttk.LabelFrame(main_frame, text="Sunucu Bağlantısı", padding="5")
        connection_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # IP adresi
        ttk.Label(connection_frame, text="Sunucu IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.server_ip_entry = ttk.Entry(connection_frame, width=15)
        self.server_ip_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        self.server_ip_entry.insert(0, self.config['client']['server_host'])
        
        # Port
        ttk.Label(connection_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.server_port_entry = ttk.Entry(connection_frame, width=8)
        self.server_port_entry.grid(row=0, column=3, sticky=tk.W)
        self.server_port_entry.insert(0, str(self.config['client']['server_port']))
        
        # Durum
        self.status_label = ttk.Label(connection_frame, text="Durum: Bağlı değil", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # Kontrol butonları
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.connect_button = ttk.Button(button_frame, text="Bağlan", command=self._connect_gui)
        self.connect_button.grid(row=0, column=0, padx=(0, 5))
        
        self.disconnect_button = ttk.Button(button_frame, text="Bağlantıyı Kes", 
                                          command=self._disconnect_gui, state=tk.DISABLED)
        self.disconnect_button.grid(row=0, column=1, padx=(5, 0))
        
        # Clipboard işlemleri
        clipboard_frame = ttk.LabelFrame(main_frame, text="Clipboard", padding="5")
        clipboard_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.clipboard_text = tk.Text(clipboard_frame, height=3, width=50)
        self.clipboard_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(clipboard_frame, text="Clipboard'a Kopyala", 
                  command=self._copy_to_clipboard).grid(row=1, column=0, padx=(0, 5))
        ttk.Button(clipboard_frame, text="Sunucuya Gönder", 
                  command=self._send_clipboard_gui).grid(row=1, column=1)
        
        # İstemci bilgileri
        info_frame = ttk.LabelFrame(main_frame, text="İstemci Bilgileri", padding="5")
        info_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Ekran: {self.client_screen.width}x{self.client_screen.height}").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=f"Platform: {self.input_handler.platform}").grid(row=1, column=0, sticky=tk.W)
        
        # Log alanı
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=60)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        connection_frame.columnconfigure(1, weight=1)
        clipboard_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _connect_gui(self):
        """GUI'den bağlantı başlatır."""
        # Giriş verilerini kontrol et
        server_ip = self.server_ip_entry.get().strip()
        server_port_str = self.server_port_entry.get().strip()
        
        if not server_ip:
            messagebox.showerror("Hata", "Sunucu IP adresi gerekli!")
            return
        
        if not validate_ip_address(server_ip):
            messagebox.showerror("Hata", "Geçersiz IP adresi!")
            return
        
        try:
            server_port = int(server_port_str)
            if not validate_port(server_port):
                messagebox.showerror("Hata", "Port numarası 1-65535 arasında olmalı!")
                return
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz port numarası!")
            return
        
        # Yapılandırmayı kaydet
        self.config['client']['server_host'] = server_ip
        self.config['client']['server_port'] = server_port
        self.config_manager.save_config(self.config)
        
        # Bağlantıyı başlat
        def connect_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self.auto_reconnect = True
                loop.run_until_complete(self.connect_to_server(server_ip, server_port))
            except Exception as e:
                self.log(f"Bağlantı hatası: {e}")
            finally:
                loop.close()
                # GUI durumunu güncelle
                self.root.after(0, self._update_connection_status, False)
        
        self.connection_task = threading.Thread(target=connect_async, daemon=True)
        self.connection_task.start()
        
        # GUI durumunu güncelle
        self._update_connection_status(True)
    
    def _disconnect_gui(self):
        """GUI'den bağlantıyı keser."""
        if self.connected:
            def disconnect_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.disconnect())
                finally:
                    loop.close()
            
            threading.Thread(target=disconnect_async, daemon=True).start()
        
        self._update_connection_status(False)
    
    def _update_connection_status(self, connecting: bool):
        """Bağlantı durumunu günceller."""
        if connecting:
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.status_label.config(text="Durum: Bağlanıyor...", foreground="orange")
        else:
            self.connect_button.config(state=tk.NORMAL)
            self.disconnect_button.config(state=tk.DISABLED)
            if self.connected:
                self.status_label.config(text="Durum: Bağlı", foreground="green")
            else:
                self.status_label.config(text="Durum: Bağlı değil", foreground="red")
    
    def _update_connection_status_connected(self):
        """Handshake başarılı olduğunda GUI durumunu 'Bağlı' olarak günceller."""
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
        self.status_label.config(text="Durum: Bağlı", foreground="green")
    
    def _copy_to_clipboard(self):
        """Metni clipboard'a kopyalar."""
        text = self.clipboard_text.get("1.0", tk.END).strip()
        if text:
            self.input_handler.set_clipboard_text(text)
            self.log("Metin clipboard'a kopyalandı")
    
    def _send_clipboard_gui(self):
        """Clipboard içeriğini sunucuya gönderir."""
        text = self.clipboard_text.get("1.0", tk.END).strip()
        if text and self.connected:
            def send_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.send_clipboard(text))
                finally:
                    loop.close()
            
            threading.Thread(target=send_async, daemon=True).start()
            self.log("Clipboard sunucuya gönderildi")
    
    def _on_closing(self):
        """Pencere kapatılırken çağrılır."""
        if self.connected:
            self._disconnect_gui()
        self.root.destroy()
    
    def run(self):
        """Uygulamayı çalıştırır."""
        self.create_gui()
        self.root.mainloop()

def main():
    """Ana fonksiyon."""
    client = SynergyClient()
    client.run()

if __name__ == "__main__":
    main() 