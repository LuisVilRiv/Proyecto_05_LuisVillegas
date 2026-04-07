import os
import sys
import subprocess
from pathlib import Path

# Dependency auto-installer
def ensure_dependencies():
    missing = []
    try:
        from PIL import Image, ImageTk
    except ImportError:
        missing.append("Pillow")
        
    if missing:
        print(f"Installing missing dependencies: {', '.join(missing)}...")
        for pkg in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                print(f"Successfully installed {pkg}.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {pkg}: {e}")

class CloudAssetManager:
    """Manages cached multimedia assets."""
    def __init__(self, download_dir: str):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.assets = {}
        self.images_cache = {} 
        self.audio_initialized = True
        
        # Archivos generados localmente
        self.MANIFEST = {
            "sound_win": "sound_win.wav",
            "sound_tick": "sound_tick.wav",
            "sound_action": "sound_action.wav",
            "texture_card_back": "texture_card_back.png",
            "texture_roulette_wheel": "texture_roulette_wheel.png"
        }

    def init_audio(self):
        pass

    def download_assets(self, progress_callback=None):
        total = len(self.MANIFEST)
        for i, (key, filename) in enumerate(self.MANIFEST.items()):
            local_path = self.download_dir / filename
            self.assets[key] = str(local_path)
            
            if progress_callback:
                progress_callback(i + 1, total, f"Cargando activo: {key}...")
                
        self.init_audio()

    def get_image(self, key: str, size: tuple = None):
        if key not in self.assets:
            return None
        path = self.assets[key]
        if not os.path.exists(path):
            return None
            
        cache_key = f"{key}_{size}" if size else key
        if cache_key in self.images_cache:
            return self.images_cache[cache_key]
            
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.images_cache[cache_key] = photo
            return photo
        except Exception as e:
            return None

    def get_rotated_image(self, key: str, angle: float, size: tuple = None):
        if key not in self.assets:
            return None
        path = self.assets[key]
        if not os.path.exists(path):
            return None
            
        angle = round(angle, 1) # Reduce cache blowup
        cache_key = f"{key}_{size}_rot_{angle}"
        
        if not hasattr(self, '_rot_cache_keys'):
            self._rot_cache_keys = []
            
        if cache_key in self.images_cache:
            return self.images_cache[cache_key]
            
        try:
            from PIL import Image, ImageTk, ImageDraw
            img = Image.open(path).convert("RGBA")
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)
                
            # Aplicar máscara circular perfecta para ocultar los bordes cuadrados al girar
            mask = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
            
            # Recortar las esquinas base y luego rotar
            img.putalpha(mask)
            # expand=False keeps size consistent so rotation doesn't wobble
            img = img.rotate(-angle, resample=Image.Resampling.BILINEAR, fillcolor=(0,0,0,0))
            
            photo = ImageTk.PhotoImage(img)
            
            if len(self._rot_cache_keys) > 100:
                oldest = self._rot_cache_keys.pop(0)
                if oldest in self.images_cache:
                    del self.images_cache[oldest]
                    
            self.images_cache[cache_key] = photo
            self._rot_cache_keys.append(cache_key)
            return photo
        except Exception as e:
            return None

    def play_sound(self, key: str):
        if key not in self.assets:
            return
        path = self.assets[key]
        if not os.path.exists(path):
            return
            
        try:
            if sys.platform.startswith("win"):
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception as e:
            pass
