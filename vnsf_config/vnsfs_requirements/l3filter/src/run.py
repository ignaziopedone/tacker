#!/usr/bin/env python
# To run this REST server, execute the following command:
# sudo XTABLES_LIBDIR=/lib/xtables PATH=$PATH python run.py

import sys
from common import settings
from iptables import iptables_wrapper
from iptables import mspl_translator

# Fix issues with decoding HTTP responses
reload(sys)
sys.setdefaultencoding('utf8')


def get_rules():
    result = iptables_wrapper.get_iptables_rules()
    return result


def set_rules(filename):
    try:
        print filename
        with open(filename, 'r') as myfile:
            data = myfile.read()
        rules = mspl_translator.xml_to_iptables(data)
        result = iptables_wrapper.set_iptables_rules(rules)
        return result
    except Exception as e:
        print e
        return False


def flush_rule(rule_id):
    try:
        result = iptables_wrapper.delete_iptables_rule_by_id(rule_id)
        return result
    except Exception as e:
        print e
        return False


def flush_rules():
    try:
        result = iptables_wrapper.flush_iptables_rules()
        return result
    except Exception as e:
        print e
        return False


def main(argv):
    if argv[0] == "set-policies":
        print set_rules(argv[1])
    if argv[0] == "get-policies":
        print get_rules()
    if argv[0] == "delete-policy":
        print flush_rule(argv[1])
    if argv[0] == "delete-policies":
        print flush_rules()


if __name__ == '__main__':
    main(sys.argv[1:])
