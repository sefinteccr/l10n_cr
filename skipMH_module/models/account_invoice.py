# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.cr_electronic_invoice.models.account_invoice as cr_account_invoice
import logging

_logger = logging.getLogger(__name__)


class AccountInvoiceSkipMH(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        # Revisamos si el ambiente para Hacienda está habilitado
        for inv in self:
            if inv.partner_id.skipMH:
               return super(cr_account_invoice.AccountInvoiceElectronic, inv).action_invoice_open()
            else:
                return super(AccountInvoiceSkipMH, inv).action_invoice_open()

