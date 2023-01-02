# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _
import logging
import json
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = 'account.move'

	def obtener_cuenta_mextranejera_cliente(self, contacto):
		if self.move_type == 'out_invoice':
			if self.currency_id.id != self.company_id.currency_id.id:
				return self.partner_id.property_account_receivable_2_id or self.partner_id.property_account_receivable_id
		
		return self.partner_id.property_account_receivable_id

	def obtener_cuenta_mextranejera_proveedor(self, contacto):
		if self.move_type == 'in_invoice':
			if self.currency_id.id != self.company_id.currency_id.id:
				return self.partner_id.property_account_payable_2_id or self.partner_id.property_account_payable_id
		
		return self.partner_id.property_account_payable_id

	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		self = self.with_company(self.journal_id.company_id)

		warning = {}
		if self.partner_id:
			rec_account = self.obtener_cuenta_mextranejera_cliente(self.partner_id)
			pay_account = self.obtener_cuenta_mextranejera_proveedor(self.partner_id)
			if not rec_account and not pay_account:
				action = self.env.ref('account.action_account_config')
				msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
				raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
			p = self.partner_id
			if p.invoice_warn == 'no-message' and p.parent_id:
				p = p.parent_id
			if p.invoice_warn and p.invoice_warn != 'no-message':
				# Block if partner only has warning but parent company is blocked
				if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
					p = p.parent_id
				warning = {
					'title': _("Warning for %s", p.name),
					'message': p.invoice_warn_msg
				}
				if p.invoice_warn == 'block':
					self.partner_id = False
				return {'warning': warning}

	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		self = self.with_company(self.journal_id.company_id)

		warning = {}
		if self.partner_id:
			rec_account = self.obtener_cuenta_mextranejera_cliente(self.partner_id)
			pay_account = self.obtener_cuenta_mextranejera_proveedor(self.partner_id)
			if not rec_account and not pay_account:
				action = self.env.ref('account.action_account_config')
				msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
				raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
			p = self.partner_id
			if p.invoice_warn == 'no-message' and p.parent_id:
				p = p.parent_id
			if p.invoice_warn and p.invoice_warn != 'no-message':
				# Block if partner only has warning but parent company is blocked
				if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
					p = p.parent_id
				warning = {
					'title': _("Warning for %s", p.name),
					'message': p.invoice_warn_msg
				}
				if p.invoice_warn == 'block':
					self.partner_id = False
				return {'warning': warning}


	def _recompute_payment_terms_lines(self):
		''' Compute the dynamic payment term lines of the journal entry.'''
		self.ensure_one()
		self = self.with_company(self.company_id)
		in_draft_mode = self != self._origin
		today = fields.Date.context_today(self)
		self = self.with_company(self.journal_id.company_id)

		def _get_payment_terms_computation_date(self):
			''' Get the date from invoice that will be used to compute the payment terms.
			:param self:    The current account.move record.
			:return:        A datetime.date object.
			'''
			if self.invoice_payment_term_id:
				return self.invoice_date or today
			else:
				return self.invoice_date_due or self.invoice_date or today

		def _get_payment_terms_account(self, payment_terms_lines):
			''' Get the account from invoice that will be set as receivable / payable account.
			:param self:                    The current account.move record.
			:param payment_terms_lines:     The current payment terms lines.
			:return:                        An account.account record.
			'''
			if payment_terms_lines:
				# Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
				return payment_terms_lines[0].account_id
			elif self.partner_id:
				# Retrieve account from partner.
				if self.is_sale_document(include_receipts=True):
					return self.obtener_cuenta_mextranejera_cliente(self.partner_id)
				else:
					return self.obtener_cuenta_mextranejera_proveedor(self.partner_id)
			else:
				# Search new account.
				domain = [
					('company_id', '=', self.company_id.id),
					('account_type', '=', 'liability_payable' if self.move_type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
				]
				return self.env['account.account'].search(domain, limit=1)

		def _compute_payment_terms(self, date, total_balance, total_amount_currency):
			''' Compute the payment terms.
			:param self:                    The current account.move record.
			:param date:                    The date computed by '_get_payment_terms_computation_date'.
			:param total_balance:           The invoice's total in company's currency.
			:param total_amount_currency:   The invoice's total in invoice's currency.
			:return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
			'''
			if self.invoice_payment_term_id:
				to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date, currency=self.company_id.currency_id)
				if self.currency_id == self.company_id.currency_id:
					# Single-currency.
					return [(b[0], b[1], b[1]) for b in to_compute]
				else:
					# Multi-currencies.
					to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date, currency=self.currency_id)
					return [(b[0], b[1], ac[1]) for b, ac in zip(to_compute, to_compute_currency)]
			else:
				return [(fields.Date.to_string(date), total_balance, total_amount_currency)]

		def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):
			''' Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
			:param self:                    The current account.move record.
			:param existing_terms_lines:    The current payment terms lines.
			:param account:                 The account.account record returned by '_get_payment_terms_account'.
			:param to_compute:              The list returned by '_compute_payment_terms'.
			'''
			# As we try to update existing lines, sort them by due date.
			existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
			existing_terms_lines_index = 0

			# Recompute amls: update existing line or create new one for each payment term.
			new_terms_lines = self.env['account.move.line']
			for date_maturity, balance, amount_currency in to_compute:
				currency = self.journal_id.company_id.currency_id
				if currency and currency.is_zero(balance) and len(to_compute) > 1:
					continue

				if existing_terms_lines_index < len(existing_terms_lines):
					# Update existing line.
					candidate = existing_terms_lines[existing_terms_lines_index]
					existing_terms_lines_index += 1
					candidate.update({
						'date_maturity': date_maturity,
						'amount_currency': -amount_currency,
						'debit': balance < 0.0 and -balance or 0.0,
						'credit': balance > 0.0 and balance or 0.0,
					})
				else:
					# Create new line.
					create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
					candidate = create_method({
						'name': self.payment_reference or '',
						'debit': balance < 0.0 and -balance or 0.0,
						'credit': balance > 0.0 and balance or 0.0,
						'quantity': 1.0,
						'amount_currency': -amount_currency,
						'date_maturity': date_maturity,
						'move_id': self.id,
						'currency_id': self.currency_id.id,
						'account_id': account.id,
						'partner_id': self.commercial_partner_id.id,
						'exclude_from_invoice_tab': True,
					})
				new_terms_lines += candidate
				if in_draft_mode:
					candidate.update(candidate._get_fields_onchange_balance(force_computation=True))
			return new_terms_lines

		existing_terms_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
		others_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
		company_currency_id = (self.company_id or self.env.company).currency_id
		total_balance = sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance)))
		total_amount_currency = sum(others_lines.mapped('amount_currency'))

		if not others_lines:
			self.line_ids -= existing_terms_lines
			return

		computation_date = _get_payment_terms_computation_date(self)
		account = _get_payment_terms_account(self, existing_terms_lines)
		to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
		new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

		# Remove old terms lines that are no longer needed.
		self.line_ids -= existing_terms_lines - new_terms_lines

		if new_terms_lines:
			self.payment_reference = new_terms_lines[-1].name or ''
			self.invoice_date_due = new_terms_lines[-1].date_maturity


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	def ejecutar_moneda_base(self, term_lines):
		moves = term_lines.move_id
		self.env.cr.execute("""
			WITH previous AS (
				SELECT DISTINCT ON (line.move_id)
					   'account.move' AS model,
					   line.move_id AS id,
					   NULL AS account_type,
					   line.account_id AS account_id
				  FROM account_move_line line
				 WHERE line.move_id = ANY(%(move_ids)s)
				   AND line.display_type = 'payment_term'
				   AND line.id != ANY(%(current_ids)s)
			),
			properties AS(
				SELECT DISTINCT ON (property.company_id, property.name)
					   'res.partner' AS model,
					   SPLIT_PART(property.res_id, ',', 2)::integer AS id,
					   CASE
						   WHEN property.name = 'property_account_receivable_id' THEN 'asset_receivable'
						   ELSE 'liability_payable'
					   END AS account_type,
					   SPLIT_PART(property.value_reference, ',', 2)::integer AS account_id
				  FROM ir_property property
				  JOIN res_company company ON property.company_id = company.id
				 WHERE property.name IN ('property_account_receivable_id', 'property_account_payable_id')
				   AND property.company_id = ANY(%(company_ids)s)
				   AND property.res_id = ANY(%(partners)s)
			  ORDER BY property.company_id, property.name, account_id
			),
			default_properties AS(
				SELECT DISTINCT ON (property.company_id, property.name)
					   'res.partner' AS model,
					   company.partner_id AS id,
					   CASE
						   WHEN property.name = 'property_account_receivable_id' THEN 'asset_receivable'
						   ELSE 'liability_payable'
					   END AS account_type,
					   SPLIT_PART(property.value_reference, ',', 2)::integer AS account_id
				  FROM ir_property property
				  JOIN res_company company ON property.company_id = company.id
				 WHERE property.name IN ('property_account_receivable_id', 'property_account_payable_id')
				   AND property.company_id = ANY(%(company_ids)s)
				   AND property.res_id IS NULL
			  ORDER BY property.company_id, property.name, account_id
			),
			fallback AS (
				SELECT DISTINCT ON (account.company_id, account.account_type)
					   'res.company' AS model,
					   account.company_id AS id,
					   account.account_type AS account_type,
					   account.id AS account_id
				  FROM account_account account
				 WHERE account.company_id = ANY(%(company_ids)s)
				   AND account.account_type IN ('asset_receivable', 'liability_payable')
			)
			SELECT * FROM previous
			UNION ALL
			SELECT * FROM properties
			UNION ALL
			SELECT * FROM default_properties
			UNION ALL
			SELECT * FROM fallback
		""", {
			'company_ids': moves.company_id.ids,
			'move_ids': moves.ids,
			'partners': [f'res.partner,{pid}' for pid in moves.commercial_partner_id.ids],
			'current_ids': term_lines.ids
		})
		accounts = {
			(model, id, account_type): account_id
			for model, id, account_type, account_id in self.env.cr.fetchall()
		}
		return accounts

	def ejecutar_moneda_extranjera(self, term_lines):
		moves = term_lines.move_id
		self.env.cr.execute("""
			WITH previous AS (
				SELECT DISTINCT ON (line.move_id)
					   'account.move' AS model,
					   line.move_id AS id,
					   NULL AS account_type,
					   line.account_id AS account_id
				  FROM account_move_line line
				 WHERE line.move_id = ANY(%(move_ids)s)
				   AND line.display_type = 'payment_term'
				   AND line.id != ANY(%(current_ids)s)
			),
			properties AS(
				SELECT DISTINCT ON (property.company_id, property.name)
					   'res.partner' AS model,
					   SPLIT_PART(property.res_id, ',', 2)::integer AS id,
					   CASE
						   WHEN property.name = 'property_account_receivable_2_id' THEN 'asset_receivable'
						   ELSE 'liability_payable'
					   END AS account_type,
					   SPLIT_PART(property.value_reference, ',', 2)::integer AS account_id
				  FROM ir_property property
				  JOIN res_company company ON property.company_id = company.id
				 WHERE property.name IN ('property_account_receivable_2_id', 'property_account_payable_2_id')
				   AND property.company_id = ANY(%(company_ids)s)
				   AND property.res_id = ANY(%(partners)s)
			  ORDER BY property.company_id, property.name, account_id
			),
			default_properties AS(
				SELECT DISTINCT ON (property.company_id, property.name)
					   'res.partner' AS model,
					   company.partner_id AS id,
					   CASE
						   WHEN property.name = 'property_account_receivable_2_id' THEN 'asset_receivable'
						   ELSE 'liability_payable'
					   END AS account_type,
					   SPLIT_PART(property.value_reference, ',', 2)::integer AS account_id
				  FROM ir_property property
				  JOIN res_company company ON property.company_id = company.id
				 WHERE property.name IN ('property_account_receivable_2_id', 'property_account_payable_2_id')
				   AND property.company_id = ANY(%(company_ids)s)
				   AND property.res_id IS NULL
			  ORDER BY property.company_id, property.name, account_id
			),
			fallback AS (
				SELECT DISTINCT ON (account.company_id, account.account_type)
					   'res.company' AS model,
					   account.company_id AS id,
					   account.account_type AS account_type,
					   account.id AS account_id
				  FROM account_account account
				 WHERE account.company_id = ANY(%(company_ids)s)
				   AND account.account_type IN ('asset_receivable', 'liability_payable')
			)
			SELECT * FROM previous
			UNION ALL
			SELECT * FROM properties
			UNION ALL
			SELECT * FROM default_properties
			UNION ALL
			SELECT * FROM fallback
		""", {
			'company_ids': moves.company_id.ids,
			'move_ids': moves.ids,
			'partners': [f'res.partner,{pid}' for pid in moves.commercial_partner_id.ids],
			'current_ids': term_lines.ids
		})
		accounts = {
			(model, id, account_type): account_id
			for model, id, account_type, account_id in self.env.cr.fetchall()
		}
		return accounts

	@api.depends('display_type', 'company_id')
	def _compute_account_id(self):
		term_lines = self.filtered(lambda line: line.display_type == 'payment_term')
		if term_lines:
			accounts_normal = self.ejecutar_moneda_base(term_lines)
			accounts = self.ejecutar_moneda_extranjera(term_lines)
			for line in term_lines:
				account_type = 'asset_receivable' if line.move_id.is_sale_document(include_receipts=True) else 'liability_payable'
				move = line.move_id
				account_id = (
					accounts.get(('account.move', move.id, None))
					or accounts.get(('res.partner', move.commercial_partner_id.id, account_type))
					or accounts.get(('res.partner', move.company_id.partner_id.id, account_type))
					or accounts.get(('res.company', move.company_id.id, account_type))
				)
				if line.move_id.fiscal_position_id:
					account_id = self.move_id.fiscal_position_id.map_account(self.env['account.account'].browse(account_id))
				line.account_id = account_id

		product_lines = self.filtered(lambda line: line.display_type == 'product' and line.move_id.is_invoice(True))
		for line in product_lines:
			if line.partner_id  and not line.product_id and line.partner_id.forzar_cuenta_extranjera:
				if line.move_id.is_sale_document(include_receipts=True):
					if line.currency_id.id != line.company_id.currency_id.id:
						line.account_id = line.partner_id.property_account_receivable_2_id
					else:
						line.account_id = line.partner_id.property_account_receivable_id
				elif line.move_id.is_purchase_document(include_receipts=True):
					if line.currency_id.id != line.company_id.currency_id.id:
						line.account_id = line.partner_id.property_account_payable_2_id.id
					else:
						line.account_id = line.partner_id.property_account_payable_id

			elif line.product_id:
				fiscal_position = line.move_id.fiscal_position_id
				accounts = line.with_company(line.company_id).product_id\
					.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
				if line.move_id.is_sale_document(include_receipts=True):
					line.account_id = accounts['income'] or line.account_id
				elif line.move_id.is_purchase_document(include_receipts=True):
					line.account_id = accounts['expense'] or line.account_id
			elif line.partner_id:
				line.account_id = self.env['account.account']._get_most_frequent_account_for_partner(
					company_id=line.company_id.id,
					partner_id=line.partner_id.id,
					move_type=line.move_id.move_type,
				)
		for line in self:
			if not line.account_id and line.display_type not in ('line_section', 'line_note'):
				previous_two_accounts = line.move_id.line_ids.filtered(
					lambda l: l.account_id and l.display_type == line.display_type
				)[-2:].account_id
				if len(previous_two_accounts) == 1:
					line.account_id = previous_two_accounts
				else:
					line.account_id = line.move_id.journal_id.default_account_id