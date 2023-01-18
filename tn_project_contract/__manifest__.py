# -*- coding: utf-8 -*-
{
    'name': "Project Contract",  
    'summary': "Manage Project Contract",  
    'description': """
Project Contract
==============
    """,  
    'author': 'Sary Babiker',
    'email': 'sarybabiker7@gmail.com',
    'category': 'Project Contract',
    'sequence': 44,
    'version': '1.2',
    'depends': ['account', 'custom_project_manager'],
    'data': [
        'security/ir.model.access.csv',
        'data/project_contract_sequence.xml',
        'views/project_contract_views.xml',
        'views/res_config_settings_views.xml',    ],

    'installable': True,
    'auto_install': False,
    'application': True,
    
}
