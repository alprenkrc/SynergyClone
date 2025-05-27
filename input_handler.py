import time
import threading
from typing import Callable, Optional
from pynput import mouse, keyboard
from pynput.mouse import Button, Listener as MouseListener
from pynput.keyboard import Key, Listener as KeyboardListener
import tkinter as tk

from utils import MouseEvent, KeyEvent, get_platform_name

class InputHandler:
    """Platform bağımsız input yakalama ve simülasyon sınıfı."""
    
    def __init__(self):
        self.platform = get_platform_name()
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
        # Event listeners
        self.mouse_listener: Optional[MouseListener] = None
        self.keyboard_listener: Optional[KeyboardListener] = None
        
        # Callback fonksiyonları
        self.on_mouse_move: Optional[Callable[[MouseEvent], None]] = None
        self.on_mouse_click: Optional[Callable[[MouseEvent], None]] = None
        self.on_mouse_scroll: Optional[Callable[[MouseEvent], None]] = None
        self.on_key_press: Optional[Callable[[KeyEvent], None]] = None
        self.on_key_release: Optional[Callable[[KeyEvent], None]] = None
        
        # Input capture durumu
        self.capturing = False
        self.suppress_input = False
        
    def start_capture(self):
        """Input yakalamayı başlatır."""
        if self.capturing:
            return
            
        self.capturing = True
        
        # Mouse listener
        self.mouse_listener = MouseListener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
            suppress=self.suppress_input
        )
        
        # Keyboard listener
        self.keyboard_listener = KeyboardListener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
            suppress=self.suppress_input
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
    def stop_capture(self):
        """Input yakalamayı durdurur."""
        if not self.capturing:
            return
            
        self.capturing = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
            
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
    def set_suppress_input(self, suppress: bool):
        """Input'u bastırma durumunu ayarlar."""
        self.suppress_input = suppress
        if self.capturing:
            self.stop_capture()
            self.start_capture()
    
    def _on_mouse_move(self, x: int, y: int):
        """Mouse hareket olayını işler."""
        if self.on_mouse_move:
            event = MouseEvent(x=x, y=y)
            self.on_mouse_move(event)
    
    def _on_mouse_click(self, x: int, y: int, button: Button, pressed: bool):
        """Mouse tıklama olayını işler."""
        if self.on_mouse_click:
            button_name = self._button_to_string(button)
            event = MouseEvent(x=x, y=y, button=button_name, pressed=pressed)
            self.on_mouse_click(event)
    
    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int):
        """Mouse scroll olayını işler."""
        if self.on_mouse_scroll:
            event = MouseEvent(x=x, y=y, scroll_x=dx, scroll_y=dy)
            self.on_mouse_scroll(event)
    
    def _on_key_press(self, key):
        """Klavye tuşu basma olayını işler."""
        if self.on_key_press:
            key_name = self._key_to_string(key)
            event = KeyEvent(key=key_name, pressed=True)
            self.on_key_press(event)
    
    def _on_key_release(self, key):
        """Klavye tuşu bırakma olayını işler."""
        if self.on_key_release:
            key_name = self._key_to_string(key)
            event = KeyEvent(key=key_name, pressed=False)
            self.on_key_release(event)
    
    def _button_to_string(self, button: Button) -> str:
        """Mouse button'ını string'e çevirir."""
        button_map = {
            Button.left: "left",
            Button.right: "right",
            Button.middle: "middle"
        }
        return button_map.get(button, "unknown")
    
    def _key_to_string(self, key) -> str:
        """Klavye tuşunu string'e çevirir."""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char
            elif hasattr(key, 'name'):
                return key.name
            else:
                return str(key)
        except AttributeError:
            return str(key)
    
    def simulate_mouse_move(self, x: int, y: int):
        """Mouse hareketini simüle eder."""
        try:
            self.mouse_controller.position = (x, y)
        except Exception as e:
            print(f"Mouse hareket simülasyonu hatası: {e}")
    
    def simulate_mouse_click(self, x: int, y: int, button: str, pressed: bool):
        """Mouse tıklamayı simüle eder."""
        try:
            # Önce mouse'u ilgili pozisyona götür
            self.mouse_controller.position = (x, y)
            time.sleep(0.01)  # Küçük bir gecikme
            
            # Button mapping
            button_map = {
                "left": Button.left,
                "right": Button.right,
                "middle": Button.middle
            }
            
            mouse_button = button_map.get(button, Button.left)
            
            if pressed:
                self.mouse_controller.press(mouse_button)
            else:
                self.mouse_controller.release(mouse_button)
                
        except Exception as e:
            print(f"Mouse tıklama simülasyonu hatası: {e}")
    
    def simulate_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Mouse scroll simüle eder."""
        try:
            self.mouse_controller.position = (x, y)
            time.sleep(0.01)
            self.mouse_controller.scroll(scroll_x, scroll_y)
        except Exception as e:
            print(f"Mouse scroll simülasyonu hatası: {e}")
    
    def simulate_key_press(self, key_name: str, pressed: bool):
        """Klavye tuşu basımını simüle eder."""
        try:
            # Özel tuşlar için mapping
            special_keys = {
                'space': Key.space,
                'enter': Key.enter,
                'tab': Key.tab,
                'shift': Key.shift,
                'ctrl': Key.ctrl,
                'alt': Key.alt,
                'cmd': Key.cmd,
                'esc': Key.esc,
                'backspace': Key.backspace,
                'delete': Key.delete,
                'up': Key.up,
                'down': Key.down,
                'left': Key.left,
                'right': Key.right,
                'home': Key.home,
                'end': Key.end,
                'page_up': Key.page_up,
                'page_down': Key.page_down,
                'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
                'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
                'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12
            }
            
            if key_name.lower() in special_keys:
                key = special_keys[key_name.lower()]
            else:
                key = key_name
            
            if pressed:
                self.keyboard_controller.press(key)
            else:
                self.keyboard_controller.release(key)
                
        except Exception as e:
            print(f"Klavye simülasyonu hatası: {e}")
    
    def get_mouse_position(self) -> tuple:
        """Mevcut mouse pozisyonunu döndürür."""
        return self.mouse_controller.position
    
    def get_clipboard_text(self) -> str:
        """Clipboard içeriğini alır."""
        try:
            root = tk.Tk()
            root.withdraw()  # Pencereyi gizle
            clipboard_text = root.clipboard_get()
            root.destroy()
            return clipboard_text
        except Exception:
            return ""
    
    def set_clipboard_text(self, text: str):
        """Clipboard içeriğini ayarlar."""
        try:
            root = tk.Tk()
            root.withdraw()  # Pencereyi gizle
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()  # Clipboard'ı güncelle
            root.destroy()
        except Exception as e:
            print(f"Clipboard ayarlama hatası: {e}")

class ScreenManager:
    """Ekran bilgilerini yöneten sınıf."""
    
    def __init__(self):
        self.screens = []
        self._update_screen_info()
    
    def _update_screen_info(self):
        """Ekran bilgilerini günceller."""
        try:
            import tkinter as tk
            root = tk.Tk()
            
            # Ana ekran bilgileri
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            
            from utils import ScreenInfo
            main_screen = ScreenInfo(
                width=width,
                height=height,
                x=0,
                y=0,
                name="Main Screen"
            )
            
            self.screens = [main_screen]
            root.destroy()
            
        except Exception as e:
            print(f"Ekran bilgisi alınamadı: {e}")
            # Varsayılan değerler
            from utils import ScreenInfo
            self.screens = [ScreenInfo(width=1920, height=1080, name="Default")]
    
    def get_primary_screen(self):
        """Ana ekran bilgisini döndürür."""
        return self.screens[0] if self.screens else None
    
    def get_all_screens(self):
        """Tüm ekran bilgilerini döndürür."""
        return self.screens.copy()
    
    def refresh(self):
        """Ekran bilgilerini yeniler."""
        self._update_screen_info() 