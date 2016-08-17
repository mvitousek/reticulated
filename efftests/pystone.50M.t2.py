from retic.opt_transient import *
from retic.typing import *
LOOPS = 50000000
from time import clock
__version__ = '1.1'
Ident1 = 1
Ident2 = 2
Ident3 = 3
Ident4 = 4
Ident5 = 5
Ident6 = 6


@fields({'StringComp': str, 'IntComp': int, 'Discr': int, 'EnumComp': int, 'PtrComp': Any, })
class PSRecord:

    def __init__(self, PtrComp=None, Discr=0, EnumComp=0, IntComp=0, StringComp=''):
        self.PtrComp = PtrComp
        self.Discr = Discr
        self.EnumComp = EnumComp
        self.IntComp = IntComp
        self.StringComp = StringComp

    def copy(self: 'PSRecord') ->'PSRecord':
        __retic_check_instance__(self, PSRecord)
        return __retic_check_instance__(PSRecord(self.PtrComp, __retic_check_int__(self.Discr), __retic_check_int__(self.EnumComp), __retic_check_int__(self.IntComp), __retic_check_str__(self.StringComp)), PSRecord)
TRUE = 1
FALSE = 0

def main(loops=LOOPS):
    (benchtime, stones) = pystones(loops)
    print(('Pystone(%s) time for %d passes = %g' % (__version__, loops, benchtime)))
    print(('This machine benchmarks at %g pystones/second' % stones))

def pystones(loops=LOOPS):
    return __retic_check_tuple__(Proc0(loops), 2)
IntGlob = 0
BoolGlob = FALSE
Char1Glob = '\x00'
Char2Glob = '\x00'
Array1Glob = __retic_check_list__(([0] * 51))
Array2Glob = [__retic_check_list__(__retic_check_list__(x)[:]) for x in ([Array1Glob] * 51)]
PtrGlb = __retic_check_instance__(__retic_check_instance__(PSRecord(), PSRecord), PSRecord)
PtrGlbNext = __retic_check_instance__(__retic_check_instance__(PSRecord(), PSRecord), PSRecord)

def Proc0(loops=LOOPS) ->(float, float):
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
    nulltime = (clock() - starttime)
    PtrGlbNext = __retic_check_instance__(__retic_check_instance__(PSRecord(), PSRecord), PSRecord)
    PtrGlb = __retic_check_instance__(__retic_check_instance__(PSRecord(), PSRecord), PSRecord)
    PtrGlb.PtrComp = PtrGlbNext
    PtrGlb.Discr = Ident1
    PtrGlb.EnumComp = Ident3
    PtrGlb.IntComp = 40
    PtrGlb.StringComp = 'DHRYSTONE PROGRAM, SOME STRING'
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
        BoolGlob = __retic_check_bool__((not __retic_check_int__(Func2(String1Loc, String2Loc))))
        while (IntLoc1 < IntLoc2):
            IntLoc3 = ((5 * IntLoc1) - IntLoc2)
            IntLoc3 = __retic_check_int__(Proc7(IntLoc1, IntLoc2))
            IntLoc1 = (IntLoc1 + 1)
        Proc8(Array1Glob, Array2Glob, IntLoc1, IntLoc3)
        PtrGlb = __retic_check_instance__(__retic_check_instance__(Proc1(PtrGlb), PSRecord), PSRecord)
        CharIndex = 'A'
        while (CharIndex <= Char2Glob):
            if (EnumLoc == __retic_check_int__(Func1(CharIndex, 'C'))):
                EnumLoc = __retic_check_int__(Proc6(Ident1))
            CharIndex = chr((ord(CharIndex) + 1))
        IntLoc3 = (IntLoc2 * IntLoc1)
        IntLoc2 = (IntLoc3 / IntLoc1)
        IntLoc2 = ((7 * (IntLoc3 - IntLoc2)) - IntLoc1)
        IntLoc1 = __retic_check_int__(Proc2(IntLoc1))
    benchtime = ((clock() - starttime) - nulltime)
    if (benchtime == 0.0):
        loopsPerBenchtime = 0.0
    else:
        loopsPerBenchtime = (loops / benchtime)
    return (benchtime, loopsPerBenchtime)

def Proc1(PtrParIn: PSRecord) ->PSRecord:
    __retic_check_instance__(PtrParIn, PSRecord)
    PtrParIn.PtrComp = NextPSRecord = __retic_check_instance__(__retic_check_callable__(PtrGlb.copy)(), PSRecord)
    PtrParIn.IntComp = 5
    NextPSRecord.IntComp = __retic_check_int__(PtrParIn.IntComp)
    NextPSRecord.PtrComp = PtrParIn.PtrComp
    NextPSRecord.PtrComp = __retic_check_instance__(Proc3(NextPSRecord.PtrComp), PSRecord)
    if (__retic_check_int__(NextPSRecord.Discr) == Ident1):
        NextPSRecord.IntComp = 6
        NextPSRecord.EnumComp = __retic_check_int__(Proc6(__retic_check_int__(PtrParIn.EnumComp)))
        NextPSRecord.PtrComp = PtrGlb.PtrComp
        NextPSRecord.IntComp = __retic_check_int__(Proc7(__retic_check_int__(NextPSRecord.IntComp), 10))
    else:
        PtrParIn = __retic_check_instance__(__retic_check_instance__(__retic_check_callable__(NextPSRecord.copy)(), PSRecord), PSRecord)
    NextPSRecord.PtrComp = None
    return PtrParIn

