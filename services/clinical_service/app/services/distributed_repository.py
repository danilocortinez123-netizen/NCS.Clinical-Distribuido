import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Any

from ..config import NODES_CONFIG, get_node_for_document


class DistributedRepository:

    def __init__(self):
        self.nodes = NODES_CONFIG

    def _connect(self, node: dict):
        return psycopg2.connect(
            host=node["host"],
            port=node["port"],
            user=node["user"],
            password=node["password"],
            dbname=node["dbname"],
        )

    def execute_query_all_nodes(self, query: str) -> dict[str, Any]:
        resultados = []
        nodos_estado = []

        for node in self.nodes:
            nodo_info = {"nodo": node["display"], "estado": "DOWN", "error": None}
            try:
                conn = self._connect(node)
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query)
                    filas = cur.fetchall()
                    resultados.extend(filas)
                conn.close()
                nodo_info["estado"] = "UP"
            except Exception as e:
                nodo_info["error"] = str(e)

            nodos_estado.append(nodo_info)

        return {"resultados": resultados, "nodos_estado": nodos_estado}

    def insert_encounter(self, data: dict) -> dict[str, Any]:
        documento_id = int(data["documento_id"])
        node = get_node_for_document(documento_id)

        columnas = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        valores = list(data.values())
        query = f"INSERT INTO atencion ({columnas}) VALUES ({placeholders}) RETURNING atencion_id"

        try:
            conn = self._connect(node)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, valores)
                result = cur.fetchone()
                conn.commit()
            conn.close()

            return {
                "success": True,
                "atencion_id": result["atencion_id"] if result else None,
                "nodo": node["display"],
                "message": f"Encounter creado en {node['display']}",
            }
        except Exception as e:
            raise Exception(f"Error al insertar encounter: {str(e)}")

    def insert_observation(self, data: dict) -> dict[str, Any]:
        import uuid
        if "tecnologia_id" not in data or not data["tecnologia_id"]:
            data["tecnologia_id"] = str(uuid.uuid4())

        documento_id = int(data["documento_id"])
        node = get_node_for_document(documento_id)

        columnas = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        valores = list(data.values())
        query = f"INSERT INTO tecnologia_salud ({columnas}) VALUES ({placeholders})"

        try:
            conn = self._connect(node)
            with conn.cursor() as cur:
                cur.execute(query, valores)
                conn.commit()
            conn.close()

            return {
                "success": True,
                "tecnologia_id": data["tecnologia_id"],
                "nodo": node["display"],
                "message": f"Observation creada en {node['display']}",
            }
        except Exception as e:
            raise Exception(f"Error al insertar observation: {str(e)}")

    def insert_condition(self, data: dict) -> dict[str, Any]:
        documento_id = int(data["documento_id"])
        node = get_node_for_document(documento_id)

        columnas = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        valores = list(data.values())
        query = f"INSERT INTO diagnostico ({columnas}) VALUES ({placeholders}) RETURNING diagnostico_id"

        try:
            conn = self._connect(node)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, valores)
                result = cur.fetchone()
                conn.commit()
            conn.close()

            return {
                "success": True,
                "diagnostico_id": result["diagnostico_id"] if result else None,
                "nodo": node["display"],
                "message": f"Condition creada en {node['display']}",
            }
        except Exception as e:
            raise Exception(f"Error al insertar condition: {str(e)}")

    def insert_discharge(self, data: dict) -> dict[str, Any]:
        documento_id = int(data["documento_id"])
        node = get_node_for_document(documento_id)

        columnas = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        valores = list(data.values())
        query = f"INSERT INTO egreso ({columnas}) VALUES ({placeholders}) RETURNING egreso_id"

        try:
            conn = self._connect(node)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, valores)
                result = cur.fetchone()
                conn.commit()
            conn.close()

            return {
                "success": True,
                "egreso_id": result["egreso_id"] if result else None,
                "nodo": node["display"],
                "message": f"Discharge creado en {node['display']}",
            }
        except Exception as e:
            raise Exception(f"Error al insertar discharge: {str(e)}")

    def check_node_health(self) -> list[dict[str, Any]]:
        nodes_status = []
        for node in self.nodes:
            info = {
                "id": node["display"],
                "status": "unknown",
                "shard": node["shard"],
            }
            try:
                conn = self._connect(node)
                conn.close()
                info["status"] = "running"
            except Exception as e:
                info["status"] = "exited"
                info["error"] = str(e)
            nodes_status.append(info)
        return nodes_status
