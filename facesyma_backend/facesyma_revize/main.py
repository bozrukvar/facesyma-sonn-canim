
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


    _argv = sys.argv
    _a1 = _argv[1]; _a2 = _argv[2]; _a3 = _argv[3]
    dir_ = "/home/facesymagroups/facesyma-backend/newfsbackend/project_fs/media/tmp/"
    path =  dir_ +str(_a1)

    if _a2 == "advisor":
        # shell -> py main.py 1.jpg "advisor" "tr"
        # print("advi ana")
        a = advisor(path, str(_a3))
    elif _a2 == "motivate":
        # shell -> py main.py 1.jpg "advisor" "tr"
        # print("advi ana")
        a = motivate(path, str(_a3))

    elif _a1 == "twins":
        # shell -> py main.py "twins" 1.jpg 2.jpg  "tr"
        # print("dail ana")
        path1 = dir_ + str(_a2)
        path2 = dir_ + str(_a3)
        a = twins(path1, path2, str(_argv[4]) )

    else:
        # shell -> py main.py 1.jpg "tr"
        # print("char ana")
        a = databases(path, str(_a2))

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


