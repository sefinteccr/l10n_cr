# -*- coding: utf-8 -*-
import json
import requests
import re
import random
import logging
from odoo.exceptions import UserError

import base64
from lxml import etree
import datetime
import time
import pytz


_logger = logging.getLogger(__name__)


def get_clave(self, tipo_documento, numeracion, sucursal, terminal, situacion='normal'):

    # tipo de documento
    tipos_de_documento = { 'FE'  : '01', # Factura Electrónica
                           'ND'  : '02', # Nota de Débito
                           'NC'  : '03', # Nota de Crédito
                           'TE'  : '04', # Tiquete Electrónico
                           'CCE' : '05', # Confirmación Comprobante Electrónico
                           'CPCE': '06', # Confirmación Parcial Comprobante Electrónico
                           'RCE' : '07'} # Rechazo Comprobante Electrónico

    if tipo_documento not in tipos_de_documento:
        raise UserError('No se encuentra tipo de documento')

    tipo_documento = tipos_de_documento[tipo_documento]

    # numeracion
    numeracion = re.sub('[^0-9]', '', numeracion)

    if len(numeracion) != 10:
        raise UserError('La numeración debe de tener 10 dígitos')

    # sucursal
    sucursal = re.sub('[^0-9]', '', str(sucursal)).zfill(3)

    # terminal
    terminal = re.sub('[^0-9]', '', str(terminal)).zfill(5)

    # tipo de identificación
    if not self.company_id.identification_id:
        raise UserError('Seleccione el tipo de identificación del emisor en el perfil de la compañía')

    # identificación
    identificacion = re.sub('[^0-9]', '', self.company_id.vat)

    if self.company_id.identification_id.code == '01' and len(identificacion) != 9:
        raise UserError('La Cédula Física del emisor debe de tener 9 dígitos')
    elif self.company_id.identification_id.code == '02' and len(identificacion) != 10:
        raise UserError('La Cédula Jurídica del emisor debe de tener 10 dígitos')
    elif self.company_id.identification_id.code == '03' and (len(identificacion) != 11 or len(identificacion) != 12):
        raise UserError('La identificación DIMEX del emisor debe de tener 11 o 12 dígitos')
    elif self.company_id.identification_id.code == '04' and len(identificacion) != 10:
        raise UserError('La identificación NITE del emisor debe de tener 10 dígitos')

    identificacion = identificacion.zfill(12)

    # situación
    situaciones = { 'normal': '1', 'contingencia': '2', 'sininternet': '3'}

    if situacion not in situaciones:
        raise UserError('No se encuentra tipo de situación')

    situacion = situaciones[situacion]

    # código de pais
    codigo_de_pais = '506'

    # fecha
    now_utc = datetime.datetime.now(pytz.timezone('UTC'))
    now_cr = now_utc.astimezone(pytz.timezone('America/Costa_Rica'))

    dia = now_cr.strftime('%d')
    mes = now_cr.strftime('%m')
    anio = now_cr.strftime('%y')

    # código de seguridad
    codigo_de_seguridad = str(random.randint(1, 99999999)).zfill(8)

    # consecutivo
    consecutivo = sucursal + terminal + tipo_documento + numeracion

    # clave
    clave = codigo_de_pais + dia + mes + anio + identificacion + consecutivo + situacion + codigo_de_seguridad

    return {'length': len(clave), 'clave': clave, 'consecutivo': consecutivo}


