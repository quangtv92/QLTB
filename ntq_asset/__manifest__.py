# -*- coding: utf-8 -*-
##############################################################################
#
#    @package ntq_asset NTQ Asset for Odoo 9.0
#    @copyright Copyright (C) 2016 NTQ Solution (aka NTQ). All rights reserved.#
#    @license http://www.gnu.org/licenses GNU Affero General Public License version 3 or later; see LICENSE.txt
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name' : 'NTQ Asset Management',
    'version': '1.0',
    'author' : 'NTQ Solutions',
    'summary': 'NTQ Asset Management',
    'website': 'http://www.ntq-solution.com.vn/',
    'sequence': 12,
    'category': 'Asset Management',
    'description':"""
NTQ asset Management
===========================

    """,
    # 'depends': ['hr', 'purchase', 'ntq_project', 'account_asset'],
    'depends': ['hr', 'purchase', 'project', 'account_asset'],
    'data': [
        'data/module_data.xml',
        'data/asset_sequence.xml',
        'data/report_data.xml',
        'security/asset_security.xml',
        'security/ir.model.access.csv',
        'wizard/asset_wizard_view.xml',
        'wizard/asset_distribution_wizard_view.xml',
        'wizard/asset_transfer_wizard_view.xml',
        'views/main_menu_view.xml',
        'views/asset_category_view.xml',
        'views/asset_group_view.xml',
        'views/product_template_view.xml',
        'views/asset_view.xml',
        'views/res_config_view.xml',
        'views/asset_distribution_new_view.xml',
        'views/asset_distribution_borrow_view.xml',
        'views/asset_distribution_line_new_view.xml',
        'views/asset_distribution_line_borrow_view.xml',
        'views/asset_transfer_new_view.xml',
        'views/asset_transfer_borrow_view.xml',
        'views/asset_transfer_collect_new_view.xml',
        'views/asset_transfer_collect_borrow_view.xml',
        'views//asset_report.xml',
        'reports/templates/report_company_info.xml',
        'reports/templates/report_asset_transfer.xml',
    ],
    'installable': True,
    'application': True,
}
