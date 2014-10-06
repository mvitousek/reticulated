# Regresssion Testing for Reticulated Python

#Notes:
# This program calls the tests listed in Files.py, runs  the file, and 
# puts the results in the variable first. We then compare that with what we 
# expect to be the result under certain semantics, variable second. 
# Depending on the result we print out some information and then due this again
# until we run out of files from Files.py.

# We made a list ending to list all of the different semantics, and to make it 
# easier to extend for the future.

# Since reticulated adds characters to the end of first, we only compare
# the amount of characters of first that is the length of second. 






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

# Here we call each element in Files.py, run them, and put their 
# results in first.
# We also use a try;exception due to subprocess ending if it finds an 
# error in one of our test cases. Due to us having error there for a 
# reason; we need a try;exception to catch that error and put it in
# first like we wanted. We then call the compare definition to compare
# the results we get with the results we expect.
    for x in files:
        try:
            first = subprocess.check_output(["python3", "/nfs/nfs4/home/stdyoung/reticulated/retic.py", x.rstrip('\n')], stderr=subprocess.STDOUT, universal_newlines=True)
            compare(x , first)

        except subprocess.CalledProcessError as e:
            compare(x, e.output)


# Here we have compare. We call the global variables to change them for
# our total count. We also have the list ending that has the different results
# for the different syntaxes we are testing. This way it is easily extendable.
# We run our expected results one at a time and use the variable second for
# both.
# Due to reticulated adding odd extra spaces on results of first; we just 
# compare only  the same length of characters from it to that of the length
# of second. (Otherwise the test always fails.)
# We then print out results, and then go back to the readin definition to
# get a new test case for the variable first.
def compare(x, first):
    global pas
    global fail
    ending =['gout', 'tout']
    for y in ending:
        second = subprocess.check_output(["cat" , (x.rstrip('py\n') + y)], stderr=subprocess.STDOUT, universal_newlines=True)
        if first[:len(second)] == second:
            print(x.rstrip('\n') + ": " + "\t" + "pass")
            pas += 1

        else: 
            print(x.rstrip('\n') + ": " + "\t" + "fail")
            print(first)
            print(second)
            print("Beginning [" , first , "] Beginning [" , second, ']', )
            fail += 1
            
    




main()
