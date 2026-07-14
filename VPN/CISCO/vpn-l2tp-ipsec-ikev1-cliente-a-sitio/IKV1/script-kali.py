#!/bin/bash
# =============================================================================
#  L2TP/IPSec IKEv1 — Setup interactivo para Kali Linux
#  Autor: Lab VPN GNS3
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()    { echo -e "${GREEN}[✔]${NC} $1"; }
warn()   { echo -e "${YELLOW}[➤]${NC} $1"; }
err()    { echo -e "${RED}[✘] ERROR: $1${NC}"; exit 1; }
title()  { echo -e "\n${CYAN}${BOLD}══════════════════════════════════════════${NC}"; \
           echo -e "${CYAN}${BOLD}  $1${NC}"; \
           echo -e "${CYAN}${BOLD}══════════════════════════════════════════${NC}\n"; }
ask()    { echo -e "${YELLOW}[?]${NC} $1"; }

[ "$EUID" -ne 0 ] && err "Ejecutar como root: sudo bash $0"

clear
echo -e "${CYAN}${BOLD}"
echo "  ██╗   ██╗██████╗ ███╗   ██╗    ██╗      █████╗ ██████╗ "
echo "  ██║   ██║██╔══██╗████╗  ██║    ██║     ██╔══██╗██╔══██╗"
echo "  ██║   ██║██████╔╝██╔██╗ ██║    ██║     ███████║██████╔╝"
echo "  ╚██╗ ██╔╝██╔═══╝ ██║╚██╗██║    ██║     ██╔══██║██╔══██╗"
echo "   ╚████╔╝ ██║     ██║ ╚████║    ███████╗██║  ██║██████╔╝"
echo "    ╚═══╝  ╚═╝     ╚═╝  ╚═══╝    ╚══════╝╚═╝  ╚═╝╚═════╝ "
echo -e "${NC}"
echo -e "${BOLD}  L2TP/IPSec IKEv1 — Configuracion automatica para GNS3${NC}"
echo -e "  ─────────────────────────────────────────────────────\n"

# =============================================================================
title "PASO 1 — Configuracion de red de Kali"
# =============================================================================

ask "IP de esta maquina Kali (eth0 - lado ISP) [default: 200.1.3.2/30]:"
read -r INPUT_KALI_IP
KALI_IP=${INPUT_KALI_IP:-"200.1.3.2/30"}

ask "Gateway del ISP hacia Kali [default: 200.1.3.1]:"
read -r INPUT_GW
ISP_GW=${INPUT_GW:-"200.1.3.1"}

ask "IP de gestion GNS3 (eth1) [default: 192.168.100.100/24]:"
read -r INPUT_MGMT
MGMT_IP=${INPUT_MGMT:-"192.168.100.100/24"}

ask "Gateway de gestion GNS3 (eth1) [default: 192.168.100.10]:"
read -r INPUT_MGMT_GW
MGMT_GW=${INPUT_MGMT_GW:-"192.168.100.10"}

# =============================================================================
title "PASO 2 — Configuracion del servidor VPN (Peear1)"
# =============================================================================

ask "IP publica del servidor VPN - Peear1 (LNS) [default: 200.1.1.2]:"
read -r INPUT_LNS
LNS_IP=${INPUT_LNS:-"200.1.1.2"}

ask "Pre-shared key IPSec [default: Cisco123]:"
read -r INPUT_PSK
PSK=${INPUT_PSK:-"Cisco123"}

ask "Contrasena del tunel L2TP [default: Cisco123]:"
read -r INPUT_L2TP_PASS
L2TP_PASS=${INPUT_L2TP_PASS:-"Cisco123"}

# =============================================================================
title "PASO 3 — Credenciales PPP del usuario VPN"
# =============================================================================

ask "Usuario VPN (PPP) [default: vpnuser]:"
read -r INPUT_USER
VPN_USER=${INPUT_USER:-"vpnuser"}

ask "Contrasena VPN (PPP) [default: VpnClient123]:"
read -r INPUT_PASS
VPN_PASS=${INPUT_PASS:-"VpnClient123"}

# =============================================================================
title "PASO 4 — Redes internas a enrutar por el tunel"
# =============================================================================

ask "Red LAN del servidor (Peear1) [default: 10.13.67.0/26]:"
read -r INPUT_LAN1
LAN1=${INPUT_LAN1:-"10.13.67.0/26"}

ask "Red LAN remota (Peear2) [default: 10.13.67.192/26]:"
read -r INPUT_LAN2
LAN2=${INPUT_LAN2:-"10.13.67.192/26"}

ask "Red del pool VPN [default: 172.20.1.0/24]:"
read -r INPUT_POOL
POOL_NET=${INPUT_POOL:-"172.20.1.0/24"}

