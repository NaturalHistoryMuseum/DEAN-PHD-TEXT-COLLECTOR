# own local imports
import text_collector_config
import eolife
#Science Direct imports
from elsapy.elsapy.elsclient import ElsClient
from elsapy.elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elsapy.elssearch import ElsSearch
from xml.dom.minidom import parseString
from xml.dom import minidom

# standard or third party imports
from os import sys
from shutil import copy2
import os
import xml.etree.cElementTree as ET
import re
import json
import urllib
import ConfigParser
import time
import threading
import numpy
import argparse
import multiprocessing
import dicttoxml
from bs4 import BeautifulSoup


#global settings 
settings = text_collector_config.BaseConfig()


## Load science direct configuration
con_file = open("elsapy/config.json")
config = json.load(con_file)
con_file.close()
# Initialize client
client = ElsClient(config['apikey'])
client.inst_token = config['insttoken']


def cleanText(textToClean):
    input_text = ""
    if(textToClean is not None):
        input_text = ''.join(e for e in textToClean if e.isalnum() or e.isspace() or e == '.' or e == ',' or e == '!' or e == '?' or e == '(' or e == ')' or e == '[' or e == ']' or e == '^' or e == '&' or e == '+' or e == '-' or e == '*' or e == '<' or e == '>' or e == '/' or e == '=' or e == '\"' or e == '\'')
        input_text = re.sub(r"\n", " ", input_text)
    return input_text

def cleanTextForVector(textToClean):
    input_text = ""
    if(textToClean is not None):
        if(textToClean is not None):
            input_text = ''.join(e for e in textToClean if e.isalnum() or e.isspace())        
            input_text = re.sub(r"\n", " ", input_text)
        #input_text = ''.join(e for e in textToClean if e.isalnum() or e.isspace())
        #input_text = re.sub(r"\n", " ", input_text)
    return input_text

# This is a thread worker function. The data is split into slices. The number of slices
# is determined by the number of cores (N) the CPU has minus 1. This will allow the 
# computer to use a core for background OS purposes.

def science_direct_xml_process_thread_function(arraySlice, startCount, idx):
    save_path = settings.RAW_PATH + "/" + settings.SD_SEARCH_TERM + "/"  
    save_text_path = settings.RAW_PATH + "/" + settings.SD_SEARCH_TERM + "/" + str(startCount) + "/"
    word_seer_xml_out_path = settings.RAW_PATH + "/" + "wordseer_xmls/"
    log_path = save_text_path + "log.txt"
    # Create the paths if they do not exist.
    if not os.path.exists(save_text_path):
        os.makedirs(save_text_path)
    loop_count = startCount
    total_count = len(arraySlice)
    for result in arraySlice:
        loop_count = loop_count+1
        try:
            prismdoi = result.get("prism:doi",  str(loop_count))
            entityID = result.get("eid")
            save_file = word_seer_xml_out_path + entityID + ".xml"
            output_block_text_path = save_text_path + "block_text.txt"
            if os.path.isfile(save_file) is False:
                article = ET.Element("article")
                ET.SubElement(article, "search_query").text = settings.SD_SEARCH_TERM
                ET.SubElement(article, "search_time").text = time.strftime("%c")
                ET.SubElement(article, "time").text = result["prism:coverDate"][0]["$"]
                ET.SubElement(article, "title").text = cleanText(result.get("dc:title",""))
                with open(output_block_text_path, "a") as block_out:
                    block_out.write(cleanTextForVector(result.get("dc:title","")).encode('utf-8').strip() + " ")        
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
                        block_out.write(cleanTextForVector(abstract).encode('utf-8').strip() + "\n")
                tree = ET.ElementTree(article)
                tree.write(save_file)
                if(loop_count%5==0):
                    print(str(loop_count) + " / " + str(total_count+startCount) + " parsed. Thread id = " + str(idx))
            else:
                print(save_file, "already exists, skipping to next : # " + str(loop_count) +"\n")
        except Exception as e:
            print("error on #" + str(loop_count) + " doi : " + prismdoi + ". Thread = " + str(idx) + "\n" )
            print(e.__doc__, e.message)
            with open(log_path, "a") as log_out:
                    log_out.write(e.message + "\n")
                    log_out.write("\n")
            pass
    return




