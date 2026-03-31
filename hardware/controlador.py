import socket
import os
import time
from dotenv import load_dotenv
from core.database import KronosDatabase

load_dotenv()

# Altere o __init__ no seu controlador.py
class KronosControlador:
    def __init__(self, db_instancia=None):
        # Em vez de criar um novo, usa o que foi passado pelo main.py
        self.db = db_instancia
        
        if not self.db:
            print("⚠️ [KRONOS] Aviso: Controlador operando sem banco de dados.")
            
        self.host_porta = "127.0.0.1" 
        self.port_porta = 65432        
        self.token_secreto = os.getenv("KRONOS_SECRET_TOKEN", "TOKEN_PADRAO_123")

    def solicitar_abertura(self, nome, confianca):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self.host_porta, self.port_porta))
                s.sendall(self.token_secreto.encode())
                
                # Recebe e limpa a resposta
                raw_resposta = s.recv(1024).decode().strip()
                
                if "OPEN_OK" in raw_resposta:
                    print(f"🔓 [KRONOS] ACESSO LIBERADO: {nome}")
                    self._seguro_registrar_log(nome, confianca, "LIBERADO")
                    return True
                else:
                    print(f"⛔ [KRONOS] TOKEN RECUSADO. Resposta: '{raw_resposta}'")
                    self._seguro_registrar_log(nome, confianca, "RECUSADO")
                    return False
        except Exception as e:
            print(f"⚠️ [KRONOS ERROR] Porta Offline: {e}")
            return False

    def _seguro_registrar_log(self, nome, conf, status):
        """Evita que erros de banco travem o sistema principal"""
        try:
            if self.db:
                self.db.registrar_acesso(nome, conf, status)
        except:
            print("⚠️ [KRONOS] Falha silenciosa ao salvar log no Banco.")

    def negar_acesso(self, nome, confianca, motivo="DESCONHECIDO"):
        print(f"🚫 [KRONOS] ACESSO NEGADO: {nome} - MOTIVO: {motivo}")
        if self.db:
            self.db.registrar_acesso(nome, confianca, f"NEGADO_{motivo}")