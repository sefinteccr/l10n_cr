# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError, Warning
from datetime import datetime, date, timedelta
import json, requests, re
import logging

_logger = logging.getLogger(__name__)

class res_company(models.Model):
    _name = 'res.company'
    _inherit = ['res.company']

    ultima_respuesta = fields.Text(string="Última Respuesta de API", help="Última Respuesta de API, esto permite depurar errores en caso de existir")
    url_base = fields.Char(string="URL Base", required=False, help="URL Base del END POINT", default="https://api.hacienda.go.cr/fe/ae?")

    url_base_yo_contribuyo = fields.Char(string="URL Base Yo Contribuyo",
                           required=False,
                           help="URL Base Yo Contribuyo",
                           default="https://api.hacienda.go.cr/fe/mifacturacorreo?")
    
    usuario_yo_contribuyo = fields.Char(string="Usuario Yo Contribuyo",
                           required=False,
                           help="Usuario Yo Contribuyo")

    token_yo_contribuyo = fields.Char(string="Token Yo Contribuyo",
                           required=False,
                           help="Token Yo Contribuyo")

    url_economic_activity = fields.Char(string="URL Actividad Económica",
                            help="Endpoint base para consultar actividades económicas",
                            default="https://api.hacienda.go.cr/fe/ae?identificacion=")


class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = "res.partner"

    def limpiar_cedula(self,vat):
        if vat:
            return ''.join(i for i in vat if i.isdigit())

    @api.onchange('vat')
    def onchange_cedula(self):
        self.name = ''
        self.identification_id = ''

    #Funcion ejecutada al haber un cambio en el campo vat(cedula)
    @api.onchange('vat')
    def onchange_vat(self):

        #Valida que el campo vat(cedula) este lleno esto evita que se ejecute el codigo al inicio
        if self.vat:
            self.vat = self.limpiar_cedula(self.vat)
            url_base = self.company_id.url_base
            self.name = ''

            url_base_yo_contribuyo = self.company_id.url_base_yo_contribuyo
            usuario_yo_contribuyo = self.company_id.usuario_yo_contribuyo
            token_yo_contribuyo = self.company_id.token_yo_contribuyo
            if url_base_yo_contribuyo and usuario_yo_contribuyo and token_yo_contribuyo:
                url_base_yo_contribuyo = url_base_yo_contribuyo.strip()

                if url_base_yo_contribuyo[-1:] == '/':
                    url_base_yo_contribuyo = url_base_yo_contribuyo[:-1]

                end_point = url_base_yo_contribuyo + 'identificacion=' + self.vat

                headers.update({
                    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                    'Content-Type': 'application/x-www-form-urlencoded, application/json',
                    'Sec-Fetch-Dest': 'iframe',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Accept-Language': 'en-US,en;q=0.9',
                })

                try:
                    peticion = requests.get(end_point, headers=headers, timeout=10)
                    all_emails_yo_contribuyo = ''

                    if peticion.status_code in (200, 202) and len(peticion._content) > 0:
                        contenido = json.loads(str(peticion._content, 'utf-8'))
                        emails_yo_contribuyo = contenido['Resultado']['Correos']
                        for email_yo_contribuyo in emails_yo_contribuyo:
                            all_emails_yo_contribuyo = all_emails_yo_contribuyo + email_yo_contribuyo['Correo'] + ','
                        all_emails_yo_contribuyo = all_emails_yo_contribuyo[:-1]
                        self.email = all_emails_yo_contribuyo

                except:
                    self.env.user.notify_default(message='The email query service is unavailable at this moment', title='Query service')

            #Valida que existan el campo url_base
            if url_base:
                #Limpia caracteres en blanco en los extremos
                url_base = url_base.strip()

                #Elimina la barra al final de la URL para prevenir error al conectarse
                if url_base[-1:] == '/':
                    url_base = url_base[:-1]

                end_point = url_base + 'identificacion=' + self.vat

                headers = {'Content-Type': 'application/json',
                           'Content-Type': 'application/x-www-form-urlencoded',
                           'Sec-Fetch-Dest': 'iframe',
                           'Sec-Fetch-User': '?1',
                           'Sec-Fetch-Mode': 'navigate',
                           'Sec-Fetch-Site': 'same-origin',
                           'Accept-Language': 'en-US,en;q=0.9',
                           'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"}

                #Petición GET a la API
                try:
                    peticion = requests.get(end_point, headers=headers, timeout=10)

                    ultimo_mensaje = 'Fecha/Hora: ' + str(datetime.now()) + ', Codigo: ' + str(peticion.status_code) + ', Mensaje: ' + str(peticion._content.decode())

                    #Respuesta de la API
                    if peticion.status_code in (200,202) and len(peticion._content) > 0:
                        contenido = json.loads(str(peticion._content,'utf-8'))
                        actividades = contenido.get('actividades')
                        self.env.cr.execute("UPDATE  res_company SET ultima_respuesta='%s' WHERE id=%s" % (ultimo_mensaje,self.company_id.id))
                        if 'nombre' in contenido:
                            #Compatibilidad con FE
                            if 'identification_id' in self._fields:
                                if 'tipoIdentificacion' in contenido:
                                    clasificacion = contenido.get('tipoIdentificacion')
                                    if clasificacion == '01':#Cedula Fisicaclasificacion
                                        self.identification_id = self.env['identification.type'].search([('code', '=', '01')], limit=1).id
                                    elif clasificacion == '02':#Cedula Juridica
                                        self.identification_id = self.env['identification.type'].search([('code', '=', '02')], limit=1).id
                                    elif clasificacion == '03':#Cedula Juridica
                                        self.identification_id = self.env['identification.type'].search([('code', '=', '03')], limit=1).id
                                    elif clasificacion == '04':#Cedula Juridica
                                        self.identification_id = self.env['identification.type'].search([('code', '=', '04')], limit=1).id
                                    elif clasificacion == '05':#Cedula Juridica
                                        self.identification_id = self.env['identification.type'].search([('code', '=', '05')], limit=1).id

                            if contenido.get('nombre') != None:
                                name = contenido.get('nombre')
                                self.name = name
                                for act in actividades:
                                    if act.get('estado') == 'A':
                                        self.activity_id = self.env['economic.activity'].search([('code', '=', str(act.get('codigo')))], limit=1).id

                    #Si la petición arroja error se almacena en el campo ultima_respuesta de res_company. Nota: se usa execute ya que el metodo por objeto no funciono
                    else:
                        self.env.cr.execute("UPDATE  res_company SET ultima_respuesta='%s' WHERE id=%s" % (ultimo_mensaje,self.company_id.id))
                except:
                    self.env.user.notify_default(message='The name query service is unavailable at this moment', title='Query service')



    @api.model
    def create_from_ui(self, partner):
        economic_activities_ids = partner.get('economic_activities_ids')
        if economic_activities_ids:
            ids_list = [int(x) for x in economic_activities_ids.split(',') if x.strip()]
            partner['economic_activities_ids'] = [(6, 0, ids_list)]

        res = super(res_partner, self).create_from_ui(partner)
        return res