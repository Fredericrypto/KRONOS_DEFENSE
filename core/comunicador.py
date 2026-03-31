import requests
import os
from dotenv import load_dotenv

load_dotenv()

class KronosAlert:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        # Removi a barra extra no final para evitar erro de URL dupla //
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    def enviar_alerta_foto(self, foto_path, nome, confianca):
        # Texto simples para garantir que nada trave a API
        caption = f"🛡️ KRONOS DEFENSE V1.0\n👤 Operário: {nome}\n🎯 Confiança: {confianca:.2%}\n🔓 ACESSO REGISTRADO"
        
        try:
            if not os.path.exists(foto_path):
                print(f"⚠️ [KRONOS] Foto não encontrada no caminho: {foto_path}")
                return

            with open(foto_path, 'rb') as foto:
                files = {'photo': foto}
                data = {'chat_id': self.chat_id, 'caption': caption} # Sem parse_mode por enquanto
                
                r = requests.post(f"{self.api_url}/sendPhoto", files=files, data=data, timeout=15)
                
                if r.status_code == 200:
                    print(f"✅ [TELEGRAM] FOTO ENVIADA: {nome}")
                else:
                    print(f"❌ [TELEGRAM] ERRO {r.status_code}: {r.text}")
                    
        except Exception as e:
            print(f"⚠️ [KRONOS] Erro crítico no Telegram: {e}")