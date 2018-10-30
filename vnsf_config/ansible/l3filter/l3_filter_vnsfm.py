import subprocess
import logging
from subprocess import Popen, PIPE
# packets_list = "nmap"
# result = subprocess.call(["ansible-playbook", playbook, "--extra-vars", "ansible_sudo_pass=quantum packets={}".format(packets_list)])
# the format of extra_vars should be "ansible_sudo_pass=quantum packets={}".format(packets_list)
def exec_ansible_playbook(filename, extra_vars):
    try:
        print "[RUN] {} playbook".format(filename)
        result = subprocess.Popen(["ansible-playbook", filename, "--extra-vars", extra_vars], stdout=PIPE)
        output, err = result.communicate()
        logging.info(output)
    except Exception as e:
        print e


def set_policies_from_file(src_mspl, target_vnsf):
    try:
        exec_ansible_playbook("set_policies_from_file.yml", "target={} src_file={}".format(target_vnsf, src_mspl))
    except Exception as e:
        print e


def get_policies(target_vnsf):
    try:
        stdout = exec_ansible_playbook("get_policies.yml", "target={}".format(target_vnsf))
        return stdout
    except Exception as e:
        print e


if __name__ == '__main__':
    try:
        print "Start configuration!"
        logging.basicConfig(filename='action.log', filemode='a', level=logging.INFO)
        #set_policies_from_file("sample.mspl", "vnsf")
        get_policies("vnsf")
    except Exception as e:
        print e
