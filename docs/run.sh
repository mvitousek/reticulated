#!/bin/bash

markdown tutorial.md > tutorial.html
xdg-open tutorial.html
sleep 3
rm tutorial.html
