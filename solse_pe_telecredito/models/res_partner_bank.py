# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import base64
import logging
_logging = logging.getLogger(__name__)


class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	tipo_cuenta = fields.Selection([('C', 'Corriente'), ('M', 'Maestra'), ('A', 'Ahorros'), ('B', 'Interbancaria'), ('D', 'Detracción'), ('E', 'Exterior')], default="C", string="Tipo de cuenta")