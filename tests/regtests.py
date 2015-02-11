#!/usr/bin/env python3

import os, sys, io
import subprocess

pyfiles = {}
trfiles = {}

passed = 0
tests = 0

print('Starting regression tests.')

try:
    pyfiles = {f[:-3]: f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py')}
    trfiles = {f[:-4]: open(f, 'r') for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.trx')}
 
   
    for file in sorted(pyfiles):
        if file in trfiles:
            exc = False

            print('Reticulating {}'.format(file))
            try: 
                result = subprocess.check_output(['retic', pyfiles[file]], 
                                                 stderr=subprocess.STDOUT).decode('utf-8').strip()
            except Exception as e:
                exc = e.output.decode('utf-8').strip()
                human_exc = '...\n' + exc[exc.rfind('File "'):]

            expected = trfiles[file].read().strip()

            if exc:
                success = expected.startswith('EXCEPTION') and \
                          (exc.find(expected[len('EXCEPTION'):].strip()) >= 0)
                message = 'Unexpected exception raised:\n{}\nWas expecting\n{}'.format(human_exc, 
                                                                                        expected)
            elif expected.startswith('SEARCH'):
                success = (result.find(expected[len('SEARCH'):].strip()) >= 0)
                message = 'Unexpected output:\n{}\nDoes not contain\n{}'.format(result, expected[len('SEARCH'):].strip())
            else:
                success = result == expected
                message = 'Unexpected output:\n{}\n=/=\n{}'.format(result, expected)
            
            tests += 1
            if success:
                passed += 1
            else:
                print('Failure reticulating {}:\n   {}'.format(file, message))

    print('{}/{} tests passed'.format(passed, tests))

finally:
    for file in trfiles:
        trfiles[file].close()
