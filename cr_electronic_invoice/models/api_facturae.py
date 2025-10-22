import requests
import datetime
import json
from . import fe_enums
import io
import re
import os
import base64
import pytz
import time
import phonenumbers
import logging
import random
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from odoo import _
from odoo.exceptions import UserError
from ..xades.context2 import XAdESContext2, PolicyId2, create_xades_epes_signature

# from cryptography.hazmat.primitives.asymmetric import padding
# from cryptography.hazmat.primitives.hashes import SHA256
# from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
# from hashlib import sha256

from xml.sax.saxutils import escape
# from xml.etree import ElementTree
# from lxml import etree
# from html import escape  # escapes &, <, > … for XML safety



try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree

try:
    from OpenSSL import crypto
except(ImportError, IOError) as err:
    logging.info(err)

# PARA VALIDAR JSON DE RESPUESTA
from .. import extensions

_logger = logging.getLogger(__name__)


def sign_xml(cert, password, xml, policy_id='https://cdn.comprobanteselectronicos.go.cr/xml-schemas/'
                'Resoluci%C3%B3n_General_sobre_disposiciones_t%C3%A9cnicas_comprobantes_electr%C3%B3nicos_para_efectos_tributarios.pdf'):
    root = etree.fromstring(xml)
    _logger.info('Firma 1')
    signature = create_xades_epes_signature()

    policy = PolicyId2()
    policy.id = policy_id

    root.append(signature)
    ctx = XAdESContext2(policy)
    certificate = crypto.load_pkcs12(base64.b64decode(cert), password)
    ctx.load_pkcs12(certificate)
    _logger.info('Firma 2')
    ctx.sign(signature)
    _logger.info('Firma 3')
    return etree.tostring(root, encoding='UTF-8', method='xml', xml_declaration=True, with_tail=False)

# # Para version python 3.10
# def sign_xml(cert, password, xml_string):
#     xml = ElementTree.fromstring(xml_string)
#     ElementTree.register_namespace('', xml.tag.split('}')[0][1:] if '}' in xml.tag else '')
#     ElementTree.register_namespace('ds', 'http://www.w3.org/2000/09/xmldsig#')
#     ElementTree.register_namespace('dsig-filter2', 'http://www.w3.org/2002/06/xmldsig-filter2')
#     ElementTree.register_namespace('xades', 'http://uri.etsi.org/01903/v1.3.2#')
#     ElementTree.indent(xml)

#     canonical_xml = ElementTree.canonicalize(ElementTree.tostring(xml))
#     document_digest = base64.b64encode(sha256(canonical_xml.encode()).digest()).decode()
#     private_key, certificate, _ = pkcs12.load_key_and_certificates(base64.b64decode(cert), password.encode('utf-8'))
#     cert_digest = base64.b64encode(certificate.fingerprint(SHA256())).decode()
#     cert_base64 = base64.b64encode(certificate.public_bytes(Encoding.DER)).decode()
#     issuer = certificate.issuer.rfc4514_string()
#     serial = certificate.serial_number
#     signing_time = datetime.datetime.now().isoformat(timespec='seconds') + 'Z'
#     policy_id = 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/Resoluci%C3%B3n_General_sobre_disposiciones_t%C3%A9cnicas_comprobantes_electr%C3%B3nicos_para_efectos_tributarios.pdf';
#     policy_digest = 'DWxin1xWOeI8OuWQXazh4VjLWAaCLAA954em7DMh0h8=';

#     signed_properties = (
#     f'<xades:SignedProperties xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" Id="p1">\n'
#     f'          <xades:SignedSignatureProperties>\n'
#     f'            <xades:SigningTime>{signing_time}</xades:SigningTime>\n'
#     f'            <xades:SigningCertificate>\n'
#     f'              <xades:Cert>\n'
#     f'                <xades:CertDigest>\n'
#     f'                  <ds:DigestMethod xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"></ds:DigestMethod>\n'
#     f'                  <ds:DigestValue xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{cert_digest}</ds:DigestValue>\n'
#     f'                </xades:CertDigest>\n'
#     f'                <xades:IssuerSerial>\n'
#     f'                  <ds:X509IssuerName xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{issuer}</ds:X509IssuerName>\n'
#     f'                  <ds:X509SerialNumber xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{serial}</ds:X509SerialNumber>\n'
#     f'                </xades:IssuerSerial>\n'
#     f'              </xades:Cert>\n'
#     f'            </xades:SigningCertificate>\n'
#     f'            <xades:SignaturePolicyIdentifier>\n'
#     f'              <xades:SignaturePolicyId>\n'
#     f'                <xades:SigPolicyId>\n'
#     f'                  <xades:Identifier>{policy_id}</xades:Identifier>\n'
#     f'                </xades:SigPolicyId>\n'
#     f'                <xades:SigPolicyHash>\n'
#     f'                  <ds:DigestMethod xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"></ds:DigestMethod>\n'
#     f'                  <ds:DigestValue xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{policy_digest}</ds:DigestValue>\n'
#     f'                </xades:SigPolicyHash>\n'
#     f'              </xades:SignaturePolicyId>\n'
#     f'            </xades:SignaturePolicyIdentifier>\n'
#     f'          </xades:SignedSignatureProperties>\n'
#     f'          <xades:SignedDataObjectProperties>\n'
#     f'            <xades:DataObjectFormat ObjectReference="#r1">\n'
#     f'              <xades:MimeType>text/xml</xades:MimeType>\n'
#     f'            </xades:DataObjectFormat>\n'
#     f'          </xades:SignedDataObjectProperties>\n'
#     f'        </xades:SignedProperties>')

#     properties_digest = base64.b64encode(sha256(signed_properties.encode()).digest()).decode()

#     signed_info = (
#     f'<ds:SignedInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">\n'
#     f'      <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"></ds:CanonicalizationMethod>\n'
#     f'      <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"></ds:SignatureMethod>\n'
#     f'      <ds:Reference Id="r1" URI="">\n'
#     f'        <ds:Transforms>\n'
#     f'          <ds:Transform Algorithm="http://www.w3.org/2002/06/xmldsig-filter2">\n'
#     f'            <dsig-filter2:XPath xmlns:dsig-filter2="http://www.w3.org/2002/06/xmldsig-filter2" Filter="subtract">/descendant::ds:Signature</dsig-filter2:XPath>\n'
#     f'          </ds:Transform>\n'
#     f'          <ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"></ds:Transform>\n'
#     f'        </ds:Transforms>\n'
#     f'        <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"></ds:DigestMethod>\n'
#     f'        <ds:DigestValue>{document_digest}</ds:DigestValue>\n'
#     f'      </ds:Reference>\n'
#     f'      <ds:Reference Type="http://uri.etsi.org/01903#SignedProperties" URI="#p1">\n'
#     f'        <ds:Transforms>\n'
#     f'          <ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"></ds:Transform>\n'
#     f'        </ds:Transforms>\n'
#     f'        <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"></ds:DigestMethod>\n'
#     f'        <ds:DigestValue>{properties_digest}</ds:DigestValue>\n'
#     f'      </ds:Reference>\n'
#     f'    </ds:SignedInfo>')

#     # Sign the signed info
#     signature_value = base64.b64encode(private_key.sign(signed_info.encode(), padding.PKCS1v15(), SHA256())).decode()

#     signature = (
#     f'<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Id="s1">\n'
#     f'    {signed_info}\n'
#     f'    <ds:SignatureValue Id="v1">{signature_value}</ds:SignatureValue>\n'
#     f'    <ds:KeyInfo>\n'
#     f'      <ds:X509Data>\n'
#     f'        <ds:X509Certificate>{cert_base64}</ds:X509Certificate>\n'
#     f'      </ds:X509Data>\n'
#     f'    </ds:KeyInfo>\n'
#     f'    <ds:Object>\n'
#     f'      <xades:QualifyingProperties xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" Target="#s1">\n'
#     f'        {signed_properties}\n'
#     f'      </xades:QualifyingProperties>\n'
#     f'    </ds:Object>\n'
#     f'  </ds:Signature>')

#     # Append signature to the canonical XML
#     xml_tree = ElementTree.fromstring(canonical_xml)
#     signature_tree = ElementTree.fromstring(signature)
#     xml_tree.append(signature_tree)

#     return ElementTree.tostring(xml_tree, encoding='UTF-8', method='xml', xml_declaration=True)


def get_time_hacienda():
    now_utc = datetime.datetime.now(pytz.timezone('UTC'))
    now_cr = now_utc.astimezone(pytz.timezone('America/Costa_Rica'))
    date_cr = now_cr.strftime("%Y-%m-%dT%H:%M:%S-06:00")

    return date_cr


# Utilizada para establecer un limite de caracteres en la cedula del cliente, no mas de 20
# de lo contrario hacienda lo rechaza
def limit(str, limit):
    return (str[:limit - 3] + '...') if len(str) > limit else str