def Proc2(IntParIO: int) ->int:
    __retic_check_int__(IntParIO)
    IntLoc = __retic_check_int__((IntParIO + 10))
    while 1:
        if (Char1Glob == 'A'):
            IntLoc = __retic_check_int__((IntLoc - 1))
            IntParIO = __retic_check_int__((IntLoc - IntGlob))
            EnumLoc = Ident1
        if (EnumLoc == Ident1):
            break
    return IntParIO

def Proc3(PtrParOut: PSRecord) ->PSRecord:
    __retic_check_instance__(PtrParOut, PSRecord)
    global IntGlob
    if (PtrGlb is not None):
        PtrParOut = __retic_check_instance__(PtrGlb.PtrComp, PSRecord)
    else:
        IntGlob = 100
    PtrGlb.IntComp = __retic_check_int__(Proc7(10, IntGlob))
    return PtrParOut

def Proc4():
    global Char2Glob
    BoolLoc = (Char1Glob == 'A')
    BoolLoc = (BoolLoc or BoolGlob)
    Char2Glob = 'B'

def Proc5():
    global Char1Glob
    global BoolGlob
    Char1Glob = 'A'
    BoolGlob = FALSE

def Proc6(EnumParIn: int) ->int:
    __retic_check_int__(EnumParIn)
    EnumParOut = EnumParIn
    if (not __retic_check_int__(Func3(EnumParIn))):
        EnumParOut = Ident4
    if (EnumParIn == Ident1):
        EnumParOut = Ident1
    elif (EnumParIn == Ident2):
        if (IntGlob > 100):
            EnumParOut = Ident1
        else:
            EnumParOut = Ident4
    elif (EnumParIn == Ident3):
        EnumParOut = Ident2
    elif (EnumParIn == Ident4):
        pass
    elif (EnumParIn == Ident5):
        EnumParOut = Ident3
    return EnumParOut

def Proc7(IntParI1: int, IntParI2: int) ->int:
    __retic_check_int__(IntParI1)
    __retic_check_int__(IntParI2)
    IntLoc = __retic_check_int__((IntParI1 + 2))
    IntParOut = __retic_check_int__((IntParI2 + IntLoc))
    return IntParOut

def Proc8(Array1Par: List(int), Array2Par: List(List(int)), IntParI1: int, IntParI2: int):
    __retic_check_list__(Array1Par)
    __retic_check_list__(Array2Par)
    __retic_check_int__(IntParI1)
    __retic_check_int__(IntParI2)
    global IntGlob
    IntLoc = __retic_check_int__((IntParI1 + 5))
    Array1Par[IntLoc] = IntParI2
    Array1Par[(IntLoc + 1)] = __retic_check_int__(Array1Par[IntLoc])
    Array1Par[(IntLoc + 30)] = IntLoc
    for IntIndex in range(IntLoc, (IntLoc + 2)):
        Array2Par[IntLoc][IntIndex] = IntLoc
    Array2Par[IntLoc][(IntLoc - 1)] = (__retic_check_int__(__retic_check_list__(Array2Par[IntLoc])[(IntLoc - 1)]) + 1)
    Array2Par[(IntLoc + 20)][IntLoc] = __retic_check_int__(Array1Par[IntLoc])
    IntGlob = 5

def Func1(CharPar1: str, CharPar2: str) ->int:
    __retic_check_str__(CharPar1)
    __retic_check_str__(CharPar2)
    CharLoc1 = CharPar1
    CharLoc2 = CharLoc1
    if (CharLoc2 != CharPar2):
        return Ident1
    else:
        return Ident2

def Func2(StrParI1: str, StrParI2: str) ->int:
    __retic_check_str__(StrParI1)
    __retic_check_str__(StrParI2)
    IntLoc = 1
    while (IntLoc <= 1):
        if (__retic_check_int__(Func1(__retic_check_str__(StrParI1[IntLoc]), __retic_check_str__(StrParI2[(IntLoc + 1)]))) == Ident1):
            CharLoc = 'A'
            IntLoc = (IntLoc + 1)
    if ((CharLoc >= 'W') and (CharLoc <= 'Z')):
        IntLoc = 7
    if (CharLoc == 'X'):
        return TRUE
    elif (StrParI1 > StrParI2):
        IntLoc = (IntLoc + 7)
        return TRUE
    else:
        return FALSE

def Func3(EnumParIn: int) ->int:
    __retic_check_int__(EnumParIn)
    EnumLoc = EnumParIn
    if (EnumLoc == Ident3):
        return TRUE
    return FALSE
if (__name__ == '__main__'):
    import sys

    def error(msg):
        print(msg, end=' ', file=sys.stderr)
        print(('usage: %s [number_of_loops]' % sys.argv[0]), file=sys.stderr)
        sys.exit(100)
    nargs = (len(sys.argv) - 1)
    if (nargs > 1):
        error(('%d arguments are too many;' % nargs))
    elif (nargs == 1):
        try:
            loops = LOOPS
        except ValueError:
            error(('Invalid argument %r;' % sys.argv[1]))
    else:
        loops = LOOPS
    main(loops)
#    import cProfile
#    cProfile.run('main(loops)', 'stats')