def make_xml_invoice(inv, tipo_documento, consecutivo, date, sale_conditions, medio_pago, total_servicio_gravado,
                     total_servicio_exento, total_mercaderia_gravado, total_mercaderia_exento, base_subtotal,
                     total_impuestos, total_descuento, lines, tipo_documento_referencia, numero_documento_referencia,
                     fecha_emision_referencia, codigo_referencia, razon_referencia, url, currency_rate):
    headers = {}
    payload = {}
    # Generar FE payload
    payload['w'] = 'genXML'
    if tipo_documento in ('FE','TE'):
        payload['r'] = 'gen_xml_fe'
    elif tipo_documento == 'NC':
        payload['r'] = 'gen_xml_nc'
    elif tipo_documento == 'ND':
        payload['r'] = 'gen_xml_nd'
    payload['clave'] = inv.number_electronic
    payload['consecutivo'] = consecutivo
    payload['fecha_emision'] = date
    payload['emisor_nombre'] = inv.company_id.name
    payload['emisor_tipo_indetif'] = inv.company_id.identification_id.code
    payload['emisor_num_identif'] = inv.company_id.vat
    payload['nombre_comercial'] = inv.company_id.commercial_name or ''
    payload['emisor_provincia'] = inv.company_id.state_id.code
    payload['emisor_canton'] = inv.company_id.county_id.code
    payload['emisor_distrito'] = inv.company_id.district_id.code
    payload['emisor_barrio'] = inv.company_id.neighborhood_id and inv.company_id.neighborhood_id.code or ''
    payload['emisor_otras_senas'] = inv.company_id.street
    payload['emisor_cod_pais_tel'] = inv.company_id.phone_code
    payload['emisor_tel'] = inv.company_id.phone and re.sub('[^0-9]+', '', inv.company_id.phone) or ''
    payload['emisor_email'] = inv.company_id.email
    if not inv.partner_id or not inv.partner_id.vat:
        payload['omitir_receptor'] = 'true'
    else:
        payload['receptor_nombre'] = inv.partner_id.name[:80]
        payload['receptor_tipo_identif'] = inv.partner_id.identification_id.code
        payload['receptor_num_identif'] = inv.partner_id.vat
        payload['receptor_provincia'] = inv.partner_id.state_id.code or ''
        payload['receptor_canton'] = inv.partner_id.county_id.code or ''
        payload['receptor_distrito'] = inv.partner_id.district_id.code or ''
        payload['receptor_barrio'] = inv.partner_id.neighborhood_id.code or ''
        payload['receptor_cod_pais_tel'] = inv.partner_id.phone_code
        payload['receptor_tel'] = inv.partner_id.phone and re.sub('[^0-9]+', '', inv.partner_id.phone) or ''
        match = re.match(r'^(\s?[^\s,]+@[^\s,]+\.[^\s,]+\s?,)*(\s?[^\s,]+@[^\s,]+\.[^\s,]+)$', inv.partner_id.email.lower())
        if match:
            payload['receptor_email'] = inv.partner_id.email
        else:
            payload['receptor_email'] = 'indefinido@indefinido.com'
    if tipo_documento == 'TE':
        payload['condicion_venta'] = sale_conditions
        payload['plazo_credito'] = '0'
        payload['cod_moneda'] = inv.company_id.currency_id.name
    else:
        payload['condicion_venta'] = sale_conditions
        payload['plazo_credito'] = inv.payment_term_id and inv.payment_term_id.line_ids[0].days or '0'
        payload['cod_moneda'] = inv.currency_id.name
    payload['medio_pago'] = medio_pago
    payload['tipo_cambio'] = currency_rate
    payload['total_serv_gravados'] = total_servicio_gravado
    payload['total_serv_exentos'] = total_servicio_exento
    payload['total_merc_gravada'] = total_mercaderia_gravado
    payload['total_merc_exenta'] = total_mercaderia_exento
    payload['total_gravados'] = total_servicio_gravado + total_mercaderia_gravado
    payload['total_exentos'] = total_servicio_exento + total_mercaderia_exento
    payload['total_ventas'] = total_servicio_gravado + total_mercaderia_gravado + total_servicio_exento + total_mercaderia_exento
    payload['total_descuentos'] = total_descuento
    payload['total_ventas_neta'] = base_subtotal
    payload['total_impuestos'] = total_impuestos
    payload['total_comprobante'] = base_subtotal + total_impuestos
    payload['otros'] = ''
    payload['detalles'] = lines

    if tipo_documento in ('NC', 'ND'):
        payload['infoRefeTipoDoc'] = tipo_documento_referencia
        payload['infoRefeNumero'] = numero_documento_referencia
        payload['infoRefeFechaEmision'] = fecha_emision_referencia
        payload['infoRefeCodigo'] = codigo_referencia
        payload['infoRefeRazon'] = razon_referencia

    response = requests.request("POST", url, data=payload, headers=headers)
    xresponse_json = response.json()
    _logger.error('MAB - create_xml_file PAYLOAD: %s' % payload)
    _logger.error('MAB - create_xml_file response: %s' % xresponse_json)
    if 200 <= response.status_code <= 299:
        response_json = {'status': 200, 'xml': xresponse_json.get('resp').get('xml')}
    else:
        response_json = {'status': response.status_code, 'text': 'make_xml_invoice failed: %s' % response.reason}

    return response_json


last_tokens = {}
last_tokens_time = {}

def token_hacienda(inv, env):
    token = last_tokens.get(inv.company_id.id,False)
    token_time = last_tokens_time.get(inv.company_id.id,False)

    current_time = time.time()

    if token and (current_time - token_time < 280):
        response_json = {'status': 200, 'token': token}
    else:
        if env == 'api-prod':
            url = 'https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token'
        else:    #if env == 'api-stag':
            url = 'https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token'

        data = {
            'client_id': env,
            'client_secret': '',
            'grant_type': 'password',
            'username': inv.company_id.frm_ws_identificador,
            'password': inv.company_id.frm_ws_password}

        try:
            response = requests.post(url, data=data)
        except requests.exceptions.RequestException as e:
            _logger.error('Exception %s' % e)
            return {'status': -1, 'text': 'Excepcion %s' % e}

        if 200 <= response.status_code <= 299:
            token = response.json().get('access_token')
            last_tokens[inv.company_id.id] = token
            last_tokens_time[inv.company_id.id] = time.time()
            response_json = {'status': 200, 'token': token}
        else:
            _logger.error('MAB - token_hacienda failed.  error: %s', response.status_code)
            response_json = {'status': response.status_code, 'text': 'token_hacienda failed: %s' % response.reason}

    return response_json

