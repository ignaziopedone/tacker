#!/bin/bash

echo "Achieving permissions"
source openrc admin
echo "Congratulations! Let's start!"

#configurazione gruppi di sicurezza permetti accesso ICMP SSH
project=$(openstack project list | awk '/ admin /{print $2}')
echo "Project admin ID: $project"

group_security_id=$(openstack security group list | awk '$10 == project {print $2}' project="$project")
echo "Security Group ID: $group_security_id"

echo "Applying changes to security group..."
openstack security group rule create --ingress --project admin --protocol ICMP --remote-ip 0.0.0.0/0 $group_security_id
openstack security group rule create --egress --project admin --protocol ICMP --remote-ip 0.0.0.0/0 $group_security_id
openstack security group rule create --project admin --protocol tcp --dst-port 22:22  --remote-ip 0.0.0.0/0 $group_security_id
echo "Applying changes to security group done!"


#create network
echo "Network Creation..."
openstack network create mgmt --provider-network-type=vlan --provider-physical-network=public --provider-segment=500 --share
openstack subnet create subnet-mgmt --subnet-range 10.208.0.0/24 --dhcp --ip-version 4 --allocation-pool start=10.208.0.2,end=10.208.0.100 --gateway 10.208.0.1 --dns-nameserver 8.8.8.8 --network mgmt

openstack network create data --provider-network-type=local --share --external
openstack subnet create subnet-data --subnet-range 10.208.1.0/24 --dhcp --ip-version 4 --allocation-pool start=10.208.1.2,end=10.208.1.100 --gateway 10.208.1.1 --dns-nameserver 8.8.8.8 --network data

openstack network create link_1 --provider-network-type=local --share
openstack subnet create a --subnet-range 11.11.11.0/24 --dhcp --ip-version 4 --allocation-pool start=11.11.11.2,end=11.11.11.100 --network link_1 --gateway none

openstack network create link_2 --provider-network-type=local --share
openstack subnet create b --subnet-range 22.22.22.0/24 --dhcp --ip-version 4 --allocation-pool start=22.22.22.2,end=22.22.22.100 --network link_2 --gateway none

openstack network create link_3 --provider-network-type=local --share
openstack subnet create c --subnet-range 33.33.33.0/24 --dhcp --ip-version 4 --allocation-pool start=33.33.33.2,end=33.33.33.100 --network link_3 --gateway none

openstack network create link_4 --provider-network-type=local --share
openstack subnet create d --subnet-range 44.44.44.0/24 --dhcp --ip-version 4 --allocation-pool start=44.44.44.2,end=44.44.44.100 --network link_4 --gateway none

openstack network create link_5 --provider-network-type=local --share
openstack subnet create e --subnet-range 55.55.55.0/24 --dhcp --ip-version 4 --allocation-pool start=55.55.55.2,end=55.55.55.100 --network link_5 --gateway none
echo "Network Creation done!"

#disable port-security
echo "Disabling port-security on some target networks..."
openstack network set link_1 --disable-port-security
openstack network set link_2 --disable-port-security
openstack network set link_3 --disable-port-security
openstack network set link_4 --disable-port-security
openstack network set link_5 --disable-port-security
openstack network set data --disable-port-security
echo "Port security disabled!"

echo "Creating router..."
#create router
openstack router create router --project admin
openstack router set router --external-gateway public --enable-snat
openstack router add subnet router subnet-mgmt
openstack router add subnet router subnet-data
echo "Router creation done!"

#upload image
echo "Uploading images..."
#Insert here some image.qcow2 path in order to load them in glance
echo "Images uploaded!"

echo "Change the last row in OpenstackConf.sh with the address or router given..."
router=$(openstack router show router | awk '/external_gateway_info/{print $12}')
echo "The router address is: $router"
