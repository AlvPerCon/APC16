# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, _
from odoo.exceptions import UserError
import logging
_logging = logging.getLogger(__name__)

class ValidateAccountMove(models.TransientModel):
	_name = "speru.telecredito.crear"
	_description = "Crear reporte para Telecredito"

	diario_pago = fields.Many2one('account.journal', 'Diario de pago', domain=[('type', 'in', ['bank'])])
	name = fields.Char('Nombre de lote')
	
	def asignar_pagos(self):
		facturas = self.env['account.move'].browse(self._context.get('active_ids', []))
		telecredito = self.env['speru.telecredito'].search([('state', '=', 'borrador')])
		if not telecredito:
			telecredito = self.env['speru.telecredito'].create({
				'name': self.name,
				'cuenta_cargo': self.diario_pago.id,
			})
		else:
			telecredito.write({
				'name': self.name,
				'cuenta_cargo': self.diario_pago.id,
			})
		for factura in facturas:
			if not factura.telecredito_id and factura.state in ['posted'] and factura.payment_state in ['not_paid', 'partial']:
				factura.write({
					'telecredito_id': telecredito.id,
				})

		action = self.env["ir.actions.actions"]._for_xml_id("solse_pe_telecredito.action_telecredito_form")
		form_view = [(self.env.ref('solse_pe_telecredito.view_telecredito_form').id, 'form')]
		if 'views' in action:
			action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
		else:
			action['views'] = form_view
		action['res_id'] = telecredito.id
		action['context'] = {}
		return action
		