def sign_xml(inv, tipo_documento, url, xml):
    payload = {}
    headers = {}
    payload['w'] = 'signXML'
    payload['r'] = 'signFE'
    payload['p12Url'] = inv.company_id.frm_apicr_signaturecode
    payload['inXml'] = xml
    payload['pinP12'] = inv.company_id.frm_pin
    payload['tipodoc'] = tipo_documento

    response = requests.request("POST", url, data=payload, headers=headers)
    if 200 <= response.status_code <= 299:
        response_json = {'status': 200, 'xmlFirmado': response.json().get('resp').get('xmlFirmado')}
    else:
        response_json = {'status': response.status_code, 'text': 'make_xml_invoice failed: %s' % response.reason}

    return response_json


def send_file(inv, token, xml, env):

    if env == 'api-stag':
        url = 'https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/recepcion/'
    elif env == 'api-prod':
        url = 'https://api.comprobanteselectronicos.go.cr/recepcion/v1/recepcion/'
    else:
        _logger.error('MAB - Ambiente no definido')
        return

    xml_decoded = base64.b64decode(xml)

    factura = etree.tostring(etree.fromstring(xml_decoded)).decode()
    factura = etree.fromstring(re.sub(' xmlns="[^"]+"', '', factura, count=1))

    Clave = factura.find('Clave')
    FechaEmision = factura.find('FechaEmision')
    Emisor = factura.find('Emisor')
    Receptor = factura.find('Receptor')

    comprobante = {}
    comprobante['clave'] = Clave.text
    comprobante["fecha"] = FechaEmision.text
    comprobante['emisor'] = {}
    comprobante['emisor']['tipoIdentificacion'] = Emisor.find('Identificacion').find('Tipo').text
    comprobante['emisor']['numeroIdentificacion'] = Emisor.find('Identificacion').find('Numero').text
    if Receptor is not None and Receptor.find('Identificacion') is not None:
        comprobante['receptor'] = {}
        comprobante['receptor']['tipoIdentificacion'] = Receptor.find('Identificacion').find('Tipo').text
        comprobante['receptor']['numeroIdentificacion'] = Receptor.find('Identificacion').find('Numero').text

    #comprobante['comprobanteXml'] = base64.b64encode(xml).decode('utf-8')
    comprobante['comprobanteXml'] = xml

    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}

    try:
        response = requests.post(url, data=json.dumps(comprobante), headers=headers)

    except requests.exceptions.RequestException as e:
        _logger.info('Exception %s' % e)
        raise Exception(e)

    return {'status': response.status_code, 'text': response.text}


def consulta_clave(clave, token, env):

    if env == 'api-stag':
        url = 'https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/recepcion/' + clave
    elif env == 'api-prod':
        url = 'https://api.comprobanteselectronicos.go.cr/recepcion/v1/recepcion/' + clave
    else:
        _logger.error('MAB - Ambiente no definido')
        return

    headers = {'Authorization': 'Bearer {}'.format(token),
               'Cache-Control': 'no-cache',
               'Content-Type': 'application/x-www-form-urlencoded',
               'Postman-Token': 'bf8dc171-5bb7-fa54-7416-56c5cda9bf5c'
    }

    try:
        #response = requests.request("GET", url, headers=headers)
        response = requests.get(url, headers=headers)
        ############################
    except requests.exceptions.RequestException as e:
        _logger.error('Exception %s' % e)
        return {'status': -1, 'text': 'Excepcion %s' % e}

    if 200 <= response.status_code <= 299:
        response_json = {
            'status': 200,
            'ind-estado': response.json().get('ind-estado'),
            'respuesta-xml': response.json().get('respuesta-xml')
        }
    elif 400 <= response.status_code <= 499:
        response_json = {'status': 400, 'ind-estado': 'error'}
    else:
        _logger.error('MAB - consulta_clave failed.  error: %s', response.status_code)
        response_json = {'status': response.status_code, 'text': 'token_hacienda failed: %s' % response.reason}
    return response_json

