import sys
import os
from dotenv import load_dotenv

# Importações dos módulos internos da KRONOS
from core.motor_ia import KronosIA
from core.database import KronosDatabase
from hardware.controlador import KronosControlador
from gui.dashboard import KronosDashboard

def inicializar_sistema():
    print("""
    #################################################
    #                                               #
    #          KRONOS DEFENSE V1.0                  #
    #       INDUSTRIAL ACCESS CONTROL               #
    #                                               #
    #################################################
    """)
    
    # 1. Carrega Variáveis de Ambiente
    load_dotenv()
    
    try:
        # 2. Inicializa Banco de Dados Único (Módulo 4)
        # Criamos a conexão centralizada aqui
        db = KronosDatabase()
        
        # 3. Inicializa Controlador de Hardware (Módulo 1)
        # Injetamos a instância do banco para evitar múltiplas conexões
        controlador = KronosControlador(db_instancia=db)
        
        # 4. Inicializa Motor de IA (Módulo 2)
        motor_ia = KronosIA(db_path="db")
        
        # 5. Inicializa Interface Gráfica (Módulo 3)
        # A Dashboard utiliza a IA e o Controlador já configurado
        print("🚀 [KRONOS] Iniciando Interface de Comando...")
        app = KronosDashboard(motor_ia, controlador)
        
        # Protocolo de fechamento seguro
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # 6. BOOT TOTAL DO SISTEMA
        app.mainloop()
        
    except Exception as e:
        print(f"❌ [KRONOS CRITICAL ERROR] Falha no boot do sistema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    inicializar_sistema()