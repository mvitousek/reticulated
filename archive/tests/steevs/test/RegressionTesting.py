# Regresssion Testing for Reticulated Python
import subprocess
pas = 0
fail = 0

# In our main we set up the variables to keep track of the
# tests that passed and failed.
# We also print out the template for our results table.
def main():
    print("Program" + "\t\t" + "Pass" + "\t" + "Fail")

# Here we open the file that contains all of the files to be
# tested, and put it in the variable files.

    f = open('Files.py')
    files = f.readlines()
    f.close()

# Then we call the method to read in the results of the files to
# compare to the results we expect.
    readin(files)

    print("Total" + "\t" + str(pas) + "\t" + str(fail))

# We set it up that for each file listed in files we run a subprocess
# to get the result and then compare that result to what we had expected. 
def readin(files):
    for x in files:
        first = subprocess.check_output(["python3", "/nfs/nfs4/home/stdyoung/reticulated/retic.py", x.rstrip('\n')], stderr=subprocess.STDOUT, universal_newlines=True)
        compare(x , first)

def compare(x, first):
    global pas
    global fail
    ending =['gout', 'tout']
    for y in ending:
        if first == subprocess.call(["cat" , (x.rstrip('py\n') + y)], stderr=subprocess.STDOUT, universal_newlines=True):
            print(x.rstrip('\n') + ": " + "\t" + "pass")
            pas += 1
        else: 
            print(x.rstrip('\n') + ": " + "\t" + "fail")
            fail += 1
            
    




main()
