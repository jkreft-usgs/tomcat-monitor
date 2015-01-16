'''
This script creates a wrapper to simplify the inclusion of these scripts
into a Jenkins job.
'''
import sys
import subprocess
import os, os.path
from tomcat_monitor import list_processes


usage = '''
This script takes the following REQUIRED arguments:
    - a server_specification, being an alias from the following: 
        'wqpdev',
        'wqpqa',
        'wqpprod',
        'wqpnwisprod',
        'wqpstoretprod'
    - an operation, being an alias from the following:
        'memory_usage',
        'reload'
    - a tomcat-script username
    - a tomcat-script password
and the following OPTIONAL argument:
    - a warning_critical reset to override the characteristic 80,90 warning
        and critical thresholds respectively
'''

# return status values
status = {}
status['ok'] = 0
status['warning'] = 1
status['critical'] = 2
status['unknown'] = 3

servers = (
    'wqpdev',
    'wqpqa',
    'wqpprod',
    'wqpnwisprod',
    'wqpstoretprod'
)

operations = (
    'memory_usage',
    'reload'
)

# sanity checks
if len(sys.argv) < 5 or len(sys.argv) > 6:
    print usage
    exit(status['unknown'])

if sys.argv[1] not in servers:
    print('"' + sys.argv[1] + '" is not a valid server alias.')
    exit(status['unknown'])

if sys.argv[2] not in operations:
    print('"' + sys.argv[2] + '" is not a valid operation alias. Must be one of (' + ','.join(operations) + ').')
    exit(status['unknown'])
    
warning = 0
critical = 0
if len(sys.argv) == 6:
    # there's a warning_critical threshold
    thresholds = sys.argv[5].split(',')
    if len(thresholds) != 2:
        print('"' + sys.argv[5] + '" is not a valid warning_threshold pair.')
        exit(status['unknown'])
    try:
        warning = int(thresholds[0])
        critical = int(thresholds[1])
    except:
        print('invalid format in warning_threshold')
        exit(status['unknown'])
        
    if warning < 1 or critical > 100 or warning > critical:
        print('warning_critical number values (' + str(warning) + ',' + str(critical) + ') are wrong.')
    
# rename/refactor parameters for clarity
server_url = 'http://cida-eros-' + sys.argv[1] + ':8080'
operation = sys.argv[2]
username = sys.argv[3]
password = sys.argv[4]

if operation == 'memory_usage':
    print('checking memory usage for "' + server_url + '":')
    try:
        script = os.path.join(os.getcwd(), 'tomcat_memory_usage.py')
        params = ['python', script, server_url, username, password]
        print(params)
        if warning and critical:
            params.append(str(warning))
            params.append(str(critical))
        print('calling: ' + str(params))
        exit_status = subprocess.call(params)
        print('exiting with status: ' + str(exit_status))
        exit(exit_status)
    except Exception as ex:
        print(str(ex))
        exit(status['unknown'])
        

elif operation == 'reload':
    print('reloading processes on "' + server_url + '".')
    text_url = os.path.join(server_url, 'manager/text')
    print('text_url = "' + text_url + '"')
    processes = list_processes(text_url, username, password)
    print('running: ' + str(processes))
    # convert unicode keys to list of strings
    contexts = [str(keyname) for keyname in processes if processes[keyname]['running']]
    # the usual suspects are the ones that might need reloading
    usual_suspects = [
        '/storetqw-codes', 
        '/stewardsqw', 
        '/wqp-aggregator', 
        '/storetqw', 
        '/nwisqw', 
        '/nwisqw-codes']
    contexts_to_reload = [context for context in contexts if context in usual_suspects]
    print('RELOADING THESE:')
    context_string = ','.join(contexts_to_reload)
    print(context_string)
    script = os.path.join(os.getcwd(), 'reload-tomcat.py')
    params = ['python', script, server_url, context_string, username, password]
    try:
        print('calling: ' + str(params))
        exit_status = subprocess.call(params)
    except Exception as ex:
        print(ex)
        exit(status['unknown'])
        
        
    



