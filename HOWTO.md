# Working Nagios-centric parts, and how to use them.

The content of this is intended to support use under [Nagios](http://www.nagios.org/).

## The Parts

# tomcat_manager_venv
This bash script is intended to serve as a virtualenv wrapper that invokes python plugins. It exits with the exit code provided by the plugin.

# tomcat_mem_usage.py
A Python plugin that contacts the Tomcat Manager via HTTP, scrapes the resulting HTML page (looks like the Tomcat Manager team ran out of steam or funding or something before they made aRESTlike interface.)

#restart-tomcat.py
A plugin that reloads a parameterized list of Tomcat context paths. It uses the Tomcat Manager's RESTlike text interface to restart every context in the provided list.
