from setuptools import setup

APP = ['openscad_version_control.py']
OPTIONS = {
    'argv_emulation': False,  # Disable argv_emulation to allow file arguments
    'packages': ['tkinter', 'git'],
    'plist': {
        'CFBundleName': 'openscad_version_control',
        'CFBundleIdentifier': 'com.yourcompany.openscadversioncontrol',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'OpenSCAD File',
                'CFBundleTypeRole': 'Editor',
                'LSItemContentTypes': ['public.text'],
            }
        ],
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
