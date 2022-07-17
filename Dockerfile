FROM     ubuntu:20.04
LABEL    author="shurik204"


# Install some packages
# Separated for faster redeployment
RUN     apt-get update && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y openssh-server sudo curl wget zip unzip git tar screen nano

# Actual setup #
        # Make  dirs for ssh
RUN     mkdir /var/run/sshd \
        # Edit ssh config
        && sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config \
        && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config \
        # SSH login fix. Otherwise users will be kicked out after login
        && sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd \
        && sed -i 's/SHELL=\/bin\/sh/SHELL=\/bin\/bash/' /etc/default/useradd

COPY    container-init.py /bin/container-init
COPY    /container/bin/* /bin/

RUN     chmod +x /bin/container-init /bin/setpassword \
        && chmod +s /bin/setpassword \
        && touch /settings.json

CMD     [ "/bin/bash", "/bin/entrypoint.sh" ]