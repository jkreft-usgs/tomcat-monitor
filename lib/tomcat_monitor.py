import requests
from bs4 import BeautifulSoup


def list_processes(text_url, username, password):
    '''
    This function queries the Tomcat Manager for a list of running 
    Tomcat container processes.
    :param:
    :returns: a dict of process information. Keys are the contxt paths; values 
        are also dictionaries with uniform keys 'running'(boolean), 
        'session_count'(int), and 'context_path'(string).
    :raises: 

    '''
    url = text_url + '/list'
    resp = requests.get(url, auth=(username, password))
    resp.raise_for_status()

    # construct dict of dicts
    processes_by_context = {}
    for line in resp.text.split('\n'):
        if line.startswith('/'):
            segments = line.split(':')
            # context path as key
            context = segments[0]
            # dict of segment name/values
            val = {}
            val['running'] = segments[1] and segments[1] == 'running'
            val['session_count'] = int(segments[2])
            val['context_path'] = segments[3]
            # make dict entry
            processes_by_context[context] = val
    return processes_by_context


def server_info(text_url, username, password):
    url = text_url + '/serverinfo'
    resp = requests.get(url, auth=(username, password))
    resp.raise_for_status()
    servinfo = {}
    lines = resp.text.split('\n')
    if lines[0].startswith('OK -'):
        for line in lines[1:]:
            parts = line.split(':')
            # lines without one ':' should be ignored
            if len(parts) > 1:
                if len(parts) > 2:
                    # there was an extra colon in the value. 
                    # Rebuild the value
                    parts = [parts[0], ':'.join(parts[1:])]
                servinfo[parts[0]] = parts[1]
    return servinfo


def jndi_resources(text_url, username, password):
    url = text_url + '/resources'
    resp = requests.get(url, auth=(username, password))
    resp.raise_for_status()
    jndis = resp.text.split('\n')
    if jndis[0].startswith('OK -'):
        if len(jndis) == 1:
            return []
        else:
            return jndis[1:]


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
            print('Out of siblings at ' + str(indx) + '. wtf.')
            return None

def scrape_table_rows(tbl, filt=None):
    '''
    Walks through the rows of a table. If a given row is not eliminated
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


def server_status(status_url, username, password):
    resp = requests.get(status_url, auth=(username, password))
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
