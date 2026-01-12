import sys
import os
import io
from PIL import Image

# Importamos los componentes de PyQt6
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QSlider, QProgressBar, 
                             QTextEdit, QMessageBox, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

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
        self.init_ui()

    def init_ui(self):
        # NOMBRE ESTILO KEYGEN
        self.setWindowTitle("HYPER-SHRINK 3000 [Unregistered]") 
        self.setGeometry(100, 100, 520, 680)
        
        # --- ESTILO VISUAL "KEYGEN 2000s" ---
        # Fondo negro, letras verde matrix/neón, fuente monoespaciada
        self.setStyleSheet("""
            QWidget { 
                background-color: #000000; 
                color: #00FF00; 
                font-family: 'Courier New', monospace; 
                font-size: 12px;
            }
            QPushButton { 
                background-color: #000000; 
                border: 2px solid #00FF00; 
                padding: 10px; 
                font-weight: bold; 
                text-transform: uppercase;
            }
            QPushButton:hover { 
                background-color: #00FF00; 
                color: #000000; 
            }
            QPushButton:disabled { 
                border: 2px solid #004400; 
                color: #004400; 
            }
            QProgressBar { 
                border: 2px solid #00FF00; 
                text-align: center; 
                color: #000000;
            }
            QProgressBar::chunk { 
                background-color: #00FF00; 
            }
            QTextEdit { 
                background-color: #050505; 
                border: 1px dashed #00FF00; 
                color: #00FF00;
            }
            QSlider::groove:horizontal { 
                height: 4px; 
                background: #004400; 
            }
            QSlider::handle:horizontal { 
                background: #00FF00; 
                width: 10px; 
                margin: -5px 0; 
                border-radius: 0px; 
            }
            QLabel {
                color: #00FF00;
            }
            QFrame {
                color: #00FF00;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # ASCII ART HEADER (Opcional, pero muy estilo keygen)
        header_text = """
  _    _v1.0__  _ 
 | |  | | \ \ / /
 | |__| |  \ V / 
 |  __  |   > <  
 | |  | |  / . \ 
 |_|  |_| /_/ \_\\
        """
        ascii_label = QLabel(header_text)
        ascii_label.setFont(QFont("Courier New", 10))
        ascii_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ascii_label)

        # Título
        title = QLabel("HYPER-SHRINK 3000")
        title.setFont(QFont("Courier New", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(">> SYSTEM READY <<")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("border: 1px solid #00FF00;")
        layout.addWidget(line)

        # Selección de Carpeta
        self.btn_select = QPushButton("[ SELECT DIRECTORY ]")
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.clicked.connect(self.select_folder)
        layout.addWidget(self.btn_select)

        self.lbl_path = QLabel("NO DIR SELECTED")
        self.lbl_path.setStyleSheet("color: #008800;")
        self.lbl_path.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_path)

        # Slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("COMPRESSION LIMIT:"))
        
        self.lbl_slider_val = QLabel("16 MB")
        self.lbl_slider_val.setStyleSheet("color: #FFFFFF; font-weight: bold;")
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

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "SELECT TARGET DIRECTORY")
        if folder:
            self.folder_path = folder
            self.lbl_path.setText(f".../{os.path.basename(folder).upper()}")
            self.lbl_path.setStyleSheet("color: #00FF00;")
            self.log_msg(f">> TARGET MOUNTED: {folder}")
            self.btn_start.setEnabled(True)
            self.pbar.setValue(0)

    def update_slider(self, value):
        self.lbl_slider_val.setText(f"{value} MB")

    def log_msg(self, msg):
        self.log_box.append(msg)

    def start_process(self):
        if not self.folder_path: return
        
        # Bloquear UI
        self.btn_select.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.slider.setEnabled(False)
        self.log_msg("\n>> INITIALIZING SEQUENCE...")

        # Iniciar hilo
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
        
        self.log_msg(f"\n>> JOB DONE. {count} FILES PROCESSED.")
        QMessageBox.information(self, "SUCCESS", f"OPERATION COMPLETED.\nPROCESSED: {count}")
        
        if sys.platform == 'darwin':
            os.system(f'open "{out_folder}"')
        elif sys.platform == 'win32':
            os.startfile(out_folder)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompressorApp()
    window.show()
    sys.exit(app.exec())