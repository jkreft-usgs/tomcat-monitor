from tomcat_monitor import server_status
import sys

usage = '''
This plugin requires the following parameters:
server (including protocol and port, e.g. "http://big.old.server.org:8080")
tomcat_manager_status_username
password
(optional: both required if either is present; these are percentages)
warning (must be a number > 0) (default 80)
critical (must be a number > warning and < 100) (default 90)
'''

# return status values
status = {}
status['ok'] = 0
status['warning'] = 1
status['critical'] = 2
status['unknown'] = 3

# alert percentages with prepopulated defaults (if these are changed,
# modify usage message to reflect that)
alert_levels = {}
alert_levels['warning'] = 80
alert_levels['critical'] = 90

# resolve params
if len(sys.argv) < 3:
    print(usage)
    exit(status['unknown'])

server_url = sys.argv[1]
status_url = server_url + '/manager/status/'
username = sys.argv[2]
password = sys.argv[3]

if len(sys.argv) == 6:
    # warning and critical values
    try:
        warning = int(sys.argv[4])
        critical = int(sys.argv[5])
    except Exception as ex:
        print('improper warning and/or critical alert values: ' + str(ex))
        exit(status['unknown'])
    if warning < 0 or critical < 0:
        print('warning and critical percentages must be positive. Passed: ' + str(warning) + ', ' + str(critical))
        exit(status['unknown'])
    if warning >= critical:
        print('warning value (passed as ' + str(warning) + ') must be less than critical value (passed as ' + str(critical) + ').')
        exit(status['unknown'])

    # looks like these values are all right
    alert_levels['warning'] = warning
    alert_levels['critical'] = critical
        
if len(sys.argv) == 5 or len(sys.argv) > 6:
    print(usage)
    exit(status['unknown'])

status_tables = {}
try:
    status_tables = server_status(status_url, username, password)
except Exception as ex:
    # any exception constitutes an UNKNOWN condition
    print(str(ex) + ' occurred while attempting to obtain status information from Tomcat Manager.')
    exit(status['unknown'])

if 'JVM' not in status_tables:
    print('Unable to extract JVM info from Tomcat Manager status page.')
    exit(status['unknown'])

memory_table = status_tables['JVM']
# basic sanity check
for row in memory_table:
    if len(row) != 6:
        print('Malformed table row: ' + str(row))
        exit(status['unknown'])

#CMS Old Gen
#Par Eden Space
#Par Survivor Space
#CMS Perm Gen
#Code Cache

pool_percentages = {}

# skip headers, read data rows
worst = 'ok'
for row in memory_table[1:]:
    memory_pool = row[0]
    pool_percentages[memory_pool] = []
    percent = row[5] 
    percent = percent.split('(')
    percent = percent[1].split('%')
    percent = percent[0]
    try:
        percent = int(percent)
        pool_percentages[memory_pool].append(percent)
        if percent >= alert_levels['critical']:
            pool_percentages[memory_pool].append('critical')
            if worst in ('ok', 'warning'):
                worst = 'critical'
        elif percent >= alert_levels['warning']:
            pool_percentages[memory_pool].append('warning')
            if worst == 'ok':
                worst = 'warning'
        else:
            pool_percentages[memory_pool].append('ok')
    except Exception as ex:
        print('Unable to determine ' + memory_pool + ' memory percentage: ' + str(ex))
        exit(status['unknown'])

print(str(pool_percentages))

print('worst: ' + worst)

exit(status[worst])
