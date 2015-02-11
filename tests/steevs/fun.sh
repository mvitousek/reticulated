#!/bin/bash

for LINE in `cat Files.py`
do
  echo $LINE
  nohup python3 $RETIC $LINE > `echo $LINE | sed 's/\(.*\.\)py/\1tout/'`
  nohup python3 $RETIC $LINE > `echo $LINE | sed 's/\(.*\.\)py/\1gout/'`
done