# =============================================================================
title "RESUMEN — Confirmar configuracion"
# =============================================================================

echo -e "  ${BOLD}Kali eth0:${NC}         $KALI_IP"
echo -e "  ${BOLD}Gateway ISP:${NC}        $ISP_GW"
echo -e "  ${BOLD}Kali eth1 (mgmt):${NC}  $MGMT_IP"
echo -e "  ${BOLD}Gateway mgmt:${NC}       $MGMT_GW"
echo -e "  ${BOLD}Servidor VPN:${NC}       $LNS_IP"
echo -e "  ${BOLD}PSK IPSec:${NC}          $PSK"
echo -e "  ${BOLD}Clave L2TP:${NC}         $L2TP_PASS"
echo -e "  ${BOLD}Usuario PPP:${NC}        $VPN_USER"
echo -e "  ${BOLD}Password PPP:${NC}       $VPN_PASS"
echo -e "  ${BOLD}LAN Peear1:${NC}         $LAN1"
echo -e "  ${BOLD}LAN Peear2:${NC}         $LAN2"
echo -e "  ${BOLD}Pool VPN:${NC}           $POOL_NET"
echo ""
ask "¿Todo correcto? Continuar con la instalacion? [S/n]:"
read -r CONFIRM
[[ "$CONFIRM" =~ ^[Nn]$ ]] && { echo "Cancelado."; exit 0; }

# Extraer solo la IP sin mascara para ipsec.secrets
KALI_IP_ONLY=$(echo "$KALI_IP" | cut -d'/' -f1)

# =============================================================================
title "INSTALANDO PAQUETES"
# =============================================================================
warn "Actualizando e instalando strongswan, xl2tpd, ppp..."
apt-get update -qq
apt-get install -y strongswan xl2tpd ppp 2>/dev/null
log "Paquetes instalados"

# =============================================================================
title "ESCRIBIENDO ARCHIVOS DE CONFIGURACION"
# =============================================================================

warn "Configurando /etc/ipsec.conf..."
cat > /etc/ipsec.conf << EOF
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
 left=${KALI_IP_ONLY}
 right=${LNS_IP}
 leftprotoport=17/1701
 rightprotoport=17/1701
EOF
log "/etc/ipsec.conf"

warn "Configurando /etc/ipsec.secrets..."
cat > /etc/ipsec.secrets << EOF
${KALI_IP_ONLY} ${LNS_IP} : PSK "${PSK}"
EOF
chmod 600 /etc/ipsec.secrets
log "/etc/ipsec.secrets"

warn "Configurando strongSwan charon unity..."
mkdir -p /etc/strongswan.d/charon
cat > /etc/strongswan.d/charon/unity.conf << EOF
unity {
    load = no
}
EOF
log "unity.conf"

warn "Configurando /etc/xl2tpd/xl2tpd.conf..."
mkdir -p /etc/xl2tpd
cat > /etc/xl2tpd/xl2tpd.conf << EOF
[global]
auth file = /etc/xl2tpd/l2tp-secrets

[lac peear1]
lns = ${LNS_IP}
ppp debug = yes
pppoptfile = /etc/ppp/options.l2tpd.client
length bit = yes
EOF

cat > /etc/xl2tpd/l2tp-secrets << EOF
* * ${L2TP_PASS}
EOF
log "/etc/xl2tpd/xl2tpd.conf"

warn "Configurando /etc/ppp/options.l2tpd.client..."
cat > /etc/ppp/options.l2tpd.client << EOF
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
name ${VPN_USER}
password ${VPN_PASS}
EOF
log "/etc/ppp/options.l2tpd.client"

warn "Creando script de red /usr/local/sbin/lab-network-setup.sh..."
cat > /usr/local/sbin/lab-network-setup.sh << EOF
#!/bin/bash
ip addr replace ${KALI_IP} dev eth0
ip link set eth0 up
ip addr replace ${MGMT_IP} dev eth1
ip link set eth1 up
ip route replace default via ${ISP_GW} dev eth0
ip route replace $(echo "$LNS_IP" | awk -F. '{print $1"."$2"."$3".0/30"}') via ${ISP_GW} dev eth0
exit 0
EOF
chmod +x /usr/local/sbin/lab-network-setup.sh
log "lab-network-setup.sh"

warn "Creando script de dial /usr/local/sbin/lab-l2tp-dial.sh..."
cat > /usr/local/sbin/lab-l2tp-dial.sh << 'EOF'
#!/bin/bash
sleep 8
echo "c peear1" > /var/run/xl2tpd/l2tp-control
EOF
chmod +x /usr/local/sbin/lab-l2tp-dial.sh
log "lab-l2tp-dial.sh"

