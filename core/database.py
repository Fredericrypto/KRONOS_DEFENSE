import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class KronosDatabase:
    def __init__(self):
        self.conn = None
        try:
            db_name = os.getenv("DB_NAME", "kronos_db")
            db_user = os.getenv("DB_USER", "postgres")
            db_pass = os.getenv("DB_PASSWORD", "")
            
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                database=db_name,
                user=db_user,
                password=db_pass
            )
            print(f"🛡️ [KRONOS DATABASE] Conexão Única estabelecida com '{db_name}'")
            
            # Garante que a estrutura física existe antes de qualquer operação
            self._verificar_tabela()
            
        except Exception as e:
            print(f"⚠️ [DATABASE ERROR] Falha Crítica: {e}")

    def _verificar_tabela(self):
        """Cria a tabela de logs automaticamente se não existir no boot."""
        try:
            cursor = self.conn.cursor()
            query = """
            CREATE TABLE IF NOT EXISTS logs_acesso (
                id SERIAL PRIMARY KEY,
                nome_detectado VARCHAR(100),
                confianca FLOAT,
                status_acesso VARCHAR(50),
                data_hora TIMESTAMP
            );
            """
            cursor.execute(query)
            self.conn.commit()
            cursor.close()
            print("✅ [KRONOS DATABASE] Estrutura de tabelas verificada/pronta.")
        except Exception as e:
            print(f"⚠️ [DATABASE ERROR] Falha ao criar tabela: {e}")

    def registrar_acesso(self, nome, confianca, status):
        """Grava o evento de acesso no banco de dados."""
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            query = "INSERT INTO logs_acesso (nome_detectado, confianca, status_acesso, data_hora) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (str(nome), float(confianca), status, datetime.now()))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            print(f"⚠️ [KRONOS DATABASE] Erro ao gravar log: {e}")
            if self.conn: self.conn.rollback()