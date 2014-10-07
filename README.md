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

Change the origin url, so you can push code to your own repo:

    git remote set-url origin <git url of new repo home>
    git push -u origin master

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
    
## Portality

For details about the modules available to you in portality, see the [README](https://github.com/richard-jones/portentious/blob/master/README.md)

If you want to make local modifications to your portality repo, with a view to merging them back into the master at some point in the future, then do the following

    cd myapp/portentious
    git checkout master
    git branch myapp
    cd ..
    git add .
    git commit -m "move my code onto custom portality branch"
    git push origin master

This means you will be able to modify the code locally, and push changes to the branch, without affecting the master.  From time to time you might
want to merge the master with your branch, to keep up to date with the latest changes.  When you want to contribute code to the master, just merge
your branch down to the master and push.