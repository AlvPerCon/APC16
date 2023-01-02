# -*- coding: utf-8 -*-
# Copyright (c) 2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
{
	'name': "Journal Users",

	'summary': """
		Journal Users
		""",

	'description': """
		Journal Users
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",

	'category': 'Uncategorized',
	'version': '15.0.1',
	'depends': ['base', 'sale_management'],
	'data': [
		'security/security.xml',
		'views/account_view.xml',
	],
	'demo': [],
	'installable': True,
	'auto_install': False,
	'application': True,
	"sequence": 1,
}