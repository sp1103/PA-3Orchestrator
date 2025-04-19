#!/usr/bin/env python3
import subprocess
import argparse
import sys

routers = [
    ("pa-3orchestrator-r4-1", "4.4.4.4", ["10.0.16.0/24", "10.0.17.0/24"], ["eth0", "eth1"]),
    ("pa-3orchestrator-r1-1", "1.1.1.1", ["10.0.14.0/24", "10.0.10.0/24", "10.0.16.0/24"], ["eth0", "eth1", "eth2"]),
    ("pa-3orchestrator-r2-1", "2.2.2.2", ["10.0.10.0/24", "10.0.11.0/24"], ["eth0", "eth1"]),
    ("pa-3orchestrator-r3-1", "3.3.3.3", ["10.0.11.0/24", "10.0.17.0/24", "10.0.15.0/24"], ["eth0", "eth1", "eth2"])
]

def build_env():
    try:
        subprocess.run(['chmod', '+x', './dockersetup'], check=True)
        subprocess.run(['sudo', './dockersetup'], check=True)

        subprocess.run(['sudo', 'docker', 'compose', 'up', '-d'], check=True)

        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-ha-1', 'ip', 'route', 'add', '10.0.15.0/24', 'via', '10.0.14.4'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-hb-1', 'ip', 'route', 'add', '10.0.14.0/24', 'via', '10.0.15.3'], check=True)

    except subprocess.CalledProcessError as e:
        sys.exit(1)

def configure():
    for router, rid, networks, interfaces in routers:
        try:
            install = """
            apt-get update && \             
            apt-get install -y curl gnupg lsb-release && \             
            curl -s https://deb.frrouting.org/frr/keys.gpg | \             
            gpg --dearmor > /usr/share/keyrings/frrouting.gpg && \             
            echo "deb [signed-by=/usr/share/keyrings/frrouting.gpg] \             
            https://deb.frrouting.org/frr $(lsb_release -s -c) frr-stable" | \             
            tee /etc/apt/sources.list.d/frr.list && \             
            apt-get update && \             
            apt-get install -y frr frr-pythontools
            """

            subprocess.run(['sudo', 'docker', 'exec', router, 'bash', '-c', install], check=True)

            subprocess.run(['sudo', 'docker', 'exec', router, 'bash', '-c', 'sed -i "s/^ospfd=no/ospfd=yes/" /etc/frr/daemons'], check=True)

            subprocess.run(['sudo', 'docker', 'exec', router, 'service', 'frr', 'restart'], check=True)

            vtysh = [
                'sudo', 'docker', 'exec', router, 'vtysh',
                '-c', 'configure terminal',
                '-c', f'router ospf',
                '-c', f'ospf router-id {rid}'
                ]

            for network in networks:
                vtysh.extend(['-c', f'network {network} area 0.0.0.0'])

            for interface in interfaces:
                vtysh.extend(['-c', f'interface {interface}', '-c', 'ip ospf cost 5'])

            vtysh.extend(['-c', 'end'])

            subprocess.run(vtysh, check=True)

            subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r1-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)
            subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r2-1', 'vtysh', '-c', 'conf t', '-c', 'int eth0', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)
            subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r2-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)
            subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r2-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)
        except subprocess.CalledProcessError as e:
           sys.exit(1)

def north():
    try:
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r1-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r2-1', 'vtysh', '-c', 'conf t', '-c', 'int eth0', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r2-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r2-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)

        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r1-1', 'vtysh', '-c', 'conf t', '-c', 'int eth2', '-c', 'ip ospf cost 100', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r4-1', 'vtysh', '-c', 'conf t', '-c', 'int eth0', '-c', 'ip ospf cost 100', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r4-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 100', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r3-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 100', '-c', 'end'], check=True)

        print("North Path")

    except subprocess.CalledProcessError as e:
        sys.exit(1)

def south():
    try:
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r1-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 100', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r2-1', 'vtysh', '-c', 'conf t', '-c', 'int eth0', '-c', 'ip ospf cost 100', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r2-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 100', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r2-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 100', '-c', 'end'], check=True)

        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r1-1', 'vtysh', '-c', 'conf t', '-c', 'int eth2', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r4-1', 'vtysh', '-c', 'conf t', '-c', 'int eth0', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r4-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)
        subprocess.run(['sudo', 'docker', 'exec', 'pa-3orchestrator-r3-1', 'vtysh', '-c', 'conf t', '-c', 'int eth1', '-c', 'ip ospf cost 5', '-c', 'end'], check=True)

        print("South Path")

    except subprocess.CalledProcessError as e:
        sys.exit(1)



def main():
    parser = argparse.ArgumentParser(description="Network Orchestrator")
    parser.add_argument("-n", action="store_true", help="North Path")
    parser.add_argument("-s", action="store_true", help="South Path")
    args = parser.parse_args()

    if args.n:
        north()
    if args.s:
        south()
    else:
        build_env()
        configure()

if __name__ == "__main__":
    main()
