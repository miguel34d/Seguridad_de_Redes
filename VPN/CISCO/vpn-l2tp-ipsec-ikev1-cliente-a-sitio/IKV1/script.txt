================================================================================
  LAB VPN L2TP/IPSec IKEv1 — CONFIGURACION COMPLETA DE TODOS LOS DISPOSITIVOS
  Topologia: ISP > Peear1 (LNS) + Peear2 + Kali-Linux-1 (cliente remoto)
================================================================================

================================================================================
 1. ROUTER ISP
================================================================================

enable
configure terminal
hostname ISP
!
interface Ethernet0/0
 description WAN-hacia-Peear1
 ip address 200.1.1.1 255.255.255.252
 no shutdown
!
interface Ethernet0/1
 description WAN-hacia-Peear2
 ip address 200.1.2.1 255.255.255.252
 no shutdown
!
interface Ethernet0/2
 description Segmento-Kali-Linux-1-cliente-remoto
 ip address 200.1.3.1 255.255.255.252
 no shutdown
!
! --- Rutas estaticas hacia LANs internas y pool VPN ---
ip route 10.13.67.0 255.255.255.192 200.1.1.2
ip route 10.13.67.192 255.255.255.192 200.1.2.2
ip route 172.20.1.0 255.255.255.0 200.1.1.2
!
end
write memory

================================================================================
 2. ROUTER PEEAR1  (Servidor VPN / LNS - L2TP Network Server)
================================================================================

enable
configure terminal
hostname Peear1
!
! --- AAA debe ir PRIMERO antes de cualquier referencia ---
aaa new-model
aaa authentication ppp default local
aaa authorization network default local
!
! --- Usuario VPN local ---
username vpnuser password VpnClient123
!
! --- Interfaces ---
interface Ethernet0/0
 description WAN-hacia-ISP
 ip address 200.1.1.2 255.255.255.252
 no shutdown
!
interface Ethernet0/1
 description LAN-Peear1-VLAN10
 ip address 10.13.67.1 255.255.255.192
 no shutdown
!
! --- Ruta por defecto hacia el ISP ---
ip route 0.0.0.0 0.0.0.0 200.1.1.1
!
! --- Ruta hacia LAN de Peear2 via ISP ---
ip route 10.13.67.192 255.255.255.192 200.1.1.1
!
! --- VPDN para terminar L2TP ---
vpdn enable
vpdn-group L2TP-DMVPN
 accept-dialin
  protocol l2tp
  virtual-template 1
 l2tp tunnel password Cisco123
!
! --- IKEv1 Fase 1 (ISAKMP) ---
crypto isakmp policy 10
 encr aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400
!
crypto isakmp key Cisco123 address 0.0.0.0 0.0.0.0
crypto isakmp keepalive 10 5
!
! --- IPSec Fase 2 modo transporte (L2TP va encapsulado dentro) ---
crypto ipsec transform-set TS_L2TP esp-aes 256 esp-sha256-hmac
 mode transport
!
crypto ipsec profile PROF_L2TP
 set transform-set TS_L2TP
!
! --- Dynamic crypto map (acepta clientes con IP variable) ---
crypto dynamic-map DYNMAP 10
 set transform-set TS_L2TP
 set pfs group14
!
crypto map CMAP_L2TP 10 ipsec-isakmp dynamic DYNMAP
!
interface Ethernet0/0
 crypto map CMAP_L2TP
!
! --- Pool de IPs para clientes VPN ---
ip local pool POOL_L2TP 172.20.1.10 172.20.1.20
!
! --- Virtual-Template con IP dedicada (NO unnumbered) ---
interface Virtual-Template1
 ip address 172.20.1.1 255.255.255.0
 peer default ip address pool POOL_L2TP
 ppp authentication ms-chap-v2 chap
!
! --- EIGRP: anunciar LAN local + pool VPN ---
router eigrp 100
 network 10.13.67.0 0.0.0.63
 network 172.20.1.0 0.0.0.255
 no auto-summary
!
end
write memory

================================================================================
 3. ROUTER PEEAR2
================================================================================

enable
configure terminal
hostname Peear2
!
interface Ethernet0/0
 description WAN-hacia-ISP
 ip address 200.1.2.2 255.255.255.252
 no shutdown
!
interface Ethernet0/1
 description LAN-Peear2-VLAN20
 ip address 10.13.67.193 255.255.255.192
 no shutdown
!
! --- Ruta por defecto ---
ip route 0.0.0.0 0.0.0.0 200.1.2.1
!
! --- Rutas hacia LAN Peear1 y pool VPN via ISP ---
ip route 10.13.67.0 255.255.255.192 200.1.2.1
ip route 172.20.1.0 255.255.255.0 200.1.2.1
!
! --- EIGRP: solo LAN local ---
router eigrp 100
 network 10.13.67.192 0.0.0.63
 no auto-summary
!
end
write memory

================================================================================
 4. SWITCH IOU4  (LAN Peear1 - VLAN 10)
================================================================================

enable
configure terminal
hostname IOU4
!
vlan 10
 name LAN-PEEAR1
!
interface Ethernet0/0
 description uplink-hacia-Peear1-e0/1
 switchport mode access
 switchport access vlan 10
 no shutdown
