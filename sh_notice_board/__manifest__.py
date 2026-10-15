# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "News Snippets",
    "author": "Softhealer Technologies",
    "website": "http://www.softhealer.com",
    "support": "support@softhealer.com",
    "license": "OPL-1",
    "category": "website",
    "summary": """
News Module, Headlines Of New Offers, News Feature, News Snippets,
Quick News Module, notice board,Shows Upcoming  Activities,New Latest Offer,
headlines Module,News Snippets,News Box, News Content Box,
News Snipet
""",
    "description": """
Do you want to update your website users with the latest
news/updates/information/offers? This module will help you to
show the latest news/updates/information/offers on the website.
You will get different styles to show news.
you can easily drag and drop anywhere on any page of your website. 
News Module in Odoo, Headlines Of New Offers Odoo.
News Feature Odoo, News Snippets Odoo, Quick News Module Odoo,
Shows Upcoming  Activities Odoo, Use For New Latest Offers,
Sales Alert, Any New Update Odoo. 
News app, headlines Module,News Snippets,
Latest Offer/Update odoo.
News Box, News Content Box, News Snippet.
""",
    "version": "19.0.0.3",
    "depends": [
        "website",
        # "web_editor",
    ],
    "application": True,
    "data": [
        # "security/notice_board_security.xml",
        "security/ir.model.access.csv",
        "views/notice_board_view.xml",
        "views/snippets/snippets.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "sh_notice_board/static/src/js/snippets.js",
            "sh_notice_board/static/src/scss/snippets.scss",
        ],
        # 'website.assets_editor': [
        #     ('include', 'web._assets_helpers'),
        #     'sh_notice_board/static/src/js/editor.js',
        # ],
        # "web_editor.assets_legacy_wysiwyg": [
        #     "sh_notice_board/static/src/js/editor.js",
        # ],
    },
    "images": [
        "static/description/background.png",
    ],
    "live_test_url": "https://youtu.be/8wMC9UVKcas",
    "auto_install": False,
    "installable": True,
    "price": 35,
    "currency": "EUR",
}
