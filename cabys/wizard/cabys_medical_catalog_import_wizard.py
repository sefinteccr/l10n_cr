# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from xlrd import open_workbook
import logging
import base64

_logger = logging.getLogger(__name__)

# Mapeo de columnas y encabezados (más mantenible)
PRODUCTS_MAP = {
    'code': 0,  # Columna 0: Código CABYS
    'description': 1  # Columna 1: Descripción del producto
}

HEADERS_MAP = [
    {'column': 0, 'header': 'Código Cabys'},
    {'column': 1, 'header': 'Descripción'}
]


class CabysCatalogImportWizard(models.TransientModel):
    _name = 'cabys.medical.catalog.import.wizard'
    _description = 'Importar Catálogo Médico CABYS desde Excel'

    cabys_excel_file = fields.Binary(
        string='Archivo Excel',
        required=True,
        help="Seleccione el archivo Excel con el catálogo CABYS médico (.xls o .xlsx)"
    )
    file_name = fields.Char(string="Nombre de archivo")
    notes = fields.Html(string="Notas", readonly=True, sanitize=False)
    button_enable = fields.Boolean(string="Habilitar Importación", default=False)

    def _validate_excel_file(self, excel_file):
        """Valida la estructura básica del archivo Excel"""
        try:
            workbook = open_workbook(file_contents=excel_file)
            xl_sheet = workbook.sheet_by_index(0)

            # Validar encabezados
            for header in HEADERS_MAP:
                cell = xl_sheet.cell(0, header['column'])
                if cell.value != header['header']:
                    return False, "El archivo no tiene el formato CABYS esperado"

            return True, "Archivo válido"
        except Exception as e:
            return False, f"Error al leer archivo: {str(e)}"

    def _analyze_excel_file(self):
        """Analiza el archivo Excel y devuelve los códigos encontrados"""
        if not self.cabys_excel_file:
            return []

        try:
            excel_file = base64.b64decode(self.cabys_excel_file)
            workbook = open_workbook(file_contents=excel_file)
            xl_sheet = workbook.sheet_by_index(0)

            codes = []
            for row in xl_sheet.get_rows():
                if row[0].value == HEADERS_MAP[0]['header']:  # Saltar encabezado
                    continue
                codes.append(row[PRODUCTS_MAP['code']].value)

            return codes
        except Exception as e:
            _logger.error("Error al analizar archivo Excel: %s", str(e))
            return []

    def _update_catalog_from_excel_file(self):
        """Actualiza el catálogo CABYS con los datos del archivo Excel"""
        medical_products_codes = []

        try:
            excel_file = base64.b64decode(self.cabys_excel_file)
            workbook = open_workbook(file_contents=excel_file)
            xl_sheet = workbook.sheet_by_index(0)

            _logger.info("Reseteando productos médicos existentes...")
            self.env['cabys.producto'].search([('cabys_medical', '=', True)]).write({'cabys_medical': False})

            _logger.info("Procesando archivo Excel...")
            for row in xl_sheet.get_rows():
                if row[0].value == HEADERS_MAP[0]['header']:  # Saltar encabezado
                    continue

                code = row[PRODUCTS_MAP['code']].value
                medical_products_codes.append(code)

                product = self.env['cabys.producto'].search([('codigo', '=', code)], limit=1)
                if product:
                    product.cabys_medical = True
                else:
                    _logger.warning("Producto CABYS no encontrado con código: %s", code)

            _logger.info("Proceso completado. %d productos procesados", len(medical_products_codes))
            return medical_products_codes

        except Exception as e:
            _logger.error("Error al procesar archivo Excel: %s", str(e))
            raise UserError(_("Error al procesar archivo Excel: %s") % str(e))

    def update_catalog(self):
        """Acción principal para importar el catálogo"""
        if not self.cabys_excel_file:
            raise UserError(_("Por favor suba un archivo Excel primero"))

        products_updated = self._update_catalog_from_excel_file()

        self.notes = f"""
        <div style='color: green; font-weight: bold;'>
            ¡Catálogo CABYS actualizado con éxito!<br/>
            <ul>
                <li>{len(products_updated)} registros procesados</li>
                <li>Archivo: {self.file_name or 'Sin nombre'}</li>
            </ul>
        </div>
        """
        self.button_enable = False

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    @api.onchange('cabys_excel_file')
    def _onchange_cabys_excel_file(self):
        """Valida el archivo Excel cuando se sube"""
        self.button_enable = False

        if not self.cabys_excel_file:
            self.notes = "Suba su archivo Excel con el catálogo médico CABYS"
            return

        # Validar extensión del archivo
        if self.file_name and not self.file_name.lower().endswith(('.xls', '.xlsx')):
            self.notes = "<div style='color: red;'>El archivo debe ser un Excel (.xls o .xlsx)</div>"
            return

        try:
            excel_file = base64.b64decode(self.cabys_excel_file)
            is_valid, message = self._validate_excel_file(excel_file)

            if not is_valid:
                self.notes = f"<div style='color: red;'>{message}</div>"
                return

            codes = self._analyze_excel_file()
            self.notes = f"""
            <div style='color: green;'>
                <b>Archivo válido detectado</b><br/>
                <ul>
                    <li>{len(codes)} productos a procesar</li>
                    <li>Archivo: {self.file_name or 'Sin nombre'}</li>
                </ul>
            </div>
            """
            self.button_enable = True

        except Exception as e:
            self.notes = f"<div style='color: red;'>Error al leer archivo: {str(e)}</div>"