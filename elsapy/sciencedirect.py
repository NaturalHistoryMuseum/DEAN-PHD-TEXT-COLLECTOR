"""An example program that uses the elsapy module"""

from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch
from xml.dom.minidom import parseString
import json, re
import xml.etree.cElementTree as ET
import urllib, os, time
import threading
import numpy
import dicttoxml
import argparse




parser = argparse.ArgumentParser()
parser.add_argument("year", help="the year to search science direct for")
args = parser.parse_args()



## Load configuration
con_file = open("config.json")
config = json.load(con_file)
con_file.close()

## Initialize client
client = ElsClient(config['apikey'])
client.inst_token = config['insttoken']

##print ("Please enter the search terms")
##s = raw_input('--> ')
## Initialize doc search object and execute search, retrieving all results
#scopus, scidir
max_Results = 400;
search_query = "biodiversity"
#search_query = "bioinformatics"

main_path = "/home/dean/phd/xmlout/"
xml_out_path = main_path + "out.xml"


loop_count = 0

### cleanText Function cleans the text to remove any characters which might confuse the NLP. 
### I've kept important characters, including basic math notation and brackets etc. These will
### need to stay as I will later be analysing references and possibally math equations.
 
def cleanText(textToClean):
    input_text = ""
    if(textToClean is not None):
        input_text = ''.join(e for e in textToClean if e.isalnum() or e.isspace() or e == '.' or e == ',' or e == '!' or e == '?' or e == '(' or e == ')' or e == '[' or e == ']' or e == '^' or e == '&' or e == '+' or e == '-' or e == '*' or e == '<' or e == '>' or e == '/' or e == '=' or e == '\"' or e == '\'')
        input_text = re.sub(r"\n", " ", input_text)
    return input_text

def checkNone(object_to_check):
    if(object_to_check is not None):
        return True
    else:
        return False


# This is a thread worker function. The data is split into slices. The number of slices
# is determined by the number of cores (N) the CPU has minus 1. This will allow the 
# computer to use a core for background OS purposes.

def worker_function(arraySlice, startCount, idx):
    save_path = main_path + search_query + "/"  
    save_text_path = main_path + search_query + "/" + str(startCount) + "/"
    log_path = save_text_path + "log.txt"
    # Create the path if it does not exist.
    if not os.path.exists(save_text_path):
        os.makedirs(save_text_path)
    
    loop_count = startCount
    total_count = len(arraySlice)
    for result in arraySlice:
        loop_count = loop_count+1
        try:
            prismdoi = result.get("prism:doi",  str(loop_count))
            entityID = result.get("eid")
            save_file = save_path + entityID + ".xml"
            output_block_text_path = save_text_path + "block_text.txt"
            if os.path.isfile(save_file) is False:
                article = ET.Element("article")
                ET.SubElement(article, "search_query").text = search_query
                ET.SubElement(article, "search_time").text = time.strftime("%c")
                ET.SubElement(article, "time").text = result["prism:coverDate"][0]["$"]
                ET.SubElement(article, "title").text = cleanText(result.get("dc:title",""))
                with open(output_block_text_path, "a") as block_out:
                    block_out.write(cleanText(result.get("dc:title","")).encode('utf-8').strip() + ". \n")        
                if result.get("authors","") != "":
                    for author in result["authors"].get("author", ""):#result["authors"]["author"]:
                        ET.SubElement(article, "author").text = author.get("surname", "") + ", " + author.get("given-name","")
                   #print("\n Debug authors adding .... ", author["surname"] + ", " + author["given-name"])
                ET.SubElement(article, "number").text = str(loop_count)
                ET.SubElement(article, "text", section="teaser").text = cleanText(result.get("prism:teaser",""))
                # Do a document search to retrieve the abstract information
                abstract = "" # start with an empty variable
                scp_doc = FullDoc(uri = result.get("prism:url",""))
                if scp_doc.read(client):
                    abstract = scp_doc.abstract
                    if abstract is not None:
                        if abstract.find('Abstract') == 0:
                            abstract = abstract[8:]
                    ET.SubElement(article, "text", section="abstract").text = cleanText(abstract)
                    with open(output_block_text_path, "a") as block_out:
                        block_out.write(cleanText(abstract).encode('utf-8').strip() + "\n")
                    #print(scp_doc.coredata)
                tree = ET.ElementTree(article)
                #sem.acquire()
                tree.write(save_file)
                #sem.release()
                #print("Saved file, EID = ", entityID)
                if(loop_count%5==0):
                    print(str(loop_count) + " / " + str(total_count+startCount) + " parsed. Thread id = " + str(idx))
            else:
                print(save_file, "already exists, skipping to next : # " + str(loop_count) +"\n")
                #skip
        except Exception as e:
            print("error on #" + str(loop_count) + " doi : " + prismdoi + ". Thread = " + str(idx) + "\n" )
            print(e.__doc__, e.message)
            with open(log_path, "a") as log_out:
                    log_out.write(e.message + "\n")
                    log_out.write("\n")
            pass



search_year = args.year
#print(search_query + "&date=" + search_year )

doc_srch = ElsSearch(search_query + "&date=" + search_year ,'scidir')
doc_srch.execute(client, get_all = True, max_results=max_Results)


n = 6

x = numpy.array_split(doc_srch.results, n)
v = len(doc_srch.results)/n

for i in xrange(0,n):
    t = threading.Thread(target=worker_function, args=(x[i],i*len(x[0]),i,))
    t.start()






