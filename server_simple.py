#!/usr/bin/env python3
"""
SynergyClone Simple Server - Accessibility izinleri olmadan test versiyonu
"""

import asyncio
import websockets
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import socket

def get_local_ip():
    """Yerel IP adresini döndürür."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

class SimpleServer:
    def __init__(self):
        self.running = False
        self.clients = {}
        self.server = None
        
        # GUI
        self.root = None
        self.status_label = None
        self.clients_listbox = None
        self.log_text = None
        
    async def start_server(self, host="0.0.0.0", port=24800):
        """WebSocket sunucusunu başlatır."""
        try:
            self.server = await websockets.serve(
                self.handle_client,
                host,
                port,
                ping_interval=30,
                ping_timeout=10
            )
            self.running = True
            
            self.log(f"Sunucu başlatıldı: {host}:{port}")
            self.log(f"Yerel IP: {get_local_ip()}")
            
            await self.server.wait_closed()
            
        except Exception as e:
            self.log(f"Sunucu başlatma hatası: {e}")
            raise
    
    async def stop_server(self):
        """Sunucuyu durdurur."""
        self.running = False
        
        # Bağlantıları kapat
        for client_id, websocket in self.clients.copy().items():
            try:
                await websocket.close()
            except:
                pass
        
        self.clients.clear()
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        self.log("Sunucu durduruldu")
    
    async def handle_client(self, websocket, path):
        """Yeni istemci bağlantısını işler."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.clients[client_id] = websocket
        
        self.log(f"Yeni istemci bağlandı: {client_id}")
        self.update_clients_list()
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.log(f"Mesaj alındı: {data.get('type', 'unknown')}")
                    
                    # Echo back
                    response = {"type": "response", "message": "Mesaj alındı"}
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    self.log(f"Geçersiz mesaj formatı: {client_id}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.log(f"İstemci bağlantısı kesildi: {client_id}")
        except Exception as e:
            self.log(f"İstemci işleme hatası: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            self.update_clients_list()
            self.log(f"İstemci ayrıldı: {client_id}")
    
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
    
    def update_clients_list(self):
        """İstemci listesini günceller."""
        if self.clients_listbox:
            try:
                self.clients_listbox.delete(0, tk.END)
                for client_id in self.clients:
                    self.clients_listbox.insert(tk.END, client_id)
            except:
                pass
    
    def create_gui(self):
        """GUI oluşturur."""
        self.root = tk.Tk()
        self.root.title("SynergyClone Simple Server")
        self.root.geometry("500x400")
        
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sunucu bilgileri
        info_frame = ttk.LabelFrame(main_frame, text="Sunucu Bilgileri", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"IP Adresi: {get_local_ip()}").pack(anchor=tk.W)
        ttk.Label(info_frame, text="Port: 24800").pack(anchor=tk.W)
        
        self.status_label = ttk.Label(info_frame, text="Durum: Durduruldu", foreground="red")
        self.status_label.pack(anchor=tk.W)
        
        # Kontrol butonları
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Sunucuyu Başlat", command=self.start_server_gui)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Sunucuyu Durdur", 
                                     command=self.stop_server_gui, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Bağlı istemciler
        clients_frame = ttk.LabelFrame(main_frame, text="Bağlı İstemciler", padding="5")
        clients_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.clients_listbox = tk.Listbox(clients_frame, height=5)
        self.clients_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Log alanı
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_server_gui(self):
        """GUI'den sunucuyu başlatır."""
        def start_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.start_server())
            except Exception as e:
                self.log(f"Sunucu hatası: {e}")
            finally:
                loop.close()
        
        self.server_thread = threading.Thread(target=start_async, daemon=True)
        self.server_thread.start()
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Durum: Çalışıyor", foreground="green")
    
    def stop_server_gui(self):
        """GUI'den sunucuyu durdurur."""
        if self.running:
            def stop_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.stop_server())
                finally:
                    loop.close()
            
            threading.Thread(target=stop_async, daemon=True).start()
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Durum: Durduruldu", foreground="red")
    
    def on_closing(self):
        """Pencere kapatılırken çağrılır."""
        if self.running:
            self.stop_server_gui()
        self.root.destroy()
    
    def run(self):
        """Uygulamayı çalıştırır."""
        self.create_gui()
        self.log("Simple Server hazır - Accessibility izinleri gerekmez")
        self.log("Bu versiyon sadece ağ bağlantısını test eder")
        self.root.mainloop()

def main():
    """Ana fonksiyon."""
    server = SimpleServer()
    server.run()

if __name__ == "__main__":
    main() 