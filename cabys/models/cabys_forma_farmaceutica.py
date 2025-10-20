# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class CabysFormaFarmaceutica(models.Model):
    _name = 'cabys.forma.farmaceutica'
    _description = 'Cabys Forma Farmaceútica'

    name = fields.Char('Forma Farmaceútica', readonly=True)
    code = fields.Char('Código', readonly=True)