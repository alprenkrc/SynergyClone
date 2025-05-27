import json
import platform
import socket
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class MessageType(Enum):
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    CLIPBOARD = "clipboard"
    SCREEN_INFO = "screen_info"
    HANDSHAKE = "handshake"
    HEARTBEAT = "heartbeat"
    DISCONNECT = "disconnect"

@dataclass
class ScreenInfo:
    width: int
    height: int
    x: int = 0
    y: int = 0
    name: str = ""

@dataclass
class MouseEvent:
    x: int
    y: int
    button: Optional[str] = None
    pressed: Optional[bool] = None
    scroll_x: Optional[int] = None
    scroll_y: Optional[int] = None

@dataclass
class KeyEvent:
    key: str
    pressed: bool

class Message:
    def __init__(self, msg_type: MessageType, data: dict = None):
        self.type = msg_type
        self.data = data or {}
        self.timestamp = None
    
    def to_json(self) -> str:
        return json.dumps({
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        data = json.loads(json_str)
        msg = cls(MessageType(data['type']), data.get('data', {}))
        msg.timestamp = data.get('timestamp')
        return msg

def get_platform_name() -> str:
    """Platform adını döndürür."""
    return platform.system().lower()

def get_local_ip() -> str:
    """Yerel IP adresini döndürür."""
    try:
        # Geçici bir bağlantı oluşturarak yerel IP'yi bul
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def normalize_coordinates(x: int, y: int, from_screen: ScreenInfo, to_screen: ScreenInfo) -> Tuple[int, int]:
    """Koordinatları bir ekrandan diğerine normalize eder."""
    # Göreceli konum hesapla
    rel_x = (x - from_screen.x) / from_screen.width
    rel_y = (y - from_screen.y) / from_screen.height
    
    # Hedef ekranda mutlak konum hesapla
    new_x = int(to_screen.x + (rel_x * to_screen.width))
    new_y = int(to_screen.y + (rel_y * to_screen.height))
    
    return new_x, new_y

def is_point_in_screen(x: int, y: int, screen: ScreenInfo) -> bool:
    """Bir noktanın belirtilen ekran içinde olup olmadığını kontrol eder."""
    return (screen.x <= x < screen.x + screen.width and 
            screen.y <= y < screen.y + screen.height)

def clamp_coordinates(x: int, y: int, screen: ScreenInfo) -> Tuple[int, int]:
    """Koordinatları ekran sınırları içinde tutar."""
    clamped_x = max(screen.x, min(x, screen.x + screen.width - 1))
    clamped_y = max(screen.y, min(y, screen.y + screen.height - 1))
    return clamped_x, clamped_y

class ConfigManager:
    """Yapılandırma yöneticisi."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_config = {
            "server": {
                "host": "0.0.0.0",
                "port": 24800,
                "password": ""
            },
            "client": {
                "server_host": "127.0.0.1",
                "server_port": 24800,
                "auto_connect": False
            },
            "screens": [],
            "settings": {
                "mouse_sensitivity": 1.0,
                "scroll_sensitivity": 1.0,
                "enable_clipboard": True,
                "enable_hotkeys": True
            }
        }
    
    def load_config(self) -> dict:
        """Yapılandırmayı yükler."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Eksik anahtarları varsayılan değerlerle doldur
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            return self.default_config.copy()
        except json.JSONDecodeError:
            return self.default_config.copy()
    
    def save_config(self, config: dict):
        """Yapılandırmayı kaydeder."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Yapılandırma kaydedilemedi: {e}")

def validate_ip_address(ip: str) -> bool:
    """IP adresinin geçerli olup olmadığını kontrol eder."""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def validate_port(port: int) -> bool:
    """Port numarasının geçerli olup olmadığını kontrol eder."""
    return 1 <= port <= 65535 