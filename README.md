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

    virtualenv venv
    source venv/bin/activate

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

    APP_CONFIG=config/rootcfg.py python app/app.py
