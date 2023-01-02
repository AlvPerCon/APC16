# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "Perú - 2Cuenta Contacto",

	'summary': """
		2Cuenta Contacto""",

	'description': """
		* Agrega un nuevo campo en el cliente para los movimientos en moneda extranjera en una cuenta contable diferente a la cuenta por defecto.
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.1',
	'license': 'Other proprietary',
	'depends': [
		'account',
		'solse_pe_edi',
	],
	'data': [
		'views/res_partner_view.xml',
	],
	'installable': True,
	'price': 30,
	'currency': 'USD',
}