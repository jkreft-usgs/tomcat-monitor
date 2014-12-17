import sys
import urlparse
from tomcat_monitor import list_processes, server_info, jndi_resources, server_status

usage = '''This script takes three parameters:
    - server, which is the entire server URL beginning with "http://" 
        and including port number as necessary
    - username, which is the user account privileged to access Tomcat MAnager text and status
    - password for that account.

    See conf/tomcat-users.xml on the target server; the role should be "manager-script".
'''

if len(sys.argv) < 4:
    print('Only ' + str(len(sys.argv)) + ' parameters passed.')
    print(usage)

server = sys.argv[1]
username = sys.argv[2]
password = sys.argv[3]

manager_url = urlparse.urljoin(server, '/manager')
print('Tomcat Manager base url: ' + manager_url)
text_url = manager_url + '/text'
print('Tomcat Manager Text interface base URL: ' + text_url)
status_url = manager_url + '/status'
print('Tomcat Manager Status Page URL: ' + status_url)

print
#print(server_info(text_url, username, password))
#print(jndi_resources(text_url, username, password))

#proc_dict = list_processes(text_url, username, password)
#for context in sorted(proc_dict):
    #print(context)
    #for keyname in ['running', 'session_count']:
        #print('\t' + keyname + ': ' + str(proc_dict[context][keyname]))
    
print
headertables = server_status(status_url, username, password)
print(headertables)
