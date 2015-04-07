#!/bin/bash

set -e

# this should go in your env...
#APWG_TOKEN="12341234"

/usr/local/bin/cif-apwg -v --apwg-token $APWG_TOKEN
