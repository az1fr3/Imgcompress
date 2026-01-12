import os
import sys
import io
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image

class ImageCompressorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- CONFIGURACIÓN DE LA VENTANA ---
        self.title("Optimizador de Imágenes WhatsApp")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Colores Tema Oscuro (Estilo "Dark Mode")
        self.bg_color = "#2b2b2b"       # Fondo gris oscuro
        self.fg_color = "#ffffff"       # Texto blanco
        self.btn_color = "#4a4a4a"      # Botones grises
        self.accent_color = "#2CC069"   # Verde WhatsApp
        
        self.configure(bg=self.bg_color)

        # Configuración de Estilos (ttk)
        self.style = ttk.Style()
        self.style.theme_use('default') # Usar base default para poder personalizar
        
        # Estilo para la Barra de Progreso
        self.style.configure("TProgressbar", thickness=20, troughcolor=self.btn_color, background=self.accent_color)
        
        # Variables de estado
        self.folder_path = None
        self.is_processing = False

        # --- INTERFAZ GRÁFICA (GUI) ---
        
        # Contenedor principal para márgenes
        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        self.label_title = tk.Label(main_frame, text="Compresor Inteligente", 
                                    font=("Helvetica", 24, "bold"), 
                                    bg=self.bg_color, fg=self.fg_color)
        self.label_title.pack(pady=(10, 5))
        
        self.label_subtitle = tk.Label(main_frame, text="Detecta y reduce imágenes > 16MB", 
                                       font=("Helvetica", 12), 
                                       bg=self.bg_color, fg="#aaaaaa")
        self.label_subtitle.pack(pady=(0, 20))

        # Botón de Selección (Usamos tk.Button normal para poder cambiar color de fondo en Mac)
        # Nota: En Mac Tk 8.5, los botones nativos no siempre aceptan bg color, 
        # usamos highlightbackground para simular borde/fondo en versiones viejas.
        self.btn_select = tk.Button(main_frame, text="Seleccionar Carpeta", 
                                    command=self.select_folder, 
                                    font=("Helvetica", 14),
                                    bg="white", fg="black", # Fallback visual
                                    highlightbackground=self.bg_color) 
        self.btn_select.pack(pady=10, ipady=5, ipadx=10)

        # Etiqueta de ruta
        self.label_path = tk.Label(main_frame, text="Ninguna carpeta seleccionada", 
                                   bg=self.bg_color, fg="gray")
        self.label_path.pack(pady=5)

        # Barra de Progreso
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=450, mode="determinate", style="TProgressbar")
        self.progress_bar.pack(pady=20)

        # Área de Texto (Log)
        self.textbox = tk.Text(main_frame, height=10, width=60, 
                               font=("Menlo", 11), 
                               bg="#1e1e1e", fg="#00ff00", # Estilo terminal hacker
                               bd=0, highlightthickness=0)
        self.textbox.pack(pady=10)
        self.textbox.insert("1.0", "Esperando instrucciones...\n")
        self.textbox.configure(state="disabled")

        # Botón de Iniciar
        self.btn_start = tk.Button(main_frame, text="INICIAR PROCESO", 
                                   command=self.start_thread, state="disabled", 
                                   font=("Helvetica", 13, "bold"),
                                   bg=self.accent_color, fg="white",
                                   highlightbackground=self.bg_color) # Parche Mac
        self.btn_start.pack(pady=20, ipady=5, ipadx=20)

    # --- LÓGICA DE INTERFAZ ---

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.label_path.configure(text=f".../{os.path.basename(folder)}")
            self.log(f"Carpeta seleccionada: {folder}")
            self.btn_start.configure(state="normal")
            self.progress_bar["value"] = 0

    def log(self, message):
        """Escribe en la caja de texto"""
        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def start_thread(self):
        if not self.folder_path:
            return
        
        self.is_processing = True
        self.btn_select.configure(state="disabled")
        self.btn_start.configure(state="disabled")
        self.progress_bar.start(10) # Animación de "pensando"
        
        threading.Thread(target=self.run_optimization_logic).start()

    # --- MOTOR DE COMPRESIÓN (Idéntico al anterior) ---
    def run_optimization_logic(self):
        try:
            limite_mb = 16
            limite_bytes = limite_mb * 1024 * 1024
            carpeta_origen = self.folder_path
            
            nombre_carpeta_destino = "Listas_WhatsApp"
            carpeta_salida = os.path.join(carpeta_origen, nombre_carpeta_destino)
            ext_validas = ('.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp')

            if not os.path.exists(carpeta_salida):
                os.makedirs(carpeta_salida)

            self.log(f"\n--- Iniciando Análisis ---")
            
            archivos = [f for f in os.listdir(carpeta_origen) 
                        if f.lower().endswith(ext_validas) and os.path.isfile(os.path.join(carpeta_origen, f))]

            if not archivos:
                self.log("No se encontraron imágenes en la carpeta.")
            
            count = 0
            
            # Detenemos la animación indeterminada y preparamos la barra real
            self.progress_bar.stop()
            self.progress_bar["maximum"] = len(archivos)
            self.progress_bar["value"] = 0

            for i, archivo in enumerate(archivos):
                # Actualizar barra de progreso
                self.progress_bar["value"] = i + 1
                
                ruta_completa = os.path.join(carpeta_origen, archivo)
                try:
                    tamano_actual = os.path.getsize(ruta_completa)
                    
                    if tamano_actual > limite_bytes:
                        self.log(f"Procesando: {archivo} ({tamano_actual/(1024*1024):.2f} MB)...")
                        
                        with Image.open(ruta_completa) as img:
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            
                            calidad = 95
                            factor_escala = 1.0
                            buffer = io.BytesIO()
                            
                            while True:
                                buffer.seek(0)
                                buffer.truncate(0)
                                
                                if calidad < 70:
                                    factor_escala *= 0.9
                                    nuevo_w = int(img.width * factor_escala)
                                    nuevo_h = int(img.height * factor_escala)
                                    img_temp = img.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
                                else:
                                    img_temp = img

                                img_temp.save(buffer, format="JPEG", quality=calidad, optimize=True)
                                tamano_nuevo = buffer.tell()
                                
                                if tamano_nuevo <= limite_bytes:
                                    nombre_nuevo = f"{os.path.splitext(archivo)[0]}_whatsapp.jpg"
                                    ruta_final = os.path.join(carpeta_salida, nombre_nuevo)
                                    
                                    with open(ruta_final, "wb") as f:
                                        f.write(buffer.getbuffer())
                                    
                                    self.log(f" -> OK: {tamano_nuevo/(1024*1024):.2f} MB")
                                    count += 1
                                    break
                                
                                calidad -= 5
                                if calidad < 10 and factor_escala < 0.1:
                                    self.log(f" -> Error: Imposible reducir {archivo}")
                                    break
                    else:
                        pass

                except Exception as e:
                    self.log(f"Error con {archivo}: {e}")

            self.log("\n--- PROCESO TERMINADO ---")
            self.log(f"Total optimizadas: {count}")
            
            self.finish_processing(count, carpeta_salida)

        except Exception as e:
            self.log(f"ERROR CRÍTICO: {e}")
            messagebox.showerror("Error", str(e))
            self.progress_bar.stop()

    def finish_processing(self, count, carpeta_salida):
        self.progress_bar["value"] = self.progress_bar["maximum"]
        self.btn_select.configure(state="normal")
        # El botón de inicio queda desactivado hasta que seleccionen otra carpeta para evitar errores
        self.is_processing = False
        
        messagebox.showinfo("Éxito", f"Proceso finalizado.\nSe crearon {count} imágenes nuevas.")
        os.system(f'open "{carpeta_salida}"')

if __name__ == "__main__":
    app = ImageCompressorApp()
    app.mainloop()