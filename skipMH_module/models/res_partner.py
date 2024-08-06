# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PartnerskipMH(models.Model):
    _inherit = "res.partner"

    skipMH = fields.Boolean(string="Brincar MH", required=False, )
