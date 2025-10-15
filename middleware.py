
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuración de los nodos
NODOS = [
    {"host": "localhost", "port": 5433, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
    {"host": "localhost", "port": 5434, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
    {"host": "localhost", "port": 5435, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
]

def ejecutar_query_en_todos_los_nodos(query):
    resultados = []
    for nodo in NODOS:
        try:
            conn = psycopg2.connect(
                host=nodo["host"],
                port=nodo["port"],
                user=nodo["user"],
                password=nodo["password"],
                dbname=nodo["dbname"]
            )
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                filas = cur.fetchall()
                resultados.extend(filas)
            conn.close()
        except Exception as e:
            print(f"Error en nodo {nodo['port']}: {e}")
    return resultados

if __name__ == "__main__":
    consulta = "SELECT documento_id, nombre_completo, edad FROM usuario;"
    resultados = ejecutar_query_en_todos_los_nodos(consulta)
    for fila in resultados:
        print(fila)