def check_year_format(year):
    if len(year) == 4:
        try:
            result = int(year)
            return True
        except ValueError:
            return True
    return False



def scienceDirectDownload(settings, startTime):
    # This function downloads the xml collected from the science direct search.
    # It then divides the xml data into chunks equal to the number of threads - 1, the CPU has.
    # Each division is is then processed by a separate CPU thread.
    # During the processing stage -- "science_direct_xml_process_thread_function", the downloaded xml is
    # looped through and it performs 2 main functions. 1 extract the information into a text file. 2 extract the information
    # in an xml format that is supported by wordseer. This is explained futher in the science_direct_xml_process_thread_function  
    # documentation notes within the function.
    
    # After all threads have finished their work, this function combines the information from the separate files into a
    # final file which is moved to the processed folder.  

    # important note! checks are done to insure that a file is only parsed and copied over to the processed folder
    # if it's date is bigger than the date timestamp generated when the program is ran. This is to stop file / text duplication 
    # in the processed files as this might be run on separate days. Downloaded files are never deleted. 


    # folder structures created:
    # %DOWNLOAD_PATH% - raw - wordseer_xmls
    #                       - %search_term%
    #                 - processed - wordseer_xmls
    #                             - %search_term%
    #

    word_seer_xml_out_path = settings.PROCESSED_PATH + "/" + "wordseer_xmls/"
    if not os.path.exists(word_seer_xml_out_path):
        os.makedirs(word_seer_xml_out_path)
    word_seer_xml_raw_path = settings.RAW_PATH + "/" + "wordseer_xmls/"
    if not os.path.exists(word_seer_xml_raw_path):
        os.makedirs(word_seer_xml_raw_path)
    doc_srch = ElsSearch(settings.SD_SEARCH_TERM + "&date=" + str(settings.SD_YEARS) ,'scidir')
    doc_srch.execute(client, get_all = True, max_results=settings.SD_MAX_RESULTS)
    x = numpy.array_split(doc_srch.results, settings.NO_CORES)
    v = len(doc_srch.results)/settings.NO_CORES
    print("processing text using number of cores (n-1) = " + str(settings.NO_CORES))
    ThreadArray = []
    for i in xrange(0,settings.NO_CORES):
        t = threading.Thread(target=science_direct_xml_process_thread_function, args=(x[i],i*len(x[0]),i,))
        t.start()
        ThreadArray.append(t)
    for t in ThreadArray:
        t.join()


    outPath = settings.PROCESSED_PATH + "/text_file/" + time.strftime("%d-%m-%y") + "/"
    if not os.path.exists(outPath):
        os.makedirs(outPath)
    outPath = outPath + "plain_text.txt"
    for i in xrange(0,settings.NO_CORES):
        fileToWriteTo = open(outPath, 'a')
        fileToConcatenate = open(settings.RAW_PATH + "/" + settings.SD_SEARCH_TERM + "/" + str(i*len(x[0])) + "/block_text.txt", 'r')
        for line in fileToConcatenate:
            fileToWriteTo.write(line)
        fileToWriteTo.close()

    fileArray = []
    for file in os.listdir(word_seer_xml_raw_path):
        fullPath = word_seer_xml_raw_path + file
        if fullPath.endswith('.xml') and os.path.getctime(fullPath) >= startTime:
            fileArray.append(fullPath)
   
    word_seer_xml_out_path = settings.PROCESSED_PATH + "/" + "wordseer_xmls/" + time.strftime("%d-%m-%y") + "/"
    fileCount = 0;
    folderIndex = 0;
    for filePath in fileArray:
        if(fileCount%settings.WS_FOLDER_SIZE==0):
            folderIndex = folderIndex + 1
            os.makedirs(word_seer_xml_out_path + str(folderIndex))
            copy2(os.path.dirname(os.path.realpath(__file__)) + "/structure.json", word_seer_xml_out_path + str(folderIndex) + "/")
        copy2(filePath, word_seer_xml_out_path + str(folderIndex) + "/")
        fileCount = fileCount + 1
    return


