#!/usr/bin/python
# Perform the functional tests on SV
import subprocess
import os
import pathlib
import traceback
import pipetestutils

def main():
    r1 = -1

     
    my_env = os.environ.copy()
    my_env["LD_LIBRARY_PATH"] = "/usr/local/lib:" + my_env["LD_LIBRARY_PATH"]

    try:
        args = ["python3", "test/functional/test_runner.py" \
                , "--extended" \
                , "--junitouput=build/reports/func-tests.xml"]
        r1 = subprocess.call(args, env=my_env)
    except Exception as e:
        print("Problem running tests")
        print("type error: " + str(e))
        print(traceback.format_exc())
        exit(-1)

    print("functional tests completed with result code {}".format(r1))
    r1 ^= 1 # 1 rather than 0 is returned on success
    exit(abs(r1))

if __name__ == '__main__':
    main()
