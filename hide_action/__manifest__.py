# pylint: skip-file
{
    "name": "Hide Action Button",
    "summary": """Hide 'Action' button from tree and form views""",
    "license": "Other OSI approved licence",
    "version": "19.0.1.0.0",
    "category": "Extra Tools",
    "website": "https://www.code137.com.br",
    "contributors": [
        "Felipe Paloschi <paloschi.eca@gmail.com>",
    ],
    "depends": ["web", "xenesis_school_base"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            # 'hide_action/static/src/js/hide_actions.js',
            "hide_action/static/src/js/hide_action_buttons_list_view.js",
            "hide_action/static/src/js/hide_action_buttons_form_view.js",
        ]
    },
    "images": ["static/description/00_action_button.png"],
}