def eolDownload(settings):
    # The total range to collect is the last index minus the start index
    valueToCollect = settings.EOL_END_NUM - settings.EOL_START_NUM
    
    print("collection size = " + str(valueToCollect))
    eol = eolife.eol()
    eol.exemplars()
    outDir = settings.PROCESSED_PATH + "/text_file/" + time.strftime("%d-%m-%y") 
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    loopCount = 0; 
    # loop through the page index range which is defined in the config settings.
    for i in range(settings.EOL_START_NUM, settings.EOL_END_NUM):
        outDir = settings.PROCESSED_PATH + "/text_file/" + time.strftime("%d-%m-%y") 
        if not os.path.exists(outDir):
            os.makedirs(outDir)
        outPath = outDir+ "/eol_text.txt"
        try:
            if not os.path.exists(outDir):
                os.makedirs(outDir)
            output_file = open(outPath, 'a')
            result = eol.page(i)

            taxonConceptItems = result.getElementsByTagName('taxonConcept')
            dataObjectItems = result.getElementsByTagName('dataObject')
    
            tl_idx = 0
            do_idx = 0

            string_out = "[PAGE_ID]="+ str(i) + "\n"

            for item in taxonConceptItems:
                taxonNameNode = item.getElementsByTagName('dwc:scientificName')
                taxonName = taxonNameNode[tl_idx].firstChild.nodeValue
                #out_text = cleanTextForVector(BeautifulSoup(taxonName.encode('ascii', 'replace'), "lxml").get_text())
                #out_text = cleanTextForVector(BeautifulSoup(taxonName, "lxml").get_text())
                out_text = BeautifulSoup(taxonName, "lxml").get_text()
                string_out = string_out + " " + out_text
                tl_idx = tl_idx + 1

            for item in dataObjectItems:
                descriptionNode = result.getElementsByTagName('dc:description')
                description = descriptionNode[do_idx].firstChild.nodeValue
                #out_text = cleanTextForVector(BeautifulSoup(description.encode('ascii', 'replace'), "lxml").get_text())
                #out_text = cleanTextForVector(BeautifulSoup(description, "lxml").get_text())
                out_text = BeautifulSoup(description, "lxml").get_text()
                string_out = string_out + " " + out_text
                do_idx = do_idx + 1

        
            string_out = string_out+"\n"
            output_file.write(string_out.encode('utf-8', 'ignore')) # utf-8 will include all standard characters
            #output_file.write(string_out)
            loopCount = loopCount + 1 
            output_file.close()
            
            if(i%200==0):
                print(str(loopCount) + " / " + str(valueToCollect) + " parsed")
            
        except Exception as e:
            error_log = outDir+"/errors.txt"
            error_log_file = open(error_log, 'a')
            error_log_file.write(e.message)
            error_log_file.write("\n This error occured on url index " + str(i))
            error_log_file.close()
            print(e.message)
    return


if __name__ == '__main__':
    #global settings
    settings = text_collector_config.BaseConfig()
    #program = os.path.basename(sys.argv[0])
    startTime = time.time()
    print(startTime)    

    if settings.USE_SCIENCE_DIRECT.lower() == "y":
        scienceDirectDownload(settings, startTime)
    if settings.USE_EOL.lower() == 'y':
        eolDownload(settings)
        print("finished EOL \n")





    
