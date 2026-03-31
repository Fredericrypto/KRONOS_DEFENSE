import customtkinter as ctk
import cv2
from PIL import Image
import threading
import time
import sys
import numpy as np
from datetime import datetime, timedelta
import random

# Bibliotecas para Gráficos
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

# Importações dos módulos internos
from core.comunicador import KronosAlert

class KronosDashboard(ctk.CTk):
    def __init__(self, motor_ia, controlador):
        super().__init__()

        # --- PALETA DE CORES KRONOS ELITE ---
        self.colors = {
            "dark": {
                "bg": "#0D1117",
                "card": "#161B22",
                "text": "#C9D1D9",
                "accent": "#58A6FF",
                "success": "#3FB950",
                "danger": "#F85149",
                "warning": "#DBAB09",
                "border": "#30363D",
                "graph_bg": "#161B22"
            },
            "light": {
                "bg": "#F0F2F5",
                "card": "#FFFFFF",
                "text": "#1F2328",
                "accent": "#0969DA",
                "success": "#1A7F37",
                "danger": "#CF222E",
                "warning": "#9A6700",
                "border": "#D0D7DE",
                "graph_bg": "#FFFFFF"
            }
        }
        self.current_theme = "dark"
        self.theme_colors = self.colors[self.current_theme]

        self.title("KRONOS DEFENSE V1.0 - COMMAND CENTER")
        self.geometry("1366x768")
        
        self.ia = motor_ia
        self.controlador = controlador
        self.cap = cv2.VideoCapture(0)
        self.alerta = KronosAlert()

        self.ultimo_registro_tempo = 0
        self.dados_grafico_tempo = []
        self.dados_grafico_contagem = []
        self._inicializar_dados_grafico_dummy()

        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._setup_video_area()
        self._setup_sidebar_com_graficos()
        
        self._aplicar_tema()
        self.update_dashboard()

    def _desenhar_mapa_termico(self, frame, landmarks, confianca):
        overlay = frame.copy()
        color = (0, 255, 100) if confianca > 0.70 else (0, 255, 255) if confianca > 0.40 else (50, 50, 255)
        for feature, pts in landmarks.items():
            pts_array = np.array(pts, np.int32)
            cv2.polylines(overlay, [pts_array], False, color, 1, cv2.LINE_AA)
            for p in pts:
                cv2.circle(overlay, p, 2, color, -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

    def _setup_video_area(self):
        self.video_frame = ctk.CTkFrame(self, fg_color="black", corner_radius=15, border_width=2)
        self.video_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.video_label = ctk.CTkLabel(self.video_frame, text="") 
        self.video_label.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_sidebar_com_graficos(self):
        self.sidebar = ctk.CTkFrame(self, width=400, corner_radius=0)
        self.sidebar.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10), padx=20)
        self.logo_label = ctk.CTkLabel(header_frame, text="KRONOS DEFENSE", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.pack(side="left")
        self.theme_switch = ctk.CTkSwitch(header_frame, text="", command=self.alternar_tema, variable=ctk.StringVar(value="dark"), onvalue="dark", offvalue="light")
        self.theme_switch.pack(side="right")
        self.status_indicator = ctk.CTkLabel(self.sidebar, text="● SISTEMA OPERACIONAL", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_indicator.pack(pady=(0, 15))
        self.graph_frame = ctk.CTkFrame(self.sidebar, fg_color=self.theme_colors["card"], corner_radius=10, border_width=1)
        self.graph_frame.pack(padx=20, pady=5, fill="both", expand=True)
        self._setup_matplotlib_graph()
        self.log_box = ctk.CTkTextbox(self.sidebar, width=350, height=200, corner_radius=8, font=("Consolas", 11))
        self.log_box.pack(padx=20, pady=5)
        self.btn_lock = ctk.CTkButton(self.sidebar, text="BLOQUEIO DE EMERGÊNCIA", height=40, font=("Inter", 14, "bold"), command=self.bloqueio_emergencia)
        self.btn_lock.pack(side="bottom", pady=20, padx=20, fill="x")

    def update_dashboard(self):
        ret, frame = self.cap.read()
        if ret:
            self.ia.processar_frame(frame)
            with self.ia.results_lock:
                for face in self.ia.faces_detectadas:
                    loc = face.get("box")
                    nome = face.get("nome")
                    conf = face.get("conf")
                    land = face.get("landmarks")
                    is_alive = face.get("liveness", False)
                    has_epi = face.get("epi", False)
                    
                    if land: self._desenhar_mapa_termico(frame, land, conf)
                    
                    top, right, bottom, left = loc
                    # Cor dinâmica: Verde se tudo OK, Vermelho se faltar algo (EPI ou Liveness)
                    color_status = (63, 185, 59) if (nome != "DESCONHECIDO" and is_alive and has_epi) else (73, 81, 248)
                    cv2.rectangle(frame, (left, top), (right, bottom), color_status, 2)
                    
                    # HUD Indicadores
                    cv2.putText(frame, f"{nome} [{conf:.0%}]", (left, top - 10), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                    
                    alive_txt = "HUMAN VALIDATED" if is_alive else "SCANNING LIVENESS..."
                    alive_col = (0, 255, 0) if is_alive else (0, 255, 255)
                    cv2.putText(frame, alive_txt, (left, bottom + 20), cv2.FONT_HERSHEY_DUPLEX, 0.5, alive_col, 1)

                    epi_txt = "HELMET: OK" if has_epi else "HELMET: REQUIRED"
                    epi_col = (0, 255, 0) if has_epi else (0, 0, 255)
                    cv2.putText(frame, epi_txt, (left, bottom + 40), cv2.FONT_HERSHEY_DUPLEX, 0.5, epi_col, 1)

                    # --- GATILHO INTELIGENTE KRONOS ---
                    agora = time.time()
                    if nome != "DESCONHECIDO" and conf > 0.60 and is_alive:
                        if (agora - self.ultimo_registro_tempo > 15):
                            self.ultimo_registro_tempo = agora
                            self._registrar_acesso_grafico()
                            # Dispara o evento: Passamos o status do EPI para a função de alerta
                            threading.Thread(target=self._processar_evento_acesso, 
                                             args=(frame.copy(), nome, conf, has_epi), daemon=True).start()

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(img, size=(850, 480))
            self.video_label.configure(image=ctk_img)
        self.after(20, self.update_dashboard)

    def _processar_evento_acesso(self, frame_captura, nome, conf, has_epi):
        try:
            foto_path = self.ia._verificar_e_capturar(frame_captura, nome, conf)
            
            if has_epi:
                self.add_log(f"ACESSO LIBERADO: {nome}", tipo="sucesso")
                # Só solicita abertura real se tiver EPI
                threading.Thread(target=self.controlador.solicitar_abertura, args=(nome, conf), daemon=True).start()
                status_msg = "✅ ACESSO COMPLETO (Identidade + EPI)"
            else:
                self.add_log(f"VIOLAÇÃO EPI: {nome} tentou acesso sem capacete", tipo="perigo")
                status_msg = "⚠️ ALERTA: Usuário detectado SEM CAPACETE!"

            if foto_path:
                # Enviamos o alerta para o Telegram com a mensagem personalizada sobre o EPI
                threading.Thread(target=self.alerta.enviar_alerta_foto, 
                                 args=(foto_path, f"{nome} | {status_msg}", conf), daemon=True).start()
        except Exception as e:
            print(f"⚠️ [KRONOS ERROR] Falha no fluxo: {e}")

    def add_log(self, msg, tipo="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("0.0", f"[{timestamp}] {msg.strip()}\n")
        
    def alternar_tema(self):
        self.current_theme = "dark" if self.theme_switch.get() == "dark" else "light"
        ctk.set_appearance_mode(self.current_theme.capitalize())
        self.theme_colors = self.colors[self.current_theme]
        self._aplicar_tema()
        self._atualizar_grafico_estilo()

    def _aplicar_tema(self):
        c = self.theme_colors
        self.video_frame.configure(border_color=c["border"], fg_color=c["bg"])
        self.sidebar.configure(fg_color=c["card"])
        self.graph_frame.configure(border_color=c["border"], fg_color=c["card"])
        self.log_box.configure(fg_color="#0D1117" if self.current_theme=="dark" else "#FFFFFF", text_color=c["text"], border_color=c["border"], border_width=1)
        self.logo_label.configure(text_color=c["accent"])
        self.status_indicator.configure(text_color=c["success"])
        self.btn_lock.configure(fg_color=self.colors["dark"]["danger"], hover_color="#B33A35")

    def _setup_matplotlib_graph(self):
        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        self._atualizar_grafico_estilo()

    def _atualizar_grafico_estilo(self):
        c = self.theme_colors
        self.ax.clear()
        self.fig.patch.set_facecolor(c["card"])
        self.ax.set_facecolor(c["card"])
        self.ax.tick_params(colors=c["text"], labelsize=8)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        self._desenhar_grafico()

    def _desenhar_grafico(self):
        if not self.dados_grafico_tempo: return
        self.ax.plot(self.dados_grafico_tempo, self.dados_grafico_contagem, color=self.theme_colors["accent"], linewidth=2)
        self.ax.set_xlim(datetime.now() - timedelta(hours=1), datetime.now())
        self.canvas.draw()

    def _inicializar_dados_grafico_dummy(self):
        agora = datetime.now()
        for i in range(60):
            self.dados_grafico_tempo.append(agora - timedelta(minutes=60-i))
            self.dados_grafico_contagem.append(random.randint(0, 2))

    def _registrar_acesso_grafico(self):
        agora = datetime.now().replace(second=0, microsecond=0)
        if agora not in self.dados_grafico_tempo:
            self.dados_grafico_tempo.append(agora)
            self.dados_grafico_contagem.append(1)
        else:
            self.dados_grafico_contagem[self.dados_grafico_tempo.index(agora)] += 1
        self._desenhar_grafico()

    def bloqueio_emergencia(self):
        self.add_log("!!! PROTOCOLO OMEGA ATIVADO !!!", "perigo")

    def on_closing(self):
        self.cap.release()
        plt.close(self.fig)
        self.destroy()
        sys.exit(0)