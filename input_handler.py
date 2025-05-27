import time
import threading
from typing import Callable, Optional
import platform
import sys

# macOS izin kontrolü için
if platform.system() == "Darwin":
    try:
        import subprocess
        import os
    except ImportError:
        pass

from utils import MouseEvent, KeyEvent, get_platform_name

def check_macos_accessibility_permissions():
    """macOS'ta accessibility izinlerini kontrol eder."""
    if platform.system() != "Darwin":
        return True
    
    try:
        # Sistem veritabanından accessibility izinlerini kontrol et
        import sqlite3
        
        # TCC (Transparency, Consent, and Control) veritabanını kontrol et
        tcc_db_path = "/Library/Application Support/com.apple.TCC/TCC.db"
        user_tcc_db_path = os.path.expanduser("~/Library/Application Support/com.apple.TCC/TCC.db")
        
        # Önce kullanıcı TCC veritabanını kontrol et
        for db_path in [user_tcc_db_path, tcc_db_path]:
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Terminal veya Python için accessibility izinlerini kontrol et
                    cursor.execute("""
                        SELECT allowed FROM access 
                        WHERE service = 'kTCCServiceAccessibility' 
                        AND (client LIKE '%Terminal%' OR client LIKE '%Python%' OR client LIKE '%python%')
                    """)
                    
                    results = cursor.fetchall()
                    conn.close()
                    
                    # Eğer izin varsa (allowed = 1)
                    for result in results:
                        if result[0] == 1:
                            return True
                            
                except Exception:
                    continue
        
        # TCC kontrolü başarısız olursa, AppleScript ile kontrol et
        script = '''
        tell application "System Events"
            try
                set frontApp to name of first application process whose frontmost is true
                return "true"
            on error
                return "false"
            end try
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return result.stdout.strip() == "true"
        
    except Exception as e:
        print(f"Accessibility izin kontrolü hatası: {e}")
        # Hata durumunda güvenli tarafta kal - izin yok varsay
        return False

def open_accessibility_settings():
    """macOS accessibility ayarlarını açar."""
    if platform.system() == "Darwin":
        try:
            subprocess.run([
                'open', 
                'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
            ])
            return True
        except Exception:
            return False
    return False

def request_macos_accessibility_permission():
    """macOS'ta accessibility izni ister."""
    if platform.system() != "Darwin":
        return True
    
    try:
        # Önce mevcut izinleri kontrol et
        if check_macos_accessibility_permissions():
            return True
        
        print("🔐 macOS Accessibility izni gerekli...")
        print("📋 Sistem otomatik olarak izin isteyecek...")
        
        # Accessibility gerektiren bir işlem yapmaya çalış
        # Bu sistem tarafından izin dialog'u tetikleyecek
        from pynput import mouse
        controller = mouse.Controller()
        
        # Mouse pozisyonunu al - bu accessibility izni tetikler
        try:
            pos = controller.position
            print(f"✅ İzin mevcut - Mouse pozisyonu: {pos}")
            return True
        except Exception as e:
            print(f"❌ Accessibility izni reddedildi: {e}")
            
            # Kullanıcıyı yönlendir
            print("\n🔧 İzin vermek için:")
            print("1. System Settings > Privacy & Security > Accessibility")
            print("2. Terminal veya Python'ı listeye ekleyin")
            print("3. İzinleri etkinleştirin")
            print("4. Bu uygulamayı yeniden başlatın")
            
            # Ayarları otomatik aç
            try:
                subprocess.run([
                    'open', 
                    'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
                ])
                print("📱 System Settings açıldı...")
            except:
                pass
            
            return False
            
    except Exception as e:
        print(f"İzin isteme hatası: {e}")
        return False

class InputHandler:
    """Platform bağımsız input yakalama ve simülasyon sınıfı."""
    
    def __init__(self):
        self.platform = get_platform_name()
        self.mouse_controller = None
        self.keyboard_controller = None
        
        # Event listeners
        self.mouse_listener: Optional = None
        self.keyboard_listener: Optional = None
        
        # Callback fonksiyonları
        self.on_mouse_move: Optional[Callable[[MouseEvent], None]] = None
        self.on_mouse_click: Optional[Callable[[MouseEvent], None]] = None
        self.on_mouse_scroll: Optional[Callable[[MouseEvent], None]] = None
        self.on_key_press: Optional[Callable[[KeyEvent], None]] = None
        self.on_key_release: Optional[Callable[[KeyEvent], None]] = None
        
        # Input capture durumu
        self.capturing = False
        self.suppress_input = False
        self.accessibility_available = False
        
        # macOS izin kontrolü
        if self.platform == "darwin":
            self.accessibility_available = check_macos_accessibility_permissions()
        else:
            self.accessibility_available = True
        
        # Pynput'u güvenli şekilde import et
        self._init_pynput()
    
    def _init_pynput(self):
        """Pynput'u güvenli şekilde başlatır."""
        try:
            from pynput import mouse, keyboard
            from pynput.mouse import Button, Listener as MouseListener
            from pynput.keyboard import Key, Listener as KeyboardListener
            
            self.mouse_controller = mouse.Controller()
            self.keyboard_controller = keyboard.Controller()
            self.MouseListener = MouseListener
            self.KeyboardListener = KeyboardListener
            self.Button = Button
            self.Key = Key
            
        except Exception as e:
            print(f"Pynput import hatası: {e}")
            self.mouse_controller = None
            self.keyboard_controller = None
    
    def check_accessibility_permissions(self):
        """Accessibility izinlerini kontrol eder ve sonucu döndürür."""
        if self.platform != "darwin":
            return True, "macOS değil"
        
        if not self.accessibility_available:
            return False, "Accessibility izinleri gerekli"
        
        return True, "İzinler mevcut"
    
    def start_capture(self):
        """Input yakalamayı başlatır."""
        if self.capturing:
            return True
        
        if not self.mouse_controller or not self.keyboard_controller:
            raise RuntimeError("Input controllers başlatılamadı")
        
        try:
            self.capturing = True
            
            # macOS'ta ekstra güvenlik kontrolü
            if self.platform == "darwin":
                # Önce basit bir test yapalım
                try:
                    test_pos = self.mouse_controller.position
                    print(f"Mouse pozisyon testi başarılı: {test_pos}")
                except Exception as e:
                    self.capturing = False
                    raise PermissionError(f"macOS accessibility izinleri eksik: {e}")
                
                # macOS'ta polling tabanlı sistem kullan (daha güvenli)
                print("🍎 macOS için polling tabanlı mouse tracking başlatılıyor...")
                self._start_macos_polling()
                print("✅ macOS polling sistemi başarıyla başlatıldı")
                return True
            
            # Windows'ta özel işlem
            elif self.platform == "windows":
                print("🪟 Windows için güvenli listener başlatılıyor...")
                return self._start_windows_safe_capture()
            
            # Linux için normal listener sistemi
            suppress_mode = self.suppress_input
            
            # Mouse listener - güvenli başlatma
            try:
                self.mouse_listener = self.MouseListener(
                    on_move=self._on_mouse_move,
                    on_click=self._on_mouse_click,
                    on_scroll=self._on_mouse_scroll,
                    suppress=suppress_mode
                )
                self.mouse_listener.start()
                time.sleep(0.2)
                
                # Mouse listener çalışıyor mu test et
                if not self.mouse_listener.running:
                    raise RuntimeError("Mouse listener başlatılamadı")
                    
            except Exception as e:
                self.capturing = False
                if self.mouse_listener:
                    try:
                        self.mouse_listener.stop()
                    except:
                        pass
                raise RuntimeError(f"Mouse listener hatası: {e}")
            
            # Keyboard listener - güvenli başlatma
            try:
                self.keyboard_listener = self.KeyboardListener(
                    on_press=self._on_key_press,
                    on_release=self._on_key_release,
                    suppress=suppress_mode
                )
                self.keyboard_listener.start()
                time.sleep(0.2)
                
                # Keyboard listener çalışıyor mu test et
                if not self.keyboard_listener.running:
                    raise RuntimeError("Keyboard listener başlatılamadı")
                    
            except Exception as e:
                self.capturing = False
                if self.mouse_listener:
                    try:
                        self.mouse_listener.stop()
                    except:
                        pass
                if self.keyboard_listener:
                    try:
                        self.keyboard_listener.stop()
                    except:
                        pass
                raise RuntimeError(f"Keyboard listener hatası: {e}")
            
            return True
            
        except Exception as e:
            self.capturing = False
            # Tüm listener'ları temizle
            if hasattr(self, 'mouse_listener') and self.mouse_listener:
                try:
                    self.mouse_listener.stop()
                except:
                    pass
                self.mouse_listener = None
                
            if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
                try:
                    self.keyboard_listener.stop()
                except:
                    pass
                self.keyboard_listener = None
                
            raise RuntimeError(f"Input capture başlatılamadı: {e}")
    
    def _start_windows_safe_capture(self):
        """Windows için güvenli input yakalama başlatır."""
        try:
            # Windows'ta sadece polling kullan - listener sorunları nedeniyle
            print("🪟 Windows polling sistemi başlatılıyor...")
            self._start_windows_polling()
            print("✅ Windows polling sistemi başarıyla başlatıldı")
            return True
            
        except Exception as e:
            print(f"Windows polling hatası: {e}")
            # Fallback: listener'ları dikkatli şekilde dene
            return self._try_windows_listeners()
    
    def _start_windows_polling(self):
        """Windows için polling tabanlı mouse tracking başlatır."""
        self.polling_active = True
        self.last_mouse_position = self.mouse_controller.position
        
        def polling_loop():
            while self.polling_active and self.capturing:
                try:
                    current_pos = self.mouse_controller.position
                    if current_pos != self.last_mouse_position:
                        self._on_mouse_move(current_pos[0], current_pos[1])
                        self.last_mouse_position = current_pos
                    time.sleep(0.01)  # 100 FPS polling
                except Exception as e:
                    print(f"Windows polling hatası: {e}")
                    break
        
        self.polling_thread = threading.Thread(target=polling_loop, daemon=True)
        self.polling_thread.start()
    
    def _try_windows_listeners(self):
        """Windows'ta listener'ları dikkatli şekilde dener."""
        try:
            print("🪟 Windows listener'ları deneniyor...")
            
            # Suppress=False ile dene (daha güvenli)
            self.mouse_listener = self.MouseListener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
                suppress=False  # Windows'ta suppress=False daha güvenli
            )
            
            self.mouse_listener.start()
            time.sleep(0.5)  # Daha uzun bekleme
            
            # Listener durumunu kontrol et
            if hasattr(self.mouse_listener, 'running') and self.mouse_listener.running:
                print("✅ Windows mouse listener başarılı")
                
                # Keyboard listener'ı da dene
                try:
                    self.keyboard_listener = self.KeyboardListener(
                        on_press=self._on_key_press,
                        on_release=self._on_key_release,
                        suppress=False
                    )
                    self.keyboard_listener.start()
                    time.sleep(0.5)
                    
                    if hasattr(self.keyboard_listener, 'running') and self.keyboard_listener.running:
                        print("✅ Windows keyboard listener başarılı")
                        return True
                    else:
                        print("⚠️ Windows keyboard listener başarısız - sadece mouse")
                        return True  # Mouse yeterli
                        
                except Exception as e:
                    print(f"Windows keyboard listener hatası: {e}")
                    return True  # Mouse yeterli
                    
            else:
                print("❌ Windows mouse listener başarısız")
                return False
                
        except Exception as e:
            print(f"Windows listener hatası: {e}")
            return False
    
    def _start_macos_polling(self):
        """macOS için polling tabanlı mouse tracking başlatır."""
        self.polling_active = True
        self.last_mouse_position = self.mouse_controller.position
        
        def polling_loop():
            while self.polling_active and self.capturing:
                try:
                    current_pos = self.mouse_controller.position
                    if current_pos != self.last_mouse_position:
                        self._on_mouse_move(current_pos[0], current_pos[1])
                        self.last_mouse_position = current_pos
                    time.sleep(0.01)  # 100 FPS polling
                except Exception as e:
                    print(f"Polling hatası: {e}")
                    break
        
        self.polling_thread = threading.Thread(target=polling_loop, daemon=True)
        self.polling_thread.start()
    
    def stop_capture(self):
        """Input yakalamayı durdurur."""
        if not self.capturing:
            return
            
        self.capturing = False
        
        # Polling sistemlerini durdur (macOS ve Windows)
        if hasattr(self, 'polling_active'):
            self.polling_active = False
            if hasattr(self, 'polling_thread') and self.polling_thread.is_alive():
                try:
                    self.polling_thread.join(timeout=1.0)
                except RuntimeError:
                    # Thread join hatası - normal durum
                    pass
        
        try:
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
                
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
        except Exception as e:
            print(f"Input capture durdurma hatası: {e}")
    
    def set_suppress_input(self, suppress: bool):
        """Input'u bastırma durumunu ayarlar."""
        self.suppress_input = suppress
        
        # Windows'ta polling kullanıyorsa yeniden başlatma
        if self.platform == "windows" and hasattr(self, 'polling_active') and self.polling_active:
            print(f"🪟 Windows polling aktif - suppress değişikliği atlanıyor: {suppress}")
            return
        
        # macOS'ta polling kullanıyorsa yeniden başlatma
        if self.platform == "darwin" and hasattr(self, 'polling_active') and self.polling_active:
            print(f"🍎 macOS polling aktif - suppress değişikliği atlanıyor: {suppress}")
            return
        
        # Sadece listener kullanıyorsa yeniden başlat
        if self.capturing:
            print(f"🔄 Listener yeniden başlatılıyor - suppress: {suppress}")
            self.stop_capture()
            self.start_capture()
    
    def _on_mouse_move(self, x: int, y: int):
        """Mouse hareket olayını işler."""
        if self.on_mouse_move:
            event = MouseEvent(x=x, y=y)
            self.on_mouse_move(event)
    
    def _on_mouse_click(self, x: int, y: int, button, pressed: bool):
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
    
    def _button_to_string(self, button) -> str:
        """Mouse button'ını string'e çevirir."""
        if not hasattr(self, 'Button'):
            return "unknown"
        
        button_map = {
            self.Button.left: "left",
            self.Button.right: "right",
            self.Button.middle: "middle"
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
        if not self.mouse_controller:
            return
        try:
            # Windows'ta daha güvenilir yöntem kullan
            if self.platform == "windows":
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    # Windows API ile mouse hareket ettir
                    ctypes.windll.user32.SetCursorPos(int(x), int(y))
                    print(f"Windows API mouse hareket: ({x}, {y})")
                    return
                except Exception as e:
                    print(f"Windows API hatası: {e}")
                    # Fallback: pynput kullan
            
            # Diğer platformlar veya Windows API başarısızsa pynput kullan
            self.mouse_controller.position = (x, y)
        except Exception as e:
            print(f"Mouse hareket simülasyonu hatası: {e}")
    
    def simulate_mouse_click(self, x: int, y: int, button: str, pressed: bool):
        """Mouse tıklamayı simüle eder."""
        if not self.mouse_controller or not hasattr(self, 'Button'):
            return
        try:
            # Windows'ta daha güvenilir yöntem kullan
            if self.platform == "windows":
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    # Önce mouse'u pozisyona götür
                    ctypes.windll.user32.SetCursorPos(int(x), int(y))
                    
                    # Button mapping
                    if button == "left":
                        down_flag = 0x0002  # MOUSEEVENTF_LEFTDOWN
                        up_flag = 0x0004    # MOUSEEVENTF_LEFTUP
                    elif button == "right":
                        down_flag = 0x0008  # MOUSEEVENTF_RIGHTDOWN
                        up_flag = 0x0010    # MOUSEEVENTF_RIGHTUP
                    elif button == "middle":
                        down_flag = 0x0020  # MOUSEEVENTF_MIDDLEDOWN
                        up_flag = 0x0040    # MOUSEEVENTF_MIDDLEUP
                    else:
                        down_flag = 0x0002  # Default to left
                        up_flag = 0x0004
                    
                    # Mouse event gönder
                    if pressed:
                        ctypes.windll.user32.mouse_event(down_flag, 0, 0, 0, 0)
                    else:
                        ctypes.windll.user32.mouse_event(up_flag, 0, 0, 0, 0)
                    
                    print(f"Windows API mouse click: ({x}, {y}) {button} {'down' if pressed else 'up'}")
                    return
                except Exception as e:
                    print(f"Windows API click hatası: {e}")
                    # Fallback: pynput kullan
            
            # Diğer platformlar veya Windows API başarısızsa pynput kullan
            # Önce mouse'u ilgili pozisyona götür
            self.mouse_controller.position = (x, y)
            time.sleep(0.01)  # Küçük bir gecikme
            
            # Button mapping
            button_map = {
                "left": self.Button.left,
                "right": self.Button.right,
                "middle": self.Button.middle
            }
            
            mouse_button = button_map.get(button, self.Button.left)
            
            if pressed:
                self.mouse_controller.press(mouse_button)
            else:
                self.mouse_controller.release(mouse_button)
                
        except Exception as e:
            print(f"Mouse tıklama simülasyonu hatası: {e}")
    
    def simulate_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Mouse scroll simüle eder."""
        if not self.mouse_controller:
            return
        try:
            self.mouse_controller.position = (x, y)
            time.sleep(0.01)
            self.mouse_controller.scroll(scroll_x, scroll_y)
        except Exception as e:
            print(f"Mouse scroll simülasyonu hatası: {e}")
    
    def simulate_key_press(self, key_name: str, pressed: bool):
        """Klavye tuşu basımını simüle eder."""
        if not self.keyboard_controller or not hasattr(self, 'Key'):
            return
        try:
            # Özel tuşlar için mapping
            special_keys = {
                'space': self.Key.space,
                'enter': self.Key.enter,
                'tab': self.Key.tab,
                'shift': self.Key.shift,
                'ctrl': self.Key.ctrl,
                'alt': self.Key.alt,
                'cmd': self.Key.cmd,
                'esc': self.Key.esc,
                'backspace': self.Key.backspace,
                'delete': self.Key.delete,
                'up': self.Key.up,
                'down': self.Key.down,
                'left': self.Key.left,
                'right': self.Key.right,
                'home': self.Key.home,
                'end': self.Key.end,
                'page_up': self.Key.page_up,
                'page_down': self.Key.page_down,
                'f1': self.Key.f1, 'f2': self.Key.f2, 'f3': self.Key.f3, 'f4': self.Key.f4,
                'f5': self.Key.f5, 'f6': self.Key.f6, 'f7': self.Key.f7, 'f8': self.Key.f8,
                'f9': self.Key.f9, 'f10': self.Key.f10, 'f11': self.Key.f11, 'f12': self.Key.f12
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
        if not self.mouse_controller:
            return (0, 0)
        try:
            return self.mouse_controller.position
        except Exception:
            return (0, 0)
    
    def get_clipboard_text(self) -> str:
        """Clipboard içeriğini alır."""
        try:
            import tkinter as tk
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
            import tkinter as tk
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
            # Platform'a göre farklı yöntemler kullan
            if platform.system() == "Windows":
                # Windows'ta DPI scaling sorununu çözmek için Windows API kullan
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    # DPI awareness ayarla
                    try:
                        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
                    except:
                        try:
                            ctypes.windll.user32.SetProcessDPIAware()
                        except:
                            pass
                    
                    # Gerçek ekran çözünürlüğünü al
                    user32 = ctypes.windll.user32
                    width = user32.GetSystemMetrics(0)   # SM_CXSCREEN
                    height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
                    
                    print(f"Windows gerçek ekran çözünürlüğü: {width}x{height}")
                    
                except Exception as e:
                    print(f"Windows API hatası: {e}")
                    # Fallback: tkinter kullan
                    import tkinter as tk
                    root = tk.Tk()
                    width = root.winfo_screenwidth()
                    height = root.winfo_screenheight()
                    root.destroy()
                    print(f"Tkinter ekran çözünürlüğü (DPI scaled): {width}x{height}")
            else:
                # macOS ve Linux için tkinter kullan
                import tkinter as tk
                root = tk.Tk()
                width = root.winfo_screenwidth()
                height = root.winfo_screenheight()
                root.destroy()
                print(f"Ekran çözünürlüğü: {width}x{height}")
            
            from utils import ScreenInfo
            main_screen = ScreenInfo(
                width=width,
                height=height,
                x=0,
                y=0,
                name="Main Screen"
            )
            
            self.screens = [main_screen]
            
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