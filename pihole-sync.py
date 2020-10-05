#!/usr/bin/python3
import difflib
import os
import subprocess
import sys

HA_MASTER_PIHOLE_DIR = '/home/ubuntu/pihole'

HA_SSH_SECONDARY_IP = '10.10.10.2'
HA_SSH_SECONDARY_USER = 'ubuntu'
HA_SECONDARY_PIHOLE_DIR = '/home/pi/hole'
HA_SECONDARY_DOCKER_CONTAINER_NAME = 'pihole'


def main():
    custom_list = get_custom_dnsmasq_list()
    dnsmasq_custom_conf = get_custom_dnsmasq_conf()

    custom_list_ssh = send_ssh_command('cat {}'.format(
        os.path.join(HA_SECONDARY_PIHOLE_DIR, 'etc-pihole/custom.list')
    ))

    dnsmasq_custom_conf_ssh = send_ssh_command('cat {}'.format(
        os.path.join(HA_SECONDARY_PIHOLE_DIR, 'etc-dnsmasq.d/02-custom.conf')
    ))

    if custom_list != custom_list_ssh or dnsmasq_custom_conf != dnsmasq_custom_conf_ssh:
        print('Remote custom.list or 02-custom.conf does not match, transferring new version...')

        send_scp_command_local_to_remote(
            os.path.join(HA_MASTER_PIHOLE_DIR, 'etc-pihole/custom.list'),
            os.path.join(HA_SECONDARY_PIHOLE_DIR, 'custom.list.temp')
        )

        send_ssh_command('sudo mv {} {}'.format(
            os.path.join(HA_SECONDARY_PIHOLE_DIR, 'custom.list.temp'),
            os.path.join(HA_SECONDARY_PIHOLE_DIR, 'etc-pihole/custom.list')
        ))

        send_scp_command_local_to_remote(
            os.path.join(HA_MASTER_PIHOLE_DIR, 'etc-dnsmasq.d/02-custom.conf'),
            os.path.join(HA_SECONDARY_PIHOLE_DIR, '02-custom.conf.temp')
        )

        send_ssh_command('sudo mv {} {}'.format(
            os.path.join(HA_SECONDARY_PIHOLE_DIR, '02-custom.conf.temp'),
            os.path.join(HA_SECONDARY_PIHOLE_DIR,
                         'etc-dnsmasq.d/02-custom.conf')
        ))

        try:
            send_ssh_command(
                f'cd {HA_SECONDARY_PIHOLE_DIR} && docker-compose restart {HA_SECONDARY_DOCKER_CONTAINER_NAME}'
            )
        except ValueError as _:
            pass
    else:
        print('Remote custom.list is up-to-date.')


def get_custom_dnsmasq_list():
    f = open(os.path.join(HA_MASTER_PIHOLE_DIR, 'etc-pihole/custom.list'), 'r')

    lines = []

    for line in f.readlines():
        lines.append(line.strip())

    return '\n'.join(lines)


def get_custom_dnsmasq_conf():
    f = open(os.path.join(HA_MASTER_PIHOLE_DIR,
                          'etc-dnsmasq.d/02-custom.conf'), 'r')

    lines = []

    for line in f.readlines():
        lines.append(line.strip())

    return '\n'.join(lines)


def send_ssh_command(command):
    ssh = subprocess.Popen(
        f'ssh {HA_SSH_SECONDARY_USER}@{HA_SSH_SECONDARY_IP} "{command}"',
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()

    ssh = (ssh[0].decode('utf-8'), ssh[1].decode('utf-8'))

    if len(ssh[1]) > 0:
        raise ValueError('Caught something in stderr: {}'.format(ssh[1]))

    return ssh[0][:-1]


def send_scp_command_local_to_remote(local_file, remote_file):
    ssh = subprocess.Popen(
        f'scp {local_file} {HA_SSH_SECONDARY_USER}@{HA_SSH_SECONDARY_IP}:{remote_file}',
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()

    ssh = (ssh[0].decode('utf-8'), ssh[1].decode('utf-8'))

    if len(ssh[1]) > 0:
        raise ValueError('Caught something in stderr: {}'.format(ssh[1]))

    return ssh[0]


if __name__ == "__main__":
    sys.exit(main())
