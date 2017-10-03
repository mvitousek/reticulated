#from retic.typing import *

#! /usr/bin/env python3

"""
"PYSTONE" Benchmark Program

Version:        Python/1.1 (corresponds to C/1.1 plus 2 Pystone fixes)

Author:         Reinhold P. Weicker,  CACM Vol 27, No 10, 10/84 pg. 1013.

                Translated from ADA to C by Rick Richardson.
                Every method to preserve ADA-likeness has been used,
                at the expense of C-ness.

                Translated from C to Python by Guido van Rossum.

Version History:

                Version 1.1 corrects two bugs in version 1.0:

                First, it leaked memory: in Proc1(), NextPSRecord ends
                up having a pointer to itself.  I have corrected this
                by zapping NextPSRecord.PtrComp at the end of Proc1().

                Second, Proc3() used the operator != to compare a
                record to None.  This is rather inefficient and not
                true to the intention of the original benchmark (where
                a pointer comparison to None is intended; the !=
                operator attempts to find a method __cmp__ to do value
                comparison of the record).  Version 1.1 runs 5-10
                percent faster than version 1.0, so benchmark figures
                of different versions can't be compared directly.

"""

LOOPS = 5000000

from time import clock

__version__ = "1.1"

Ident1 = 1
Ident2 = 2
Ident3 = 3
Ident4 = 4
Ident5 = 5
Ident6 = 6

@fields({'StringComp': str, 'IntComp' : int, 'Discr' : int, 'EnumComp' : int, 'PtrComp': PSRecord})
class PSRecord:

    def __init__(self:PSRecord, PtrComp:PSRecord = None, Discr:int = 0, EnumComp:int = 0,
                       IntComp:int = 0, StringComp:str = ''):
        self.PtrComp = PtrComp
        self.Discr = Discr
        self.EnumComp = EnumComp
        self.IntComp = IntComp
        self.StringComp = StringComp

    def copy(self:PSRecord)->PSRecord:
        return PSRecord(self.PtrComp, self.Discr, self.EnumComp,
                      self.IntComp, self.StringComp)

TRUE = 1
FALSE = 0

def main(loops:int=LOOPS)->None:
    benchtime, stones = pystones(loops)
    print("Pystone(%s) time for %d passes = %g" % \
          (__version__, loops, benchtime))
    print("This machine benchmarks at %g pystones/second" % stones)


def pystones(loops:int=LOOPS)->(float, float):
    return Proc0(loops)

IntGlob = 0
BoolGlob = FALSE
Char1Glob = '\0'
Char2Glob = '\0'
Array1Glob = [0]*51
Array2Glob = [x[:] for x in [Array1Glob]*51]
PtrGlb = PSRecord()
PtrGlbNext = PSRecord()

def Proc0(loops:int=LOOPS)->(float,float):
    global IntGlob
    global BoolGlob
    global Char1Glob
    global Char2Glob
    global Array1Glob
    global Array2Glob
    global PtrGlb
    global PtrGlbNext

    starttime = clock()
    for i in range(loops):
        pass
    nulltime = clock() - starttime

    PtrGlbNext = PSRecord()
    PtrGlb = PSRecord()
    PtrGlb.PtrComp = PtrGlbNext
    PtrGlb.Discr = Ident1
    PtrGlb.EnumComp = Ident3
    PtrGlb.IntComp = 40
    PtrGlb.StringComp = "DHRYSTONE PROGRAM, SOME STRING"
    String1Loc = "DHRYSTONE PROGRAM, 1'ST STRING"
    Array2Glob[8][7] = 10

    starttime = clock()

    for i in range(loops):
        Proc5()
        Proc4()
        IntLoc1 = 2
        IntLoc2 = 3
        String2Loc = "DHRYSTONE PROGRAM, 2'ND STRING"
        EnumLoc = Ident2
        BoolGlob = not Func2(String1Loc, String2Loc)
        while IntLoc1 < IntLoc2:
            IntLoc3 = 5 * IntLoc1 - IntLoc2
            IntLoc3 = Proc7(IntLoc1, IntLoc2)
            IntLoc1 = IntLoc1 + 1
        Proc8(Array1Glob, Array2Glob, IntLoc1, IntLoc3)
        PtrGlb = Proc1(PtrGlb)
        CharIndex = 'A'
        while CharIndex <= Char2Glob:
            if EnumLoc == Func1(CharIndex, 'C'):
                EnumLoc = Proc6(Ident1)
            CharIndex = chr(ord(CharIndex)+1)
        IntLoc3 = IntLoc2 * IntLoc1
        IntLoc2 = IntLoc3 // IntLoc1
        IntLoc2 = 7 * (IntLoc3 - IntLoc2) - IntLoc1
        IntLoc1 = Proc2(IntLoc1)

    benchtime = clock() - starttime - nulltime
    if benchtime == 0.0:
        loopsPerBenchtime = 0.0
    else:
        loopsPerBenchtime = (loops / benchtime)
    return benchtime, loopsPerBenchtime

