import sys
import os
import io
import random  # Necesario para el efecto Matrix/Glitch
from PIL import Image

# Importamos los componentes de PyQt6
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QSlider, QProgressBar, 
                             QTextEdit, QMessageBox, QHBoxLayout, QFrame, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer # Agregamos QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

# Módulo Multimedia para el Chiptune
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# --- CLASE TRABAJADOR (Hilo en segundo plano) ---
class Worker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(int, str) # count, path

    def __init__(self, folder_path, target_mb):
        super().__init__()
        self.folder_path = folder_path
        self.target_mb = target_mb
        self.is_running = True

    def run(self):
        try:
            limit_bytes = self.target_mb * 1024 * 1024
            output_folder = os.path.join(self.folder_path, "X-TREME_COMPRESSED")
            
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            exts = ('.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp')
            files = [f for f in os.listdir(self.folder_path) 
                     if f.lower().endswith(exts) and os.path.isfile(os.path.join(self.folder_path, f))]

            if not files:
                self.log.emit(">> NO FILES FOUND.")
                self.finished.emit(0, output_folder)
                return

            self.log.emit(f">> SYSTEM READY. TARGET: {self.target_mb} MB")
            self.log.emit(f">> INITIALIZING ALGORITHM...")
            
            count = 0
            total = len(files)

            for i, f in enumerate(files):
                if not self.is_running: break
                
                # Reportar progreso
                self.progress.emit(int(((i + 1) / total) * 100))
                
                full_path = os.path.join(self.folder_path, f)
                try:
                    size = os.path.getsize(full_path)
                    if size > limit_bytes:
                        self.log.emit(f"PROCESSING: {f} ({size/1024/1024:.1f} MB)")
                        
                        with Image.open(full_path) as img:
                            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                            
                            qual = 95
                            scale = 1.0
                            buf = io.BytesIO()
                            
                            while True:
                                buf.seek(0); buf.truncate(0)
                                if qual < 70:
                                    scale *= 0.9
                                    w, h = int(img.width * scale), int(img.height * scale)
                                    img_temp = img.resize((w, h), Image.Resampling.LANCZOS)
                                else:
                                    img_temp = img
                                
                                img_temp.save(buf, "JPEG", quality=qual, optimize=True)
                                
                                if buf.tell() <= limit_bytes:
                                    out_name = f"{os.path.splitext(f)[0]}_XTREME.jpg"
                                    with open(os.path.join(output_folder, out_name), "wb") as outfile:
                                        outfile.write(buf.getbuffer())
                                    self.log.emit(f" [OK] REDUCED TO: {buf.tell()/1024/1024:.1f} MB")
                                    count += 1
                                    break
                                
                                qual -= 5
                                if qual < 10 and scale < 0.1:
                                    self.log.emit(f" [FAIL] COULD NOT COMPRESS: {f}")
                                    break
                    else:
                        pass # Ya es pequeña
                except Exception as e:
                    self.log.emit(f" [ERROR] {f}: {e}")

            self.finished.emit(count, output_folder)

        except Exception as e:
            self.log.emit(f"CRITICAL ERROR: {str(e)}")
            self.finished.emit(0, "")

    def stop(self):
        self.is_running = False

