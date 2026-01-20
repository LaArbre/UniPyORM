from .database import Database, record_history
from .sqltypes import *
from typing import Any, Dict, List, Optional, Type

database = Database()


class Model:
    def __init_subclass__(cls, **kwargs):
        cls._columns: Dict[str, SQLType] = {
            name: value for name, value in cls.__dict__.items() if hasattr(value, "sql_definition")
        }

        primary_keys = [name for name, col in cls._columns.items() if getattr(col, "primary_key", False)]
        if len(primary_keys) == 0:
            raise ValueError(f"La classe {cls.__name__} doit avoir une clé primaire.")
        if len(primary_keys) > 1:
            raise ValueError(f"La classe {cls.__name__} ne peut avoir qu'une seule clé primaire (trouvé {primary_keys}).")

        cls._child_class = type(
            f"_{cls.__name__}Row",
            (ChildModel,),
            {"_parent": cls, "_columns": cls._columns}
        )

        database.create_table(cls.__name__, cls._columns)

    @classmethod
    def _prepare_value(cls, name: str, value: Any) -> Any:
        col = cls._columns[name]

        if value is None and col.default is not None:
            value = col.default() if callable(col.default) else col.default

        if not col.validate(value):
            raise TypeError(f"Valeur invalide pour la colonne {name}: {value!r}")

        return col.to_sql(value)

    @classmethod
    def new(cls, **kwargs) -> "ChildModel":
        data: Dict[str, Any] = {}
        for name, col in cls._columns.items():
            if getattr(col, "primary_key", False) and name in kwargs:
                raise ValueError(f"La clé primaire '{name}' est auto-incrémentée et ne doit pas être fournie")

            value = kwargs.get(name, None)
            data[name] = cls._prepare_value(name, value)

        pk_name = next(name for name, col in cls._columns.items() if getattr(col, "primary_key", False))
        row_id = database.insert(cls.__name__, {k: v for k, v in data.items() if k != pk_name})
        data[pk_name] = row_id

        for k, col in cls._columns.items():
            data[k] = col.from_sql(data[k])

        return cls._child_class(**data)

    @classmethod
    def get(cls, **where) -> Optional["ChildModel"]:
        if not where or not isinstance(where, dict):
            raise ValueError("Le paramètre 'where' doit être un dictionnaire non vide")

        rows = database.select(cls.__name__, where=where)
        if not rows:
            return None
        if len(rows) > 1:
            raise ValueError(f"get() a trouvé plusieurs résultats pour {where}")

        data = dict(zip(cls._columns.keys(), rows[0]))
        for k, col in cls._columns.items():
            data[k] = col.from_sql(data[k])

        return cls._child_class(**data)

    @classmethod
    def all(cls) -> List["ChildModel"]:
        rows = database.select(cls.__name__)
        result = []
        for row in rows:
            data = dict(zip(cls._columns.keys(), row))
            for k, col in cls._columns.items():
                data[k] = col.from_sql(data[k])
            result.append(cls._child_class(**data))
        return result

    @classmethod
    def delete(cls, **where) -> None:
        if not where:
            raise ValueError("delete() nécessite un filtre non vide")
        database.delete(cls.__name__, where)


class ChildModel:
    _parent: Type[Model] = None
    _columns: Dict[str, SQLType] = {}

    def __init__(self, **kwargs):
        for col, value in kwargs.items():
            object.__setattr__(self, col, value)

    def __getattribute__(self, name: str) -> Any:
        val = object.__getattribute__(self, name)
        columns: Dict[str, SQLType] = object.__getattribute__(self, "_columns")
        col = columns.get(name)

        if not isinstance(col, ForeignKey) or val is None or not isinstance(val, int):
            return val

        obj = col.from_sql(val)
        object.__setattr__(self, name, obj)
        return obj

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self._columns:
            value = self._parent._prepare_value(name, value)
        object.__setattr__(self, name, value)

    def save(self) -> None:
        pk_name = next(name for name, col in self._columns.items() if getattr(col, "primary_key", False))
        pk_value = getattr(self, pk_name, None)
        if pk_value is None:
            raise ValueError("Impossible de sauvegarder : aucune clé primaire")

        data = {c: self._columns[c].to_sql(getattr(self, c)) for c in self._columns if c != pk_name}
        database.update(self._parent.__name__, data, {pk_name: pk_value})

    def delete(self) -> None:
        pk_name = next(name for name, col in self._columns.items() if getattr(col, "primary_key", False))
        pk_value = getattr(self, pk_name, None)
        if pk_value is None:
            raise ValueError("Impossible de supprimer : aucune clé primaire")
        database.delete(self._parent.__name__, {pk_name: pk_value})
        setattr(self, pk_name, None)

    def __repr__(self) -> str:
        cols = {c: getattr(self, c, None) for c in self._columns}
        return f"<{self._parent.__name__}Row {cols}>"
