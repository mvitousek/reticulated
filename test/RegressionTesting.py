# Regresssion Testing for Reticulated Python
import subprocess

# In our main we set up the variables to keep track of the
# tests that passedsed and faileded.
# We also print out the template for our results table.

def main():
    passed = 0
    failed = 0
    print("Program" + "\t\t" + "passed" + "\t" + "failed")

# Here we open the file that contains all of the files to be
# tested, and put it in the variable files.

    f = open('/nfs/nfs4/home/stdyoung/reticulated/test/Files.py')
    files = f.readlines()
    f.close()

# Then we call the method to read in the results of the files to
# compare to the results we expect.
    readin(files)

# We set it up that for each file listed in files we run a subprocess
# to get the result and then compare that result to what we had expected. 
def readin(files):
    for x in files:
        first = subprocess.call('python3 $RETIC ' + x, stdin=None, stdout=None, stderr=None, shell=False, timeout=None)
        compare(first, passed, failed)

def compare(first, passed, failed):
    for x in ending:
        if first == subprocess.call((first.rstrip(2) + x), stdin=None, stdout=None, stderr=None, shell=False, timeout=None):
            testpassed = 1
            passed += 1
    else:
        compareerror(first, passed, failed) 
        testfailed = 1
        failed += 1
    
    print(first + " " + testpassed + " " + testfailed)

def compareerror(first, passed, failed):
    print("End")


main()
