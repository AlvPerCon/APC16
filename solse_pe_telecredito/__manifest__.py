# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': 'Perú - Telecrédito',
	'version': '16.0.0.1',
	'license': 'Other proprietary',
	'category': 'Financial',
	'summary': 'Perú - Telecrédito',
	'depends': [
		'account',
		'solse_pe_edi',
		'solse_pe_cpe',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/telecredito_view.xml',
		'views/res_partner_view.xml',
		'wizard/pago_telecredito_view.xml',
	],
	'external_dependencies': {
		'python': [
			'pandas',
			'xlsxwriter',
		],
	},
	'auto_install': False,
	'installable': True,
	'application': True,
	'sequence': 1,
}
