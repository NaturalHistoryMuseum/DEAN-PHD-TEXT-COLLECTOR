import threading
import multiprocessing
import os

def get_default_cores():
    number_of_available_cores = multiprocessing.cpu_count()
    cores_to_allocate = number_of_available_cores - 1
    return cores_to_allocate


class BaseConfig(object):
    DOWNLOAD_PATH = "/home/dean/phd/nlp_text_downloads"
    RAW_PATH = DOWNLOAD_PATH + "/raw"
    PROCESSED_PATH = DOWNLOAD_PATH + "/processed"


    USE_SCIENCE_DIRECT = 'N'
    # SD_YEARS format = 'xxxx' OR 'xxxx-xxxx' 
    SD_YEARS = '2012'
    SD_SEARCH_TERM = 'biodiversity'
    # SD_MAX_RESULTS muse be multiples of 200's as it collects batches of 200 a time
    SD_MAX_RESULTS = 200
    USE_EOL = 'Y'
    EOL_START_NUM = 1 #650000
    EOL_END_NUM = 1000 #1000000
    EOL_NUM_RESULTS = 50000
    EOL_BATCH_COLLECTION = 'Y'
    EOL_MAX_DESC = '10'

    # WORDSEER variables
    WS_FOLDER_SIZE = 50
    
    
    

    # SYSTEM variables:
    NO_CORES = get_default_cores()
    
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
    if not os.path.exists(RAW_PATH):
        os.makedirs(RAW_PATH)
    if not os.path.exists(PROCESSED_PATH):
        os.makedirs(PROCESSED_PATH)


if __name__ == '__main__':
    settings = BaseConfig()
    print("Running from system. Basic test output is ... Number of CPU cores (n-1) = " + str(settings.NO_CORES))
    #program = os.path.basename(sys.argv[0])

