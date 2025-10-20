{
    'name': "Catálogo de bienes y servicios para uso tributario y Cuentas Nacionales",

    'summary': "Catálogo de bienes y servicios para uso tributario y Cuentas Nacionales",
    'author': 'info@fakturacion.com',
    'website': "https://github.com/odoocr/cabys",
    'category': 'Account',
    'version': '12.0.0.0.1',
    'license': 'OPL-1',
    'depends': [
        'base', 'product',
    ],
    'data': [
        'views/cabys_producto_views.xml',
        'views/cabys_forma_farmaceutica_views.xml',
        'views/cabys_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'views/product_category_views.xml',
        'views/assets.xml',
        'views/res_company_views.xml',
        'data/ir_cron_data.xml',
        'data/ir_chanel_data.xml',
        'wizard/cabys_medical_catalog_import_wizard.xml',
        'data/cabys.forma.farmaceutica.csv',
        'security/ir.model.access.csv',
        'views/medical_report_views.xml',

    ],
    'qweb': [
        "static/src/xml/cabys_templates.xml",
    ],
    'installable': True,
}
