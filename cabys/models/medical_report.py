# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import base64
import io
import xlsxwriter
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError


class MedicalReport(models.TransientModel):
    _name = 'medical.report'
    _description = 'Reporte de Registros Farmacéuticos'

    # Campos para selección de fechas
    date_from = fields.Date(string='Desde', required=True, default=lambda self: fields.Date.to_date('2025-01-01'))
    date_to = fields.Date(string='Hasta', required=True, default=fields.Date.context_today)

    def generate_medical_report(self):
        """Genera el reporte Excel de registros farmacéuticos"""
        # Validar fechas
        if self.date_from > self.date_to:
            raise UserError("La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'")

        # Buscar en facturas de proveedor en el rango de fechas
        invoices = self.env['account.invoice'].search([
            ('date_invoice', '>=', self.date_from),
            ('date_invoice', '<=', self.date_to),
            ('type', 'in', ['in_invoice', 'in_refund']),
        ])

        if not invoices:
            raise UserError(f"No se encontraron registros desde {self.date_from} hasta {self.date_to}.")

        total_records = 0
        all_medical_data = []
        registros_vistos = set()  # ✅ Para controlar duplicados

        for invoice in invoices:
            xml_content = self.find_xml_attachment(invoice)

            if xml_content:
                medical_data = self.extract_xml_data(xml_content)

                if medical_data:
                    for data in medical_data:
                        registro_med = data['registro_medicamento']

                        # ✅ FILTRO ANTI-DUPLICADOS: Ignorar si ya vimos este registro
                        if registro_med not in registros_vistos:
                            registros_vistos.add(registro_med)

                            # Acumular datos para Excel
                            all_medical_data.append({
                                'fecha_factura': invoice.date_invoice or '',
                                'proveedor': invoice.partner_id.name or '',
                                'numero_factura': invoice.number or '',
                                'detalle': data['detalle'],
                                'registro_medicamento': registro_med,
                                'forma_farmaceutica': data['forma_farmaceutica'],
                            })
                            total_records += 1

        if total_records > 0:
            return self.generate_excel_file(all_medical_data)
        else:
            raise UserError(f"No se encontraron registros farmacéuticos desde {self.date_from} hasta {self.date_to}.")

    def find_xml_attachment(self, invoice):
        """Busca el attachment XML válido para la factura"""
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.invoice'),
            ('res_id', '=', invoice.id),
            '|', ('mimetype', '=', 'application/xml'),
            ('name', 'ilike', '.xml')
        ])

        for attachment in attachments:
            try:
                xml_content = base64.b64decode(attachment.datas).decode('utf-8')
                # Verificar si es una Factura Electrónica válida (ambas versiones)
                if 'FacturaElectronica' in xml_content and 'comprobanteselectronicos.go.cr' in xml_content:
                    return xml_content
            except:
                continue
        return None

    def extract_xml_data(self, xml_content):
        """Extrae SOLO los datos médicos específicos del XML para versiones 4.3 y 4.4"""
        try:
            # Namespaces para ambas versiones
            namespaces_list = [
                {'ns': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica'},
                {'ns': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.3/facturaElectronica'}
            ]

            root = ET.fromstring(xml_content)
            medical_data = []

            for namespaces in namespaces_list:
                for line in root.findall('.//ns:LineaDetalle', namespaces):
                    detalle = line.find('ns:Detalle', namespaces)
                    registro_med = line.find('ns:RegistroMedicamento', namespaces)
                    forma_farm = line.find('ns:FormaFarmaceutica', namespaces)

                    # Doble filtro existe RegistroMedicamento y no está vacio
                    if (registro_med is not None and
                            registro_med.text is not None and
                            registro_med.text.strip() != ''):
                        medical_data.append({
                            'detalle': detalle.text if detalle is not None else '',
                            'registro_medicamento': registro_med.text.strip(),
                            'forma_farmaceutica': forma_farm.text if forma_farm is not None else '',
                        })

                # Si encontramos datos con este namespace, salimos
                if medical_data:
                    break

            return medical_data

        except ET.ParseError as e:
            raise UserError(f"Error al parsear XML: {str(e)}")
        except Exception as e:
            raise UserError(f"Error al procesar XML: {str(e)}")

    def generate_excel_file(self, data):
        """Genera y descarga el reporte Excel"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Registros Farmacéuticos')

        # Formatos
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#366092',
            'font_color': 'white',
            'border': 1,
            'align': 'center'
        })

        cell_format = workbook.add_format({'border': 1})

        # Encabezados
        headers = [
            'Fecha Factura',
            'Proveedor',
            'Número Factura',
            'Detalle',
            'Registro Medicamento',
            'Forma Farmacéutica'
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 20)

        # Datos
        for row, record in enumerate(data, 1):
            worksheet.write(row, 0, str(record['fecha_factura']), cell_format)
            worksheet.write(row, 1, record['proveedor'], cell_format)
            worksheet.write(row, 2, record['numero_factura'], cell_format)
            worksheet.write(row, 3, record['detalle'], cell_format)
            worksheet.write(row, 4, record['registro_medicamento'], cell_format)
            worksheet.write(row, 5, record['forma_farmaceutica'], cell_format)

        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()

        # Crear attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'Registros_Farmaceuticos.xlsx',
            'datas': base64.b64encode(xlsx_data),
            'datas_fname': 'Registros_Farmaceuticos.xlsx',
            'res_model': 'medical.report',
            'res_id': self.id,
            'type': 'binary',
        })

        # Descargar archivo de Excel
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }