# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
_logging = logging.getLogger(__name__)

class AccountPayment(models.Model):
	_inherit = "account.payment"

	telecredito_id = fields.Many2one('speru.telecredito', string='Telecrédito')