#################################
##### Name:
##### Uniqname:
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

CACHE_FILENAME = "nps_cache.json"


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    
    url : string
        the url of a national site
    '''
    def __init__(self, category, name, address, zipcode, phone, url):
        self.category = category
        self.name = name
        self. address = address
        self.zipcode = zipcode
        self.phone = phone
        self.url = url
    
    def info(self): 
        return(self.name + " (" + self.category + "): " + self.address + " " + self.zipcode)
        


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    state_url = {}
    response = requests.get("https://www.nps.gov/findapark/index.htm")
    soup = BeautifulSoup(response.text, 'html.parser')
    maps = soup.find('map')
    areas = maps.find_all('area')
    for i in areas:
        state = i['alt'].lower()
        url = i['href']
        state_url[state] = "https://www.nps.gov" + url
    return state_url

       

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    response = requests.get(site_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    name = soup.find('a', class_ = "Hero-title").text
    try:
        category = soup.find('span', class_ = 'Hero-designation').text
    except:
        category = "no category"
    try:
        address1 = soup.find('span', itemprop = 'addressLocality').text
    except:
        address1 = "no local address"
    try:
        address2 = soup.find('span', itemprop = 'addressRegion').text
    except:
        address2 = "no regional address"
    address = address1 + ", " + address2
    try:
        zipcode = soup.find('span', itemprop = 'postalCode').text.strip()
    except:
        zipcode = "no zipcode"
    try:
        phone = soup.find('span', itemprop = 'telephone').text.strip()
    except:
        phone = "no phone"
    instance = NationalSite(category, name, address, zipcode, phone, site_url)
    return instance


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    sitelist=[]
    response = requests.get(state_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    ul = soup.find('ul', id = 'list_parks')
    li = ul.find_all('li', class_='clearfix')
    for i in li:
        h3 = i.find('h3')
        a = h3.find('a')
        url = a['href']
        site_url = "https://www.nps.gov" + url
        site = get_site_instance(site_url)
        sitelist.append(site) 
    return sitelist



def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    params = {'key':secrets.API_KEY, 'origin':site_object.zipcode, 'radius': 10, 'maxMatches': 10,'ambiguities':"ignore", 'outFormat':"json"}
    
    url = "http://www.mapquestapi.com/search/v2/radius"
    page = requests.get(url, params)
    return json.loads(page.text)



def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

def print_state_list_with_cache():
    ''' print a list of sites for a state with cache
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    while(1):
        CACHE_DICT = open_cache()
        statedict = build_state_url_dict()
        statename = input("Enter a state name(e.g. Michigan, michigan) or \"exit\":")
        statename = statename.lower()
        if( statename == "exit"):
            break
        elif statename not in statedict.keys():
            print("[Error] Enter proper state name")
            continue
        else:
            try:
                statelist_info = CACHE_DICT[statename]["statelist_info"]
                for i in statelist_info:
                    print("Using Cache")
                
            except:
                stateurl = statedict[statename]
                statelist = get_sites_for_state(stateurl)
                statelist_info = []
                site_urls = []
                for i in statelist:
                    site_url = i.url
                    statelist_info.append(i.info())
                    site_urls.append(site_url)
                    print("Fetching")
                CACHE_DICT[statename] = {}
                CACHE_DICT[statename]["statelist_info"] = statelist_info
                CACHE_DICT[statename]["site_urls"] = site_urls
                save_cache(CACHE_DICT)
       
            
            print("---------------------------------------")
            print("List of national sites in " + statename)
            print("---------------------------------------")

            for i in range(len(statelist_info)):
                print("[" + str(i+1) + "]" + statelist_info[i])
            
            detail_search_with_cache(statename, CACHE_DICT)
            break


def detail_search_with_cache(statename, CACHE_DICT):
    ''' Print nearby sites of the place that user choose
    
    Parameters
    ----------
    statename: string
        The name of the state that user search
    CACHE_DICT : dict
        The dict that stores all cache data
    
    Returns
    -------
    None
    '''
    while(1):
        detailnum = input("Choose the number for detail search or \"exit\" or \"back\" ")
        if(detailnum == "exit"):
            break
        elif(detailnum == "back"):
            print_state_list_with_cache()
            break
        elif(int(detailnum) > 0 and int(detailnum) <= len(CACHE_DICT[statename]["statelist_info"])):
            siteobject = get_site_instance(CACHE_DICT[statename]["site_urls"][int(detailnum) - 1])
            try:
                nearby_place = CACHE_DICT[statename][siteobject.name]
                print("Using cache")

            except:
                CACHE_DICT[statename][siteobject.name] = {}
                nearby_place = get_nearby_places(siteobject)
                CACHE_DICT[statename][siteobject.name] = nearby_place["searchResults"]
                save_cache(CACHE_DICT)
                print("Fetching")
            print("---------------------------------------")
            print("Places near " + siteobject.name)
            print("---------------------------------------")
            for i in CACHE_DICT[statename][siteobject.name]:
                if len(i["fields"]["group_sic_code_name_ext"]) == 0:
                    i["fields"]["group_sic_code_name_ext"] = "no category"
                if len(i["fields"]["address"]) == 0:
                    i["fields"]["address"] = "no address"
                if len(i["fields"]["city"]) == 0:
                    i["fields"]["city"] = "no city"
                print("-" + i["name"] + " (" + i["fields"]["group_sic_code_name_ext"] +"): " + i["fields"]["address"] + ", " + i["fields"]["city"])
            continue
        else:
            print("[Error] Invalid input")
            continue





if __name__ == "__main__":

    print_state_list_with_cache()