def Proc1(PtrParIn : PSRecord) -> PSRecord:
    PtrParIn.PtrComp = NextPSRecord = PtrGlb.copy()
    PtrParIn.IntComp = 5
    NextPSRecord.IntComp = PtrParIn.IntComp
    NextPSRecord.PtrComp = PtrParIn.PtrComp
    NextPSRecord.PtrComp = Proc3(NextPSRecord.PtrComp)
    if NextPSRecord.Discr == Ident1:
        NextPSRecord.IntComp = 6
        NextPSRecord.EnumComp = Proc6(PtrParIn.EnumComp)
        NextPSRecord.PtrComp = PtrGlb.PtrComp
        NextPSRecord.IntComp = Proc7(NextPSRecord.IntComp, 10)
    else:
        PtrParIn = NextPSRecord.copy()
    NextPSRecord.PtrComp = None
    return PtrParIn

def Proc2(IntParIO:int)->int:
    IntLoc = IntParIO + 10
    while 1:
        if Char1Glob == 'A':
            IntLoc = IntLoc - 1
            IntParIO = IntLoc - IntGlob
            EnumLoc = Ident1
        if EnumLoc == Ident1:
            break
    return IntParIO

def Proc3(PtrParOut:PSRecord)->PSRecord:
    global IntGlob

    if PtrGlb is not None:
        PtrParOut = PtrGlb.PtrComp
    else:
        IntGlob = 100
    PtrGlb.IntComp = Proc7(10, IntGlob)
    return PtrParOut

def Proc4()->None:
    global Char2Glob

    BoolLoc = Char1Glob == 'A'
    BoolLoc = BoolLoc or BoolGlob
    Char2Glob = 'B'

def Proc5()->None:
    global Char1Glob
    global BoolGlob

    Char1Glob = 'A'
    BoolGlob = FALSE

def Proc6(EnumParIn:int)->int:
    EnumParOut = EnumParIn
    if not Func3(EnumParIn):
        EnumParOut = Ident4
    if EnumParIn == Ident1:
        EnumParOut = Ident1
    elif EnumParIn == Ident2:
        if IntGlob > 100:
            EnumParOut = Ident1
        else:
            EnumParOut = Ident4
    elif EnumParIn == Ident3:
        EnumParOut = Ident2
    elif EnumParIn == Ident4:
        pass
    elif EnumParIn == Ident5:
        EnumParOut = Ident3
    return EnumParOut

def Proc7(IntParI1:int, IntParI2:int)->int:
    IntLoc = IntParI1 + 2
    IntParOut = IntParI2 + IntLoc
    return IntParOut

def Proc8(Array1Par:List(int), Array2Par:List(List(int)), IntParI1:int, IntParI2:int) -> None:
    global IntGlob

    IntLoc = IntParI1 + 5
    Array1Par[IntLoc] = IntParI2
    Array1Par[IntLoc+1] = Array1Par[IntLoc]
    Array1Par[IntLoc+30] = IntLoc
    for IntIndex in range(IntLoc, IntLoc+2):
        Array2Par[IntLoc][IntIndex] = IntLoc
    Array2Par[IntLoc][IntLoc-1] = Array2Par[IntLoc][IntLoc-1] + 1
    Array2Par[IntLoc+20][IntLoc] = Array1Par[IntLoc]
    IntGlob = 5

def Func1(CharPar1:str, CharPar2:str)->int:
    CharLoc1 = CharPar1
    CharLoc2 = CharLoc1
    if CharLoc2 != CharPar2:
        return Ident1
    else:
        return Ident2

def Func2(StrParI1:str, StrParI2:str)->int:
    IntLoc = 1
    while IntLoc <= 1:
        if Func1(StrParI1[IntLoc], StrParI2[IntLoc+1]) == Ident1:
            CharLoc = 'A'
            IntLoc = IntLoc + 1
    if CharLoc >= 'W' and CharLoc <= 'Z':
        IntLoc = 7
    if CharLoc == 'X':
        return TRUE
    else:
        if StrParI1 > StrParI2:
            IntLoc = IntLoc + 7
            return TRUE
        else:
            return FALSE

def Func3(EnumParIn:int)->int:
    EnumLoc = EnumParIn
    if EnumLoc == Ident3: return TRUE
    return FALSE

if __name__ == '__main__':
    import sys
    def error(msg:str)->None:
        print(msg, end=' ', file=sys.stderr)
        print("usage: %s [number_of_loops]" % sys.argv[0], file=sys.stderr)
        sys.exit(100)
    nargs = len(sys.argv) - 1
    if nargs > 1:
        error("%d arguments are too many;" % nargs)
    elif nargs == 1:
        try: loops = LOOPS
        except ValueError:
            error("Invalid argument %r;" % sys.argv[1])
    else:
        loops = LOOPS
    main(loops)