warn "Creando /etc/ppp/ip-up.d/10-lab-route..."
cat > /etc/ppp/ip-up.d/10-lab-route << EOF
#!/bin/bash
ip route replace ${LAN1}    via "\$5" dev "\$1"
ip route replace ${LAN2}    via "\$5" dev "\$1"
ip route replace ${POOL_NET} dev "\$1"
EOF
chmod +x /etc/ppp/ip-up.d/10-lab-route
log "ip-up.d/10-lab-route"

warn "Creando servicios systemd..."
cat > /etc/systemd/system/lab-network.service << 'EOF'
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
EOF

cat > /etc/systemd/system/lab-l2tp-dial.service << 'EOF'
[Unit]
Description=Auto-dial tunel L2TP peear1
After=xl2tpd.service strongswan-starter.service
Requires=xl2tpd.service strongswan-starter.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/lab-l2tp-dial.sh

[Install]
WantedBy=multi-user.target
EOF
log "Servicios systemd"

# =============================================================================
title "HABILITANDO SERVICIOS"
# =============================================================================
systemctl daemon-reload
systemctl enable lab-network.service
systemctl enable strongswan-starter
systemctl enable xl2tpd
systemctl enable lab-l2tp-dial.service
log "Servicios habilitados para arranque automatico"

# =============================================================================
title "LEVANTANDO EL TUNEL"
# =============================================================================
warn "Aplicando configuracion de red..."
bash /usr/local/sbin/lab-network-setup.sh
log "Red configurada"

warn "Iniciando strongSwan (IPSec)..."
systemctl restart strongswan-starter
sleep 4

warn "Iniciando xl2tpd (L2TP)..."
systemctl restart xl2tpd
sleep 3

warn "Enviando dial al servidor $LNS_IP..."
echo "c peear1" > /var/run/xl2tpd/l2tp-control

warn "Esperando que ppp0 levante (15 seg)..."
for i in $(seq 1 15); do
    echo -ne "  ${YELLOW}[${i}/15]${NC} Esperando ppp0...\r"
    sleep 1
    if ip a show ppp0 &>/dev/null; then
        echo ""
        break
    fi
done
echo ""

# =============================================================================
title "VERIFICACION COMPLETA DEL TUNEL VPN"
# =============================================================================

if ! ip a show ppp0 &>/dev/null; then
    err "ppp0 no levanto. Revisa: journalctl -u strongswan-starter -u xl2tpd -n 40"
fi

PPP_IP=$(ip a show ppp0 | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
PPP_PEER=$(ip a show ppp0 | grep "inet " | awk '{print $4}' | cut -d'/' -f1)

echo -e "\n${BOLD}━━━ INTERFAZ PPP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
ip a show ppp0
echo ""

echo -e "${BOLD}━━━ TABLA DE RUTAS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
ip route
echo ""

echo -e "${BOLD}━━━ ESTADO IPSEC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
ipsec statusall 2>/dev/null | grep -E "ESTABLISHED|INSTALLED|IKE proposal|ESP SPI|bytes"
echo ""

echo -e "${BOLD}━━━ PRUEBAS DE CONECTIVIDAD ━━━━━━━━━━━━━━━━━━━━━${NC}"

check_ping() {
    local HOST=$1
    local DESC=$2
    echo -ne "  Ping a ${BOLD}${HOST}${NC} (${DESC})... "
    if ping -c2 -W2 "$HOST" &>/dev/null; then
        echo -e "${GREEN}${BOLD}✔ ALCANZABLE${NC}"
    else
        echo -e "${RED}✘ SIN RESPUESTA${NC}"
    fi
}

check_ping "$PPP_PEER"        "Gateway PPP / Peear1 virtual-template"
check_ping "$(echo $LAN1 | cut -d'/' -f1 | awk -F. '{print $1"."$2"."$3".1"}')" "Peear1 LAN gateway"
check_ping "$(echo $LAN1 | cut -d'/' -f1 | awk -F. '{print $1"."$2"."$3".2"}')" "PC1"
check_ping "$(echo $LAN2 | cut -d'/' -f1 | awk -F. '{print $1"."$2"."$3".194"}')" "PC2 (via EIGRP)"

echo ""
echo -e "${BOLD}━━━ RESUMEN FINAL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}${BOLD}IP asignada por VPN:${NC}  $PPP_IP"
echo -e "  ${GREEN}${BOLD}Peer (servidor):${NC}      $PPP_PEER"
echo -e "  ${GREEN}${BOLD}Servidor VPN:${NC}         $LNS_IP"
echo -e "  ${GREEN}${BOLD}Cifrado:${NC}              AES-256 / SHA-256 / DH-14 (IKEv1)"
echo -e "  ${GREEN}${BOLD}Protocolo tunel:${NC}      L2TP sobre IPSec (transporte)"
echo ""
log "Configuracion completa. El tunel levanta automaticamente al reiniciar."
echo ""


