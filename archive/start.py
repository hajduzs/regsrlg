# New entry point, preprocessing and other operations are done in advance and saved to save time.

import os 
from datetime import datetime 

# Entry params and etc.

C_rootout = '/home/zsomb/work/regsrlg/out'
C_rootin = '/home/zsomb/work/regsrlg/debug'

V_script_start_time = datetime.now().strftime("%Y%m%d_%H%M%S")


root, subdirs, files = next(os.walk(C_rootin))



print("finished")