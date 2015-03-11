#!/bin/bash
source /etc/environment

source $allproxy_path/config/config.sh #&

echo "setting default gateway to " $nproxy_gateway

sudo ip route add to 202.141.80.0/23 via $nproxy_gateway

def_gate=$(/sbin/ip route | awk '/default/ { print $3 }')
if [ ! "$def_gate" == "$nproxy_gateway" ]
then
	if [ -e /usr/bin/zenity ]; then		

		OUTPUT=$(zenity --forms --title="Allproxy" --text="Proxy Settings" --separator=","  \
		   --add-entry="Proxy Gateway" )

		accepted=$?
		if [ ! "$accepted" -eq "0" ]; then
			echo "Tproxy aborted !!"
		    exit 1
		else
			tproxy_gateway=$(echo $OUTPUT | awk -F, '{print $1}')

			sudo ip route del default
			sudo ip route add default via $tproxy_gateway
		fi

		

	fi
	
fi