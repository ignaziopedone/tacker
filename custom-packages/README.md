# Let's start with VNFFGs and NSDs

We wanna show a first simple example of deploying of VNF forwarding graph. This deploy must contains 2 VNFs and other two support VMs (HTTP client/server).

The firsto operation is to clone the repository with the following command:

```bash
$ git clone https://github.com/ignaziopedone/tacker.git
```

N.B. We suppose you have already installed correctly openstack tacker with the instruction presented in the initial documentation page.

After this process we have to do two operations in order to create the right context in which we will deploy our instances. The latters operation are the following:

* we need to create a new `flavor` in openstack called `user` and with those features:

 * VCPUs : 1
 * RAM : 512 MB
 * Root Disk : 0 GB
 * Ephemeral Disk : 0 GB
 * Swap Disk : 0 GB
 * RX/TX factor : 3.0


* we need to update a `xenial ubuntu image (16.04 LTS)` in openstack glance as well, in order to use the smoothest configuration of the instances which we have provided.

After this very first set up we should start creating the real environment and setting up the instances for testing purpose. We start launching the following script:

```bash
$ cd tacker/custom-packages/tacker-config
$ ./ns-config.sh
```

As result the script should deploy the 2 instances and some other configurazion needed. After that we could start the VNFs and the NSD containing the right VNFFG:

```bash
$ cd ../vnffg-nsd

# Create the VNF descriptors
$ openstack vnf descriptor create --vnfd-file tosca-vnfd1-sample.yaml sample-vnfd1
$ openstack vnf descriptor create --vnfd-file tosca-vnfd2-sample.yaml sample-vnfd2

# Deploy the NSD with the VNFFG
$ openstack ns create --nsd-template tosca-multiple-vnffg-nsd.yaml --param-file ns_param.yaml NS2
```

Now let's wait some time (about 1 minute in order to have alla the machines and parameters well configured) and see what we have really done here. We can show this through the NSD descriptor reported here:

```yaml
tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0

description: Import VNFDs(already on-boarded) with input parameters
imports:
    - sample-vnfd1
    - sample-vnfd2

topology_template:
  inputs:
    vl1_name:
      type: string
      description: name of VL1 virtuallink
      default: net_mgmt
    vl2_name:
      type: string
      description: name of VL2 virtuallink
      default: net0
    net_src_port_id:
      type: string
      description: neutron port id of source port
    ip_dest_prefix:
      type: string
      description: IP prefix of destination port

  node_templates:
    VNF1:
      type: tosca.nodes.nfv.VNF1
      requirements:
        - virtualLink1: VL1

    VNF2:
      type: tosca.nodes.nfv.VNF2

    VL1:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: {get_input: vl1_name}
        vendor: tacker

    VL2:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: {get_input: vl2_name}
        vendor: tacker

    Forwarding_path1:
      type: tosca.nodes.nfv.FP.TackerV2
      description: creates path inside ns (src_port->CP12->CP22->dst_port)
      properties:
        id: 51
        symmetrical: true
        policy:
          type: ACL
          criteria:
            - name: block_tcp
              classifier:
                network_src_port_id: {get_input: net_src_port_id}
                destination_port_range: 80-1024
                ip_proto: 6
                ip_dst_prefix: {get_input: ip_dest_prefix}
        path:
          - forwarder: sample-vnfd1
            capability: CP12
          - forwarder: sample-vnfd2
            capability: CP22

    Forwarding_path2:
      type: tosca.nodes.nfv.FP.TackerV2
      description: creates path inside ns (src_port->CP12->CP22->dst_port)
      properties:
        id: 52
        symmetrical: false
        policy:
          type: ACL
          criteria:
            - name: block_tcp
              classifier:
                network_src_port_id: {get_input: net_src_port_id}
                destination_port_range: 8080-8080
                ip_proto: 6
                ip_dst_prefix: {get_input: ip_dest_prefix}
        path:
          - forwarder: sample-vnfd1
            capability: CP12

  groups:

    VNFFG1:
      type: tosca.groups.nfv.VNFFG
      description: HTTP to Corporate Net
      properties:
        vendor: tacker
        version: 1.0
        number_of_endpoints: 2
        dependent_virtual_link: [VL1, VL2]
        connection_point: [CP12, CP22]
        constituent_vnfs: [sample-vnfd1, sample-vnfd2]
      members: [Forwarding_path1]

    VNFFG2:
      type: tosca.groups.nfv.VNFFG
      description: HTTP to Corporate Net
      properties:
        vendor: tacker
        version: 1.0
        number_of_endpoints: 1
        dependent_virtual_link: [VL1]
        connection_point: [CP12]
        constituent_vnfs: [sample-vnfd1]
      members: [Forwarding_path2]
```

First of all we had a `ns-param.yaml` in which are shown the src,dst (HTTP client/server) details. As shown in the scriptor then we create a situation as the one following:

```
                       +------------+        +------------+
                       |    VNF1    |        |    VNF2    |
                       |            |        |            |
                       |    CP12    |        |    CP22    |
                       +--^-+---^-+-+        +----^--+----+
                          | |   | |               |  |
                          | |   | |               |  |
+-------------+ VNFFG1    | |   | |               |  |               +-------------+
|             +-----------+ +---------------------+  +--------------->             |
| http_client |                 | |                                  | http_server |
|             +-----------------+ +---------------------------------->             |
+-------------+ VNFFG2                                               +-------------+

```

Basically we want to forwardi with two different paths the traffic from an HTTP client to an HTTP server. The First path carries the `tcp` traffic with destination port `8080`. The second one carries the `tcp` traffic with destination port in the range `80-1024`. Of course they share the same destination IP. The traffic classification is performed by a common component in a NFV/SDN evironment called `classifier`. As we could notice in the test we have a classifier per VNFFG, this means that it exists a VNFFG, a forwarding path and a classifier for every single traffic path that we want to model and implement. Conceptually a classifier is a software module, in a pratical way it's a simply set of OVS rules enforced on the openstack Open vSwitch through a set of API given by openstack. The first path pass through only the first VNF, while the second one pass through both the VNF.

Now we can test with some openstack command the successful deploy of the scenario:

```bash
$ openstack ns list --fit-width
$ openstack vnf graph list --fit-width
$ openstack vnf list --fit-width
$ openstack vnf network forwarding path list
$ openstack sfc port chain list --fit-width
```

We can now test the traffic flow simply in the client with some `wget` or `ns` using as a target the HTTP server, of course monitoring the iface of the VNFs and the server. We could also block some traffic in one or both the VNFs and see that actually the latter doesn't reach the server.

In order to clean all the environment we can use the following command:
```bash
$ ./ns-clean.sh
```
