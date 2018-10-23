#!/bin/bash

sudo ip link set br-ex up
sudo ip route add 172.24.4.0/24 dev br-ex
sudo ip addr add 172.24.4.1/24 dev br-ex
sudo iptables -t nat -A POSTROUTING -o enp0s25 -j MASQUERADE #change the network interface
sudo route add -net 10.208.0.0/24 gw 172.24.4.4 #change this number with the router created by openstack script configuration
