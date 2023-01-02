# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logging = logging.getLogger(__name__)

class AccountPaymentRegisterTemp(models.TransientModel):
	_inherit = 'account.payment.register'
	_name = 'account.payment.register.temp'
	_description = 'Register Payment'

	line_ids = fields.Many2many('account.move.line', 'account_payment_register_temp_move_line_rel', 'wizard_id', 'line_id',
		string="Journal items", readonly=True, copy=False,)

	@api.model
	def _get_wizard_values_from_batch(self, batch_result):
		payment_values = batch_result['payment_values']
		lines = batch_result['lines']
		company = lines[0].company_id
		factura = lines[0].move_id

		source_amount = abs(sum(lines.mapped('amount_residual')))
		retencion = factura.monto_retencion
		detraccion = factura.monto_detraccion
		source_amount = source_amount - retencion - detraccion
		if payment_values['currency_id'] == company.currency_id.id:
			source_amount_currency = source_amount
		else:
			source_amount_currency = abs(sum(lines.mapped('amount_residual_currency')))
			retencion_currency = factura.monto_retencion_base
			detraccion_currency = factura.monto_detraccion_base
			source_amount_currency = source_amount_currency - retencion_currency - detraccion_currency

		return {
			'company_id': company.id,
			'partner_id': payment_values['partner_id'],
			'partner_type': payment_values['partner_type'],
			'payment_type': payment_values['payment_type'],
			'source_currency_id': payment_values['currency_id'],
			'source_amount': source_amount,
			'source_amount_currency': source_amount_currency,
		}
