# App Template

Use this to seed new Flask projects

## Creating a new project

Clone the App Template project:

    git clone https://github.com/richard-jones/app-template.git myapp

get all the submodules

    cd myapp
    git submodule init
    git submodule update

This will initialise and clone the esprit and portentious libraries

Then get the submodules for portality

    cd myapp/portentious
    git submodule init
    git submodule update

Create your virtualenv and activate it

    virtualenv /path/to/venv
    source /path/tovenv/bin/activate

Install esprit and portality (in that order)

    cd myapp/esprit
    pip install -e .
    
    cd myapp/portentious
    pip install -e .
    
Create your local config

    cd myapp
    touch local.cfg

Then you can override any config values that you need to

Update setup.py, to include your app's name and description

    vim setup.py

Finally, start your app with

    python service/web.py

If you want to specify your own root config file, you can use

    APP_CONFIG=path/to/rootcfg.py python service/web.py
    
## Portentious

For details about the modules available to you in portentions, see the [README](https://github.com/richard-jones/portentious/blob/master/README.md)
