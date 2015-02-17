#!/usr/bin/env retic
import math

# A class representing two dimensional points, with
# the x and y coordinates as fields.
class Point2D(object):
  def __init__(self, x, y):
    self.x = x
    self.y = y
  def distance(self, other):
    return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

