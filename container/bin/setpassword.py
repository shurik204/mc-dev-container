#!/bin/python3
import sys
import os

try:
    if os.geteuid() != 0:
        print("[X] This script must be run as root")
        exit(101)

    def get_password_hash(user: str):
        return os.popen(f'awk -v user={user} -F : \'user == $1 {{print $2}}\' /etc/shadow').read().strip(' \n')

    def get_id_by_name(user_id: str):
        return os.popen(f'awk -v name={user_id} -F : \'name == $1 {{print $3}}\' /etc/passwd').read().strip(' \n')

    if get_password_hash(sys.argv[1]) != '!':
        os.setuid(int(get_id_by_name(sys.argv[1])))

    exit(os.system(f'/bin/passwd {sys.argv[1]}'))

except KeyboardInterrupt:
    pass