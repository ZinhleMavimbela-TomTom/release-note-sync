from bs4 import BeautifulSoup
import re
import csv
import os
import mysql.connector 
import fnmatch


region =str(os.getenv("regions"))
version =str(os.getenv("version"))
remove_keyword= str(os.getenv("Remove_Word"))
change_from = str(os.getenv("Change_parameter1"))
change_to = str(os.getenv("Change_parameter2"))

csvfilepath = 'country_names.csv'
# local container for country name and description
country_isocode_description = []

# list to store unmatched country codes
unmatched_countries = []

# class CountryData is to hold the name, the ISO code, and the description of each country found in the HTML file
class CountryData:
    def __init__(self, name, data_ver, code, description):
        self.name = name
        self.data_ver = data_ver
        self.code = code
        self.description = description

    # printing helper
    def __str__(self):
        return "country name: %s, country ISO code: %s, \ndescription: %s" % (self.data_ver, self.name, self.code, self.description)

def storage_db(data_ver, c_code, descript):
    # connection to database credentials
    release_user = os.getenv('User_name')
    release_pass = os.getenv('MTC_autobuild_pass')
    release_host_name = os.getenv('MTC_autobuild_Host')
    release_DB_name = os.getenv('DB_name')
    
    conn = mysql.connector.connect(user=release_user, password=release_pass, host=release_host_name, database=release_DB_name)
    conn_cursor = conn.cursor()
    insert_stmt = ("INSERT INTO release_notes (data_source_version, country, highlights) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE highlights=values(highlights)")
    data = (data_ver, c_code, descript)
    conn_cursor.execute(insert_stmt, data)
    conn.commit()
    conn.close()

# function to match the country name with the ISO code from the country_names csv file
def matching_country_code(name):
    with open(csvfilepath, 'r') as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader)
        for row in datareader:
            if row[1] == name:
                return row[0]
            else:
                if re.search(row[1], name):
                    return row[0]

# main function to read the HTML file and parse through and extract the country name and the country description
def pulling_data():
    file_list = f'/share/nds-sources/products/commercial/{region}{version}/documentation/mn/release_notes/release_notes/whats_new/'
    pattern = f'highlights_and_improvements_mn_{region}_{version}.html'
    
    with open(os.path.join(file_list, pattern), 'r') as html_file:
            content = html_file.read()
            soup = BeautifulSoup(content, 'html.parser')
            # get the data source version from the html title
            title_string = (soup.find('title'))
            data_source_version = ((title_string.text).split()[2])

            # country names have the h2 tag in the HTML file
            country_name_tags = soup.find_all('h2')
            country_names = []
            # remove extra spaces from the country names
            for c in country_name_tags:
                sanitize = re.sub(r"[\n\t]*", "", c.text)
                sanitize = re.sub(' +', " ", sanitize)
                country_names.append(sanitize)

            # descriptions have the ul tag in the HTML file
            description_tags = soup.find_all("ul", {"class": "CountryRemark"})

            descriptions = []
            for d in description_tags:
                result = d.find_all("li")
                country_descrip = []
                for li in result:
                    # fix random newlines, tabs, spaces in strings
                    sanitize = u''.join(li.findAll(text=True))
                    sanitize = re.sub(r"[\n\t]*", "", sanitize)
                    sanitize = re.sub(' +', " ", sanitize)
                    sanitize =re.sub('\xa0',"",sanitize)
                    if ((len(remove_keyword))!=0):
                        split_remove =remove_keyword.split(",")
                        for i in range(len(split_remove)):
                            sanitize=re.sub(split_remove[i], "",sanitize)
                    if ((len(change_from)!=0) and (len(change_to)!=0)):
                        #splits the change parameter 1 and change parameter 2 if there are multiple parameters 
                        split_change_to = change_to.split(",")
                        split_change_from = change_from.split(",")
                        #loops through the str array with divided words and does replacement by mapping the words 
                        #for example "Approximately" updated to "change" therefore split_change_to[0] maps to split_change_to[0]
                        for m,j in zip(range(len(split_change_to)),range(len(split_change_from))):
                            sanitize=re.sub(split_change_from[m],split_change_to[j],sanitize)
                    sanitize = sanitize.strip()
                    country_descrip.append(sanitize)
                descriptions.append(country_descrip)
                del country_descrip

            # remove introduction and general from both country names and the descriptions
            del country_names[:1]
            del descriptions[:1]

            # find the ISO codes based on the country name
            iso_codes = []
            for country_name in country_names:
                iso = matching_country_code(country_name)
                iso_codes.append(iso)
                if iso is None:
                    unmatched_countries.append(country_name)

             # order matters, so first error checking is to make sure there is a 1:1:1 correlation between all individual lists
            if(len(country_names) == len(iso_codes) == len(descriptions)):
                for i in range(len(country_names)):
                    # combine all information into the class
                    country_isocode_description.append(CountryData(
                        country_names[i], data_source_version, iso_codes[i], descriptions[i]))
            else:
                print("Error sizes do not match")
                print(len(country_names))
                for country in country_names:
                    print(country)
                print("------")
                print(len(iso_codes))
                for iso in iso_codes:
                    print(iso)
                print("------")
                print(len(descriptions))
                for description in descriptions:
                    print(description)
                print("------")
    
def print_all():
    # print to check
    print("____________________________________________________________________________________________________________________________________")
    for entry in country_isocode_description:
        print("__________________________________________________________________________________________________________________________________")
        print(entry.name, "(", entry.code, ")-", entry.data_ver, "\n", entry.description)

def pushing_data():
    for country in country_isocode_description:
        one_country_description_as_string = ""
        for single in country.description:
            one_country_description_as_string = one_country_description_as_string + single
            one_country_description_as_string = one_country_description_as_string + "\n"
        storage_db(country.data_ver, country.code, one_country_description_as_string)
        one_country_description_as_string = ""

pulling_data()
print("Total Country Count: ", len(country_isocode_description))

if (len(unmatched_countries) == 0):
    print("Pushing to Database")
    pushing_data()
else:
    print("ERROR: These countries have no match in the csv file, please update csv file firstly and run again: ")
    for unmatch in unmatched_countries:
        print(unmatch)
        
print_all()