# --- VENTANA PRINCIPAL ---
class CompressorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.folder_path = None
        self.has_audio = False
        
        # --- CONFIGURACIÓN DE ANIMACIÓN ASCII ---
        # Logo base
        raw_ascii = """
  _    _v1.0__  _ 
 | |  | | \ \ / /
 | |__| |  \ V / 
 |  __  |   > <  
 | |  | |  / . \ 
 |_|  |_| /_/ \_\\
"""
        # Procesar el ASCII para que sea un bloque rectangular perfecto
        lines = [line for line in raw_ascii.split('\n') if line] # Eliminar lineas vacias
        if lines:
            max_width = max(len(line) for line in lines)
            # Rellenar con espacios para que todas las líneas tengan el mismo ancho
            self.rect_ascii = "\n".join([line.ljust(max_width) for line in lines])
        else:
            self.rect_ascii = raw_ascii

        # Caracteres para el efecto "Matrix Rain"
        self.matrix_chars = "010101XYZA$#@&%* " # Agregamos espacios para que no sea SOLO ruido
        
        # Timer para la animación
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate_ascii)
        
        # Inicializar UI
        self.init_ui()
        # Inicializar Audio
        self.init_audio()
        # Aplicar tema por defecto
        self.apply_theme("KEYGEN STYLE")

    def init_audio(self):
        """Configura el reproductor de música"""
        try:
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            
            # Buscar carpeta BreakProtocol
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                
            music_folder = os.path.join(base_dir, "BreakProtocol")
            
            mp3_file = None
            if os.path.exists(music_folder):
                for f in os.listdir(music_folder):
                    if f.lower().endswith(".mp3"):
                        mp3_file = os.path.join(music_folder, f)
                        break
            
            if mp3_file:
                url = QUrl.fromLocalFile(mp3_file)
                self.player.setSource(url)
                self.player.setLoops(QMediaPlayer.Loops.Infinite) 
                self.audio_output.setVolume(0.5)
                self.has_audio = True
                self.log_msg(">> AUDIO MODULE: LOADED [BreakProtocol]")
            else:
                self.log_msg(">> AUDIO MODULE: NO MP3 FOUND")
                
        except Exception as e:
            print(f"Error de audio: {e}")
            self.has_audio = False

    def init_ui(self):
        self.setWindowTitle("HYPER-SHRINK 3000") 
        self.setGeometry(100, 100, 520, 720)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- SELECTOR DE TEMA ---
        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        theme_label = QLabel("INTERFACE THEME:")
        theme_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        theme_layout.addWidget(theme_label)
        
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["KEYGEN STYLE", "MODO NATIVO (MAC)"])
        self.theme_selector.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_selector.currentTextChanged.connect(self.apply_theme)
        theme_layout.addWidget(self.theme_selector)
        
        layout.addLayout(theme_layout)

        # ASCII ART HEADER
        self.ascii_label = QLabel(self.rect_ascii)
        self.ascii_label.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self.ascii_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Importante: ancho fijo para evitar saltos raros en la animación
        self.ascii_label.setFixedWidth(480) 
        layout.addWidget(self.ascii_label)

        # Título
        self.title_label = QLabel("HYPER-SHRINK 3000")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(">> SYSTEM READY <<")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle_label)

        # Separador
        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(self.line)

        # Selección de Carpeta
        self.btn_select = QPushButton("[ SELECT DIRECTORY ]")
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.clicked.connect(self.select_folder)
        layout.addWidget(self.btn_select)

        self.lbl_path = QLabel("NO DIR SELECTED")
        self.lbl_path.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_path)

        # Slider
        slider_layout = QHBoxLayout()
        self.slider_label = QLabel("COMPRESSION LIMIT:")
        slider_layout.addWidget(self.slider_label)
        
        self.lbl_slider_val = QLabel("16 MB")
        self.lbl_slider_val.setStyleSheet("font-weight: bold;") 
        slider_layout.addWidget(self.lbl_slider_val)
        layout.addLayout(slider_layout)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(50)
        self.slider.setValue(16)
        self.slider.valueChanged.connect(self.update_slider)
        layout.addWidget(self.slider)

        # Barra de progreso
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)

        # Log
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setText(">> WAITING FOR USER INPUT...")
        layout.addWidget(self.log_box)

        # Botón Inicio
        self.btn_start = QPushButton(">> EXECUTE <<")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_process)
        layout.addWidget(self.btn_start)

        # Branding (Inicialización con soporte para links)
        self.branding_label = QLabel()
        self.branding_label.setOpenExternalLinks(True) # ¡Importante! Permite hacer clic
        self.branding_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.branding_label)

        self.setLayout(layout)

    def animate_ascii(self):
        """Genera el efecto glitch/matrix en TODO el cuadro del logo"""
        final_text = []
        
        for char in self.rect_ascii:
            if char == '\n':
                final_text.append('\n')
            # Probabilidad de glitch (15%) afecta a CUALQUIER caracter (letras o espacios)
            elif random.random() < 0.15: 
                final_text.append(random.choice(self.matrix_chars))
            else:
                final_text.append(char)
        
        self.ascii_label.setText("".join(final_text))

    def apply_theme(self, theme_name):
        if theme_name == "KEYGEN STYLE":
            # --- ACTIVAR ANIMACIÓN Y MÚSICA ---
            self.anim_timer.start(80) # Un poco más rápido para más caos
            
            if self.has_audio:
                if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                    self.player.play()

            # --- ESTILO HACKER ---
            self.setWindowTitle("HYPER-SHRINK 3000 [Unregistered]")
            self.ascii_label.show()
            self.title_label.setText("HYPER-SHRINK 3000")
            self.title_label.setFont(QFont("Courier New", 20, QFont.Weight.Bold))
            self.subtitle_label.setText(">> SYSTEM READY <<")
            
            self.btn_select.setText("[ SELECT DIRECTORY ]")
            self.btn_start.setText(">> EXECUTE <<")
            self.slider_label.setText("COMPRESSION LIMIT:")

            # Branding con estilo HTML para el link (Verde oscuro)
            self.branding_label.setText('<a href="https://linktr.ee/az1fr3" style="color: #004400; text-decoration: none;">Created by Azufr3</a>')
            self.branding_label.setStyleSheet("font-size: 10px; font-style: italic;")

            self.setStyleSheet("""
                QWidget { background-color: #000000; color: #00FF00; font-family: 'Courier New', monospace; }
                QComboBox { background-color: #000000; border: 1px solid #00FF00; color: #00FF00; padding: 5px; }
                QPushButton { background-color: #000000; border: 2px solid #00FF00; padding: 10px; font-weight: bold; }
                QPushButton:hover { background-color: #00FF00; color: #000000; }
                QPushButton:disabled { border: 2px solid #004400; color: #004400; }
                QProgressBar { border: 2px solid #00FF00; text-align: center; color: #000000; }
                QProgressBar::chunk { background-color: #00FF00; }
                QTextEdit { background-color: #050505; border: 1px dashed #00FF00; color: #00FF00; }
                QSlider::groove:horizontal { height: 4px; background: #004400; }
                QSlider::handle:horizontal { background: #00FF00; width: 10px; margin: -5px 0; }
                QFrame { border: 1px solid #00FF00; }
            """)
            
        else:
            # --- DESACTIVAR ANIMACIÓN Y MÚSICA ---
            self.anim_timer.stop()
            # Restaurar texto original limpio (sin glitches)
            self.ascii_label.setText(self.rect_ascii) 
            
            if self.has_audio:
                self.player.stop()

            # --- ESTILO NATIVO ---
            self.setWindowTitle("Compresor de Imágenes")
            self.ascii_label.hide()
            self.title_label.setText("Compresor de Imágenes")
            self.title_label.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
            self.subtitle_label.setText("Modo Profesional Activado")
            
            self.btn_select.setText("Seleccionar Carpeta")
            self.btn_start.setText("Iniciar Compresión")
            self.slider_label.setText("Tamaño Máximo:")

            # Branding con estilo HTML para el link (Gris profesional)
            self.branding_label.setText('<a href="https://linktr.ee/az1fr3" style="color: #888888; text-decoration: none;">Created by Azufr3</a>')
            self.branding_label.setStyleSheet("font-size: 10px; font-family: Helvetica;")

            self.setStyleSheet("") 
            
            self.log_box.setStyleSheet("background-color: #FFFFFF; color: #000000; border: 1px solid #CCC;")
            if self.palette().color(QPalette.ColorRole.Window).value() < 100: 
                self.log_box.setStyleSheet("background-color: #1E1E1E; color: #EEE; border: 1px solid #555;")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "SELECT TARGET DIRECTORY")
        if folder:
            self.folder_path = folder
            self.lbl_path.setText(f".../{os.path.basename(folder)}")
            
            if self.theme_selector.currentText() == "KEYGEN STYLE":
                self.lbl_path.setStyleSheet("color: #00FF00;")
                self.log_msg(f">> TARGET MOUNTED: {folder}")
            else:
                self.lbl_path.setStyleSheet("color: blue;")
                self.log_msg(f"Carpeta lista: {folder}")

            self.btn_start.setEnabled(True)
            self.pbar.setValue(0)

    def update_slider(self, value):
        self.lbl_slider_val.setText(f"{value} MB")

    def log_msg(self, msg):
        self.log_box.append(msg)

    def start_process(self):
        if not self.folder_path: return
        
        self.btn_select.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.slider.setEnabled(False)
        self.theme_selector.setEnabled(False)
        
        if self.theme_selector.currentText() == "KEYGEN STYLE":
            self.log_msg("\n>> INITIALIZING SEQUENCE...")
        else:
            self.log_msg("\nIniciando proceso...")

        self.worker = Worker(self.folder_path, self.slider.value())
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log_msg)
        self.worker.finished.connect(self.process_finished)
        self.worker.start()

    def update_progress(self, val):
        self.pbar.setValue(val)

    def process_finished(self, count, out_folder):
        self.btn_select.setEnabled(True)
        self.btn_start.setEnabled(True)
        self.slider.setEnabled(True)
        self.theme_selector.setEnabled(True)
        
        is_keygen = self.theme_selector.currentText() == "KEYGEN STYLE"
        
        msg_title = "SUCCESS" if is_keygen else "Éxito"
        msg_body = f"OPERATION COMPLETED.\nPROCESSED: {count}" if is_keygen else f"Proceso finalizado.\nImágenes procesadas: {count}"
        
        self.log_msg(f"\n>> {msg_body}")
        QMessageBox.information(self, msg_title, msg_body)
        
        if sys.platform == 'darwin':
            os.system(f'open "{out_folder}"')
        elif sys.platform == 'win32':
            os.startfile(out_folder)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompressorApp()
    window.show()
    sys.exit(app.exec())