#!/usr/bin/env python

import os
import sys

def do_work():
  walk_path = sys.argv[1]
  for path, dirs, files in os.walk(walk_path):
    for ifile in files:
      html_path = os.path.join(path, ifile)
      fi = open(os.path.join(path, ifile), 'r')
      res = ' '.join([itm.strip() for itm in fi.readlines()])
      fi.close()
      print '%s\t%s' %(html_path, res)

if __name__ == '__main__':
  do_work()
