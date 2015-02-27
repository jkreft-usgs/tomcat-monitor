#from tomcat_monitor import server_status
import sys

#==================== Rude HACK to get everything working (copied necessary
#                       stuff from "tomcat_monitor.py" to avoid issues of import
#                       in nagios context)

def find_named_sibling(tag, desired_name, how_many_tries=5):
    '''
    Convenience method. Given a BeautifulSoup tag, finds the first occurrence
    of the desired_name in a sibling tag. Will look for up to how_many_tries.
    '''
    sib = tag
    for indx in range(how_many_tries):
        if sib.next_sibling:
            sib = sib.next_sibling
            if sib.name == desired_name:
                return sib
        else:
            # print('Out of siblings at ' + str(indx) + '. wtf.')
            return None

def scrape_table_rows(tbl, filt=None):
    '''
    Walks through the rows of an HTML table. If a given row is not eliminated
    by filter function 'filt', the row is converted into a list of string
    values of the th or td tags in the row.

    The 'filt' function must return True if the row is desired, else False.
    '''
    retrows = []
    rows = tbl.find_all('tr')
    if filt:
        rows = [row for row in rows if filt(row)]
    for row in rows:
        retrows.append([str(cell.string) for cell in row.find_all(['td', 'th'])])
    return retrows

def skip_ready_threads(row):
    '''
    Filter method: returns True IFF the parameter has a first cell that does
    not contain the string value "R". Intended to eliminate thread table
    rows that are in "Ready" state (i.e., not working.)
    :param row: A beautiful soup tag for an HTML row
    :returns: False if the parameter is None, has no first cell, or has a 
        first cell with string value "R"; else True
    '''
    if row:
        firstcell = row.find(['th', 'td'])
        if firstcell:
            firstcontent = firstcell.string
            return firstcontent != 'R'
        else:
            return False
    else:
        return False



import requests
from bs4 import BeautifulSoup

def server_status(status_url, username, password):
    resp = requests.get(status_url, auth=(username, password))
    # raise an Exception if HTTP status code indicates error (4xx or 5xx)
    resp.raise_for_status()

    #scrape the HTML
    soup = BeautifulSoup(resp.text)

    # html headers are defined as header name (page content) and filter (function)
    header_defs = {'JVM': None, '"http-bio-8080"': skip_ready_threads}

    hdrs = soup.find_all('h1')
    headertables = {}
    for hdr in hdrs:
        headername = str(hdr.string)
        if headername in header_defs:
            tbl = find_named_sibling(hdr, 'table')
            if tbl:
                rows = scrape_table_rows(tbl, filt=header_defs[headername])
                headertables[headername] = rows
    return headertables

def warn_crit(warncrit):
    '''This function expects an integer pair string "w,c" such that 0 < w < c < 100.
    If the w and c values are valid, they will be returned as the integer tuple (w,c).
    If the values of w and c are invalid, it will raise a ValueError
    If it's not a string containing a single comma, it is treated as a 
    non-parameter and the returned val is None.
    '''
    retval = None
    if warncrit:
        warncrit = warncrit.split(',')
        if len(warncrit) == 2:
            retval = (int(warncrit[0]), int(warncrit[1]))
            if warncrit[0] <= 0 or warncrit[1] < 0:
                errmsg = 'warning and critical percentages must be positive. Passed: ' 
                errmsg += '(' + str(warncrit[0]) + ', ' + str(warncrit[1]) + ')'
                raise ValueError(errmsg)
            if warncrit[0] >= warncrit[1]:
                errmsg = 'warning value (passed as ' + str(warncrit[0]) 
                errmsg += ') must be less than critical value (passed as '  
                errmsg +=  str(warncrit[1]) + ').'
                raise ValueError(errmsg)
    return retval

#======================== end of rude HACK


usage = '''
This plugin requires the following parameters:
 - hostname (e.g. "big.old.server.some.rg")
 - port (e.g. "8080")
 - tomcat_manager_status_username
 - password
 - warning_crit_threshold (must be form 'w,c'; integer vae,ues 0 < w < c < 100, else Python False, None, empty, etc)
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
if len(sys.argv) < 5:
    print(usage)
    exit(status['unknown'])

server_url = 'http://' + sys.argv[1] + ':' + sys.argv[2]
status_url = server_url + '/manager/status/'
username = sys.argv[3]
password = sys.argv[4]

if len(sys.argv) >= 6:
    # warning and critical values
    warncrit = []
    try:
        warncrit = warn_crit(sys.argv[5])
        # if not of the form 'w,c' the returned value will be None
    except Exception as ex:
        # puked on integer parse or manual ValueError condition
        print('improper warning and/or critical alert values: ' + str(ex))
        exit(status['unknown'])
    if warncrit:
        # looks like these override values are all right
        alert_levels['warning'] = warncrit[0]
        alert_levels['critical'] = warncrit[1]
 
        
if len(sys.argv) < 5:
    # not enough args
    print ('arguments: ' + str(sys.argv))
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
        print('Malformed status table row: ' + str(row))
        exit(status['unknown'])

# The JVM memory space is divided up into "pools":
#  - CMS Old Gen
#  - Par Eden Space
#  - Par Survivor Space
#  - CMS Perm Gen
#  - Code Cache

pool_percentages = {}

worst = 'ok'
# skip headers, read data rows
for row in memory_table[1:]:
    # row[x] will be a column.
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

worst_percentage = sorted(pool_percentages.values(), reverse=True)[0]
baddest_pools = []
for pool in pool_percentages:
    if pool_percentages[pool] == worst_percentage:
        baddest_pools.append(pool)

output_msg = 'Check complete. Overall status is ' + worst + '. Max: ' + str(worst_percentage) + ': ' + str(baddest_pools) + '.'
performance_data = str(pool_percentages)

print('|'.join((output_msg, performance_data)))

exit(status[worst])
