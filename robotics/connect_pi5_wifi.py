#!/usr/bin/env python3
import time
import subprocess
import os
import sys

print("[*] OfficePi -> Pi5 Bridge & Wi-Fi Auto-Provisioner running...")

def log(msg):
    print(f"[{time.strftime('%X')}] {msg}", flush=True)

def get_carrier():
    try:
        with open("/sys/class/net/eth0/carrier", "r") as f:
            return f.read().strip() == "1"
    except Exception:
        return False

# Try forcing link auto-negotiation if carrier is 0
subprocess.run(["sudo", "ip", "link", "set", "eth0", "up"], capture_output=True)

while True:
    carrier = get_carrier()
    if carrier:
        log("Ethernet link DETECTED (carrier=1)!")
        time.sleep(3)
        
        target_ip = None
        
        # 1. Check dnsmasq leases
        for lf in ["/var/lib/misc/dnsmasq.leases", "/var/lib/NetworkManager/dnsmasq-eth0.leases"]:
            if os.path.exists(lf):
                with open(lf, "r") as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 3 and parts[2].startswith("10.42.0."):
                            target_ip = parts[2]
                            log(f"Found DHCP lease: {target_ip} ({parts[3] if len(parts)>3 else ''})")
                            break
        
        # 2. Ping sweep 10.42.0.x
        if not target_ip:
            for i in range(2, 30):
                ip = f"10.42.0.{i}"
                res = subprocess.run(["ping", "-c", "1", "-W", "1", ip], capture_output=True)
                if res.returncode == 0:
                    target_ip = ip
                    log(f"Ping responded: {target_ip}")
                    break
        
        # 3. mDNS lookup
        if not target_ip:
            res = subprocess.run(["ping", "-c", "1", "-W", "1", "lekshmi.local"], capture_output=True)
            if res.returncode == 0:
                target_ip = "lekshmi.local"
                log("Resolved lekshmi.local")

        # 4. Check ARP / Neighbor table
        if not target_ip:
            neigh = subprocess.run(["ip", "neigh", "show", "dev", "eth0"], capture_output=True, text=True)
            for l in neigh.stdout.splitlines():
                if "10.42.0." in l:
                    target_ip = l.split()[0]
                    log(f"Found neighbor: {target_ip}")
                    break

        if target_ip:
            log(f"Connecting to Pi 5 at {target_ip} over SSH...")
            wifi_nm = """[connection]
id=preconfigured
uuid=082b8d81-bce1-42de-8457-b34757a61ad9
type=wifi
[wifi]
mode=infrastructure
ssid=Asianetgigafiber
hidden=false
[ipv4]
method=auto
[ipv6]
addr-gen-mode=default
method=auto
[proxy]
[wifi-security]
key-mgmt=wpa-psk
psk=200e9fb504233cb3898dce540842a137f253ab54e44842331fb7ab19a578b51e
"""
            import paramiko
            try:
                p5 = paramiko.SSHClient()
                p5.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                p5.connect(target_ip, username="lekshmi", password="123456", timeout=5)
                log(f"[✓] SSH SUCCESS into Pi 5 ({target_ip})!")
                
                # Write NetworkManager profile
                sftp = p5.open_sftp()
                with sftp.file("/tmp/preconfigured.nmconnection", "w") as f:
                    f.write(wifi_nm)
                sftp.close()
                
                apply_cmd = "echo 123456 | sudo -S cp /tmp/preconfigured.nmconnection /etc/NetworkManager/system-connections/preconfigured.nmconnection && sudo chmod 600 /etc/NetworkManager/system-connections/preconfigured.nmconnection && sudo nmcli con reload && (sudo nmcli con up preconfigured || sudo systemctl restart NetworkManager)"
                stdin, stdout, stderr = p5.exec_command(apply_cmd)
                out = stdout.read().decode()
                log(f"NM Output: {out}")
                
                time.sleep(3)
                stdin, stdout, stderr = p5.exec_command("ip -br a; hostname -I")
                net_out = stdout.read().decode()
                log(f"[✓] Pi 5 Interfaces:\n{net_out}")
                
                p5.close()
                log("[🎉] Wi-Fi Successfully Configured on Pi 5!")
                break
            except Exception as e:
                log(f"SSH Error to {target_ip}: {e}")
        else:
            log("Waiting for Pi 5 DHCP lease...")
    else:
        # Carrier 0
        pass
    time.sleep(2)
