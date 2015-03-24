from setuptools import setup, find_packages

setup(
    name = 'lantern',
    version = '1.0.0',
    packages = find_packages(),
    install_requires = [
        "octopus==1.0.0",
        "esprit",
        "Flask==0.9",
        "WTForms==2.0.1",
        "flask_mail==0.9.1",
        "newrelic==2.42.0.35",
        "gunicorn==19.1.1"
    ],
    url = 'https://github.com/CottageLabs/lantern',
    author = 'Cottage Labs LLP',
    author_email = 'us@cottagelabs.com',
    description = 'Lantern: Open Access Compliance',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: Apache2',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
