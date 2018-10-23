# Tacker installation via devstack
In order to install properly all the components of openstack (basic services + nfv servicies) we have to follow the procedure reported below.

To start we should install an Ubuntu 16.04 LTS instance on a physical host or a VM. We could use the following link to download the iso [(download)](https://www.ubuntu-it.org/download).

After that we could start clean and to begin with we could install git on the host/VM with ubuntu installed.

```bash
$ sudo apt install git
```

In order to avoid problem with the other user, we could create another user to separate the scope of openstack:

```bash
$ sudo useradd -s /bin/bash -d /opt/stack -m stack
```

Since this user will be making many changes to your system, it should have sudo privileges:

```bash
$ echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/stack
$ sudo su - stack
```

Now we must clone the appropriate repository of devstack (pay attention to the branch desired, we suggest "stable/queens"):

```bash
$ git clone https://git.openstack.org/openstack-dev/devstack -b <branch-name>
$ cd devstack
```

Since we want to recreate the whole openstack environment and also add tacker as service we can follow this procedure to automate the process. To begin with we have to create a file `local.conf` in the `devstack` folder. The latter is the main responsible of configuring the openstack deployment. We give a precise example of how have to be written down this configuration file:

```yaml

[[local|localrc]]
############################################################
# Customize the following HOST_IP based on your installation
############################################################
HOST_IP=127.0.0.1

ADMIN_PASSWORD=devstack
MYSQL_PASSWORD=devstack
RABBIT_PASSWORD=devstack
SERVICE_PASSWORD=$ADMIN_PASSWORD
SERVICE_TOKEN=devstack

############################################################
# Customize the following section based on your installation
############################################################

# Pip
PIP_USE_MIRRORS=False
USE_GET_PIP=1

#OFFLINE=False
#RECLONE=True

# Logging
LOGFILE=$DEST/logs/stack.sh.log
VERBOSE=True
ENABLE_DEBUG_LOG_LEVEL=True
ENABLE_VERBOSE_LOG_LEVEL=True

# Neutron ML2 with OpenVSwitch
Q_PLUGIN=ml2
Q_AGENT=openvswitch

# Disable security groups
Q_USE_SECGROUP=False
LIBVIRT_FIREWALL_DRIVER=nova.virt.firewall.NoopFirewallDriver

# Enable heat, networking-sfc, barbican and mistral
enable_plugin heat https://git.openstack.org/openstack/heat master
enable_plugin networking-sfc git://git.openstack.org/openstack/networking-sfc master
enable_plugin barbican https://git.openstack.org/openstack/barbican master
enable_plugin mistral https://git.openstack.org/openstack/mistral master

# Ceilometer
#CEILOMETER_PIPELINE_INTERVAL=300
enable_plugin ceilometer https://git.openstack.org/openstack/ceilometer master
enable_plugin aodh https://git.openstack.org/openstack/aodh master

# Tacker
enable_plugin tacker https://git.openstack.org/openstack/tacker master

enable_service n-novnc
enable_service n-cauth

disable_service tempest

# Enable Kubernetes and kuryr-kubernetes
#KUBERNETES_VIM=True
#NEUTRON_CREATE_INITIAL_NETWORKS=False
#enable_plugin kuryr-kubernetes https://git.openstack.org/openstack/kuryr-kubernetes master
#enable_plugin neutron-lbaas git://git.openstack.org/openstack/neutron-lbaas master
#enable_plugin devstack-plugin-container #https://git.openstack.org/openstack/devstack-plugin-container master

[[post-config|/etc/neutron/dhcp_agent.ini]]
[DEFAULT]
enable_isolated_metadata = True

```

N.B. We commented the part of kubernetes, involved in the container orchestration, because we want to dealing with VM for now. Basically we will use nova with KVM.

As is shown in the `local.conf` file the user will be `admin` and the password `devstack`, In order to reach the GUI (Horizon service) go to http://IP_HOST, where the `IP_HOST` was the one of the physical host or VM.

# Let's start with a VNF

## Register a VIM
In order to start every configuration and deploy the VNF the first step should be register a VIM (the actual openstack installed on the machine).
In order to doing this you must follow this command:

```bash
$ openstack vim register --config-file vim_config.yaml --description 'my first vim' --is-default hellovim
```

The `vim_config.yaml` should report these informations:

```json
auth_url: 'https://10.1.0.5:5000'
username: 'nfv_user'
password: 'mySecretPW'
project_name: 'nfv'
project_domain_name: 'Default'
user_domain_name: 'Default'

# cert_verify: 'True' This line is optional
```

## VNF Descriptor (VNFD)

In order to create a vnf instance we have to define its descriptor first. Openstack tacker have, as usual for a openstack service, a simple cli and we will show below how to use it. To begin with we could define a simple vnf descriptor (in TOSCA language) `example.yaml`:

```yaml
tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0

description: Demo example

metadata:
  template_name: sample-tosca-vnfd

topology_template:
  node_templates:
    VDU1:
      type: tosca.nodes.nfv.VDU.Tacker
      capabilities:
        nfv_compute:
          properties:
            num_cpus: 1
            mem_size: 512 MB
            disk_size: 3 GB
      properties:
        image: ubuntu
        availability_zone: nova
        mgmt_driver: noop
        user_data_format: RAW
        user_data: |
          #!/bin/sh
          cat << EOF >> /etc/network/interfaces
          auto ens4
          iface ens4 inet dhcp
          auto ens5
          iface ens5 inet dhcp
          EOF
          ifup ens4
          ifup ens5
        config: |
          param0: key1
          param1: key2
        monitoring_policy:
          name: ping
          parameters:
            monitoring_delay: 45
            count: 3
            interval: 1
            timeout: 2
          actions:
            failure: respawn

    CP1:
      type: tosca.nodes.nfv.CP.Tacker
      properties:
        management: true
        order: 0
        anti_spoofing_protection: false
      requirements:
        - virtualLink:
            node: VL1
        - virtualBinding:
            node: VDU1

    CP2:
      type: tosca.nodes.nfv.CP.Tacker
      properties:
        order: 1
        anti_spoofing_protection: false
      requirements:
        - virtualLink:
            node: VL2
        - virtualBinding:
            node: VDU1

    CP3:
      type: tosca.nodes.nfv.CP.Tacker
      properties:
        order: 2
        anti_spoofing_protection: false
      requirements:
        - virtualLink:
            node: VL3
        - virtualBinding:
            node: VDU1

    VL1:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: net_mgmt
        vendor: Tacker

    VL2:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: net0
        vendor: Tacker

    VL3:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: net1
        vendor: Tacker

```

We basically describe in the descriptor how have to be the flavour of the VM containing the VNF, the intefaces and the software image used with the related configuration. We assume that the concepts of Virtual Deployment Unit (VDU), Connection Point (CP) and Virtual Link (VL) are best known. For other documentation we remind to [(Deploying a simple VNF with Tacker)](https://docs.openstack.org/tacker/latest/install/deploy_openwrt.html).

## Create a VNFD and deploy your first instance

In the previous section we show how a VNFD have to be. Now we will focus our attention to how create an openstack tracker descriptor and how to deploy a VNF.

In order to create a VNFD:

```bash
$ openstack vnf descriptor create --vnfd-file example.yaml cloud-vnfd
```

We use for this example a cloud-image of ubuntu xenial. __You should install this image before on your VIM__.

In order to create a simple VNF:

```bash
$ openstack vnf create --vnfd-name cloud-vnfd test-vnf
```

__The latter command DEPLOY your first VNF!__.

If you have some specific configuration to do, you can use an external configuration file as in the example below. __This example concerns another VNF__:

```bash
openstack vnf create --vnfd-name firewall --config-file tosca-config-openwrt-firewall.yaml config-firewall
```

Below there is an example of `tosca-config-openwrt.yaml` file:

```yaml
vdus:
  VDU1:
    config:
      firewall: |
        package firewall

        config defaults
            option syn_flood '1'
            option input 'ACCEPT'
            option output 'ACCEPT'
            option forward 'REJECT'

        config zone
            option name 'lan'
            list network 'lan'
            option input 'ACCEPT'
            option output 'ACCEPT'
            option forward 'ACCEPT'

        config zone
            option name 'wan'
            list network 'wan'
            list network 'wan6'
            option input 'REJECT'
            option output 'ACCEPT'
            option forward 'REJECT'
            option masq '1'
            option mtu_fix '1'

        config forwarding
            option src 'lan'
            option dest 'wan'

        config rule
            option name 'Allow-DHCP-Renew'
            option src 'wan'
            option proto 'udp'
            option dest_port '68'
            option target 'ACCEPT'
            option family 'ipv4'

        config rule
            option name 'Allow-Ping'
            option src 'wan'
            option proto 'icmp'
            option icmp_type 'echo-request'
            option family 'ipv4'
            option target 'ACCEPT'

        config rule
            option name 'Allow-IGMP'
            option src 'wan'
            option proto 'igmp'
            option family 'ipv4'
            option target 'ACCEPT'

        config rule
            option name 'Allow-DHCPv6'
            option src 'wan'
            option proto 'udp'
            option src_ip 'fe80::/10'
            option src_port '547'
            option dest_ip 'fe80::/10'
            option dest_port '546'
            option family 'ipv6'
            option target 'ACCEPT'

        config rule
            option name 'Allow-MLD'
            option src 'wan'
            option proto 'icmp'
            option src_ip 'fe80::/10'
            list icmp_type '130/0'
            list icmp_type '131/0'
            list icmp_type '132/0'
            list icmp_type '143/0'
            option family 'ipv6'
            option target 'ACCEPT'

        config rule
            option name 'Allow-ICMPv6-Input'
            option src 'wan'
            option proto 'icmp'
            list icmp_type 'echo-request'
            list icmp_type 'echo-reply'
            list icmp_type 'destination-unreachable'
            list icmp_type 'packet-too-big'
            list icmp_type 'time-exceeded'
            list icmp_type 'bad-header'
            list icmp_type 'unknown-header-type'
            list icmp_type 'router-solicitation'
            list icmp_type 'neighbour-solicitation'
            list icmp_type 'router-advertisement'
            list icmp_type 'neighbour-advertisement'
            option limit '190/sec'
            option family 'ipv6'
            option target 'REJECT'

```
__N.B. The last configuration file and the related descriptor (VNFD), not linked to the first example, is reported in the git repository [(Openstack tacker github)](https://github.com/openstack/tacker/tree/master/samples/tosca-templates)__.


# Troubleshooting

## Problem creating openstack volumes (Snapshot are your best friends!)

A typical problem in devstack deployment concerns volumes creation. In particular we should notice this behaviour, after the reboot of the host/VM in which devstack lies. There would be different solutions to the latter problem, but we use the simplest one, in order to simplify the other tasks. We should remind that our goal is to use openstack as test VIM not as a full function infrastracture. In order to solve this problem we instal openstack/devstack on a VM with kvm and immediately after the end of the installation process we made a snapshot of full working environment. We did this to simplify the VIM processing in a testing phase.

## Problem with the external connection of Devstack
Basically every VNF have a management interface (mgmt). In order to reach this interface for configuration purpose, we have to expose it and assure that it is reacheable from the controller/orchestrator network. More simply in our case we want to reach a vnf to control it. In devstack we have to activate the bridge for externatl connection, in order to give a floating IP to the mgmt interface. In our case we will assign a public ip (privider network).

```bash
# Set up the bridge
sudo ip link set br-ex up
# Set the route through the bridge
sudo ip route add 172.24.4.0/24 dev br-ex
# Assign an IP address to the bridge
sudo ip addr add 172.24.4.1/24 dev br-ex
```

Now basically we shoul assign a public address to the mgmt interface through the VNFD. There could be other problems as well, in that case we suggest to install another router and connect a public interface with them. All that in order to connect an entire mgmt network to the provider network. Some details are shown [(Openstack configuration)](https://github.com/ignaziopedone/network_sec_manager/tree/master/configurazione_openstack).

## Problem using noVNC
We could also solve the connectivity problem to the VM with the noVNC protocol. In order to solve eventually troubles due to the local installation (on 127.0.0.1) we can set up a ssh tunnel as shown below:

```bash
$ sudo ssh -f user_HOST_VM_devstack@HOST_VM_devstack -L 6080:127.0.0.1:6080 -N
```

## Problem with port security/ip-spoofing protection
We should consider the possibility to disable the port-security on the link directly from the descriptor as follows:

```bash
    CP1:
      type: tosca.nodes.nfv.CP.Tacker
      properties:
        order: 0
        anti_spoofing_protection: false  # <--- HERE
      requirements:
        - virtualLink:
            node: VL1
        - virtualBinding:
            node: VDU1
```


# A couple of interesting links to keep in mind
[(Openstack tacker github)](https://github.com/openstack/tacker): you can fid there all the samples and documentation about NFV orchestration through Openstack.

[(Devstack documentation)](https://docs.openstack.org/devstack/latest/).

[(Openstack tacker documentation)](https://docs.openstack.org/devstack/latest/).

[()]():

[()]():
