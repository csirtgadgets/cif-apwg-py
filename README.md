# [APWG](http://apwg.org) CIF Application

# Installation
## Ubuntu
  ```bash
  $ apt-get install -y python-dev python-pip git
  $ pip install git+https://github.com/csirtgadgets/py-cifapwg.git
  ```
  
# Examples
  ```bash
  $ export APWG_TOKEN="123412341234"
  $ cif-apwg -h
  $ cif-apwg -v --hours 12 --token $APWG_TOKEN
  ```

# License and Copyright

Copyright (C) 2015 [the CSIRT Gadgets Foundation](http://csirtgadgets.org)

Free use of this software is granted under the terms of the [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html) (LGPL v3.0). For details see the file ``LICENSE`` included with the distribution.
