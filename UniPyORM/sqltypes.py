from datetime import datetime
import json
from typing import Any

class SQLType:
    sql_name: str = "TEXT"

    def __init__(self, primary_key=False, unique=False, not_null=False, default=None):
        self.primary_key = primary_key
        self.unique = unique
        self.not_null = not_null
        self.default = default

    def to_sql(self, value: Any) -> Any:
        return value

    def from_sql(self, value: Any) -> Any:
        return value

    def validate(self, value: Any) -> bool:
        return True

    def sql_definition(self, name: str) -> str:
        parts = [f'"{name}"', self.sql_name]
        if self.primary_key:
            parts.append("PRIMARY KEY AUTOINCREMENT")
        if self.unique:
            parts.append("UNIQUE")
        if self.not_null:
            parts.append("NOT NULL")
        if self.default is not None and not callable(self.default):
            val = self._format_default_value(self.default)
            if val is not None:
                parts.append(f"DEFAULT {val}")
        return " ".join(parts)

    def _format_default_value(self, value: Any) -> str | None:
        if isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif value is None:
            return "NULL"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, datetime):
            return f"'{value.isoformat()}'"
        else:
            return None


class TEXT(SQLType):
    sql_name = "TEXT"
    def validate(self, value: Any) -> bool:
        return isinstance(value, str) or value is None


class INTEGER(SQLType):
    sql_name = "INTEGER"
    def to_sql(self, value: Any) -> int | None:
        return int(value) if value is not None else None
    def from_sql(self, value: Any) -> int | None:
        return int(value) if value is not None else None
    def validate(self, value: Any) -> bool:
        return isinstance(value, int) or value is None


class REAL(SQLType):
    sql_name = "REAL"
    def to_sql(self, value: Any) -> float | None:
        return float(value) if value is not None else None
    def from_sql(self, value: Any) -> float | None:
        return float(value) if value is not None else None


class DATETIME(SQLType):
    sql_name = "DATETIME"
    def to_sql(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        raise TypeError("DATETIME attend un objet datetime")
    def from_sql(self, value: str) -> datetime | None:
        return datetime.fromisoformat(value) if value else None


class BOOLEAN(SQLType):
    sql_name = "INTEGER"
    def to_sql(self, value: Any) -> int:
        return 1 if value else 0
    def from_sql(self, value: Any) -> bool:
        return bool(value)


class JSON(SQLType):
    sql_name = "TEXT"
    def to_sql(self, value: Any) -> str | None:
        return json.dumps(value, ensure_ascii=False) if value is not None else None
    def from_sql(self, value: str) -> Any:
        return json.loads(value) if value else None
    def validate(self, value: Any) -> bool:
        return value is None or isinstance(value, (dict, list, str, int, float, bool))


class ForeignKey(SQLType):
    def __init__(self, model_class, not_null=False, default=None):
        super().__init__(primary_key=False, not_null=not_null, default=default)
        self.model_class = model_class
        self.sql_name = "INTEGER"

    def to_sql(self, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, self.model_class._child_class):
            return value.id
        return int(value)

    def from_sql(self, value: Any) -> Any:
        if value is None:
            return None
        obj = self.model_class.get(id=value)
        if obj is None:
            raise ValueError(f"ForeignKey: aucun objet {self.model_class.__name__} trouvé pour id={value}")
        return obj

    def validate(self, value: Any) -> bool:
        ModelRow = self.model_class._child_class
        return value is None or isinstance(value, (int, ModelRow))
