#!/bin/bash

# force bash
[ -z $BASH ] && { exec bash "$0" "$@" || exit; }

source /etc/environment
source $allproxy_path/config/config.sh

python main.py $1 $2 &

echo $! > $allproxy_path/pid/dproxy #&
