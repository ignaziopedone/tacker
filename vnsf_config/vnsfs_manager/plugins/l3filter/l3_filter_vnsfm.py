import subprocess
import logging
from subprocess import Popen, PIPE
import sys
# packets_list = "nmap"
# result = subprocess.call(["ansible-playbook", playbook, "--extra-vars", "ansible_sudo_pass=quantum packets={}".format(packets_list)])
# the format of extra_vars should be "ansible_sudo_pass=quantum packets={}".format(packets_list)


def exec_ansible_playbook(filename, extra_vars):
    try:
        print "[RUN] {} playbook".format(filename)
        result = subprocess.Popen(
            ["ansible-playbook", filename, "--extra-vars", extra_vars], stdout=PIPE)
        output, err = result.communicate()
        logging.info(output)
    except Exception as e:
        print e


def set_policies_from_file(src_mspl, target_vnsf):
    try:
        exec_ansible_playbook("playbooks/set_policies_from_file.yml",
                              "target={} src_file={}".format(target_vnsf, src_mspl))
    except Exception as e:
        print e


def get_policies(target_vnsf):
    try:
        exec_ansible_playbook("playbooks/get_policies.yml", "target={}".format(target_vnsf))
    except Exception as e:
        print e


def flush_policy(target_rule, target_vnsf):
    try:
        exec_ansible_playbook("playbooks/flush_policy.yml",
                              "target={} rule={}".format(target_vnsf, target_rule))
    except Exception as e:
        print e


def flush_policies(target_vnsf):
    try:
        exec_ansible_playbook("playbooks/flush_policies.yml", "target={}".format(target_vnsf))
    except Exception as e:
        print e

# In order to use the script you should use this format:
# python run.py <action_name> <target_vnsf> <additional_attributes>
# "set-policies": python run.py vnsf set-policies sample.mspl
# "get-policies": python run.py vnsf get-policies
# "delete-policy": python run.py vnsf delete-policy 1
# "delete-policies": python run.py vnsf delete-get_policies
# You could monitor the action result through the action.log


def main(argv):
    try:
        print "[INFO] Configuration Firewall started"
        logging.basicConfig(filename='action.log', filemode='a', level=logging.INFO)

        if argv[0] == "set-policies":
            set_policies_from_file(argv[2], argv[1])
        if argv[0] == "get-policies":
            get_policies(argv[1])
        if argv[0] == "delete-policy":
            flush_policy(argv[2], argv[1])
        if argv[0] == "delete-policies":
            flush_policies(argv[1])

    except Exception as e:
        print e


if __name__ == '__main__':
    main(sys.argv[1:])
