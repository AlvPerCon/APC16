# -*- coding: utf-8 -*-
# Copyright (c) 2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

class AccountJournal(models.Model):
	_inherit = "account.journal"

	usuario_ids = fields.Many2many("res.users", "journal_id_user_id", "journal_id", "user_id", string="Usuarios")