def get_mr_sequencevalue(inv):
    '''Verificamos si el ID del mensaje receptor es válido'''
    mr_mensaje_id = int(inv.state_invoice_partner)
    if mr_mensaje_id < 1 or mr_mensaje_id > 3:
        raise UserError('El ID del mensaje receptor es inválido.')
    elif mr_mensaje_id is None:
        raise UserError('No se ha proporcionado un ID válido para el MR.')

    if inv.state_invoice_partner == '1':
        detalle_mensaje = 'Aceptado'
        tipo = 1
        tipo_documento = fe_enums.TipoDocumento['CCE']
        sequence = inv.env['ir.sequence'].next_by_code(
            'sequence.electronic.doc.confirmation')

    elif inv.state_invoice_partner == '2':
        detalle_mensaje = 'Aceptado parcial'
        tipo = 2
        tipo_documento = fe_enums.TipoDocumento['CPCE']
        sequence = inv.env['ir.sequence'].next_by_code(
            'sequence.electronic.doc.partial.confirmation')
    else:
        detalle_mensaje = 'Rechazado'
        tipo = 3
        tipo_documento = fe_enums.TipoDocumento['RCE']
        sequence = inv.env['ir.sequence'].next_by_code(
            'sequence.electronic.doc.reject')

    return {'detalle_mensaje': detalle_mensaje, 'tipo': tipo, 'tipo_documento': tipo_documento, 'sequence': sequence}


def get_consecutivo_hacienda(tipo_documento, consecutivo, sucursal_id, terminal_id):
    tipo_doc = fe_enums.TipoDocumento[tipo_documento]

    inv_consecutivo = str(consecutivo).zfill(10)
    inv_sucursal = str(sucursal_id).zfill(3)
    inv_terminal = str(terminal_id).zfill(5)

    consecutivo_mh = inv_sucursal + inv_terminal + tipo_doc + inv_consecutivo

    return consecutivo_mh


def get_clave_hacienda(doc, tipo_documento, consecutivo, sucursal_id, terminal_id, situacion='normal'):
    tipo_doc = fe_enums.TipoDocumento[tipo_documento]

    '''Verificamos si el consecutivo indicado corresponde a un numero'''
    inv_consecutivo = re.sub('[^0-9]', '', consecutivo)
    if len(inv_consecutivo) != 10:
        raise UserError('La numeración debe de tener 10 dígitos')

    '''Verificamos la sucursal y terminal'''
    inv_sucursal = re.sub('[^0-9]', '', str(sucursal_id)).zfill(3)
    inv_terminal = re.sub('[^0-9]', '', str(terminal_id)).zfill(5)

    '''Armamos el consecutivo pues ya tenemos los datos necesarios'''
    consecutivo_mh = inv_sucursal + inv_terminal + tipo_doc + inv_consecutivo

    if not doc.company_id.identification_id:
        raise UserError(
            'Seleccione el tipo de identificación del emisor en el pérfil de la compañía')

    '''Obtenemos el número de identificación del Emisor y lo validamos númericamente'''
    inv_cedula = re.sub('[^0-9]', '', doc.company_id.vat)

    '''Validamos el largo de la cadena númerica de la cédula del emisor'''
    if doc.company_id.identification_id.code == '01' and len(inv_cedula) != 9:
        raise UserError('La Cédula Física del emisor debe de tener 9 dígitos')
    elif doc.company_id.identification_id.code == '02' and len(inv_cedula) != 10:
        raise UserError(
            'La Cédula Jurídica del emisor debe de tener 10 dígitos')
    elif doc.company_id.identification_id.code == '03' and len(inv_cedula) not in (11, 12):
        raise UserError(
            'La identificación DIMEX del emisor debe de tener 11 o 12 dígitos')
    elif doc.company_id.identification_id.code == '04' and len(inv_cedula) != 10:
        raise UserError(
            'La identificación NITE del emisor debe de tener 10 dígitos')

    inv_cedula = str(inv_cedula).zfill(12)

    '''Limitamos la cedula del emisor a 20 caracteres o nos dará error'''
    cedula_emisor = limit(inv_cedula, 20)

    '''Validamos la situación del comprobante electrónico'''
    situacion_comprobante = fe_enums.SituacionComprobante.get(situacion)
    if not situacion_comprobante:
        raise UserError(
            'La situación indicada para el comprobante electŕonico es inválida: ' + situacion)

    '''Creamos la fecha para la clave'''
    dia = str(doc.date_invoice.day).zfill(2)  # [8:10]#'%02d' % now_cr.day,
    mes = str(doc.date_invoice.month).zfill(2)  # [5:7]#'%02d' % now_cr.month,
    anno = str(doc.date_invoice.year)[2:]  # str(now_cr.year)[2:4],
    cur_date = dia + mes + anno

    phone = phonenumbers.parse(doc.company_id.phone,
                               doc.company_id.country_id and doc.company_id.country_id.code or 'CR')
    codigo_pais = str(phone and phone.country_code or 506)

    '''Creamos un código de seguridad random'''
    codigo_seguridad = str(random.randint(1, 99999999)).zfill(8)

    clave_hacienda = codigo_pais + cur_date + cedula_emisor + \
                     consecutivo_mh + situacion_comprobante + codigo_seguridad

    return {'length': len(clave_hacienda), 'clave': clave_hacienda, 'consecutivo': consecutivo_mh}


'''Variables para poder manejar el Refrescar del Token'''
last_tokens = {}
last_tokens_time = {}
last_tokens_expire = {}
last_tokens_refresh = {}


def get_token_hacienda(inv, tipo_ambiente):
    global last_tokens
    global last_tokens_time
    global last_tokens_expire
    global last_tokens_refresh

    token = last_tokens.get(inv.company_id.id, False)
    token_time = last_tokens_time.get(inv.company_id.id, False)
    token_expire = last_tokens_expire.get(inv.company_id.id, 0)
    current_time = time.time()

    if token and (current_time - token_time < token_expire - 10):
        token_hacienda = token
    else:
        headers = {}
        data = {
                'client_id': tipo_ambiente,
                'client_secret': '',
                'grant_type': 'password',
                'username': inv.company_id.frm_ws_identificador,
                'password': inv.company_id.frm_ws_password
        }

        # establecer el ambiente al cual me voy a conectar
        endpoint = fe_enums.UrlHaciendaToken[tipo_ambiente]

        try:
            # enviando solicitud post y guardando la respuesta como un objeto json
            response = requests.request(
                "POST", endpoint, data=data, headers=headers)
            response_json = response.json()

            # respuesta = extensions.response_validator.assert_valid_schema(
            #     response_json, 'token.json')

            if 200 <= response.status_code <= 299:
                token_hacienda = response_json.get('access_token')
                last_tokens[inv.company_id.id] = token
                last_tokens_time[inv.company_id.id] = time.time()
                last_tokens_expire[inv.company_id.id] = response_json.get(
                    'expires_in')
                last_tokens_refresh[inv.company_id.id] = response_json.get(
                    'refresh_expires_in')
            else:
                _logger.error('FECR - token_hacienda failed.  error: %s' % (response.status_code))

        except requests.exceptions.RequestException as e:
            raise Warning(_('Error Obteniendo el Token desde MH. Excepcion %s' % (e)))

    return token_hacienda


def refresh_token_hacienda(tipo_ambiente, token):
    headers = {}
    data = {'client_id': tipo_ambiente,
            'client_secret': '',
            'grant_type': 'refresh_token',
            'refresh_token': token
            }

    # establecer el ambiente al cual me voy a conectar
    endpoint = fe_enums.UrlHaciendaToken[tipo_ambiente]

    try:
        # enviando solicitud post y guardando la respuesta como un objeto json
        response = requests.request(
            "POST", endpoint, data=data, headers=headers)
        response_json = response.json()
        token_hacienda = response_json.get('access_token')
        return token_hacienda
    except ImportError:
        raise Warning('Error Refrescando el Token desde MH')

def get_totals_xml_mr(invoice):
    try:
        invoice_xml = etree.fromstring(base64.b64decode(invoice.xml_supplier_approval))
        document_type = re.search('FacturaElectronica|NotaCreditoElectronica|NotaDebitoElectronica|TiqueteElectronico',
                                  invoice_xml.tag).group(0)

        if document_type == 'TiqueteElectronico':
            raise UserError(_("This is a Electronic Ticket only a Electronic Bill are valid for taxes"))

    except Exception as e:
        invoice.unlink()
        raise UserError(_("This XML does not comply with the necessary structure to be processed. Error: %s") % e)
    namespaces = invoice_xml.nsmap
    inv_xmlns = namespaces.pop(None)
    namespaces['inv'] = inv_xmlns
    values = {
        'amount_total_electronic_invoice': invoice_xml.xpath("inv:ResumenFactura/inv:TotalComprobante", namespaces=namespaces)[0].text,
        'amount_tax_electronic_invoice': '0.0'
    }
    tax_node = invoice_xml.xpath("inv:ResumenFactura/inv:TotalImpuesto", namespaces=namespaces)
    if tax_node:
        values['amount_tax_electronic_invoice'] = tax_node[0].text
    return values