"""
def consulta_lista(clave, token, env):

import json
import requests
import re
import random
import logging
from odoo.exceptions import UserError

import base64
from lxml import etree
import datetime
import time
import pytz

#env == 'api-prod'
#url = 'https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token'
envi = 'api-stag'
url = 'https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token'

cia = env['res.company'].browse(1)


data = {
    'client_id': envi,
    'client_secret': '',
    'grant_type': 'password',
    'username': cia.frm_ws_identificador,
    'password': cia.frm_ws_password}
response = requests.post(url, data=data)

if 200 <= response.status_code <= 299:
    token = response.json().get('access_token')
else:
    print 'error token'
    print response.reason
    

if envi == 'api-stag':
    url = 'https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/comprobantes/?offset=1&limit=50'
    url = 'https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/comprobantes/?offset=1&limit=50&emisor=0200' + cia.vat
    url = 'https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/comprobantes/50613111800310103790200100001010000000009139220851'
    url = 'https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/recepcion/50615111800310103790209900099010000000010165340485'
elif envi == 'api-prod':
    url = 'https://api.comprobanteselectronicos.go.cr/recepcion/v1/comprobantes/?offset=1&limit=50'

headers = {'Authorization': 'Bearer {}'.format(token),
}

#           'Cache-Control': 'no-cache',
#           'Content-Type': 'application/x-www-form-urlencoded',
#           'Postman-Token': 'bf8dc171-5bb7-fa54-7416-56c5cda9bf5c'

response = requests.get(url, headers=headers)
if 200 <= response.status_code <= 299:
    response_json = response.json()
else:
    print 'error obteniendo lista comprobantes'
    print response.reason
    
"""

def consulta_documentos(self, inv, env, token_m_h, url, date_cr, xml_firmado):
    payload = {}
    headers = {}
    payload['w'] = 'consultar'
    payload['r'] = 'consultarCom'
    payload['client_id'] = env
    payload['token'] = token_m_h
    payload['clave'] = inv.number_electronic
    response = requests.request("POST", url, data=payload, headers=headers)
    response_json = response.json()
    estado_m_h = response_json.get('resp').get('ind-estado')

    # Siempre sin importar el estado se actualiza la fecha de acuerdo a la devuelta por Hacienda y
    # se carga el xml devuelto por Hacienda
    if inv.type == 'out_invoice' or inv.type == 'out_refund':
        # Se actualiza el estado con el que devuelve Hacienda
        inv.state_tributacion = estado_m_h
        inv.date_issuance = date_cr
        inv.fname_xml_comprobante = 'comprobante_' + inv.number_electronic + '.xml'
        inv.xml_comprobante = xml_firmado
    elif inv.type == 'in_invoice' or inv.type == 'in_refund':
        inv.fname_xml_comprobante = 'receptor_' + inv.number_electronic + '.xml'
        inv.xml_comprobante = xml_firmado
        inv.state_send_invoice = estado_m_h

    # Si fue aceptado o rechazado por haciendo se carga la respuesta
    if (estado_m_h == 'aceptado' or estado_m_h == 'rechazado') or (inv.type == 'out_invoice'  or inv.type == 'out_refund'):
        inv.fname_xml_respuesta_tributacion = 'respuesta_' + inv.number_electronic + '.xml'
        inv.xml_respuesta_tributacion = response_json.get('resp').get('respuesta-xml')

    # Si fue aceptado por Hacienda y es un factura de cliente o nota de crédito, se envía el correo con los documentos
    if estado_m_h == 'aceptado':
        if not inv.partner_id.opt_out:
            if inv.type == 'in_invoice' or inv.type == 'in_refund':
                email_template = self.env.ref('cr_electronic_invoice.email_template_invoice_vendor', False)
            else:
                email_template = self.env.ref('account.email_template_edi_invoice', False)

            attachments = []

            attachment = self.env['ir.attachment'].search(
                [('res_model', '=', 'account.invoice'), ('res_id', '=', inv.id),
                 ('res_field', '=', 'xml_comprobante')], limit=1)
            if attachment.id:
                attachment.name = inv.fname_xml_comprobante
                attachment.datas_fname = inv.fname_xml_comprobante
                attachments.append(attachment.id)

            attachment_resp = self.env['ir.attachment'].search(
                [('res_model', '=', 'account.invoice'), ('res_id', '=', inv.id),
                 ('res_field', '=', 'xml_respuesta_tributacion')], limit=1)
            if attachment_resp.id:
                attachment_resp.name = inv.fname_xml_respuesta_tributacion
                attachment_resp.datas_fname = inv.fname_xml_respuesta_tributacion
                attachments.append(attachment_resp.id)

            if len(attachments) == 2:
                email_template.attachment_ids = [(6, 0, attachments)]

                email_template.with_context(type='binary', default_type='binary').send_mail(inv.id,
                                                                                            raise_exception=False,
                                                                                            force_send=True)  # default_type='binary'

                # limpia el template de los attachments
                email_template.attachment_ids = [(5)]
