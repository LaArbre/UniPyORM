from typing import Any, List, Dict, Tuple
from .model import Model

class ViewResult:
    def __init__(self, rows: List[Dict[str, Any]]):
        self._rows = rows

    def all(self) -> List[Dict[str, Any]]:
        return self._rows

    def __getitem__(self, index: int) -> Dict[str, Any]:
        return self._rows[index]

    def __len__(self) -> int:
        return len(self._rows)


class View:
    def __init__(self, base_model, name=None):
        if not issubclass(base_model, Model):
            raise TypeError("base_model doit être une classe Model")
        self.base_model = base_model
        self.name = name or base_model.__name__ + "View"
        self._select_cols = list(base_model._columns.keys())
        self._joins = []  # Liste de tuples : (source_model, source_col, target_model, target_cols)

    def select(self, model_cls, columns=None):
        cols = columns or list(model_cls._columns.keys())
        self._select_cols = cols
        return self  # pour chaînage

    def join(self, source_model, source_col, target_model, target_cols=None):
        self._joins.append((source_model, source_col, target_model, target_cols or list(target_model._columns.keys())))
        return self

    def validate(self):
        base_rows = self.base_model.all()
        result = []

        for row in base_rows:
            row_dict = {col: getattr(row, col) for col in self._select_cols}

            # Appliquer les jointures
            for src_model, src_col, tgt_model, tgt_cols in self._joins:
                fk_obj = getattr(row, src_col)
                if fk_obj is None:
                    for c in tgt_cols:
                        row_dict[c] = None
                else:
                    for c in tgt_cols:
                        row_dict[c] = getattr(fk_obj, c)
            result.append(row_dict)

        return result
