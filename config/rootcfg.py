# absolute paths, or relative paths from root directory, to the desired config files (in the order you want them loaded)
CONFIG_FILES = [
    "portentious/portality/config/webapp.py",
    "config/dev.py"
]

# absolute paths, or relative paths from root directory, to the template directories (in the order you want them looked at)
TEMPLATE_PATHS = [
    "app/templates",
    "portentious/portality/templates"
]

# absolute paths, or relative paths from the root directory, to the static file directories (in the order you want them looked at)
STATIC_PATHS = [
    "app/static",
    "portentious/portality/static"
]