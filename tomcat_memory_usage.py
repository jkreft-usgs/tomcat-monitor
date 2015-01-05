from tomcat_monitor import server_status

# resolve params


usage = '''
This plugin accepts the following parameters:
server
port
username
password
'''

# return status values
status = {}
status['ok'] = 0
status['warning'] = 1
status['critical'] = 2
status['unknown'] = 3

#CMS Old Gen
#Par Eden Space
#Par Survivor Space
#CMS Perm Gen
#Code Cache

status_tables = {}
try:
    status_tables = server_status(status_url, username, password)
except Exception as ex:
    # any exception constitutes an UNKNOWN condition
    print(str(type(ex)) + ' occurred while attempting to obtain status information from Tomcat Manager.')
    exit(status['unknown'])

if 'JVM' not in status_tables:
    print('Unable to extract JVM info from Tomcat Manager status page.')
    exit(status['unknown'])


