## Catalog Project

This repo contains a vagrant file and python web application that manages a fake portfolio of stocks.

Executing `catalog/application.py` will serve a web server that can be viewed at http://localhost:5000/

### Requires

VirtualBox https://www.virtualbox.org/wiki/Downloads
Vagrant https://www.vagrantup.com/downloads.html

### To Run

1. Navigate to the folder with the Vagrantfile in it
2. run `vagrant up`
3. run `vagrant ssh`
4. navigate to shared folder with `cd /vagrant`
5. navigate to logs folder with `cd catalog`
6. execute program with `python application.py`
7. Open http://localhost:5000/ in a Web Browser