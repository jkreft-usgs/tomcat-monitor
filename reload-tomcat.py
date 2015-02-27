import requests
import sys

usage = '''
This plugin requires the following parameters:
server (e.g. "big.old.server.some.org")
port (e.g. "8080")
tomcat_manager_text_username
password
warning_crit_threshold (should be "none")
context_to_reload (the context path or paths to reload;
    - this parameter contains NO spaces
    - multiple values are comma-separated
    - each path must begin with "/"
    - each path must correspond to a valid context path for the Tomcat instance.)

'''


# return status values
status = {}
status['ok'] = 0
status['warning'] = 1
status['critical'] = 2
status['unknown'] = 3


# resolve params
if len(sys.argv) != 7:
    print(usage)
    exit(status['unknown'])
    
server_url = 'http://' + sys.argv[1] + ':' + sys.argv[2]
text_url = server_url + '/manager/text'
reload_url = text_url + '/reload'
username = sys.argv[3]
password = sys.argv[4]
contexts = sys.argv[6].split(',')

print('Reloading ' + server_url + ' contexts ' + str(contexts) + '.')

#safety and sanity
if '/manager' in contexts:
    print('INVALID: this process will not shut down the Tomcat Manager.')
    exit(status['unknown'])
elif '/probe' in contexts:
    print('INVALID: this process will not interfere with PSI Probe.')
    exit(status['unknown'])
    

for context in contexts:
    action_url = reload_url + '?path=' + context
    print('executing: "' + action_url + '":')
    try:
        resp = requests.get(action_url, auth=(username, password))
        resp.raise_for_status()
    except Exception as ex:
        print(str(ex) + ' occurred while attempting to reload "' + context + '".')
        exit(status['unknown'])
