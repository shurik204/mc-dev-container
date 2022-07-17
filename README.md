# Minecraft map development container

Opening remote folder using some SFTP extension or just manually pushing updates to the server is pretty slow. Been there, done that. VS Code's Remote SSH is a great option, but you have to give shell access to all users.

So here's my solution: create an isolated docker container that users can SSH into to use all VS Code features on a server and have access to minecraft server files. It supports multiple users and servers with access by groups. Each server has a group assigned that can access that server. Users can be a member of multiple groups.

Requirements:
 - Pterodactyl panel
 - Docker (which you should already have on a server with Wings daemon)
 - VS Code Remote SSH extension

## How to setup:
```sh
git clone https://github.com/shurik204/mc-dev-container
cd mc-dev-container
```

Copy settings file:
```sh
cp settings-example.json settings.json
```

And edit it however you need.

Run `host-init.py` script as root (or with sudo):
```sh
python3 host-init.py
```

After setup is done, you can SSH into container with the following command:
```sh
ssh -i "~/.ssh/private_ssh_key" developer1@your_server_ip -p 2222
```
Users can set/change their password using `setpassword` command. By default, server files are stored in `/servers/folder-name` inside the container.

*Feel free to reach out to me or open an issue if you find bugs or have any ideas for improvements.*