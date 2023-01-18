# -*- coding: utf-8 -*-
{
    'name': "Custom Project Manager", 
    'version' : '1.2', 
    'summary': "Customization Project manager",
    'description': """
Project Manager
==============
    """, 
    'author': "Sary Babiker",
    'category': 'Project',
    'depends': ['material_purchase_requisitions', 'purchase','stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/project_manager.xml',
        'views/purchase_requisition_view.xml',
        'views/stock_picking_view.xml',
    ],
}
