import cv2
import face_recognition
import numpy as np
import threading
import os
import time
from datetime import datetime
from ultralytics import YOLO  # Necessário: pip install ultralytics

class KronosIA:
    def __init__(self, db_path="db"):
        self.db_path = db_path
        self.capturas_path = os.path.join(db_path, "capturas")
        self.encodings_autorizados = []
        self.nomes_autorizados = []
        self.results_lock = threading.Lock()
        self.faces_detectadas = []
        self.ultimo_alerta = {} 
        
        # --- NOVOS ATRIBUTOS ELITE ---
        # Carrega modelo YOLOv8 para Capacete (existem modelos prontos no hub da ultralytics)
        # Se não tiver o .pt, ele baixará um padrão, mas recomendo um treinado para 'helmet'
        self.modelo_epi = YOLO('yolov8n.pt') 
        self.olhos_historico = {} # Para rastrear piscadas por pessoa
        
        if not os.path.exists(self.capturas_path):
            os.makedirs(self.capturas_path)
            
        self._limpar_evidencias_antigas()
        self._carregar_base_militar()

    def _carregar_base_militar(self):
        print("🛡️ [KRONOS IA] Carregando protocolos...")
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
            
        for arquivo in os.listdir(self.db_path):
            if arquivo.lower().endswith((".jpg", ".png", ".jpeg")):
                img = face_recognition.load_image_file(os.path.join(self.db_path, arquivo))
                encs = face_recognition.face_encodings(img)
                if encs:
                    self.encodings_autorizados.append(encs[0])
                    self.nomes_autorizados.append(os.path.splitext(arquivo)[0].upper())
        print(f"✅ [KRONOS IA] {len(self.nomes_autorizados)} Operários carregados.")

    def _calcular_ear(self, pontos_olho):
        """Calcula o Eye Aspect Ratio para detectar piscadas."""
        # Distâncias verticais
        v1 = np.linalg.norm(np.array(pontos_olho[1]) - np.array(pontos_olho[5]))
        v2 = np.linalg.norm(np.array(pontos_olho[2]) - np.array(pontos_olho[4]))
        # Distância horizontal
        h = np.linalg.norm(np.array(pontos_olho[0]) - np.array(pontos_olho[3]))
        return (v1 + v2) / (2.0 * h)

    def processar_frame(self, frame):
        # 1. Detecção de EPI (Capacete) com YOLO
        # Filtramos apenas a classe 'person' e 'helmet' (dependendo do modelo)
        resultados_yolo = self.modelo_epi(frame, conf=0.5, verbose=False)
        tem_capacete = False
        for r in resultados_yolo:
            for c in r.boxes.cls:
                nome_classe = self.modelo_epi.names[int(c)]
                if nome_classe in ['helmet', 'hat']: # Classes comuns em datasets de segurança
                    tem_capacete = True

        # 2. Processamento Facial
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        locs = face_recognition.face_locations(rgb_small)
        landmarks = face_recognition.face_landmarks(rgb_small, locs)
        encs = face_recognition.face_encodings(rgb_small, locs)

        novos_resultados = []
        
        for enc, loc, land in zip(encs, locs, landmarks):
            # Reconhecimento
            matches = face_recognition.compare_faces(self.encodings_autorizados, enc, tolerance=0.5)
            nome = "DESCONHECIDO"
            confianca = 0.0

            distancias = face_recognition.face_distance(self.encodings_autorizados, enc)
            if len(distancias) > 0:
                melhor_match = np.argmin(distancias)
                if matches[melhor_match]:
                    nome = self.nomes_autorizados[melhor_match]
                    confianca = 1 - distancias[melhor_match]

            # 3. ANTI-FRAUDE: Verificação de Piscada (Liveness)
            ear_esq = self._calcular_ear(land['left_eye'])
            ear_dir = self._calcular_ear(land['right_eye'])
            ear_medio = (ear_esq + ear_dir) / 2.0
            
            # Lógica simples: se EAR < 0.2, a pessoa piscou (não é uma foto estática)
            is_alive = False
            if nome not in self.olhos_historico: self.olhos_historico[nome] = []
            self.olhos_historico[nome].append(ear_medio)
            
            # Mantém apenas os últimos 30 frames
            if len(self.olhos_historico[nome]) > 30: self.olhos_historico[nome].pop(0)
            
            # Se houver uma variação brusca (piscada) no histórico, validamos como humano
            if any(v < 0.21 for v in self.olhos_historico[nome]):
                is_alive = True

            t, r, b, l = loc
            land_orig = {feature: [(p[0]*4, p[1]*4) for p in pts] for feature, pts in land.items()}

            novos_resultados.append({
                "box": (t*4, r*4, b*4, l*4),
                "nome": nome,
                "conf": confianca,
                "landmarks": land_orig,
                "liveness": is_alive,     # NOVO
                "epi": tem_capacete       # NOVO
            })

        with self.results_lock:
            self.faces_detectadas = novos_resultados

    def _verificar_e_capturar(self, frame, nome, confianca):
        # Agora o acesso só é capturado se passar nos filtros extras (opcional aqui ou na GUI)
        agora = time.time()
        if nome != "DESCONHECIDO" and confianca > 0.60:
            if (nome not in self.ultimo_alerta or agora - self.ultimo_alerta[nome] > 15):
                self.ultimo_alerta[nome] = agora
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ALERTA_{nome}_{timestamp}.jpg"
                path = os.path.join(self.capturas_path, filename)
                cv2.imwrite(path, frame)
                return path 
        return None

    def _limpar_evidencias_antigas(self):
        try:
            if not os.path.exists(self.capturas_path): return
            arquivos_removidos = 0
            limite = time.time() - (7 * 86400) 
            for f in os.listdir(self.capturas_path):
                caminho = os.path.join(self.capturas_path, f)
                if os.path.isfile(caminho) and os.path.getmtime(caminho) < limite:
                    os.remove(caminho)
                    arquivos_removidos += 1
            print(f"✅ [KRONOS PREVENT] Limpeza concluída ({arquivos_removidos} removidos).")
        except Exception as e:
            print(f"⚠️ [KRONOS IA ERROR] Falha na autolimpeza: {e}")