#!/usr/bin/env python3
"""
SynergyClone Simple Client - Test istemcisi
"""

import asyncio
import websockets
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time

class SimpleClient:
    def __init__(self):
        self.connected = False
        self.websocket = None
        
        # GUI
        self.root = None
        self.status_label = None
        self.server_ip_entry = None
        self.server_port_entry = None
        self.log_text = None
        self.message_entry = None
        
    async def connect_to_server(self, host, port):
        """Sunucuya bağlanır."""
        try:
            self.log(f"Sunucuya bağlanılıyor: {host}:{port}")
            
            self.websocket = await websockets.connect(
                f"ws://{host}:{port}",
                ping_interval=30,
                ping_timeout=10
            )
            
            self.connected = True
            self.log("Sunucuya bağlandı!")
            
            # Test mesajı gönder
            test_msg = {"type": "test", "message": "Merhaba sunucu!"}
            await self.websocket.send(json.dumps(test_msg))
            
            # Mesaj dinleme döngüsü
            await self.message_loop()
            
        except websockets.exceptions.ConnectionClosed:
            self.log("Sunucu bağlantısı kesildi")
        except ConnectionRefusedError:
            self.log("Sunucuya bağlanılamadı - bağlantı reddedildi")
        except Exception as e:
            self.log(f"Bağlantı hatası: {e}")
        finally:
            self.connected = False
    
    async def disconnect(self):
        """Sunucudan bağlantıyı keser."""
        self.connected = False
        
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            finally:
                self.websocket = None
        
        self.log("Sunucudan bağlantı kesildi")
    
    async def message_loop(self):
        """Sunucudan gelen mesajları dinler."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    self.log(f"Sunucudan mesaj: {data}")
                except json.JSONDecodeError:
                    self.log(f"Geçersiz mesaj: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def send_message(self, message):
        """Sunucuya mesaj gönderir."""
        if self.connected and self.websocket:
            try:
                msg = {"type": "user_message", "message": message}
                await self.websocket.send(json.dumps(msg))
                self.log(f"Mesaj gönderildi: {message}")
            except Exception as e:
                self.log(f"Mesaj gönderme hatası: {e}")
    
    def log(self, message):
        """Log mesajı ekler."""
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        if self.log_text:
            try:
                self.log_text.insert(tk.END, log_msg + "\n")
                self.log_text.see(tk.END)
            except:
                pass
    
    def create_gui(self):
        """GUI oluşturur."""
        self.root = tk.Tk()
        self.root.title("SynergyClone Simple Client")
        self.root.geometry("500x400")
        
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Bağlantı ayarları
        connection_frame = ttk.LabelFrame(main_frame, text="Sunucu Bağlantısı", padding="5")
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # IP ve Port
        ip_frame = ttk.Frame(connection_frame)
        ip_frame.pack(fill=tk.X)
        
        ttk.Label(ip_frame, text="Sunucu IP:").pack(side=tk.LEFT)
        self.server_ip_entry = ttk.Entry(ip_frame, width=15)
        self.server_ip_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.server_ip_entry.insert(0, "192.168.2.199")  # Varsayılan IP
        
        ttk.Label(ip_frame, text="Port:").pack(side=tk.LEFT)
        self.server_port_entry = ttk.Entry(ip_frame, width=8)
        self.server_port_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.server_port_entry.insert(0, "24800")
        
        # Durum
        self.status_label = ttk.Label(connection_frame, text="Durum: Bağlı değil", foreground="red")
        self.status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Kontrol butonları
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.connect_button = ttk.Button(button_frame, text="Bağlan", command=self.connect_gui)
        self.connect_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disconnect_button = ttk.Button(button_frame, text="Bağlantıyı Kes", 
                                          command=self.disconnect_gui, state=tk.DISABLED)
        self.disconnect_button.pack(side=tk.LEFT)
        
        # Mesaj gönderme
        msg_frame = ttk.LabelFrame(main_frame, text="Mesaj Gönder", padding="5")
        msg_frame.pack(fill=tk.X, pady=(0, 10))
        
        msg_input_frame = ttk.Frame(msg_frame)
        msg_input_frame.pack(fill=tk.X)
        
        self.message_entry = ttk.Entry(msg_input_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', self.send_message_gui)
        
        ttk.Button(msg_input_frame, text="Gönder", command=self.send_message_gui).pack(side=tk.RIGHT)
        
        # Log alanı
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def connect_gui(self):
        """GUI'den bağlantı başlatır."""
        server_ip = self.server_ip_entry.get().strip()
        server_port_str = self.server_port_entry.get().strip()
        
        if not server_ip:
            messagebox.showerror("Hata", "Sunucu IP adresi gerekli!")
            return
        
        try:
            server_port = int(server_port_str)
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz port numarası!")
            return
        
        def connect_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.connect_to_server(server_ip, server_port))
            except Exception as e:
                self.log(f"Bağlantı hatası: {e}")
            finally:
                loop.close()
                # GUI durumunu güncelle
                self.root.after(0, self.update_connection_status, False)
        
        self.connection_task = threading.Thread(target=connect_async, daemon=True)
        self.connection_task.start()
        
        # GUI durumunu güncelle
        self.update_connection_status(True)
    
    def disconnect_gui(self):
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
        
        self.update_connection_status(False)
    
    def send_message_gui(self, event=None):
        """GUI'den mesaj gönderir."""
        message = self.message_entry.get().strip()
        if message and self.connected:
            def send_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.send_message(message))
                finally:
                    loop.close()
            
            threading.Thread(target=send_async, daemon=True).start()
            self.message_entry.delete(0, tk.END)
    
    def update_connection_status(self, connecting):
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
    
    def on_closing(self):
        """Pencere kapatılırken çağrılır."""
        if self.connected:
            self.disconnect_gui()
        self.root.destroy()
    
    def run(self):
        """Uygulamayı çalıştırır."""
        self.create_gui()
        self.log("Simple Client hazır")
        self.log("Sunucuya bağlanarak test edebilirsiniz")
        self.root.mainloop()

def main():
    """Ana fonksiyon."""
    client = SimpleClient()
    client.run()

if __name__ == "__main__":
    main() 