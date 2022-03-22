from bs4 import BeautifulSoup
import re
import csv
import os
#import mysql.connector 

#filepath = 'highlights_and_improvements_mn_eur_2021_12_000.html'
folderpath= str(os.getenv("folderpath"))

#csvfilepath ='country_names.csv'
csvfilepath = str(os.getenv("csvfilepath"))

#local container for country name and description
country_isocode_description = []

# class CountryData is to hold the name, the ISO code, and the description of each country found in the HTML file
html_countryname=[]
class CountryData:
    def __init__(self,data_ver, name, code, description):
        self.name = name
        self.code = code
        self.description = description
 # printing helper    
    def __str__(self):
        return "country name: %s, country ISO code: %s, \ndescription: %s" % (self.data_ver, self.name, self.code, self.description)

#def storage_db(b,c,d):
#    data_ver=os.getenv("RealeaseVersion")
 #   cnx = mysql.connector.connect(user='test_user', password= '123456',
 #                              host='127.0.0.1',
 #                               database='mtc_autobuild')
 #  cnx_cursor=cnx.cursor()
  #  insert_stmt =("INSERT INTO release_notes (data_source_version, country, highlights) VALUES (%s, %s, %s)" \
  #      f" ON DUPLICATE KEY UPDATE highlights=values(highlights)")
  #  data=(b, c, d)
  #  cnx_cursor.execute(insert_stmt,data)
   # cnx.commit()
   # cnx.close()


# function to match the country name with the ISO code from the country_names csv file
def matching_country_code(name):
    with open(csvfilepath, 'r') as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader)
        for row in datareader:
            if row[1]==name:
                return row[0]
            else:
                #if re.search(name,row[1]):
                #    return row[0]
                if re.search(row[1], name):
                    return row[0]
        
        html_countryname.append(name)
       

# main function to read the HTML file and parse through and extract the country name and the country description        

def pulling_data():
    file_list = os.listdir(folderpath)
    for file in file_list:
        with open(os.path.join(folderpath,file), 'r') as html_file:
            content = html_file.read()
            soup = BeautifulSoup(content, 'html.parser')
             #get the data source version from the html title
            title_string=(soup.find('title'))
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
            description_tags = soup.find_all('ul')

            # remove extra spaces from the country names
            descriptions = []
            for d in description_tags:
                 # remove the extra spaces, random new lines, and tabs found in the descriptions
                sanitize = re.sub(r"[\n\t]*", "", d.text)
                sanitize = re.sub(' +', " ", sanitize)
                # replace the periods with periods and new line
                if((sanitize).find('. ')):
                    sanitize = re.sub('\.', ".\\n", sanitize)
                sanitize = sanitize.strip()
                descriptions.append(sanitize)
            #remove introduction and general from both country names and the descriptions
            del country_names[:2]
            del descriptions[:2]
            
            # find the ISO codes based on the country name 
            iso_codes = []
            for country_name in country_names:
                iso = matching_country_code(country_name)
                iso_codes.append(iso)
    
            
             # order matters, so first error checking is to make sure there is a 1:1:1 correlation between all individual lists
            if(len(country_names) == len(iso_codes) == len(descriptions)):
                for i in range(len(country_names)):
                     # combine all information into the class
                    country_isocode_description.append(CountryData(data_source_version,country_names[i], iso_codes[i], descriptions[i]))
            else:
                print("Error sizes do not match")

             # print to check 
            print("____________________________________________________________________________________________________________________________________")
            print(data_source_version)
            for entry in country_isocode_description:
                print("__________________________________________________________________________________________________________________________________")
                print(entry.name,"(",entry.code,")","\n",entry.description)
            
 
#def pushing_data():
 #   for country in country_isocode_description:
 #       storage_db(country.data_ver,country.code, country.description)


pulling_data()
#pushing_data()
