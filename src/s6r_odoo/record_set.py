# Copyright (C) 2024 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from .record import OdooRecord

class OdooRecordSet(set):
    _odoo = None
    _model = None

    def __init__(self, seq=(), model=None):
        super().__init__(seq)
        if model:
            self._model = model
            self._odoo = self._model._odoo


    def save(self, batch_size=100, skip_line=0):
        values_list = [r.get_update_values() for r in self]
        self._model.load_batch(values_list, batch_size=batch_size, skip_line=skip_line)
        for r in self:
            r._updated_values = {}
        return True

    def get_ids(self):
        return [r.id for r in self]

    def unlink(self):
        ids = self.get_ids()
        self._model.unlink(ids)
        for key in ids:
            self._model._cache.pop(key, None)
        self.clear()
