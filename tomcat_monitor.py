import requests
from bs4 import BeautifulSoup



def list_processes(password, username, text_url):
    '''
    This function queries the Tomcat Manager for a list of running 
    Tomcat container processes.
    returns: a dict whose keys are the contxt paths and whose values are 
        "running", "session_count", and "display_name"
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


def server_info(password, username, text_url):
    url = text_url + '/serverinfo'
    resp = requests.get(url, auth=(username, password))
    resp.raise_for_status()
    return resp.text


def jndi_resources(password, username, text_url):
    url = text_url + '/resources'
    resp = requests.get(url, auth=(username, password))
    #print('\nstatus_code: ' + str(resp.status_code))
    #print(resp.headers)
    print('\njndi resources:')
    print resp.text

def find_named_sibling(tag, desired_name, how_many_tries=5):
    sib = tag
    for indx in range(how_many_tries):
        if sib.next_sibling:
            sib = sib.next_sibling
            if sib.name == desired_name:
                return sib
        else:
            print('Out of siblings at ' + str(indx) + '. wtf.')
            return None

def scrape_table(tbl, filt=None):
    retrows = []
    rows = tbl.find_all('tr')
    if filt:
        rows = [row for row in rows if filt(row)]
    for row in rows:
        retrows.append([str(cell.string) for cell in row.find_all(['td', 'th'])])
    return retrows

def skip_ready_threads(row):
    if row:
        firstcell = row.find(['th', 'td'])
        if firstcell:
            firstcontent = firstcell.string
            return firstcontent != 'R'
        else:
            return False
    else:
        return False


def server_status(password, username, status_url):
    print('calling ' + status_url)
    resp = requests.get(status_url, auth=(username, password))
    body = resp.text
    soup = BeautifulSoup(body)

    print
    hdrs = soup.find_all('h1')
    for hdr in hdrs:
        if hdr.string == 'JVM':
            print('Found the JVM header!')
            tbl = find_named_sibling(hdr, 'table')
            if tbl:
                print('got a table!')
                rows = scrape_table(tbl)
                print('...with ' + str(len(rows)) + ' rows!')
                for row in rows:
                    print row
            
        elif 'http-bio-8080' in hdr.string:
            print('Found the http-bio-8080 header!')
            tbl = find_named_sibling(hdr, 'table')
            if tbl:
                print('got a table!')
                rows = scrape_table(tbl, filt=skip_ready_threads)
                print('...with ' + str(len(rows)) + ' rows!')           
                for row in rows:
                    print row
