# -*- coding: utf-8 -*-
{
    'name': 'ncss_custody_request',
    'version': '15.0.1',
    'summary': 'ncss_custody_request',
    'category': 'ncsscustody_request',
    'author': 'Magdy,TeleNoc',
    'description': """
    custody_request
    """,
    'depends': ['base', 'mail', 'hr', 'account'],
    'data': [
        'security/security.xml',
        #'security/ir.model.access.csv',
        'demo/custody_description.xml',
        'views/custody_sequence.xml',
        'views/custody_request.xml',
        'views/custody_request_setting.xml',
    ]
}
