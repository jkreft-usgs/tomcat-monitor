import sys
from urlparse import urljoin

usage = '''This script takes three parameters:
    - server, which is the entire server hostname including port numbers as necessary
    - username, which is the user account privileged to access Tomcat MAnager text and status
    - password for that account.

    See conf/tomcat-users.xml on the target server; the role should be "manager-script".
'''

if len(sys.argv) < 4:
    return usage

server = sys.argv[1]
username = sys.argv[2]
password = sys.argv[3]

manager_url = urlparse.urljoin(server, '/manager')
print('Tomcat Manager base url: ' + manager_url)
text_url = manager_url + '/text'
print('Tomcat Manager Text interface base URL: ' + text_url)
status_url = manager_url + '/status'
print('Tomcat Manager Status Page URL: ' + status_url)

server_info(password, username, text_url)
jndi_resources(password, username, text_url)
list_processes(password, username, text_url)

#server_status(password, username, status_url)
