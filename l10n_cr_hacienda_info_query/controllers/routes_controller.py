# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError, Warning
from datetime import datetime, date, timedelta
import json, requests, re, logging

from odoo import http
from odoo.http import request


_logger = logging.getLogger(__name__)

class actualizar_pos_api(http.Controller):

    #https://api.thunder.com.ve/control_rig/84:F3:EB:22:6E:D9
    @http.route(['/cedula/<vat>',], type='http', auth="user", website=True)
    def index(self,vat):

        company_id = http.request.env['res.company'].sudo().search([],limit=1)

        url_base_yo_contribuyo = company_id.url_base_yo_contribuyo
        usuario_yo_contribuyo = company_id.usuario_yo_contribuyo
        token_yo_contribuyo = company_id.token_yo_contribuyo
        all_emails_yo_contribuyo = ""
        name = None
        identification_id = ""
        # logger.info(url_base_yo_contribuyo + " " + usuario_yo_contribuyo + " " + token_yo_contribuyo)
        if url_base_yo_contribuyo and usuario_yo_contribuyo and token_yo_contribuyo:
            url_base_yo_contribuyo = url_base_yo_contribuyo.strip()

            if url_base_yo_contribuyo[-1:] == '/':
                url_base_yo_contribuyo = url_base_yo_contribuyo[:-1]
            end_point = url_base_yo_contribuyo + 'identificacion=' + vat
            headers = requests.utils.default_headers()
            headers.update({
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                'Content-Type': 'application/x-www-form-urlencoded, application/json',
                'Sec-Fetch-Dest': 'iframe',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Accept-Language': 'en-US,en;q=0.9',
            })

            peticion = requests.get(end_point, headers=headers, timeout=10)
            all_emails_yo_contribuyo = ''

            if peticion.status_code in (200, 202) and len(peticion._content) > 0:
                contenido = json.loads(str(peticion._content, 'utf-8'))
                emails_yo_contribuyo = contenido['Resultado']['Correos']
                for email_yo_contribuyo in emails_yo_contribuyo:
                    all_emails_yo_contribuyo = all_emails_yo_contribuyo + email_yo_contribuyo['Correo'] + ','
                all_emails_yo_contribuyo = all_emails_yo_contribuyo[:-1]

        url_base = company_id.url_base

        if url_base:
            #Elimina la barra al final de la URL para prevenir error al conectarse
            if url_base[-1:] == '/':
                url_base = url_base[:-1]

            end_point = url_base + 'identificacion=' + vat

            headers = {'Content-Type': 'application/json',
               'Content-Type': 'application/x-www-form-urlencoded',
               'Sec-Fetch-Dest': 'iframe',
               'Sec-Fetch-User': '?1',
               'Sec-Fetch-Mode' : 'navigate',
               'Sec-Fetch-Site' : 'same-origin',
               'Accept-Language' : 'en-US,en;q=0.9',
               'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"}

            #Petición GET a la API
            peticion = requests.get(end_point, headers=headers, timeout=3)
            ultimo_mensaje = 'Fecha/Hora: ' + str(datetime.now()) + ', Codigo: ' + str(peticion.status_code) + ', Mensaje: ' + str(peticion._content.decode())

            #Respuesta de la API
            if peticion.status_code in (200,202) and len(peticion._content) > 0:
                contenido = json.loads(str(peticion._content,'utf-8'))
                http.request.env.cr.execute("UPDATE res_company SET ultima_respuesta='%s' WHERE id=%s" % (ultimo_mensaje,company_id.id))

                if 'nombre' in contenido:

                    res_partner = http.request.env['res.partner']

                    if 'identification_id' in res_partner:

                        id_type = http.request.env['identification.type']

                        if 'tipoIdentificacion' in contenido:
                                clasificacion = contenido.get('tipoIdentificacion')
                                if clasificacion == '01':#Cedula Fisicaclasificacion
                                    identification_id = id_type.search([('code', '=', '01')], limit=1).id
                                elif clasificacion == '02':#Cedula Juridica
                                    identification_id = id_type.search([('code', '=', '02')], limit=1).id
                                elif clasificacion == '03':#Cedula Juridica
                                    identification_id = id_type.search([('code', '=', '03')], limit=1).id
                                elif clasificacion == '04':#Cedula Juridica
                                    identification_id = id_type.search([('code', '=', '04')], limit=1).id
                                elif clasificacion == '05':#Cedula Juridica
                                    identification_id = id_type.search([('code', '=', '05')], limit=1).id
                        name = contenido.get('nombre')

            #Si la petición arroja error se almacena en el campo ultima_respuesta de res_company. Nota: se usa execute ya que el metodo por objeto no funciono
            else:
                http.request.env.cr.execute("UPDATE  res_company SET ultima_respuesta='%s' WHERE id=%s" % (ultimo_mensaje,company_id.id))
        
        actividades = []
        url_economic_activity = company_id.url_economic_activity
        if url_economic_activity:
            url_economic_activity = url_economic_activity.strip()
            if url_economic_activity[-1:] == '/':
                url_economic_activity = url_economic_activity[:-1]

            endpoint = url_economic_activity + vat
            headers = {'Content-Type': 'application/json', 'User-Agent': "Mozilla/5.0"}

            try:
                response = requests.get(endpoint, headers=headers, timeout=10, verify=False)
                if 200 <= response.status_code <= 299 and response.content:
                    contenido = response.json()
                    for act in contenido.get("actividades", []):
                        if act.get("estado") == "A" and act.get("codigo") != '960113':
                            econ_act = http.request.env['economic.activity'].with_context(active_test=False).search([('code', '=', act.get("codigo"))])
                            if not econ_act:

                                new_act = http.request.env['economic.activity'].create({
                                    'code': act.get("codigo"),
                                    'name': act.get("descripcion"),
                                    'active': False
                                })
                                econ_act = new_act

                            if econ_act:
                                actividades.append({
                                    "id": econ_act.id,
                                    "code": act.get("codigo"),
                                    "descripcion": act.get("descripcion"),
                                })
            except Exception as e:
                _logger.error(" Error consultando actividades económicas: %s", e)

        retorno = {
            "nombre": str(name) if name else "",
            "identification_id": str(identification_id),
            "email": str(all_emails_yo_contribuyo),
            "actividades": actividades
        }
        return json.dumps(retorno, ensure_ascii=False)

    @http.route(['/economic_activities/<vat>',], type='http', auth="user", website=True)
    def economical_activities(self,vat):
        actividades = []
        company_id = http.request.env['res.company'].sudo().search([],limit=1)
        url_economic_activity = company_id.url_economic_activity
        if url_economic_activity:
            url_economic_activity = url_economic_activity.strip()
            if url_economic_activity[-1:] == '/':
                url_economic_activity = url_economic_activity[:-1]

            endpoint = url_economic_activity + vat
            headers = {'Content-Type': 'application/json', 'User-Agent': "Mozilla/5.0"}

            try:
                response = requests.get(endpoint, headers=headers, timeout=10, verify=False)
                if 200 <= response.status_code <= 299 and response.content:
                    contenido = response.json()
                    for act in contenido.get("actividades", []):
                        if act.get("estado") == "A" and act.get("codigo") != '960113':
                            econ_act = http.request.env['economic.activity'].with_context(active_test=False).search([('code', '=', act.get("codigo"))])
                            if not econ_act:
                                
                                new_act = http.request.env['economic.activity'].create({
                                    'code': act.get("codigo"),
                                    'name': act.get("descripcion"),
                                    'active': False
                                })
                                econ_act = new_act
                            if econ_act:
                                actividades.append({
                                    "id": econ_act.id,
                                    "code": act.get("codigo"),
                                    "descripcion": act.get("descripcion"),
                                })
            except Exception as e:
                _logger.error(" Error consultando actividades económicas: %s", e)

        retorno = {
            "actividades": actividades
        }
        return json.dumps(retorno, ensure_ascii=False) 