def gen_xml_mr_43(inv, clave, cedula_emisor, fecha_emision, id_mensaje,
                  detalle_mensaje, cedula_receptor,
                  consecutivo_receptor,
                  monto_impuesto=0, total_factura=0,
                  codigo_actividad=False,
                  condicion_impuesto=False,
                  monto_total_impuesto_acreditar=False,
                  monto_total_gasto_aplicable=False):
    '''Verificamos si la clave indicada corresponde a un numeros'''
    if clave:
        mr_clave = re.sub('[^0-9]', '', clave)
    else:
        mr_clave = False
    if len(mr_clave) != 50:
        raise UserError(
            'La clave a utilizar es inválida. Debe contener al menos 50 digitos')

    '''Obtenemos el número de identificación del Emisor y lo validamos númericamente'''
    mr_cedula_emisor = re.sub('[^0-9]', '', cedula_emisor)
    def get_cedula(cedula):
        dic_cedula = {
            '01': len(cedula) == 9,
            '02': len(cedula) == 10, 
            '03': len(cedula) in (11,12), 
            '04': len(cedula) == 10, 
            '05': str(cedula).zfill(12), 
            '06': str(cedula).zfill(12), 
        }
        return dic_cedula.get(inv.partner_id.identification_id.code, False)
    
    if get_cedula(mr_cedula_emisor):
        mr_cedula_emisor = mr_cedula_emisor
    elif mr_cedula_emisor is None:
        raise UserError('La cédula del Emisor en el MR es inválida.')

    mr_fecha_emision = fecha_emision
    if mr_fecha_emision is None:
        raise UserError('La fecha de emisión en el MR es inválida.')

    '''Verificamos si el ID del mensaje receptor es válido'''
    mr_mensaje_id = int(id_mensaje)
    if mr_mensaje_id < 1 and mr_mensaje_id > 3:
        raise UserError('El ID del mensaje receptor es inválido.')
    elif mr_mensaje_id is None:
        raise UserError('No se ha proporcionado un ID válido para el MR.')

    mr_cedula_receptor = re.sub('[^0-9]', '', cedula_receptor)
    if get_cedula(mr_cedula_receptor):
        mr_cedula_receptor = mr_cedula_receptor
    elif mr_cedula_receptor is None:
        raise UserError(
            'No se ha proporcionado una cédula de receptor válida para el MR.')

    '''Verificamos si el consecutivo indicado para el mensaje receptor corresponde a numeros'''
    mr_consecutivo_receptor = re.sub('[^0-9]', '', consecutivo_receptor)
    if len(mr_consecutivo_receptor) != 20:
        raise UserError('La clave del consecutivo para el mensaje receptor es inválida. '
                        'Debe contener al menos 50 digitos')

    mr_monto_impuesto = monto_impuesto
    mr_detalle_mensaje = detalle_mensaje
    mr_total_factura = total_factura

    '''Iniciamos con la creación del mensaje Receptor'''
    sb = StringBuilder()

    sb.Append('<MensajeReceptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
    sb.Append('xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/mensajeReceptor" ')
    sb.Append('xsi:schemaLocation="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/mensajeReceptor ')
    sb.Append('https://www.hacienda.go.cr/ATV/ComprobanteElectronico/docs/esquemas/2024/v4.4/MensajeReceptor_V4.4.xsd">')
    sb.Append('<Clave>' + mr_clave + '</Clave>')
    sb.Append('<NumeroCedulaEmisor>' + mr_cedula_emisor + '</NumeroCedulaEmisor>')
    sb.Append('<FechaEmisionDoc>' + mr_fecha_emision + '</FechaEmisionDoc>')
    sb.Append('<Mensaje>' + str(mr_mensaje_id) + '</Mensaje>')

    if mr_detalle_mensaje is not None:
        sb.Append('<DetalleMensaje>' + escape(mr_detalle_mensaje) + '</DetalleMensaje>')

    ######## SE lee el xml para que llene la informacion correcta de impuesto
    totales = get_totals_xml_mr(inv)

    if mr_monto_impuesto is not None and mr_monto_impuesto > 0:
        sb.Append('<MontoTotalImpuesto>' + totales['amount_tax_electronic_invoice'] + '</MontoTotalImpuesto>')

    if codigo_actividad:
        sb.Append('<CodigoActividad>' + str(codigo_actividad) + '</CodigoActividad>')

    sb.Append('<CondicionImpuesto>' + str(condicion_impuesto) + '</CondicionImpuesto>')

    # TODO: Estar atento a la publicación de Hacienda de cómo utilizar esto
    if monto_total_impuesto_acreditar:
        sb.Append(
            '<MontoTotalImpuestoAcreditar>' +
            str(monto_total_impuesto_acreditar) +
            '</MontoTotalImpuestoAcreditar>')

    # TODO: Estar atento a la publicación de Hacienda de cómo utilizar esto
    if monto_total_gasto_aplicable:
        sb.Append('<MontoTotalDeGastoAplicable>' +
                  str(monto_total_gasto_aplicable) +
                  '</MontoTotalDeGastoAplicable>')
    if mr_total_factura is not None and mr_total_factura > 0:
        sb.Append('<TotalFactura>' + totales['amount_total_electronic_invoice'] + '</TotalFactura>')
    else:
        raise UserError(
            'El monto Total de la Factura para el Mensaje Receptro es inválido'
        )

    sb.Append('<NumeroCedulaReceptor>' + mr_cedula_receptor + '</NumeroCedulaReceptor>')
    sb.Append('<NumeroConsecutivoReceptor>' + mr_consecutivo_receptor + '</NumeroConsecutivoReceptor>')
    sb.Append('</MensajeReceptor>')

    return str(sb)

def gen_xml_v43(inv, sale_conditions, total_servicio_gravado,
                total_servicio_exento, totalServExonerado,
                total_mercaderia_gravado, total_mercaderia_exento,
                totalMercExonerada, totalServNoSujeto, totalMercNoSujeta, 
                totalOtrosCargos, total_iva_devuelto, base_total,
                total_impuestos, total_desgloce_impuesto, total_descuento, lines,
                otrosCargos, currency_rate, invoice_comments,
                tipo_documento_referencia, numero_documento_referencia,
                fecha_emision_referencia, codigo_referencia, razon_referencia):
    numero_linea = 0
    payment_methods_id = []

    if inv._name == 'pos.order':
        plazo_credito = '0'
        payment_methods_id = {}
        for st in inv.statement_ids:
            payment_methods_id.setdefault(st.journal_id.id, {'TipoMedioPago':'01', 'TotalMedioPago':0.0})
            if st.journal_id.payment_method_id:
                payment_methods_id[st.journal_id.id]['TipoMedioPago'] = st.journal_id.payment_method_id.sequence
            payment_methods_id[st.journal_id.id]['TotalMedioPago'] += st.amount

        # inv_statement_length = len(inv.statement_ids)
        # for statement_counter in range(inv_statement_length):
        #     payment_method_id
        #     if inv.statement_ids[statement_counter].statement_id.journal_id.type == 'cash':
        #         payment_methods_id.append('01')
        #     else:
        #         payment_methods_id.append('02')

        cod_moneda = str(inv.company_id.currency_id.name)
    else:
        payment_methods_id.append(str(inv.payment_methods_id.sequence))
        plazo_credito = str(inv.payment_term_id and inv.payment_term_id.line_ids[0].days or 0)
        cod_moneda = str(inv.currency_id.name)

    if inv.tipo_documento == 'FEC':
        issuing_company = inv.partner_id
        receiver_company = inv.company_id
        issuing_company_name = issuing_company.name
    else:
        issuing_company = inv.company_id
        receiver_company = inv.partner_id
        issuing_company_name = issuing_company.legal_name or issuing_company.name

    sb = StringBuilder()
    sb.Append(
        '<' + fe_enums.tagName[inv.tipo_documento] + ' xmlns="' + fe_enums.XmlnsHacienda[inv.tipo_documento] + '" ')
    sb.Append('xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xsd="http://www.w3.org/2001/XMLSchema" ')
    sb.Append('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
    sb.Append('xsi:schemaLocation="' + fe_enums.schemaLocation[inv.tipo_documento] + '">')

    sb.Append('<Clave>' + inv.number_electronic + '</Clave>')
    sb.Append('<ProveedorSistemas>' + inv.company_id.vat + '</ProveedorSistemas>') # esto es porque es un desarrollo propio/local si es externo entonces se agrega el codigo del proveedor
    
    if inv.tipo_documento in ["FE","FEE","TE","ND","NC"]:
        sb.Append('<CodigoActividadEmisor>' + inv.economic_activity_id.code + '</CodigoActividadEmisor>')

    if inv.tipo_documento in ["FE","FEC","NC","ND"]:
        if inv.partner_id.activity_id.code:
            sb.Append('<CodigoActividadReceptor>' + str(inv.partner_id.activity_id.code) + '</CodigoActividadReceptor>')

    sb.Append('<NumeroConsecutivo>' + inv.number_electronic[21:41] + '</NumeroConsecutivo>')
    sb.Append('<FechaEmision>' + inv.date_issuance + '</FechaEmision>')
    sb.Append('<Emisor>')
    sb.Append('<Nombre>' + escape(issuing_company_name) + '</Nombre>')
    sb.Append('<Identificacion>')
    sb.Append('<Tipo>' + issuing_company.identification_id.code + '</Tipo>')
    sb.Append('<Numero>' + issuing_company.vat + '</Numero>')
    sb.Append('</Identificacion>')
    # Registrofiscal8707 No porque solo empresas que registran codigo CAByS
    if inv.tipo_documento not in ["REP"]:
        sb.Append('<NombreComercial>' + escape(str(issuing_company.commercial_name or 'No disponible')) + '</NombreComercial>')
        sb.Append('<Ubicacion>')
        sb.Append('<Provincia>' + issuing_company.state_id.code + '</Provincia>')
        sb.Append('<Canton>' + issuing_company.county_id.code + '</Canton>')
        sb.Append('<Distrito>' + issuing_company.district_id.code + '</Distrito>')

        if issuing_company.neighborhood_id and issuing_company.neighborhood_id.code:
            neighborhood_value = normalize_neighborhood(
                issuing_company.neighborhood_id.name
            )
            if neighborhood_value:
                 sb.Append("<Barrio>"+str(neighborhood_value)+"</Barrio>")

        sb.Append('<OtrasSenas>' + escape(str(issuing_company.street or 'No disponible')) + '</OtrasSenas>')
        sb.Append('</Ubicacion>')

        # if inv.tipo_documento in ['FEC']
        #     sb.Append('<OtrasSenasExtranjero>' + escape(str(issuing_company.street2 or 'No disponible')) + '</OtrasSenasExtranjero>')

        if issuing_company.phone:
            phone = phonenumbers.parse(issuing_company.phone, (issuing_company.country_id.code or 'CR'))
            sb.Append('<Telefono>')
            sb.Append('<CodigoPais>' + str(phone.country_code) + '</CodigoPais>')
            sb.Append('<NumTelefono>' + str(phone.national_number) + '</NumTelefono>')
            sb.Append('</Telefono>')

    sb.Append('<CorreoElectronico>' + str(issuing_company.email) + '</CorreoElectronico>')
    sb.Append('</Emisor>')

    if inv.tipo_documento == 'TE' or (inv.tipo_documento == 'NC' and not receiver_company.vat):
        pass
    else:
        vat = re.sub('[^0-9]', '', receiver_company.vat)
        if not receiver_company.identification_id:
            if len(vat) == 9:  # cedula fisica
                id_code = '01'
            elif len(vat) == 10:  # cedula juridica
                id_code = '02'
            elif len(vat) == 11 or len(vat) == 12:  # dimex
                id_code = '03'
            else:
                id_code = '05'
        else:
            id_code = receiver_company.identification_id.code

        if receiver_company.name:
            sb.Append('<Receptor>')
            sb.Append('<Nombre>' + escape(str(receiver_company.name[:99])) + '</Nombre>')
            sb.Append('<Identificacion>')
            sb.Append('<Tipo>' + id_code + '</Tipo>')
            sb.Append('<Numero>' + vat + '</Numero>')
            sb.Append('</Identificacion>')
            if inv.tipo_documento not in ['REP']:
                # NombreComercial # Este nodo es opcional
                if inv.tipo_documento != 'FEE':
                    if receiver_company.state_id and receiver_company.county_id and receiver_company.district_id and receiver_company.neighborhood_id:
                        sb.Append('<Ubicacion>')
                        sb.Append('<Provincia>' + str(receiver_company.state_id.code or '') + '</Provincia>')
                        sb.Append('<Canton>' + str(receiver_company.county_id.code or '') + '</Canton>')
                        sb.Append('<Distrito>' + str(receiver_company.district_id.code or '') + '</Distrito>')

                        if receiver_company.neighborhood_id and receiver_company.neighborhood_id.code:
                            receiver_neighborhood_value = normalize_neighborhood(
                                receiver_company.neighborhood_id.name
                            )
                            if receiver_neighborhood_value:
                                sb.Append("<Barrio>"+str(receiver_neighborhood_value)+"</Barrio>")

                        sb.Append('<OtrasSenas>' + escape(str(receiver_company.street or 'No disponible')) + '</OtrasSenas>')
                        sb.Append('</Ubicacion>')

                        # if inv.tipo_documento in ['FEC']:
                        # sb.Append('<OtrasSenasExtranjero>' + escape(str(receiver_company.street or 'No disponible')) + '</OtrasSenasExtranjero>')

                if receiver_company.phone:
                    try:
                        phone = phonenumbers.parse(receiver_company.phone, (receiver_company.country_id.code or 'CR'))
                        sb.Append('<Telefono>')
                        sb.Append('<CodigoPais>' + str(phone.country_code) + '</CodigoPais>')
                        sb.Append('<NumTelefono>' + str(phone.national_number) + '</NumTelefono>')
                        sb.Append('</Telefono>')
                    except:
                        pass

                match = receiver_company.email and re.match(
                    r'^(\s?[^\s,]+@[^\s,]+\.[^\s,]+\s?,)*(\s?[^\s,]+@[^\s,]+\.[^\s,]+)$',
                    receiver_company.email.lower())
                if match:
                    email_receptor = receiver_company.email
                else:
                    email_receptor = 'indefinido@indefinido.com'
                sb.Append('<CorreoElectronico>' + email_receptor + '</CorreoElectronico>')

            sb.Append('</Receptor>')

    sb.Append('<CondicionVenta>' + sale_conditions + '</CondicionVenta>')
    if sale_conditions == '99':
        sb.Append('<CondicionVentaOtros>' + inv.condicionVentaOtros or "Otras condiciones de venta" + '</CondicionVentaOtros>')

    sb.Append('<PlazoCredito>' + plazo_credito + '</PlazoCredito>')

    if lines:
        sb.Append('<DetalleServicio>')

        for (k, v) in lines.items():
            numero_linea = numero_linea + 1

            sb.Append('<LineaDetalle>')
            sb.Append('<NumeroLinea>' + str(numero_linea) + '</NumeroLinea>')

            if inv.tipo_documento == 'FEE' and v.get('partidaArancelaria'):
                sb.Append('<PartidaArancelaria>' + str(v['partidaArancelaria']) + '</PartidaArancelaria>')

            if v.get('codigoCabys'):
                sb.Append('<CodigoCABYS>' + (v['codigoCabys']) + '</CodigoCABYS>')

            if v.get('codigo'):
                sb.Append('<CodigoComercial>')
                sb.Append('<Tipo>04</Tipo>')
                sb.Append('<Codigo>' + (v['codigo']) + '</Codigo>')
                sb.Append('</CodigoComercial>')

            sb.Append('<Cantidad>' + str(v['cantidad']) + '</Cantidad>')
            sb.Append('<UnidadMedida>' + str(v['unidadMedida']) + '</UnidadMedida>')
            sb.Append('<Detalle>' + str(v['detalle']) + '</Detalle>')

            if v.get('RegistroMedicamento'):
                sb.Append('<RegistroMedicamento>' + (v['RegistroMedicamento']) + '</RegistroMedicamento>')
            if v.get('FormaFarmaceutica'):
                sb.Append('<FormaFarmaceutica>' + (v['FormaFarmaceutica']) + '</FormaFarmaceutica>')
            sb.Append('<PrecioUnitario>' + str(v['precioUnitario']) + '</PrecioUnitario>')
            sb.Append('<MontoTotal>' + str(v['montoTotal']) + '</MontoTotal>')
            if v.get('montoDescuento'):
                sb.Append('<Descuento>')
                sb.Append('<MontoDescuento>' + str(v['montoDescuento']) + '</MontoDescuento>')
                sb.Append('<CodigoDescuento>' + str(v.get('codigoDescuento', '07')) + '</CodigoDescuento>')

                if v.get('naturalezaDescuento'):
                    sb.Append('<CodigoDescuentoOTRO>' + str(v['codigoDescuentoOTRO']) + '</CodigoDescuentoOTRO>')
                    sb.Append('<NaturalezaDescuento>' + str(v['naturalezaDescuento']) + '</NaturalezaDescuento>')
                sb.Append('</Descuento>')

            sb.Append('<SubTotal>' + str(v['subtotal']) + '</SubTotal>')

            # TODO: ¿qué es base imponible? ¿porqué podría ser diferente del subtotal?

            if v.get('impuesto'):
                if inv.tipo_documento not in ['FEE', 'REP']:
                    if v['impuesto'][1]['codigo']=='01' and v['subtotal'] > 0:
                        sb.Append('<BaseImponible>' + str(v['subtotal']) + '</BaseImponible>')
                    
                    # En caso que el impuesto sea: selectivo de consumo (02),
                    # entonces BaseImponible se obtiene de la suma entre el campo “Subtotal”, más el impuesto selectivo de consumo (02)
                    # o el impuesto al cemento (12)
                    elif v['impuesto'][1]['codigo']=='02' or v['impuesto'][1]['codigo']=='12':
                        sum_baseImponible = v['subtotal'] + v['impuesto'][1]['monto']
                        sb.Append('<BaseImponible>' + str(sum_baseImponible) + '</BaseImponible>')

                for (a, b) in v['impuesto'].items():
                    tax_code = str(b['iva_tax_code'])
                    sb.Append('<Impuesto>')
                    sb.Append('<Codigo>' + str(b['codigo']) + '</Codigo>')
                    if tax_code.isdigit():
                        sb.Append('<CodigoTarifaIVA>' + tax_code + '</CodigoTarifaIVA>')
                    sb.Append('<Tarifa>' + str(b['tarifa']) + '</Tarifa>')
                    sb.Append('<Monto>' + str(b['monto']) + '</Monto>')

                    if inv.tipo_documento != 'FEE':
                        if b.get('exoneracion'):
                            if ( receiver_company.type_exoneration.code and receiver_company.exoneration_number and receiver_company.institution_name and receiver_company.date_issue):
                                sb.Append('<Exoneracion>')
                                sb.Append('<TipoDocumentoEX1>' + receiver_company.type_exoneration.code + '</TipoDocumentoEX1>')
                                sb.Append('<NumeroDocumento>' + receiver_company.exoneration_number + '</NumeroDocumento>')
                                if receiver_company.type_exoneration.code in ["02", "03", "06", "07", "08"]:
                                    sb.Append('<Articulo>' + str(receiver_company.exo_aticle) + '</Articulo>')
                                    sb.Append('<Inciso>' + str(receiver_company.exo_inciso) + '</Inciso>')
                                sb.Append('<NombreInstitucion>' + receiver_company.institution_name + '</NombreInstitucion>')
                                sb.Append('<FechaEmisionEX>' + str(receiver_company.date_issue) + 'T00:00:00-06:00' + '</FechaEmisionEX>')
                                sb.Append('<TarifaExonerada>' + str(b['exoneracion']['porcentajeCompra']) + '</TarifaExonerada>')
                                sb.Append('<MontoExoneracion>' + str(b['exoneracion']['montoImpuesto']) + '</MontoExoneracion>')
                                sb.Append('</Exoneracion>')
                            else:
                                inv.message_post(subject='Error',body='The invoice was sent but some information is missing. Please check the customer exoneration information.')
                                sb.Append('<Exoneracion>')
                                sb.Append('</Exoneracion>')
                    sb.Append('</Impuesto>')

                if inv.tipo_documento not in ['FEE','FEC','REP']:
                    sb.Append('<ImpuestoAsumidoEmisorFabrica>' + str(0) + '</ImpuestoAsumidoEmisorFabrica>')
                if inv.tipo_documento != 'FEE':
                    sb.Append('<ImpuestoNeto>' + str(v['impuestoNeto']) + '</ImpuestoNeto>')

            sb.Append('<MontoTotalLinea>' + str(v['montoTotalLinea']) + '</MontoTotalLinea>')
            sb.Append('</LineaDetalle>')
        sb.Append('</DetalleServicio>')

    if otrosCargos:
        sb.Append('<OtrosCargos>')
        for otro_cargo in otrosCargos:
            sb.Append('<TipoDocumentoOC>' +str(otrosCargos[otro_cargo]['TipoDocumento']) +'</TipoDocumentoOC>')

            if otrosCargos[otro_cargo].get('NumeroIdentidadTercero'):
                sb.Append('<NumeroIdentidadTercero>' + str(otrosCargos[otro_cargo]['NumeroIdentidadTercero']) + '</NumeroIdentidadTercero>')

            if otrosCargos[otro_cargo].get('NombreTercero'):
                sb.Append('<NombreTercero>' + str(otrosCargos[otro_cargo]['NombreTercero']) + '</NombreTercero>')

            sb.Append('<Detalle>' + str(otrosCargos[otro_cargo]['Detalle']) + '</Detalle>')

            if otrosCargos[otro_cargo].get('Porcentaje'):
                sb.Append('<PorcentajeOC>' + str(otrosCargos[otro_cargo]['Porcentaje']) + '</PorcentajeOC>')

            sb.Append('<MontoCargo>' + str(otrosCargos[otro_cargo]['MontoCargo']) + '</MontoCargo>')
        sb.Append('</OtrosCargos>')

    sb.Append('<ResumenFactura>')
    sb.Append('<CodigoTipoMoneda><CodigoMoneda>' +
              cod_moneda +
              '</CodigoMoneda><TipoCambio>' +
              str(currency_rate) +
              '</TipoCambio></CodigoTipoMoneda>')

    sb.Append('<TotalServGravados>' + str(total_servicio_gravado) + '</TotalServGravados>')
    sb.Append('<TotalServExentos>' + str(total_servicio_exento) + '</TotalServExentos>')

    if inv.tipo_documento != 'FEE':
        sb.Append('<TotalServExonerado>' + str(totalServExonerado) + '</TotalServExonerado>')
        sb.Append('<TotalServNoSujeto>' + str(totalServNoSujeto) + '</TotalServNoSujeto>')

    sb.Append('<TotalMercanciasGravadas>' + str(total_mercaderia_gravado) + '</TotalMercanciasGravadas>')
    sb.Append('<TotalMercanciasExentas>' + str(total_mercaderia_exento) + '</TotalMercanciasExentas>')

    if inv.tipo_documento != 'FEE':
        sb.Append('<TotalMercExonerada>' + str(totalMercExonerada) + '</TotalMercExonerada>')
        sb.Append('<TotalMercNoSujeta>' + str(totalMercNoSujeta) + '</TotalMercNoSujeta>')


    sb.Append('<TotalGravado>' + str(round(total_servicio_gravado + total_mercaderia_gravado, 5)) + '</TotalGravado>')
    sb.Append('<TotalExento>' + str(round(total_servicio_exento + total_mercaderia_exento, 5)) + '</TotalExento>')

    if inv.tipo_documento != 'FEE':
        sb.Append('<TotalExonerado>' + str(round(totalServExonerado + totalMercExonerada, 5)) + '</TotalExonerado>')
        sb.Append('<TotalNoSujeto>' + str(round(totalServNoSujeto + totalMercNoSujeta, 5)) + '</TotalNoSujeto>')

    sb.Append('<TotalVenta>' +
              str(round(
                  total_servicio_gravado + 
                  total_mercaderia_gravado + 
                  total_servicio_exento + 
                  total_mercaderia_exento + 
                  totalServExonerado + 
                  totalMercExonerada +
                  totalServNoSujeto + 
                  totalMercNoSujeta, 5)) +
              '</TotalVenta>')
    sb.Append('<TotalDescuentos>' + str(round(total_descuento, 5)) + '</TotalDescuentos>')
    sb.Append('<TotalVentaNeta>' + str(round(base_total, 5)) + '</TotalVentaNeta>')

    for tax_code in total_desgloce_impuesto:
        for iva_tax in total_desgloce_impuesto[tax_code]:
            sb.Append('<TotalDesgloseImpuesto>') 
            sb.Append('<Codigo>' + str(tax_code) + '</Codigo>')
            sb.Append('<CodigoTarifaIVA>' + str(iva_tax) + '</CodigoTarifaIVA>')
            sb.Append('<TotalMontoImpuesto>' + str(round(total_desgloce_impuesto[tax_code][iva_tax], 5)) + '</TotalMontoImpuesto>')
            sb.Append('</TotalDesgloseImpuesto>')
    sb.Append('<TotalImpuesto>' + str(round(total_impuestos, 5)) + '</TotalImpuesto>')

    if total_iva_devuelto:
        sb.Append('<TotalIVADevuelto>' + str(round(total_iva_devuelto, 5)) + '</TotalIVADevuelto>')

    sb.Append('<TotalOtrosCargos>' + str(totalOtrosCargos) + '</TotalOtrosCargos>')

    # Medio de pago
    if inv._name == 'pos.order':
        payment_methods = list(payment_methods_id.values())
        for payments in payment_methods:
            sb.Append('<MedioPago>')
            sb.Append('<TipoMedioPago>' + payments['TipoMedioPago'] + '</TipoMedioPago>')
            sb.Append('<TotalMedioPago>' + str(round(abs(payments['TotalMedioPago']), 5)) + '</TotalMedioPago>')
            sb.Append('</MedioPago>')

    else:
        sb.Append('<MedioPago>')
        payment_method_length = len(payment_methods_id)
        total_payment_method = round(base_total + total_impuestos + totalOtrosCargos - total_iva_devuelto, 5)
        for payment_method_counter in range(min(payment_method_length, 4)):
            sb.Append('<TipoMedioPago>' + payment_methods_id[payment_method_counter] + '</TipoMedioPago>')
            # sb.Append('<MedioPagoOtros>' + payment_methods_id[payment_method_counter] + '</TipoMedioPago>') ▪Será obligatorio en caso de utilizar el código 99 de “Otros” de la nota 6
            sb.Append('<TotalMedioPago>' + str(total_payment_method)+ '</TotalMedioPago>')
        sb.Append('</MedioPago>')

    sb.Append('<TotalComprobante>' + str(
        round(base_total + total_impuestos + totalOtrosCargos - total_iva_devuelto, 5)) + '</TotalComprobante>')
    sb.Append('</ResumenFactura>')
    if tipo_documento_referencia and numero_documento_referencia and fecha_emision_referencia:
        sb.Append('<InformacionReferencia>')
        sb.Append('<TipoDocIR>' + str(tipo_documento_referencia) + '</TipoDocIR>')
        sb.Append('<Numero>' + str(numero_documento_referencia) + '</Numero>')
        sb.Append('<FechaEmisionIR>' + fecha_emision_referencia + '</FechaEmisionIR>')
        sb.Append('<Codigo>' + str(codigo_referencia) + '</Codigo>')
        sb.Append('<Razon>' + str(razon_referencia) + '</Razon>')
        sb.Append('</InformacionReferencia>')
    if invoice_comments:
        sb.Append('<Otros>')
        sb.Append('<OtroTexto>' + str(invoice_comments) + '</OtroTexto>')
        sb.Append('</Otros>')

    sb.Append('</' + fe_enums.tagName[inv.tipo_documento] + '>')

    return sb


# Funcion para enviar el XML al Ministerio de Hacienda
def send_xml_fe(inv, token, date, xml, tipo_ambiente):
    headers = {'Authorization': 'Bearer ' +
                                token, 'Content-type': 'application/json'}

    # establecer el ambiente al cual me voy a conectar
    endpoint = fe_enums.UrlHaciendaRecepcion[tipo_ambiente]

    xml_base64 = stringToBase64(xml)

    data = {'clave': inv.number_electronic,
            'fecha': date,
            'emisor': {
                'tipoIdentificacion': inv.company_id.identification_id.code,
                'numeroIdentificacion': inv.company_id.vat
            },
            'comprobanteXml': xml_base64
            }
    if inv.partner_id and inv.partner_id.vat:
        if not inv.partner_id.identification_id:
            if len(inv.partner_id.vat) == 9:  # cedula fisica
                id_code = '01'
            elif len(inv.partner_id.vat) == 10:  # cedula juridica
                id_code = '02'
            elif len(inv.partner_id.vat) == 11 or len(inv.partner_id.vat) == 12:  # dimex
                id_code = '03'
            else:
                id_code = '05'
        else:
            id_code = inv.partner_id.identification_id.code

        data['receptor'] = {
            'tipoIdentificacion': id_code,
            'numeroIdentificacion': inv.partner_id.vat
        }

    json_hacienda = json.dumps(data)

    try:
        #  enviando solicitud post y guardando la respuesta como un objeto json
        response = requests.request(
            "POST", endpoint, data=json_hacienda, headers=headers)

        # Verificamos el codigo devuelto, si es distinto de 202 es porque hacienda nos está devolviendo algun error
        if response.status_code != 202:
            error_caused_by = response.headers.get(
                'X-Error-Cause') if 'X-Error-Cause' in response.headers else ''
            error_caused_by += response.headers.get('validation-exception', '')
            _logger.error('Status: {}, Text {}'.format(
                response.status_code, error_caused_by))

            return {'status': response.status_code, 'text': error_caused_by}
        else:
            # respuesta_hacienda = response.status_code
            return {'status': response.status_code, 'text': response.reason}
            # return respuesta_hacienda

    except ImportError:
        raise Warning('Error enviando el XML al Ministerior de Hacienda')


def schema_validator(xml_file, xsd_file) -> bool:
    """
    verifies a xml
    :param xml_invoice: Invoice xml
    :param  xsd_file: XSD File Name
    :return:
    """

    xmlschema = etree.XMLSchema(etree.parse(os.path.join(
        os.path.dirname(__file__), "xsd/" + xsd_file
    )))

    xml_doc = base64decode(xml_file)
    root = etree.fromstring(xml_doc, etree.XMLParser(remove_blank_text=True))
    result = xmlschema.validate(root)

    return result


# Obtener Attachments para las Facturas Electrónicas
def get_invoice_attachments(invoice, record_id):
    attachments = []

    attachment = invoice.env['ir.attachment'].search(
        [('res_model', '=', 'account.invoice'), ('res_id', '=', record_id),
         ('res_field', '=', 'xml_comprobante')], limit=1)

    if attachment.id:
        attachment.name = invoice.fname_xml_comprobante
        attachment.datas_fname = invoice.fname_xml_comprobante
        attachments.append(attachment.id)

    attachment_resp = invoice.env['ir.attachment'].search(
        [('res_model', '=', 'account.invoice'), ('res_id', '=', record_id),
         ('res_field', '=', 'xml_respuesta_tributacion')], limit=1)

    if attachment_resp.id:
        attachment_resp.name = invoice.fname_xml_respuesta_tributacion
        attachment_resp.datas_fname = invoice.fname_xml_respuesta_tributacion
        attachments.append(attachment_resp.id)

    return attachments


def parse_xml(name):
    return etree.parse(name).getroot()


# CONVIERTE UN STRING A BASE 64
def stringToBase64(s):
    return base64.b64encode(s).decode()


# TOMA UNA CADENA Y ELIMINA LOS CARACTERES AL INICIO Y AL FINAL
def stringStrip(s, start, end):
    return s[start:-end]


# Tomamos el XML y le hacemos el decode de base 64, esto por ahora es solo para probar
# la posible implementacion de la firma en python
def base64decode(string_decode):
    return base64.b64decode(string_decode)


# TOMA UNA CADENA EN BASE64 Y LA DECODIFICA PARA ELIMINAR EL b' Y DEJAR EL STRING CODIFICADO
# DE OTRA MANERA HACIENDA LO RECHAZA
def base64UTF8Decoder(s):
    return s.decode("utf-8")


# CLASE PERSONALIZADA (NO EXISTE EN PYTHON) QUE CONSTRUYE UNA CADENA MEDIANTE APPEND SEMEJANTE
# AL STRINGBUILDER DEL C#
class StringBuilder:
    _file_str = None

    def __init__(self):
        self._file_str = io.StringIO()

    def Append(self, str):
        self._file_str.write(str)

    def __str__(self):
        return self._file_str.getvalue()


def consulta_clave(clave, token, tipo_ambiente):
    endpoint = fe_enums.UrlHaciendaRecepcion[tipo_ambiente] + clave

    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    _logger.debug('FECR - consulta_clave - url: %s' % endpoint)

    try:
        # response = requests.request("GET", url, headers=headers)
        response = requests.get(endpoint, headers=headers)
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
        _logger.error('FECR - 400 - consulta_clave failed.  error: %s reason: %s',
                      response.status_code, response.reason)
        response_json = {'status': 400, 'ind-estado': 'error'}
    else:
        _logger.error('FECR - consulta_clave failed.  error: %s',
                      response.status_code)
        response_json = {'status': response.status_code,
                         'text': 'token_hacienda failed: %s' % response.reason}
    return response_json


def get_economic_activities(company):
    endpoint = "https://api.hacienda.go.cr/fe/ae?identificacion=" + company.vat

    headers = {'Content-Type': 'application/json',
               'Content-Type': 'application/x-www-form-urlencoded',
               'Sec-Fetch-Dest': 'iframe',
               'Sec-Fetch-User': '?1',
               'Sec-Fetch-Mode': 'navigate',
               'Sec-Fetch-Site': 'same-origin',
               'Accept-Language': 'en-US,en;q=0.9',
               'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"}

    try:
        response = requests.get(endpoint, headers=headers, verify=False)
    except requests.exceptions.RequestException as e:
        _logger.error('Exception %s' % e)
        return {'status': -1, 'text': 'Excepcion %s' % e}

    if 200 <= response.status_code <= 299:
        _logger.debug('FECR - get_economic_activities response: %s' % (response.json()))
        response_json = {
            'status': 200,
            'activities': response.json().get('actividades'),
            'name': response.json().get('nombre')
        }
    # elif 400 <= response.status_code <= 499:
    #    response_json = {'status': 400, 'ind-estado': 'error'}
    else:
        _logger.error('FECR - get_economic_activities failed.  error: %s',
                      response.status_code)
        response_json = {'status': response.status_code,
                         'text': 'get_economic_activities failed: %s' % response.reason}
    return response_json


def consulta_documentos(self, inv, env, token_m_h, date_cr, xml_firmado):
    if (inv.type == 'in_invoice' or inv.type == 'in_refund') and (inv.tipo_documento != 'FEC'):
        clave = inv.number_electronic + "-" + inv.consecutive_number_receiver
    else:
        clave = inv.number_electronic

    response_json = consulta_clave(clave, token_m_h, env)
    _logger.debug(response_json)
    estado_m_h = response_json.get('ind-estado')

    # Siempre sin importar el estado se actualiza la fecha de acuerdo a la devuelta por Hacienda y
    # se carga el xml devuelto por Hacienda
    last_state = inv.state_tributacion
    inv.state_tributacion = estado_m_h
    if inv.type == 'out_invoice' or inv.type == 'out_refund':
        # Se actualiza el estado con el que devuelve Hacienda
        inv.date_issuance = date_cr
        if xml_firmado:
            inv.fname_xml_comprobante = 'comprobante_' + inv.number_electronic + '.xml'
            inv.xml_comprobante = xml_firmado
    elif inv.type == 'in_invoice' or inv.type == 'in_refund':
        if xml_firmado:
            inv.fname_xml_comprobante = 'receptor_' + inv.number_electronic + '.xml'
            inv.xml_comprobante = xml_firmado

    # Si fue aceptado o rechazado por haciendo se carga la respuesta
    if (estado_m_h == 'aceptado' or estado_m_h == 'rechazado') or (
            inv.type == 'out_invoice' or inv.type == 'out_refund'):
        inv.fname_xml_respuesta_tributacion = 'respuesta_' + inv.number_electronic + '.xml'
        inv.xml_respuesta_tributacion = response_json.get('respuesta-xml')

    # Si fue aceptado por Hacienda y es un factura de cliente o nota de crédito, se envía el correo con los documentos
    if inv.tipo_documento != 'FEC' and estado_m_h == 'aceptado' and (last_state is False or last_state == 'procesando'):
        # if not inv.partner_id.opt_out:
        if inv.type == 'in_invoice' or inv.type == 'in_refund':
            email_template = self.env.ref(
                'cr_electronic_invoice.email_template_invoice_vendor', False)
        else:
            email_template = self.env.ref(
                'account.email_template_edi_invoice', False)

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

            try:
                email_template.with_context(type='binary', default_type='binary').send_mail(inv.id,
                                                                                            raise_exception=False,
                                                                                            force_send=True)  # default_type='binary'
            except:
                _logger.error('FECR - consulta documento error al enviar correo: %s',
                              inv.number_electronic)

            # limpia el template de los attachments
            email_template.attachment_ids = [(5, 0, 0)]


def send_message(inv, date_cr, xml, token, env):
    endpoint = fe_enums.UrlHaciendaRecepcion[env]

    vat = re.sub('[^0-9]', '', inv.partner_id.vat)
    xml_base64 = stringToBase64(xml)

    comprobante = {
        'clave': inv.number_electronic,
        'consecutivoReceptor': inv.consecutive_number_receiver,
        "fecha": date_cr,
        'emisor': {
            'tipoIdentificacion': str(inv.partner_id.identification_id.code),
            'numeroIdentificacion': vat,
        },
        'receptor': {
            'tipoIdentificacion': str(inv.company_id.identification_id.code),
            'numeroIdentificacion': inv.company_id.vat,
        },
        'comprobanteXml': xml_base64,
    }

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer {}'.format(token)}
    try:
        response = requests.post(endpoint, data=json.dumps(comprobante), headers=headers)

    except requests.exceptions.RequestException as e:
        _logger.info('Exception %s' % e)
        return {'status': 400, 'text': u'Excepción de envio XML'}
        # raise Exception(e)

    if not (200 <= response.status_code <= 299):
        _logger.error('FECR - ERROR SEND MESSAGE - RESPONSE:%s' %
                      response.headers.get('X-Error-Cause', 'Unknown'))
        return {'status': response.status_code, 'text': response.headers.get('X-Error-Cause', 'Unknown')}
    else:
        return {'status': response.status_code, 'text': response.text}


def load_xml_data(invoice, load_lines, account_id, product_id=False, analytic_account_id=False):
    try:
        invoice_xml = etree.fromstring(base64.b64decode(invoice.xml_supplier_approval))
        document_type = re.search('FacturaElectronica|NotaCreditoElectronica|NotaDebitoElectronica|TiqueteElectronico',
                                  invoice_xml.tag).group(0)

        if document_type == 'TiqueteElectronico':
            raise UserError(_("This is a TICKET only invoices are valid for taxes"))

    except Exception as e:
        raise UserError(_("This XML file is not XML-compliant. Error: %s") % e)

    namespaces = invoice_xml.nsmap
    inv_xmlns = namespaces.pop(None)
    namespaces['inv'] = inv_xmlns

    # invoice.consecutive_number_receiver = invoice_xml.xpath("inv:NumeroConsecutivo", namespaces=namespaces)[0].text
    invoice.reference = invoice_xml.xpath("inv:NumeroConsecutivo", namespaces=namespaces)[0].text

    invoice.number_electronic = invoice_xml.xpath("inv:Clave", namespaces=namespaces)[0].text
    activity_node = invoice_xml.xpath("inv:CodigoActividad", namespaces=namespaces)
    activity_id = False
    activity = False
    if activity_node:
        activity = invoice.env['economic.activity'].with_context(active_test=False).search([('code', '=', activity_node[0].text)], limit=1)
        activity_id = activity.id
        
    invoice.economic_activity_id = activity
    invoice.date_issuance = invoice_xml.xpath("inv:FechaEmision", namespaces=namespaces)[0].text
    invoice.date_invoice = invoice.date_issuance
    invoice.tipo_documento = False

    emisor = invoice_xml.xpath("inv:Emisor/inv:Identificacion/inv:Numero", namespaces=namespaces)[0].text
    tipo_emisor = invoice_xml.xpath("inv:Emisor/inv:Identificacion/inv:Tipo", namespaces=namespaces)[0].text
    nombre_emisor = invoice_xml.xpath("inv:Emisor/inv:Nombre", namespaces=namespaces)[0].text
    pais_emisor = invoice.env['res.country'].search([('name', '=', 'Costa Rica')], limit=1).id
    try:
        telefono_emisor = invoice_xml.xpath("inv:Emisor/inv:Telefono/inv:NumTelefono", namespaces=namespaces)[0].text
    except IndexError:
        telefono_emisor = ''
    otrassenas_emisor = invoice_xml.xpath("inv:Emisor/inv:Ubicacion/inv:OtrasSenas", namespaces=namespaces)[0].text
    correo_emisor = invoice_xml.xpath("inv:Emisor/inv:CorreoElectronico", namespaces=namespaces)[0].text

    receptor_node = invoice_xml.xpath("inv:Receptor/inv:Identificacion/inv:Numero", namespaces=namespaces)
    if receptor_node:
        receptor = receptor_node[0].text
    else:
        raise UserError('El receptor no está definido en el xml')  # noqa

    if receptor != invoice.company_id.vat:
        raise UserError('El receptor no corresponde con la compañía actual con identificación ' +
                        receptor + '. Por favor active la compañía correcta.')  # noqa

    currency_node = invoice_xml.xpath("inv:ResumenFactura/inv:CodigoTipoMoneda/inv:CodigoMoneda", namespaces=namespaces)

    if currency_node:
        invoice.currency_id = invoice.env['res.currency'].search([('name', '=', currency_node[0].text)], limit=1).id
    else:
        invoice.currency_id = invoice.env['res.currency'].search([('name', '=', 'CRC')], limit=1).id

    partner = invoice.env['res.partner'].search([('vat', '=', emisor),
                                                 ('supplier', '=', True),
                                                 '|',
                                                 ('company_id', '=', invoice.company_id.id),
                                                 ('company_id', '=', False)],
                                                limit=1)

    if partner:
        invoice.partner_id = partner
    else:
        new_partner = invoice.env['res.partner'].create({
                                                        'name': nombre_emisor,
                                                        'vat': emisor,
                                                        'identification_id': tipo_emisor,
                                                        'type':'contact',
                                                        'country_id': pais_emisor,
                                                        'phone': telefono_emisor,
                                                        'email': correo_emisor,
                                                        'street': otrassenas_emisor,
                                                        'supplier': 'True'})
        if new_partner:
            invoice.partner_id = new_partner
        else:
            raise UserError(_('The provider in the invoice does not exists. I tried to created without success. Please review it.'))

    invoice.account_id = partner.property_account_payable_id
    invoice.payment_term_id = partner.property_supplier_payment_term_id

    payment_method_node = invoice_xml.xpath("inv:MedioPago", namespaces=namespaces)
    if payment_method_node:
        invoice.payment_methods_id = invoice.env['payment.methods'].search(
            [('sequence', '=', payment_method_node[0].text)], limit=1)
    else:
        invoice.payment_methods_id = partner.payment_methods_id

    _logger.debug('FECR - load_lines: %s - account: %s' %
                  (load_lines, account_id))

    product = False
    if product_id:
        product = product_id.id

    analytic_account = False
    if analytic_account_id:
        analytic_account = analytic_account_id.id

    # if load_lines and not invoice.invoice_line_ids:
    if load_lines:
        lines = invoice_xml.xpath("inv:DetalleServicio/inv:LineaDetalle", namespaces=namespaces)
        new_lines = invoice.env['account.invoice.line']
        for line in lines:
            product_uom = invoice.env['uom.uom'].search(
                [('code', '=', line.xpath("inv:UnidadMedida", namespaces=namespaces)[0].text)],
                limit=1).id
            total_amount = float(line.xpath("inv:MontoTotal", namespaces=namespaces)[0].text)

            discount_percentage = 0.0
            discount_note = None

            if total_amount > 0:
                discount_node = line.xpath("inv:Descuento", namespaces=namespaces)
                if discount_node:
                    discount_amount_node = discount_node[0].xpath("inv:MontoDescuento", namespaces=namespaces)[0]
                    discount_amount = float(discount_amount_node.text or '0.0')
                    discount_percentage = discount_amount / total_amount * 100
                    discount_note = discount_node[0].xpath("inv:NaturalezaDescuento", namespaces=namespaces)[0].text
                else:
                    discount_amount_node = line.xpath("inv:MontoDescuento", namespaces=namespaces)
                    if discount_amount_node:
                        discount_amount = float(discount_amount_node[0].text or '0.0')
                        discount_percentage = discount_amount / total_amount * 100
                        discount_note = line.xpath("inv:NaturalezaDescuento", namespaces=namespaces)[0].text

            total_tax = 0.0
            taxes = []
            tax_nodes = line.xpath("inv:Impuesto", namespaces=namespaces)
            for tax_node in tax_nodes:
                tax_code = re.sub(r"[^0-9]+", "", tax_node.xpath("inv:Codigo", namespaces=namespaces)[0].text)
                tax_amount = float(tax_node.xpath("inv:Tarifa", namespaces=namespaces)[0].text)
                _logger.debug('FECR - tax_code: %s', tax_code)
                _logger.debug('FECR - tax_amount: %s', tax_amount)

                if product_id and product_id.non_tax_deductible:
                    tax = invoice.env['account.tax'].search(
                        [('tax_code', '=', tax_code),
                         ('amount', '=', tax_amount),
                         ('type_tax_use', '=', 'purchase'),
                         ('non_tax_deductible', '=', True),
                         ('active', '=', True)],
                        limit=1)
                else:
                    tax = invoice.env['account.tax'].search(
                        [('tax_code', '=', tax_code),
                         ('amount', '=', tax_amount),
                         ('type_tax_use', '=', 'purchase'),
                         ('non_tax_deductible', '=', False),
                         ('active', '=', True)],
                        limit=1)

                if tax:
                    total_tax += float(tax_node.xpath("inv:Monto", namespaces=namespaces)[0].text)

                    exonerations = tax_node.xpath("inv:Exoneracion", namespaces=namespaces)
                    if exonerations:
                        for exoneration_node in exonerations:
                            exoneration_percentage = float(
                                exoneration_node.xpath("inv:PorcentajeExoneracion", namespaces=namespaces)[0].text)
                            tax = invoice.env['account.tax'].search(
                                [('percentage_exoneration', '=', exoneration_percentage),
                                 ('type_tax_use', '=', 'purchase'),
                                 ('non_tax_deductible', '=', False),
                                 ('has_exoneration', '=', True),
                                 ('active', '=', True)],
                                limit=1)
                            taxes.append((4, tax.id))
                    else:
                        taxes.append((4, tax.id))
                else:
                    if product_id and product_id.non_tax_deductible:
                        raise UserError(
                            _('Tax code %s and percentage %s as non-tax deductible is not registered in the system' % (
                            tax_code, tax_amount)))
                    else:
                        raise UserError(
                            _('Tax code %s and percentage %s is not registered in the system' % (tax_code, tax_amount)))

            _logger.debug('FECR - impuestos de linea: %s' % (taxes))
            invoice_line = invoice.env['account.invoice.line'].create({
                'name': line.xpath("inv:Detalle", namespaces=namespaces)[0].text,
                'invoice_id': invoice.id,
                'price_unit': line.xpath("inv:PrecioUnitario", namespaces=namespaces)[0].text,
                'quantity': line.xpath("inv:Cantidad", namespaces=namespaces)[0].text,
                'uom_id': product_uom,
                'sequence': line.xpath("inv:NumeroLinea", namespaces=namespaces)[0].text,
                'discount': discount_percentage,
                'discount_note': discount_note,
                'product_id': product,
                'account_id': account_id.id,
                'account_analytic_id': analytic_account,
                'amount_untaxed': float(line.xpath("inv:SubTotal", namespaces=namespaces)[0].text),
                'total_tax': total_tax,
                # 'economic_activity_id': invoice.economic_activity_id.id,
            })

            # This must be assigned after line is created
            invoice_line.invoice_line_tax_ids = taxes
            invoice_line.economic_activity_id = activity
            new_lines += invoice_line

        otrosCargos = invoice_xml.xpath("inv:OtrosCargos", namespaces=namespaces)
        
        _logger.info('\n estoy imprmiendo \n %r \n\n', otrosCargos)
        if otrosCargos:
            for line in otrosCargos:
                percentage = line.xpath("inv:Porcentaje", namespaces=namespaces)
                type_document = line.xpath("inv:TipoDocumento", namespaces=namespaces)[0].text
                details = line.xpath("inv:Detalle", namespaces=namespaces)[0].text
                if percentage:
                    percentage=percentage[0].text
                amount_charge = line.xpath("inv:MontoCargo", namespaces=namespaces)[0].text
                product = invoice.env['product.product'].search([('default_code','=',type_document)],limit=1)
                taxes=product.supplier_taxes_id.filtered(lambda t:t.active==True)
                _logger.info('\n imprimiendo los taxs\n %r \n\n', [product.supplier_taxes_id,product.id,account_id.id,invoice.id])
                invoice_line = invoice.env['account.invoice.line'].create({
                    'name': line.xpath("inv:Detalle", namespaces=namespaces)[0].text,
                    'invoice_id': invoice.id,
                    'price_unit': line.xpath("inv:MontoCargo", namespaces=namespaces)[0].text,
                    'quantity': 1,
                    'uom_id': product.uom_id.id,
                    'product_id': product.id,
                    'account_id': account_id.id,
                    'account_analytic_id': analytic_account,
                    'invoice_line_tax_ids':[(4,taxes.id)]
                    })
                #_logger.info('\n imprimiendo los taxs\n %r \n\n', [product.uom_id.id,taxes_id,product.id,account_id.id,invoice.id])
                invoice_line.economic_activity_id = activity
                new_lines += invoice_line
                _logger.info('\n imprimiendo los activity \n %r \n\n',activity)
                _logger.info('\n imprimiendo los new lines \n %r \n\n',new_lines)


        invoice.invoice_line_ids = new_lines
        _logger.info('\n imprimiendo los new lines ids \n %r \n\n',new_lines)

    invoice.amount_total_electronic_invoice = \
    invoice_xml.xpath("inv:ResumenFactura/inv:TotalComprobante", namespaces=namespaces)[0].text

    tax_node = invoice_xml.xpath("inv:ResumenFactura/inv:TotalImpuesto", namespaces=namespaces)
    if tax_node:
        invoice.amount_tax_electronic_invoice = tax_node[0].text
    invoice.compute_taxes()


def p12_expiration_date(p12file, password):
    try:
        pkcs12 = crypto.load_pkcs12(base64.b64decode(p12file), password)
        data = crypto.dump_certificate(crypto.FILETYPE_PEM, pkcs12.get_certificate())
        cert = x509.load_pem_x509_certificate(data, default_backend())
        return cert.not_valid_after
    except crypto.Error as crypte:
        exc_str = str(crypte)
        if exc_str.find('mac verify failure'):
            raise
        else:
            raise

def normalize_neighborhood(name: str) -> str:
    """
    Ensures the <Barrio> value meets Hacienda's minLength=5 rule.

    - Empty input  → returns "" (caller should skip the tag).
    - Length ≤ 4   → prepends 'Barrio ' to reach ≥ 5 characters.
    - Always XML-escapes the result.

    Parameters
    ----------
    name : str
        The raw neighborhood name from the database.

    Returns
    -------
    str
        A normalized, XML-safe string (or empty if name is falsy).
    """
    if not name:
        return ""
    name = name.strip()
    if len(name) < 5:  # 1-4 chars trigger prefix
        name = "Barrio %s"% name
    return escape(name)