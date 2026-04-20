
from pymongo import database
from database import *
from calculator import *
import sys
import argparse as ar
from database_daily import *
from database_advisor import *
from database_twins import *
from database_motivate import *

#"C:\\facesyma-backend\\media\\"+str(sys.argv[1])

def main():


    dir_ = "/home/facesymagroups/facesyma-backend/newfsbackend/project_fs/media/tmp/"
    path =  dir_ +str(sys.argv[1])

    if sys.argv[2] == "advisor": 
        # shell -> py main.py 1.jpg "advisor" "tr"
        # print("advi ana")
        a = advisor(path, str(sys.argv[3]))
    elif sys.argv[2] == "motivate": 
        # shell -> py main.py 1.jpg "advisor" "tr"
        # print("advi ana")
        a = motivate(path, str(sys.argv[3]))
        
    elif sys.argv[1] == "twins": 
        # shell -> py main.py "twins" 1.jpg 2.jpg  "tr"
        # print("dail ana")
        path1 = dir_ + str(sys.argv[2])
        path2 = dir_ + str(sys.argv[3])
        a = twins(path1, path2, str(sys.argv[4]) )

    else:
        # shell -> py main.py 1.jpg "tr"
        # print("char ana")
        a = databases(path, str(sys.argv[2])) 

    return print(a)

# a = main()
# print(a)

try:
    a = main()
    print(a)
except FileNotFoundError as e:
    print("ERROR - No such file or directory")
    print(e)
except ValueError as e:
    print("ERROR - Face not found")
    print(e)
except UnboundLocalError as e:
    print("ERROR - Face not found")
    print(e)
except EOFError as e:
    exit("ERROR - closed")
    print(e)
except Exception as e:
    print("ERROR - Any mistake")
    print(e)


