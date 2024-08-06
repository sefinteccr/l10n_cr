# -*- coding: utf-8 -*-

{
	'name': 'UltraFit',
	'version': '12.0.2.0.0',
	'author': 'Sefinteccr S.A.',
    'license': 'OPL-1',
	'website': 'http://www.sefinteccr.com',
	'category': 'Account',
	'description':
		'''
		Skip MH
		''',
	'depends': ['cr_electronic_invoice','point_of_sale'],
	'data': ['views/res_partner_views.xml','views/pos_templates.xml'],
	'qweb': ['static/src/xml/*.xml'],
	'installable': True,
}