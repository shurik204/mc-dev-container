#!/bin/python3

# CRON_FILE_PATH = '/etc/cron.d/chmod_server_folders'

import contextlib
import json
import sys
import os
import re

NO_EXEC = sys.argv.count('--dry-run')

if os.geteuid() != 0 and not NO_EXEC:
    print("[!] This script must be run as root")
    exit(1)

def run_command(cmd: str) -> int:
    if NO_EXEC:
        print(f"[*] Running: {cmd}")
        return 0
    
    return os.system(cmd)

# Read and validate settings
# Kinda dumb way to do this, but it works
try:
    config = json.load(open('settings.json' ,'r'))

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
        assert type(server['host-folder']) is str and server['host-folder'] != '' and (os.path.exists(server['host-folder']) or NO_EXEC)
    
    for user in config['users']:
        assert type(user['name']) is str and user['name'] != ''
        assert type(user['groups']) is list
        for group in user['groups']:
            assert type(group) is str and group != ''

        assert ('publickey' in user['auth'].keys() and user['auth']['publickey'] != []) or ('password' in user['auth'].keys() and type(user['auth']['password']) is str)
        
except (AssertionError, TypeError) as e:
    print(f"[!] Settings validation failed. {e.__class__.__name__}")
    exit(2)
except KeyError as e:
    print(f"[!] Settings validation failed. {e.__class__.__name__}: {e.args[0]}")
    exit(3)
except json.decoder.JSONDecodeError:
    print("[!] Failed to parse settings.json")
    exit(4)
except FileNotFoundError:
    print("[!] settings.json not found")
    if 'settings-example.json' in os.listdir('.'):
        os.rename('settings-example.json', 'settings.json')
        print("[.] Created settings.json from settings-example.json")
    exit(5)

##########################################

print(f'[.] Creating groups')
# Create groups
for group in config['groups']:
    print(f'[.] Creating group "{group["name"]}"')
    run_command(f'groupadd {group["name"]} -g {group["id"]}')

##########################################

# cron_tasks = []
print('[.] Creating host folders')

host_container_folder_home = os.path.join(config['host']['container-folder'], 'home')
if not NO_EXEC:
    os.makedirs(config['host']['servers-folder'], exist_ok=True)
    os.makedirs(config['host']['container-folder'], exist_ok=True)
    with contextlib.suppress(FileExistsError):
        os.mkdir(host_container_folder_home)

print(f'[.] Setting up servers')
for server in config['servers']:
    print(f'[.] Setting up server "{server["name"]}"')

    run_command(f'mkdir -p {os.path.join(config["host"]["servers-folder"], server["folder"])}')
    run_command(f'mount --bind {server["host-folder"]} {os.path.join(config["host"]["servers-folder"], server["folder"])}')
    run_command(f'chown -R {config["host"]["wings-user"]}:{server["group"]} {server["host-folder"]}')
    run_command(f'chmod -R 2770 {server["host-folder"]}')

# I need to add pterodactyl user to all server groups
# so it can still access the server folders, because 
# newly created files will have permissions set to user:server_group.
print(f'[.] Adding Wings user "{config["host"]["wings-user"]}" to {config["groups"].__len__()} groups')
for group in config['groups']:
    run_command(f'usermod -a -G {group["name"]} {config["host"]["wings-user"]}')

def configure_wings():
    # Make sure Wings doesn't mess up permissions that we set
    OPTION_NAME = "check_permissions_on_boot"
    if not NO_EXEC:
        # read config
        with open('/etc/pterodactyl/config.yml', 'r') as f: wings_conf = f.read()
        # Check if option exists and is set to true
        if re.search(f'{OPTION_NAME} *: *false', wings_conf) != None:
            print(f'[!] Wings option "{OPTION_NAME}"  is already set')
            return
        # If not set to true, check if it exists and replace if it does
        elif re.search(f'{OPTION_NAME} *:.*', wings_conf) != None: wings_conf = re.sub(f'{OPTION_NAME} *: *true', f'{OPTION_NAME}: false', wings_conf)
        # If not set to true nor found in file, just append it 
        else: wings_conf += f'\n{OPTION_NAME}: false\n'

        # Write changes to file
        with open('/etc/pterodactyl/config.yml', 'w') as f: f.write(wings_conf)

    print(f'[.] Restarting wings')
    run_command(f'systemctl restart {config["host"]["wings-service"]}')

print(f'[.] Configuring Wings daemon')
configure_wings()

print(f'[.] Copying settings.json to {config["host"]["container-folder"]}')
run_command(f'cp settings.json {config["host"]["container-folder"]}')

# Create container
print('[.] [1/3] Setting up container. Building...')
res_code = run_command('docker build . -t shurik204/ssh-ubuntu')
if res_code != 0:
    print('[!] Error occured while building container.')
    exit(10)
print('[.] [2/3] Setting up container. Creating...')
res_code = run_command(f'docker create --name {config["host"]["container-name"]} --hostname {config["host"]["container-name"]} --restart unless-stopped -v {host_container_folder_home}:/home -v {config["host"]["servers-folder"]}:/servers --mount type=bind,source={config["host"]["container-folder"]}/settings.json,target=/settings.json -p 2222:2222 shurik204/ssh-ubuntu:latest')
if res_code == 125:
    print('[!] Got non-zero exit code. Container already exists?')
print('[.] [3/3] Setting up container. Starting...')
res_code = run_command(f'docker start {config["host"]["container-name"]}')
if res_code == 125:
    print('[!] Got non-zero exit code. Container is already running?')