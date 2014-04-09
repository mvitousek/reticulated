# Copyright (c) 1999-2007 Gary Strangman; All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal 8/6/9
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Comments and/or additions are welcome (send e-mail to:
# strang@nmr.mgh.harvard.edu).
# 
"""
List = lambda x:x
Dyn = 1
Int = 1
Float = 1
"""
"""
pstat.py module

#################################################
#######  Written by:  Gary Strangman  ###########
#######  Last modified:  Dec 18, 2007 ###########
#################################################

This module provides some useful list and array manipulation routines
modeled after those found in the |Stat package by Gary Perlman, plus a
number of other useful list/file manipulation functions.  The list-based
functions include:

      abut (source,*args)
      simpleabut (source, addon)
      colex (listoflists,cnums)
      collapse (listoflists,keepcols,collapsecols,fcn1=None,fcn2=None,cfcn=None)
      dm (listoflists,criterion)
      flat (l)
      linexand (listoflists,columnlist,valuelist)
      linexor (listoflists,columnlist,valuelist)
      linedelimited (inlist,delimiter)
      lineincols (inlist,colsize) 
      lineincustcols (inlist,colsizes)
      list2string (inlist)
      makelol(inlist)
      makestr(x)
      printcc (lst,extra=2)
      printincols (listoflists,colsize)
      pl (listoflists)
      printl(listoflists)
      replace (lst,oldval,newval)
      recode (inlist,listmap,cols='all')
      remap (listoflists,criterion)
      roundlist (inlist,num_digits_to_round_floats_to)
      sortby(listoflists,sortcols)
      unique (inlist)
      duplicates(inlist)
      writedelimited (listoflists, delimiter, file, writetype='w')

Some of these functions have alternate versions which are defined only if
Numeric (NumPy) can be imported.  These functions are generally named as
above, with an 'a' prefix.

      aabut (source, *args)
      acolex (a,indices,axis=1)
      acollapse (a,keepcols,collapsecols,sterr=0,ns=0)
      adm (a,criterion)
      alinexand (a,columnlist,valuelist)
      alinexor (a,columnlist,valuelist)
      areplace (a,oldval,newval)
      arecode (a,listmap,col='all')
      arowcompare (row1, row2)
      arowsame (row1, row2)
      asortrows(a,axis=0)
      aunique(inarray)
      aduplicates(inarray)

Currently, the code is all but completely un-optimized.  In many cases, the
array versions of functions amount simply to aliases to built-in array
functions/methods.  Their inclusion here is for function name consistency.
"""

## CHANGE LOG:
## ==========
## 07-11-26 ... edited to work with numpy
## 01-11-15 ... changed list2string() to accept a delimiter
## 01-06-29 ... converted exec()'s to eval()'s to make compatible with Py2.1
## 01-05-31 ... added duplicates() and aduplicates() functions
## 00-12-28 ... license made GPL, docstring and import requirements
## 99-11-01 ... changed version to 0.3
## 99-08-30 ... removed get, getstrings, put, aget, aput (into io.py)
## 03/27/99 ... added areplace function, made replace fcn recursive
## 12/31/98 ... added writefc function for ouput to fixed column sizes
## 12/07/98 ... fixed import problem (failed on collapse() fcn)
##              added __version__ variable (now 0.2)
## 12/05/98 ... updated doc-strings
##              added features to collapse() function
##              added flat() function for lists
##              fixed a broken asortrows() 
## 11/16/98 ... fixed minor bug in aput for 1D arrays
##
## 11/08/98 ... fixed aput to output large arrays correctly

import stats  # required 3rd party module
import string, copy
from typed_math import *

__version__ = 0.4

###===========================  LIST FUNCTIONS  ==========================
###
### Here are the list functions, DEFINED FOR ALL SYSTEMS.
### Array functions (for NumPy-enabled computers) appear below.
###

#GN
def abut (source,*args)->List(Dyn):
    """
Like the |Stat abut command.  It concatenates two lists side-by-side
and returns the result.  '2D' lists are also accomodated for either argument
(source or addon).  CAUTION:  If one list is shorter, it will be repeated
until it is as long as the longest list.  If this behavior is not desired,
use pstat.simpleabut().

Usage:   abut(source, args)   where args=any # of lists
Returns: a list of lists as long as the LONGEST list past, source on the
         'left', lists in <args> attached consecutively on the 'right'
"""

    if not any(isinstance(source, t) for t in [list,tuple]):
        source = [source]
    for addon in args:
        if not any(isinstance(addon, t) for t in [list,tuple]):
            addon = [addon]
        if len(addon) < len(source):                # is source list longer?
            if len(source) % len(addon) == 0:        # are they integer multiples?
                repeats = len(source)/len(addon)    # repeat addon n times
                origadd = copy.deepcopy(addon)
                for i in range(repeats-1):
                    addon = addon + origadd
            else:
                repeats = len(source)/len(addon)+1  # repeat addon x times,
                origadd = copy.deepcopy(addon)      #    x is NOT an integer
                for i in range(repeats-1):
                    addon = addon + origadd
                    addon = addon[0:len(source)]
        elif len(source) < len(addon):                # is addon list longer?
            if len(addon) % len(source) == 0:        # are they integer multiples?
                repeats = len(addon)/len(source)    # repeat source n times
                origsour = copy.deepcopy(source)
                for i in range(repeats-1):
                    source = source + origsour
            else:
                repeats = len(addon)/len(source)+1  # repeat source x times,
                origsour = copy.deepcopy(source)    #   x is NOT an integer
                for i in range(repeats-1):
                    source = source + origsour
                source = source[0:len(addon)]

        source = simpleabut(source,addon)
    return source

#GN
def simpleabut (source:List(Dyn), addon:List(Dyn))->List(Dyn):
    """
Concatenates two lists as columns and returns the result.  '2D' lists
are also accomodated for either argument (source or addon).  This DOES NOT
repeat either list to make the 2 lists of equal length.  Beware of list pairs
with different lengths ... the resulting list will be the length of the
FIRST list passed.

Usage:   simpleabut(source,addon)  where source, addon=list (or list-of-lists)
Returns: a list of lists as long as source, with source on the 'left' and
                 addon on the 'right'
"""
    if not any(isinstance(source, t) for t in [list,tuple]):
        source = [source]
    if not any(isinstance(addon, t) for t in [list,tuple]):
        addon = [addon]
    minlen = min(len(source),len(addon))
    _list = copy.deepcopy(source)                # start abut process
    if not any(isinstance(source[0], t) for t in [list,tuple]):
        if not any(isinstance(addon[0], t) for t in [list,tuple]):
            for i in range(minlen):
                _list[i] = [source[i]] + [addon[i]]        # source/addon = column
        else:
            for i in range(minlen):
                _list[i] = [source[i]] + addon[i]        # addon=list-of-lists
    else:
        if not any(isinstance(addon[0], t) for t in [list,tuple]):
            for i in range(minlen):
                _list[i] = source[i] + [addon[i]]        # source=list-of-lists
        else:
            for i in range(minlen):
                _list[i] = source[i] + addon[i]        # source/addon = list-of-lists
    source = _list
    return source
#GM
def colex (listoflists:List(List(Dyn)),cnums):
    """
Extracts from listoflists the columns specified in the list 'cnums'
(cnums can be an integer, a sequence of integers, or a string-expression that
corresponds to a slice operation on the variable x ... e.g., 'x[3:]' will colex
columns 3 onward from the listoflists).

Usage:   colex (listoflists,cnums)
Returns: a list-of-lists corresponding to the columns from listoflists
         specified by cnums, in the order the column numbers appear in cnums
"""
    global index
    column = 0
    if type(cnums) in [list,tuple]:   # if multiple columns to get
        index = cnums[0]
        column = [x[index] for x in listoflists]
        for col in cnums[1:]:
            index = col
            column = abut(column,[x[index] for x in listoflists])
    elif type(cnums) == str:              # if an 'x[3:]' type expr.
        evalstring = 'map(lambda x: x'+cnums+', listoflists)'
        column = eval(evalstring)
    else:                                     # else it's just 1 col to get
        index = cnums
        column = [x[index] for x in listoflists]
    return column

#GX
def collapse (listoflists,keepcols,collapsecols,fcn1=None,fcn2=None,cfcn=None):
     """
Averages data in collapsecol, keeping all unique items in keepcols
(using unique, which keeps unique LISTS of column numbers), retaining the
unique sets of values in keepcols, the mean for each.  Setting fcn1
and/or fcn2 to point to a function rather than None (e.g., stats.sterr, len)
will append those results (e.g., the sterr, N) after each calculated mean.
cfcn is the collapse function to apply (defaults to mean, defined here in the
pstat module to avoid circular imports with stats.py, but harmonicmean or
others could be passed).

Usage:    collapse (listoflists,keepcols,collapsecols,fcn1=None,fcn2=None,cfcn=None)
Returns: a list of lists with all unique permutations of entries appearing in
     columns ("conditions") specified by keepcols, abutted with the result of
     cfcn (if cfcn=None, defaults to the mean) of each column specified by
     collapsecols.
"""
     def collmean (inlist:List(float))->float:
         s = 0.
         for item in inlist:
             s = s + item
         return s/float(len(inlist))

     if type(keepcols) not in [list,tuple]:
         keepcols = [keepcols]
     if type(collapsecols) not in [list,tuple]:
         collapsecols = [collapsecols]
     if cfcn == None:
         cfcn = collmean
     if keepcols == []:
         means = dyn([0]*len(collapsecols))
         for i in range(len(collapsecols)):
             avgcol = colex(listoflists,collapsecols[i])
             means[i] = cfcn(avgcol)
             if fcn1:
                 try:
                     test = fcn1(avgcol)
                 except:
                     test = 'N/A'
                     means[i] = [means[i], test]
             if fcn2:
                 try:
                     test = fcn2(avgcol)
                 except:
                     test = 'N/A'
                 try:
                     means[i] = means[i] + [len(avgcol)]
                 except TypeError:
                     means[i] = [means[i],len(avgcol)]
         return means
     else:
         values = colex(listoflists,keepcols)
         uniques = unique(values)
         uniques.sort()
         newlist = []
         if type(keepcols) not in [list,tuple]:  keepcols = [keepcols]
         for item in uniques:
             if type(item) not in [list,tuple]:  item =[item]
             tmprows = linexand(listoflists,keepcols,item)
             for col in collapsecols:
                 avgcol = colex(tmprows,col)
                 item.append(cfcn(avgcol))
                 if fcn1 != None:
                     try:
                         test = fcn1(avgcol)
                     except:
                         test = 'N/A'
                     item.append(test)
                 if fcn2 != None:
                     try:
                         test = fcn2(avgcol)
                     except:
                         test = 'N/A'
                     item.append(test)
                 newlist.append(item)
         return newlist

#GN
def dm (listoflists:List(List(Dyn)),criterion:str)->List(Dyn):
    """
Returns rows from the passed list of lists that meet the criteria in
the passed criterion expression (a string as a function of x; e.g., 'x[3]>=9'
will return all rows where the 4th column>=9 and "x[2]=='N'" will return rows
with column 2 equal to the string 'N').

Usage:   dm (listoflists, criterion)
Returns: rows from listoflists that meet the specified criterion.
"""
    function = 'filter(lambda x: '+criterion+',listoflists)'
    lines = list(eval(function))
    return lines

#GY
def flat(l:List(List(Dyn)))->List(Dyn):
    """
Returns the flattened version of a '2D' list.  List-correlate to the a.ravel()()
method of NumPy arrays.

Usage:    flat(l)
"""
    newl = []
    for i in range(len(l)):
        for j in range(len(l[i])):
            newl.append(l[i][j])
    return newl

#GN
def linexand (listoflists:List(List(Dyn)),columnlist,valuelist)->List(List(Dyn)):
    """
Returns the rows of a list of lists where col (from columnlist) = val
(from valuelist) for EVERY pair of values (columnlist[i],valuelists[i]).
len(columnlist) must equal len(valuelist).

Usage:   linexand (listoflists,columnlist,valuelist)
Returns: the rows of listoflists where columnlist[i]=valuelist[i] for ALL i
"""
    if type(columnlist) not in [list,tuple]:
        columnlist = [columnlist]
    if type(valuelist) not in [list,tuple]:
        valuelist = [valuelist]
    criterion = ''
    for i in range(len(columnlist)):
        if type(valuelist[i])==str:
            critval = '\'' + valuelist[i] + '\''
        else:
            critval = str(valuelist[i])
        criterion = criterion + ' x['+str(columnlist[i])+']=='+critval+' and'
    criterion = criterion[0:-3]         # remove the "and" after the last crit
    function = 'filter(lambda x: '+criterion+',listoflists)'
    lines = list(eval(str(function)))
    return lines

#GN
def linexor (listoflists:List(List(Dyn)),columnlist,valuelist)->List(List(Dyn)):
    """
Returns the rows of a list of lists where col (from columnlist) = val
(from valuelist) for ANY pair of values (colunmlist[i],valuelist[i[).
One value is required for each column in columnlist.  If only one value
exists for columnlist but multiple values appear in valuelist, the
valuelist values are all assumed to pertain to the same column.

Usage:   linexor (listoflists,columnlist,valuelist)
Returns: the rows of listoflists where columnlist[i]=valuelist[i] for ANY i
"""
    if type(columnlist) not in [list,tuple]:
        columnlist = [columnlist]
    if type(valuelist) not in [list,tuple]:
        valuelist = [valuelist]
    criterion = ''
    if len(columnlist) == 1 and len(valuelist) > 1:
        columnlist = columnlist*len(valuelist)
    for i in range(len(columnlist)):          # build an exec string
        if type(valuelist[i])==str:
            critval = '\'' + valuelist[i] + '\''
        else:
            critval = str(valuelist[i])
        criterion = criterion + ' x['+str(columnlist[i])+']=='+critval+' or'
    criterion = criterion[0:-2]         # remove the "or" after the last crit
    function = 'filter(lambda x: '+criterion+',listoflists)'
    lines = list(eval(function))
    return lines

#GM
def linedelimited (inlist:List(Dyn),delimiter:str)->str:
    """
Returns a string composed of elements in inlist, with each element
separated by 'delimiter.'  Used by function writedelimited.  Use '\t'
for tab-delimiting.

Usage:   linedelimited (inlist,delimiter)
"""
    outstr = ''
    for item in inlist:
        if type(item) != str:
            item = str(item)
        outstr = outstr + item + delimiter
    outstr = outstr[0:-1]
    return outstr

#GM
def lineincols (inlist:List(Dyn),colsize:int)->str:
    """
Returns a string composed of elements in inlist, with each element
right-aligned in columns of (fixed) colsize.

Usage:   lineincols (inlist,colsize)   where colsize is an integer
"""
    outstr = ''
    for item in inlist:
        if type(item) != str:
            item = str(item)
        size = len(item)
        if size <= colsize:
            for i in range(colsize-size):
                outstr = outstr + ' '
            outstr = outstr + item
        else:
            outstr = outstr + item[0:colsize+1]
    return outstr

#GM
def lineincustcols (inlist:List(Dyn),colsizes:List(int))->str:
    """
Returns a string composed of elements in inlist, with each element
right-aligned in a column of width specified by a sequence colsizes.  The
length of colsizes must be greater than or equal to the number of columns
in inlist.

Usage:   lineincustcols (inlist,colsizes)
Returns: formatted string created from inlist
"""
    outstr = ''
    for i in range(len(inlist)):
        if type(inlist[i]) != str:
            item = str(inlist[i])
        else:
            item = inlist[i]
        size = len(item)
        if size <= colsizes[i]:
            for j in range(colsizes[i]-size):
                outstr = outstr + ' '
            outstr = outstr + item
        else:
            outstr = outstr + item[0:colsizes[i]+1]
    return outstr

#GY
def list2string (inlist,delimit=' ')->str:
    """
Converts a 1D list to a single long string for file output, using
the string.join function.

Usage:   list2string (inlist,delimit=' ')
Returns: the string created from inlist
"""
    stringlist = list(map(makestr,inlist))
    return string.join(stringlist,delimit)

#GY
def makelol(inlist:List(Dyn))->List(List(Dyn)):
    """
Converts a 1D list to a 2D list (i.e., a list-of-lists).  Useful when you
want to use put() to write a 1D list one item per line in the file.

Usage:   makelol(inlist)
Returns: if l = [1,2,'hi'] then returns [[1],[2],['hi']] etc.
"""
    x = []
    for item in inlist:
        x.append([item])
    return x

#GX
def makestr (x)->str:
    if type(x) != str:
        x = str(x)
    return x

#GN
def printcc (lst,extra=2):
    """
Prints a list of lists in columns, customized by the max size of items
within the columns (max size of items in col, plus 'extra' number of spaces).
Use 'dashes' or '\\n' in the list-of-lists to print dashes or blank lines,
respectively.

Usage:   printcc (lst,extra=2)
Returns: None
"""
    if type(lst[0]) not in [list,tuple]:
        lst = [lst]
    rowstokill = []
    list2print = copy.deepcopy(lst)
    for i in range(len(lst)):
        if lst[i] == ['\n'] or lst[i]=='\n' or lst[i]=='dashes' or lst[i]=='' or lst[i]==['']:
            rowstokill = rowstokill + [i]
    rowstokill.reverse()   # delete blank rows from the end
    for row in rowstokill:
        del list2print[row]
    maxsize = [0]*len(list2print[0])
    for col in range(len(list2print[0])):
        items = colex(list2print,col)
        items = list(map(makestr,items))
        maxsize[col] = max(list(map(len,items))) + extra
    for row in lst:
        if row == ['\n'] or row == '\n' or row == '' or row == ['']:
            print()
        elif row == ['dashes'] or row == 'dashes':
            dashes = dyn([0]*len(maxsize))
            for j in range(len(maxsize)):
                dashes[j] = '-'*(maxsize[j]-2)
            print(lineincustcols(dashes,maxsize))
        else:
            print(lineincustcols(row,maxsize))
    return None

#GM
def printincols (listoflists:List(List(Dyn)),colsize:int):
    """
Prints a list of lists in columns of (fixed) colsize width, where
colsize is an integer.

Usage:   printincols (listoflists,colsize)
Returns: None
"""
    for row in listoflists:
        print(lineincols(row,colsize))
    return None

#GY
def pl (listoflists:List(List(Dyn))):
    """
Prints a list of lists, 1 list (row) at a time.

Usage:   pl(listoflists)
Returns: None
"""
    for row in listoflists:
        if row[-1] == '\n':
            print(row, end=' ')
        else:
            print(row)
    return None

#GX
def printl(listoflists:List(List(Dyn))):
    """Alias for pl."""
    pl(listoflists)
    return

#GY
def replace (inlst:List(Dyn),oldval,newval)->List(Dyn):
    """
Replaces all occurrences of 'oldval' with 'newval', recursively.

Usage:   replace (inlst,oldval,newval)
"""
    lst = inlst*1
    for i in range(len(lst)):
        if type(lst[i]) not in [list,tuple]:
            if lst[i]==oldval: lst[i]=newval
        else:
            lst[i] = replace(lst[i],oldval,newval)
    return lst

#GM
def recode (inlist,listmap,cols=None)->List(Dyn):
    """
Changes the values in a list to a new set of values (useful when
you need to recode data from (e.g.) strings to numbers.  cols defaults
to None (meaning all columns are recoded).

Usage:   recode (inlist,listmap,cols=None)  cols=recode cols, listmap=2D list
Returns: inlist with the appropriate values replaced with new ones
"""
    lst = copy.deepcopy(inlist)
    if cols != None:
        if type(cols) not in [list,tuple]:
            cols = [cols]
        for col in cols:
            for row in range(len(lst)):
                try:
                    idx = colex(listmap,0).index(lst[row][col])
                    lst[row][col] = listmap[idx][1]
                except ValueError:
                    pass
    else:
        for row in range(len(lst)):
            for col in range(len(lst)):
                try:
                    idx = colex(listmap,0).index(lst[row][col])
                    lst[row][col] = listmap[idx][1]
                except ValueError:
                    pass
    return lst

#GN
def remap (listoflists:List(List(Dyn)),criterion:str)->List(Dyn):
    """
Remaps values in a given column of a 2D list (listoflists).  This requires
a criterion as a function of 'x' so that the result of the following is
returned ... map(lambda x: 'criterion',listoflists).  

Usage:   remap(listoflists,criterion)    criterion=string
Returns: remapped version of listoflists
"""
    function = 'map(lambda x: '+criterion+',listoflists)'
    lines = eval(function)
    return lines

#GN
def roundlist (inlist:List(Dyn),digits:int)->List(Dyn):
    """
Goes through each element in a 1D or 2D inlist, and applies the following
function to all elements of FloatType ... round(element,digits).

Usage:   roundlist(inlist,digits)
Returns: list with rounded floats
"""
    if type(inlist[0]) in [int, float]:
        inlist = [inlist]
    l = inlist*1
    for i in range(len(l)):
        for j in range(len(l[i])):
            if type(l[i][j])==float:
                l[i][j] = round(l[i][j],digits)
    return l

#GN
def sortby(listoflists:List(List(Dyn)),sortcols:List(Dyn))->List(List(Dyn)):
    """
Sorts a list of lists on the column(s) specified in the sequence
sortcols.

Usage:   sortby(listoflists,sortcols)
Returns: sorted list, unchanged column ordering
"""
    newlist = abut(colex(listoflists,sortcols),listoflists)
    newlist.sort()
    try:
        numcols = len(sortcols)
    except TypeError:
        numcols = 1
    crit = '[' + str(numcols) + ':]'
    newlist = colex(newlist,crit)
    return newlist

#GY
def unique (inlist:List(Dyn))->List(Dyn):
    """
Returns all unique items in the passed list.  If the a list-of-lists
is passed, unique LISTS are found (i.e., items in the first dimension are
compared).

Usage:   unique (inlist)
Returns: the unique elements (or rows) in inlist
"""
    uniques = []
    for item in inlist:
        if item not in uniques:
            uniques.append(item)
    return uniques

#GY
def duplicates(inlist:List(Dyn))->List(Dyn):
    """
Returns duplicate items in the FIRST dimension of the passed list.

Usage:   duplicates (inlist)
"""
    dups = []
    for i in range(len(inlist)):
        if inlist[i] in inlist[i+1:]:
            dups.append(inlist[i])
    return dups

#GY
def nonrepeats(inlist:List(Dyn))->List(Dyn):
    """
Returns items that are NOT duplicated in the first dim of the passed list.

Usage:   nonrepeats (inlist)
"""
    nonrepeat = []
    for i in range(len(inlist)):
        if inlist.count(inlist[i]) == 1:
            nonrepeat.append(inlist[i])
    return nonrepeat


#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
#===================   PSTAT ARRAY FUNCTIONS  =====================
