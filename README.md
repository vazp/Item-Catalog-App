# Item Catalog App
Full Stack Web Developer Nanodegree

This project was made using Python, Flask, SQLAlchemy and Vagrant to run a Linux-based virtual machine configured with all the requirements.
To set up the environment, you can download and install the following software:
 * [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
 * [Vagrant](https://www.vagrantup.com/downloads.html)

The virtual machine configuration file can be found [here](https://github.com/udacity/fullstack-nanodegree-vm)

Once everything is downloaded and installed you can run the command *vagrant up* from the directory where the vagrantfile is located to start the virtual machine, and the command *vagrant ssh* to log in the virtual machine.

You can also manually install [Python 2.7](https://www.python.org/downloads/) and run *pip install -t lib -r requirements.txt*

This project makes use of the Google Sign-In service and to configure it you must:
* Set up a new project at [Google Developers Console](https://console.developers.google.com/)
* Create credentials. A tutorial on how to do this can be found [here](https://developers.google.com/identity/sign-in/web/devconsole-project). In the Authorized JavaScript origins field put the following line *http://localhost:8000*
* Download *client_secret_xxxx.json*, rename it to *client_secrets.json*
* Place *client_secrets.json* at root of this project
* Replace the line on *static/script.js* with your client id from the developer console

To generate the database for the app you can run the following command at the root of this project
```
python db_model.py
```

To run the app you can execute the following command at the root of this project
```
python project.py
```