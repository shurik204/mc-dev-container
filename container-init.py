#!/bin/python3

import secrets
import json
import sys
import os

NO_EXEC = sys.argv.count('--dry-run')

if os.geteuid() != 0 and not NO_EXEC:
    print("[X] This script must be run as root")
    exit(1)

def run_command(cmd: str) -> int:
    if NO_EXEC:
        print(f"[*] Running: {cmd}")
        return 0
    
    code = os.system(cmd)

    return code

# Read and validate settings
# Kinda dumb way to do this, but it works
try:
    config = json.load(open('/settings.json','r'))

    assert config['host']['container-folder'] != ''
    assert config['host']['servers-folder'] != ''
    assert config['host']['container-name'] != ''
    assert config['host']['wings-service'] != ''
    assert config['host']['wings-user'] != ''

    for group in config['groups']:
        assert type(group['name']) is str and group['name'] != ''
        assert type(group['id']) is int and group['id'] > 0

    t = [server['folder'] for server in config['servers']]
    assert t.__len__() == set(t).__len__()

    for server in config['servers']:
        assert type(server['name']) is str and server['name'] != ''
        assert type(server['group']) is str and server['group'] != ''
        assert type(server['folder']) is str and server['folder'] != ''
        assert type(server['host-folder']) is str and server['host-folder'] != ''
    
    for user in config['users']:
        assert type(user['name']) is str and user['name'] != ''
        assert type(user['groups']) is list
        for group in user['groups']:
            assert type(group) is str and group != ''
        
        assert ('publickey' in user['auth'].keys() and user['auth']['publickey'] != []) or ('password' in user['auth'].keys() and type(user['auth']['password']) is str)
except (AssertionError, TypeError) as e:
    print(f"[X] Settings validation failed. {e.__class__.__name__}")
    exit(2)
except KeyError as e:
    print(f"[X] Settings validation failed. {e.__class__.__name__}: {e.args[0]}")
    exit(3)
except json.decoder.JSONDecodeError:
    print("[X] Failed to parse settings.json")
    exit(4)
except FileNotFoundError:
    print("[X] settings.json not found")
    exit(5)
##########################################

print(f'[.] Creating groups')
# Create groups
for group in config['groups']:
    print(f'[.] Creating group "{group["name"]}"')
    run_command(f'groupadd {group["name"]} -g {group["id"]}')

##########################################

print(f'[.] Adding public keys for root user')
run_command(f'mkdir -p /root/.ssh')
run_command(f'rm /root/.ssh/authorized_keys')
for key in config['container']['root-public-keys']:
    run_command(f'echo "{key}" >> /root/.ssh/authorized_keys')

run_command(f'chown root:root /root/.ssh/authorized_keys')
run_command(f'chmod 600 /root/.ssh/authorized_keys')

print(f'[.] Creating users')
# Create groups
for user in config['users']:
    print(f'[.] Creating user "{user["name"]}"')
    res_code = run_command(f'useradd {user["name"]} -m {"-G" if user["groups"].__len__() != 0 else ""} {",".join(user["groups"])}')
    if res_code != 0:
        continue

    if 'publickey' in user['auth'].keys() and user['auth']['publickey'] != []:
        print(f'[.] Adding public keys')
        run_command(f'mkdir -p /home/{user["name"]}/.ssh')
        run_command(f'rm /home/{user["name"]}/.ssh/authorized_keys')
        for key in user['auth']['publickey']:
            run_command(f'echo "{key}" >> /home/{user["name"]}/.ssh/authorized_keys')
        
        run_command(f'chown {user["name"]}:{user["name"]} /home/{user["name"]}/.ssh/authorized_keys')
        run_command(f'chmod 600 /home/{user["name"]}/.ssh/authorized_keys')

    if 'password' in user['auth'].keys():
        print(f'[.] Setting password')
        password = user['auth']['password']
        if password == '':
            password = secrets.token_urlsafe(16)
            print(f'[!] Generated password for "{user["name"]}" is "{password}"')

        run_command(f'echo "{user["name"]}:{password}" | chpasswd')

print('[.] Finishing up')
run_command(f'chmod 665 {config["container"]["servers-folder"]}')

##########################################