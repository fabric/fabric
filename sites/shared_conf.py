import types
from os.path import join
from datetime import datetime

import alabaster


# Alabaster theme + mini-extension
html_theme_path = [alabaster.get_path()]
extensions = ['alabaster']
# Paths relative to invoking conf.py - not this shared file
html_static_path = [join('..', '_shared_static')]
html_theme = 'alabaster'
html_theme_options = {
    'logo': 'logo.png',
    'logo_name': True,
    'logo_text_align': 'center',
    'description': "Pythonic remote execution",
    'github_user': 'fabric',
    'github_repo': 'fabric',
    'travis_button': True,
    'analytics_id': 'UA-18486793-1',

    'link': '#3782BE',
    'link_hover': '#3782BE',
}
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'searchbox.html',
        'donate.html',
    ]
}

# Regular settings
project = 'Fabric'
year = datetime.now().year
copyright = '%d Jeff Forcier' % year
master_doc = 'index'
templates_path = ['_templates']
exclude_trees = ['_build']
source_suffix = '.rst'
default_role = 'obj'



# Restore decorated functions so that autodoc inspects the right arguments
def unwrap_decorated_functions():
    from fabric import operations, context_managers
    for module in [context_managers, operations]:
        for name, obj in vars(module).iteritems():
            if (
                # Only function objects - just in case some real object showed
                # up that had .undecorated
                isinstance(obj, types.FunctionType)
                # Has our .undecorated 'cache' of the real object
                and hasattr(obj, 'undecorated')
            ):
                setattr(module, name, obj.undecorated)

unwrap_decorated_functions()