!
interface Ethernet0/1
 description hacia-PC1
 switchport mode access
 switchport access vlan 10
 no shutdown
!
end
write memory

================================================================================
 5. SWITCH IOU5  (LAN Peear2 - VLAN 20)
================================================================================

enable
configure terminal
hostname IOU5
!
vlan 20
 name LAN-PEEAR2
!
interface Ethernet0/0
 description uplink-hacia-Peear2-e0/1
 switchport mode access
 switchport access vlan 20
 no shutdown
!
interface Ethernet0/1
 description hacia-PC2
 switchport mode access
 switchport access vlan 20
 no shutdown
!
end
write memory

================================================================================
 6. PC1 (VPCS - LAN Peear1 / VLAN 10)
================================================================================

ip 10.13.67.2 255.255.255.192 10.13.67.1
save

================================================================================
 7. PC2 (VPCS - LAN Peear2 / VLAN 20)
================================================================================

ip 10.13.67.194 255.255.255.192 10.13.67.193
save

================================================================================
 8. KALI-LINUX-1 — Archivos de configuracion (o usar kali-vpn-setup.sh)
================================================================================

--- /usr/local/sbin/lab-network-setup.sh ---
#!/bin/bash
ip addr replace 200.1.3.2/30 dev eth0
ip link set eth0 up
ip addr replace 192.168.100.100/24 dev eth1
ip link set eth1 up
ip route replace default via 200.1.3.1 dev eth0
ip route replace 200.1.1.0/30 via 200.1.3.1 dev eth0
exit 0

--- /etc/ipsec.conf ---
config setup
    charondebug="ike 1, knl 1, cfg 1"

conn L2TP-PSK
 keyexchange=ikev1
 authby=secret
 auto=start
 keyingtries=3
 rekey=no
 ikelifetime=8h
 keylife=1h
 type=transport
 ike=aes256-sha256-modp2048!
 esp=aes256-sha256-modp2048!
 left=200.1.3.2
 right=200.1.1.2
 leftprotoport=17/1701
 rightprotoport=17/1701

--- /etc/ipsec.secrets ---
200.1.3.2 200.1.1.2 : PSK "Cisco123"

--- /etc/strongswan.d/charon/unity.conf ---
unity {
    load = no
}

--- /etc/xl2tpd/xl2tpd.conf ---
[global]
auth file = /etc/xl2tpd/l2tp-secrets

[lac peear1]
lns = 200.1.1.2
ppp debug = yes
pppoptfile = /etc/ppp/options.l2tpd.client
length bit = yes

--- /etc/xl2tpd/l2tp-secrets ---
* * Cisco123

--- /etc/ppp/options.l2tpd.client ---
ipcp-accept-local
ipcp-accept-remote
refuse-eap
require-mschap-v2
noccp
noauth
idle 1800
mtu 1410
mru 1410
usepeerdns
debug
connect-delay 5000
name vpnuser
password VpnClient123

--- /etc/ppp/ip-up.d/10-lab-route ---
#!/bin/bash
ip route replace 10.13.67.0/26   via "$5" dev "$1"
ip route replace 10.13.67.192/26 via "$5" dev "$1"
ip route replace 172.20.1.0/24   dev "$1"

--- /etc/systemd/system/lab-network.service ---
[Unit]
Description=Configuracion de red estatica - Lab VPN
After=network-pre.target
Before=strongswan-starter.service xl2tpd.service
Wants=network-pre.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/lab-network-setup.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target

--- /usr/local/sbin/lab-l2tp-dial.sh ---
#!/bin/bash
sleep 8
echo "c peear1" > /var/run/xl2tpd/l2tp-control

--- /etc/systemd/system/lab-l2tp-dial.service ---
[Unit]
Description=Auto-dial tunel L2TP peear1
After=xl2tpd.service strongswan-starter.service
Requires=xl2tpd.service strongswan-starter.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/lab-l2tp-dial.sh

[Install]
WantedBy=multi-user.target

--- Comandos para activar todo en Kali ---
chmod +x /usr/local/sbin/lab-network-setup.sh
chmod +x /usr/local/sbin/lab-l2tp-dial.sh
chmod +x /etc/ppp/ip-up.d/10-lab-route
systemctl daemon-reload
systemctl enable lab-network.service strongswan-starter xl2tpd lab-l2tp-dial.service
reboot

================================================================================
 9. COMANDOS DE VERIFICACION (para el video)
================================================================================

--- En PEEAR1 ---
show version
show ip interface brief
show crypto isakmp sa
show crypto ipsec sa
show vpdn session
show ip route
show ip local pool POOL_L2TP

--- En PEEAR2 ---
show ip interface brief
show ip route

--- En ISP ---
show ip interface brief
show ip route

--- En KALI (tras conectar) ---
ip a show ppp0
ip route
ipsec statusall
ping -c3 172.20.1.1
ping -c3 10.13.67.1
ping -c3 10.13.67.2
ping -c3 10.13.67.194

--- En PC1 ---
ping 10.13.67.194
ping 172.20.1.10

--- En PC2 ---
ping 10.13.67.2
ping 172.20.1.10

