import sqlite3
import pymysql
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

def record_history(log: Dict[str, Any], table_name: str, action: str, keys: List[str], values: Dict[str, Any]):
    log["cursor"].execute("""
        INSERT INTO history (table_name, action, keys, text_values, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        table_name,
        action,
        ",".join(keys) if isinstance(keys, (list, tuple)) else str(keys),
        json.dumps(values, ensure_ascii=False),
        datetime.now().isoformat()
    ))
    log["connect"].commit()


class Database:

    def __init__(self):
        self.use_mysql = bool(os.getenv("DB_SQL", False))
        if self.use_mysql:
            self.data: Dict[str, Any] = {
                "connect": pymysql.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    user=os.getenv("DB_USER", "root"),
                    password=os.getenv("DB_PASSWORD", ""),
                    database=os.getenv("DB_NAME", ""),
                    charset="utf8mb4",
                    cursorclass=pymysql.cursors.Cursor
                )
            }
            self.placeholder = "%s"
        else:
            self.data: Dict[str, Any] = {
                "connect": sqlite3.connect(os.getenv("DB_BASE_PATH", "local.db"))
            }
            self.placeholder = "?"

        self.data["cursor"] = self.data["connect"].cursor()

        # Journalisation
        self.log: Dict[str, Any] = {"connect": sqlite3.connect(os.getenv("DB_LOG_PATH", "logs.db"))}
        self.log["cursor"] = self.log["connect"].cursor()
        self.log["cursor"].execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                action TEXT,
                keys TEXT,
                text_values TEXT,
                timestamp TEXT
            )
        """)
        self.log["connect"].commit()

    # --------------------- TABLE ---------------------
    def table_exists(self, table_name: str) -> bool:
        if self.use_mysql:
            self.data["cursor"].execute("SHOW TABLES LIKE %s", (table_name,))
        else:
            self.data["cursor"].execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return self.data["cursor"].fetchone() is not None

    def create_table(self, table_name: str, columns: Dict[str, Any]) -> None:
        if self.table_exists(table_name):
            return

        col_defs = [columns[col].sql_definition(col) for col in columns]
        query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(col_defs)})'

        self.data["cursor"].execute(query)
        self.data["connect"].commit()

    # --------------------- CRUD ---------------------
    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        filtered_data = {k: v for k, v in data.items() if k != "id"}
        keys = ", ".join(f'"{k}"' for k in filtered_data)
        holder = (f"{self.placeholder}, " * len(filtered_data))[:-2]
        query = f'INSERT INTO "{table_name}" ({keys}) VALUES ({holder})'

        self.data["cursor"].execute(query, tuple(filtered_data.values()))
        self.data["connect"].commit()

        record_history(self.log, table_name, "INSERT", list(filtered_data.keys()), filtered_data)
        return self.data["cursor"].lastrowid

    def update(self, table_name: str, data: Dict[str, Any], where: Dict[str, Any]) -> None:
        set_clause = ", ".join([f'"{k}" = {self.placeholder}' for k in data])
        where_clause = " AND ".join([f'"{k}" = {self.placeholder}' for k in where])
        query = f'UPDATE "{table_name}" SET {set_clause} WHERE {where_clause}'
        self.data["cursor"].execute(query, tuple(data.values()) + tuple(where.values()))
        self.data["connect"].commit()
        record_history(self.log, table_name, "UPDATE", list(data.keys()), data)

    def delete(self, table_name: str, where: Dict[str, Any]) -> None:
        where_clause = " AND ".join([f'"{k}" = {self.placeholder}' for k in where])
        query = f'DELETE FROM "{table_name}" WHERE {where_clause}'
        self.data["cursor"].execute(query, tuple(where.values()))
        self.data["connect"].commit()
        record_history(self.log, table_name, "DELETE", list(where.keys()), where)

    def select(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Any, ...]]:
        column_part = ", ".join(f'"{c}"' for c in columns) if columns else "*"
        where = where or {}
        if where:
            conditions = [f'"{k}" = {self.placeholder}' for k in where]
            where_clause = " WHERE " + " AND ".join(conditions)
            params = tuple(where.values())
        else:
            where_clause = ""
            params = ()

        query = f'SELECT {column_part} FROM "{table_name}"{where_clause}'
        self.data["cursor"].execute(query, params)
        return self.data["cursor"].fetchall()

    # --------------------- FERMETURE ---------------------
    def close(self) -> None:
        self.data["connect"].close()
        self.log["connect"].close()
