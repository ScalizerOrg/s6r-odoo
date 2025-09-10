# Copyright (C) 2025 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import csv
import os
from datetime import datetime
import sys
import xlrd
import openpyxl

def get_file_full_path(path):
    if not path:
        return ''
    param_path = path
    if not os.path.isfile(path):
        path = os.path.join(os.path.dirname(sys.argv[0]), param_path)
    if not os.path.isfile(path):
        raise FileNotFoundError('%s not found!' % param_path)
    return path

class FileImport:
    name_create_enabled_fields = ''
    context = False
    limit = 0
    skip_line = 0
    batch_size = 100
    thread = 0
    ignore_errors = []

    def __init__(self, odoo, **kwargs):
        self.odoo = odoo
        self.logger = odoo.logger
        self._context = odoo._context.copy()
        self.set_params(kwargs)

    @staticmethod
    def parse_csv_file(file_path, delimiter=","):
        vals = []
        with open(os.path.dirname(__file__) + '/' + file_path, 'r') as csvfile:
            reader = csv.reader(csvfile, skipinitialspace=True, delimiter=delimiter)
            next(reader)
            for line in reader:
                vals.append(line)
        return vals

    @staticmethod
    def clean_field(field):
        if "/" in field:
            field = field.split("/")[0]
        if "." in field:
            field = field.split(".")[0]
        return field

    @staticmethod
    def field_check_integer(field, data):
        if field['name'] == 'id':
            return data
        if not data:
            return data
        data = int(data)
        return data

    @staticmethod
    def field_check_float(field, data):
        if not data:
            return data
        if isinstance(data, str) and "," in data:
            data = data.replace(',', '.')
        data = float(data)
        return data

    @staticmethod
    def field_check_monetary(field, data):
        return FileImport.field_check_float(field, data)

    @staticmethod
    def field_check_date(field, data):
        if not data:
            return data
        format_ok = False
        try:
            datetime.strptime(data, '%Y-%m-%d')
            format_ok = True
        except:
            format_ok = False
        if not format_ok:
            try:
                data = datetime.strptime(data, '%d/%m/%Y').strftime('%Y-%m-%d')
                format_ok = True
            except Exception as e:
                format_ok = False
        return data

    @staticmethod
    def field_check_datetime(field, data):
        if not data:
            return data
        format_ok = False
        try:
            datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
            format_ok = True
        except Exception as e:
            format_ok = False
        if not format_ok:
            try:
                data = datetime.strptime(data, '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                format_ok = True
            except Exception as e:
                format_ok = False
        if not format_ok:
            data = FileImport.field_check_date(field, data)
            data += " 00:00:00"

        return data

    def parse_csv_file_dictreader(self, file_path, fields, delimiter=","):
        vals = []
        file_path = get_file_full_path(file_path)
        with open(file_path, 'r') as csvfile:
            header = csvfile.readline()
            csvfile.seek(0, 0)
            if delimiter not in header:
                if ';' in header:
                    delimiter = ';'
            reader = csv.DictReader(csvfile, skipinitialspace=True, delimiter=delimiter, quotechar='"')
            cc = 0
            line_count = 0
            for line in reader:
                if self.skip_line and cc < self.skip_line:
                    cc += 1
                    continue
                if self.limit and line_count == self.limit:
                    break
                cc += 1
                line_count += 1
                for field in line:
                    clean_field = FileImport.clean_field(field)
                    method = "field_check_%s" % (fields.get(clean_field,{}).get('type'))
                    if hasattr(FileImport, method):
                        method_to_call = getattr(FileImport, method)
                        line[field] = method_to_call(fields[clean_field], line[field])
                vals.append(line)
        return vals

    def set_params(self, params):
        self.name_create_enabled_fields = params.get('name_create_enabled_fields', '')
        self.context = params.get('context', False)
        self.limit = params.get('limit', 0)
        self.skip_line = params.get('skip_line', 0)
        self.batch_size = params.get('batch_size', 100)
        self.thread = params.get('thread', 0)
        self.ignore_errors = params.get('ignore_errors', [])

        if self.name_create_enabled_fields:
            create_enabled_fields = dict([x, 1] for x in set(self.name_create_enabled_fields.split(",")))
            self._context.update({'name_create_enabled_fields': create_enabled_fields})
        if self.context:
            self._context.update(self.context)

    def import_csv(self, file_path, model, **kwargs):
        self.set_params(kwargs)
        fields = self.odoo.get_fields(model)
        raw_datas = self.parse_csv_file_dictreader(file_path, fields)
        if raw_datas:
            return self.odoo.load_batch(model, raw_datas, batch_size=self.batch_size)

    def _xls_rows_to_values(self, rows, fields):
        values = []
        headers = rows.pop(0)
        for row in rows:
            value = {}
            for header in [h for h in headers if h]:
                value[header] = row[headers.index(header)]
            values.append(self.check_values(value, fields))
        if self.skip_line:
            values = values[self.skip_line:]
        if self.limit:
            values = values[:self.limit]
        return values

    def check_values(self, values, fields):
        for field in values:
            clean_field = FileImport.clean_field(field)
            method = "field_check_%s" % (fields.get(clean_field, {}).get('type'))
            if hasattr(FileImport, method):
                method_to_call = getattr(FileImport, method)
                values[field] = method_to_call(fields[clean_field], values[field])
        return values

    def read_xls(self, file_path):
        file_path = get_file_full_path(file_path)
        book = xlrd.open_workbook(file_path)
        sheets = book.sheet_names()
        sheet = sheets[0]
        return self._read_xls_book(book, sheet)

    def read_xlsx(self, file_path):
        file_path = get_file_full_path(file_path)
        book = openpyxl.load_workbook(file_path)
        sheets = book.sheetnames
        sheet = sheets[0]
        return self._read_xlsx_book(book, sheet)

    def _read_xlsx_book(self, book, sheet_name):
        sheet = book.get_sheet_by_name(sheet_name)
        rows = []
        for row in sheet.rows:
            values = []
            for colx, cell in enumerate(row, 1):
                if cell.data_type == 'n' and cell.value is not None:
                    is_float = cell.value % 1 != 0.0
                    values.append(str(cell.value) if is_float else str(int(cell.value)))
                elif cell.data_type == 'd':
                    dt = cell.value
                    value = dt.strftime("%Y-%m-%d %H:%M:%S") if isinstance(dt, datetime) else dt.strftime("%Y-%m-%d")
                    values.append(value)
                elif cell.data_type == 'b':
                    values.append(u'True' if cell.value else u'False')
                elif cell.value is not None:
                    values.append(cell.value)
            if any(x for x in values if x.strip()):
                rows.append(values)
        return rows

    def _read_xls_book(self, book, sheet_name):
        sheet = book.sheet_by_name(sheet_name)
        rows = []
        for row in map(sheet.row, range(sheet.nrows)):
            values = []
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    value = str(cell.value) if is_float else str(int(cell.value))
                    values.append(value)
                elif cell.ctype is xlrd.XL_CELL_DATE:
                    is_datetime = cell.value % 1 != 0.0
                    dt = datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                    value = dt.strftime("%Y-%m-%d %H:%M:%S") if is_datetime else dt.strftime("%Y-%m-%d")
                    values.append(value)
                elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
                    values.append(u'True' if cell.value else u'False')
                else:
                    values.append(cell.value)
            if any(x for x in values if x.strip()):
                rows.append(values)

        return rows

    def import_xls(self, file_path, model, **kwargs):
        self.set_params(kwargs)
        fields = self.odoo.get_fields(model)
        rows = self.read_xls(file_path)
        raw_datas = self._xls_rows_to_values(rows, fields)
        if raw_datas:
            return self.odoo.load_batch(model, raw_datas, batch_size=self.batch_size)

    def import_xlsx(self, file_path, model, **kwargs):
        self.set_params(kwargs)
        fields = self.odoo.get_fields(model)
        rows = self.read_xlsx(file_path)
        raw_datas = self._xls_rows_to_values(rows, fields)
        if raw_datas:
            return self.odoo.load_batch(model, raw_datas, batch_size=self.batch_size)
