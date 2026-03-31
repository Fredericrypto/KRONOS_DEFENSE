import socket
import sys

def iniciar_simulador():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 65432))
        s.listen(1)
        print("🟢 [KRONOS] SIMULADOR ONLINE (Porta 65432)")
        
        while True:
            conn, addr = s.accept()
            data = conn.recv(1024)
            if data:
                print(f"📥 Token: {data.decode()[:10]}... OK!")
                conn.sendall(b"OPEN_OK")
            conn.close()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    iniciar_simulador()