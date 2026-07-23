# 🔐 VPN Client-to-Site — L2TP/IPsec (IKEv1)

![Materia](https://img.shields.io/badge/Materia-TSI--203-1E1E1E?style=flat-square)
![Estado](https://img.shields.io/badge/Estado-Completado-2ea043?style=flat-square)
![Protocolo](https://img.shields.io/badge/Protocolo-L2TP%2FIPsec%20IKEv1-red?style=flat-square)
![Topología](https://img.shields.io/badge/Topología-Client--to--Site-blue?style=flat-square)
![Fase1](https://img.shields.io/badge/Fase%201-ISAKMP%20PSK-orange?style=flat-square)
![Fase2](https://img.shields.io/badge/Fase%202-Modo%20Transporte-orange?style=flat-square)

![Herramientas](https://img.shields.io/badge/Herramientas-GNS3%20%7C%20Cisco%20IOS%20%7C%20Windows%2010%20%7C%20PowerShell%20%7C%20VPCS-6f42c1?style=flat-square)

**Cliente VPN:** Windows10-1 &nbsp;→&nbsp; **Servidor VPN (LNS):** R3 &nbsp;→&nbsp; **LAN protegida:** PC2

---

## 📑 Tabla de contenido

- [Resumen de la topología](#-resumen-de-la-topología)
- [¿Por qué L2TP/IPsec y no site-to-site?](#-por-qué-l2tpipsec-y-no-un-site-to-site-clásico)
- [Direccionamiento IP](#️-direccionamiento-ip)
- [R1 — Nodo de tránsito (ISP)](#-r1--nodo-de-tránsito--isp)
- [R2 — Gateway del cliente + NAT](#️-r2--gateway-del-lado-cliente)
- [R3 — Servidor VPN (LNS)](#️-r3--servidor-vpn--lns-l2tpipsec)
- [Switch1 — VLAN 10](#-switch1--lado-cliente--vlan-10)
- [Switch2 — VLAN 20](#-switch2--lan-protegida--vlan-20)
- [PC2 — VPCS](#-pc2--consola-vpcs)
- [Cliente Windows — Configuración GUI](#-windows10-1--configuración-del-túnel-vía-interfaz-gráfica)
- [Cliente Linux — Alternativa](#-cliente-linux--alternativa-networkmanager-l2tp--strongswan--xl2tpd)
- [Verificación final](#-verificación-final--el-túnel-l2tpipsec-funciona)

---

## 🗺️ Resumen de la topología

```
Windows10-1 ── Switch1 ── R2 ── R1 (ISP/Tránsito) ── R3 ── Switch2 ── PC2
 (Cliente VPN)   VLAN10   Gateway            Servidor VPN   VLAN20   (Host destino)
                          Cliente             LNS
                          (NAT overload)
```

| Rol | Dispositivo |
|---|---|
| Nodo central de tránsito (ISP) | **R1** |
| Gateway/ISP del lado Cliente | **R2** |
| Servidor VPN — LNS (L2TP/IPsec) | **R3** |
| Switch lado Cliente (VLAN 10) | **Switch1** |
| Switch lado LAN protegida (VLAN 20) | **Switch2** |
| Cliente VPN (Windows) | **Windows10-1** (NIC1) |
| Host destino en la LAN protegida | **PC2** (VPCS) |

> ⚠️ **Restricción de diseño:** R1 representa el **ISP** y solo tiene direccionamiento IP público en sus interfaces. **No lleva ninguna ruta estática ni protocolo de enrutamiento configurado.** Por eso el acceso hacia/desde las LANs privadas (10.13.67.0/24 y 20.13.67.0/24) se resuelve con **NAT overload (PAT) en R2**, no con rutas en el ISP.

---

## 📌 ¿Por qué L2TP/IPsec y no un site-to-site clásico?

| Aspecto | Site-to-Site (DMVPN/GRE+IPsec) | Client-to-Site (L2TP/IPsec) |
|---|---|---|
| Extremos del túnel | Dos routers (red a red) | Un **host remoto** (PC/laptop) y un router (LNS) |
| Protocolo de transporte | GRE multipunto (mGRE) | **L2TP** (UDP 1701) sobre **PPP** |
| Autenticación de usuario | No aplica (autentica el router) | **Sí** — usuario/contraseña vía PPP (MS-CHAPv2) |
| Modo IPsec | Puede ser túnel o transporte | **Transporte** (L2TP ya encapsula, IPsec solo cifra el UDP) |
| Asignación de IP al remoto | Ruta estática/dinámica normal | **Pool de direcciones** entregado por PPP |
| Versión de IKE típica | IKEv2 (moderno) | **IKEv1** — único soportado por el cliente nativo de Windows |

---

## 🗺️ Direccionamiento IP

| Dispositivo | Interfaz | Dirección IP | Descripción |
|---|---|---|---|
| R1 | Fa0/0 | `200.13.67.1/30` | Enlace a R2 (IP pública) |
| R1 | Fa0/1 | `200.13.67.5/30` | Enlace a R3 (IP pública) |
| R2 | Fa0/0 | `200.13.67.2/30` | WAN hacia R1 (ISP) — IP pública NAT |
| R2 | Fa0/1 | `10.13.67.1/24` | LAN cliente — VLAN 10 (privada) |
| R3 | Fa0/0 | `200.13.67.6/30` | WAN hacia R1 — **IP pública del servidor VPN** |
| R3 | Fa0/1 | `20.13.67.1/24` | LAN protegida — VLAN 20 |
| R3 | Virtual-Template1 | *(unnumbered a Fa0/1)* | Interfaz virtual PPP para clientes L2TP |
| Windows10-1 | NIC1 | `10.13.67.10/24` GW `10.13.67.1` | Cliente VPN (equipo remoto) |
| PC2 | NIC | `20.13.67.10/24` GW `20.13.67.1` | Host destino protegido |
| Pool VPN | — | `192.168.100.10 – 192.168.100.20` | Asignado por PPP al conectar |

---

## 🌐 R1 — Nodo de tránsito / ISP

### ⚙️ Configuración de Interfaz

```bash
configure terminal
hostname R1

interface FastEthernet0/0
 description ENLACE_A_R2
 ip address 200.13.67.1 255.255.255.252
 no shutdown

interface FastEthernet0/1
 description ENLACE_A_R3
 ip address 200.13.67.5 255.255.255.252
 no shutdown

end
write
```

> ✅ R1 **no lleva ninguna ruta estática ni protocolo de enrutamiento** (sin `ip route`, sin OSPF/EIGRP). Solo conoce sus dos redes conectadas directamente. Todo el tráfico que cruza el ISP viaja entre IPs públicas (`200.13.67.2` ⇄ `200.13.67.6`) gracias al NAT hecho en R2.

---

## 🛡️ R2 — Gateway del lado Cliente

### ⚙️ Configuración de Interfaz

```bash
configure terminal
hostname R2

interface FastEthernet0/0
 description WAN_HACIA_ISP_R1
 ip address 200.13.67.2 255.255.255.252
 no shutdown

interface FastEthernet0/1
 description LAN_CLIENTE_VLAN10
 ip address 10.13.67.1 255.255.255.0
 no shutdown

end
```

### 🧭 Configuración de Enrutamiento

```bash
ip route 200.13.67.4 255.255.255.252 200.13.67.1

end
```

### 🔁 Configuración de NAT (PAT / Overload)

> Como el ISP (R1) no puede tener rutas hacia `10.13.67.0/24`, el cliente sale a Internet **traducido** a la IP pública de R2 (`200.13.67.2`). Así R1 nunca necesita saber de la LAN privada.

```bash
configure terminal

ip access-list standard NAT_CLIENTE
 permit 10.13.67.0 0.0.0.255

interface FastEthernet0/1
 ip nat inside

interface FastEthernet0/0
 ip nat outside

ip nat inside source list NAT_CLIENTE interface FastEthernet0/0 overload

end
write
```

> 📌 **NAT-T:** como el tráfico IPsec pasa por NAT, el cliente (Windows o Linux) debe negociar **NAT-Traversal (UDP 4500)**. El cliente nativo de Windows lo detecta automáticamente. En Linux/strongSwan, si no se activa solo, forzar con `forceencaps=yes` en `ipsec.conf`.

---

## 🛡️ R3 — Servidor VPN / LNS (L2TP/IPsec)

### ⚙️ Configuración de Interfaz

```bash
configure terminal
hostname R3

interface FastEthernet0/0
 description WAN_HACIA_ISP_R1_IP_PUBLICA
 ip address 200.13.67.6 255.255.255.252
 no shutdown

interface FastEthernet0/1
 description LAN_PROTEGIDA_VLAN20
 ip address 20.13.67.1 255.255.255.0
 no shutdown

end
```

### 🔑 Configuración de Fase 1 — IKEv1 (crypto isakmp)

```bash
crypto isakmp policy 10
 encr aes 256
 hash sha
 authentication pre-share
 group 5
 lifetime 86400

crypto isakmp policy 20
 encr 3des
 hash sha
 authentication pre-share
 group 2
 lifetime 86400

crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0

crypto isakmp keepalive 10 3
```

### 🔒 Configuración de Fase 2 — IPsec (Transform-Set, modo transporte)

```bash
crypto ipsec transform-set TSET_L2TP esp-aes 256 esp-sha-hmac
 mode transport

crypto ipsec transform-set TSET_L2TP_LEGACY esp-3des esp-sha-hmac
 mode transport

crypto dynamic-map DYNMAP_L2TP 10
 set transform-set TSET_L2TP TSET_L2TP_LEGACY
 set security-association lifetime seconds 3600

crypto map CMAP_L2TP 10 ipsec-isakmp dynamic DYNMAP_L2TP
```

### 🔗 Aplicación del Crypto Map en la interfaz WAN

```bash
interface FastEthernet0/0
 crypto map CMAP_L2TP
```

### 👤 Configuración de AAA y Base de Usuarios (PPP)

```bash
aaa new-model
aaa authentication ppp default local
aaa authorization network default local

username vpnuser secret cisco123

ip local pool POOL_L2TP 192.168.100.10 192.168.100.20
```

### 📡 Configuración de L2TP (VPDN + Virtual-Template)

```bash
vpdn enable
vpdn-group VPDN_L2TP_WINDOWS
 accept-dialin
  protocol l2tp
  virtual-template 1
 no l2tp tunnel authentication

interface Virtual-Template1
 ip unnumbered FastEthernet0/1
 peer default ip address pool POOL_L2TP
 ppp authentication ms-chap-v2 chap pap
 ppp encrypt mppe auto
```

### 🧭 Configuración de Enrutamiento

```bash
ip route 200.13.67.0 255.255.255.252 200.13.67.5

end
write
```

---

## 🖧 Switch1 — Lado Cliente (VLAN 10)

### ⚙️ Configuración de Interfaz

```bash
configure terminal
hostname Switch1

vlan 10
 name VLAN_CLIENTE_VPN

interface Ethernet0/0
 description ENLACE_A_R2
 switchport mode access
 switchport access vlan 10
 switchport nonegotiate

interface Ethernet0/1
 description PC_WINDOWS10-1_NIC1
 switchport mode access
 switchport access vlan 10
 switchport nonegotiate

interface range Ethernet0/2 - 3
 switchport mode access
 switchport access vlan 999
 shutdown

vlan 999
 name VLAN_APAGADA_NO_USAR
```

### 🛡️ Configuración de Seguridad

```bash
enable secret cisco123
service password-encryption

interface Ethernet0/0
 spanning-tree portfast
 spanning-tree bpduguard enable

interface Ethernet0/1
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation restrict
 switchport port-security mac-address sticky
 spanning-tree portfast
 spanning-tree bpduguard enable

username admin secret cisco123
line vty 0 4
 login local
 transport input ssh
line con 0
 login local

end
write
```

---

## 🖧 Switch2 — LAN Protegida (VLAN 20)

### ⚙️ Configuración de Interfaz

```bash
configure terminal
hostname Switch2

vlan 20
 name VLAN_LAN_PROTEGIDA

interface Ethernet0/0
 description ENLACE_A_R3
 switchport mode access
 switchport access vlan 20
 switchport nonegotiate

interface Ethernet0/1
 description PC2_VPCS
 switchport mode access
 switchport access vlan 20
 switchport nonegotiate

interface range Ethernet0/2 - 3
 switchport mode access
 switchport access vlan 999
 shutdown

vlan 999
 name VLAN_APAGADA_NO_USAR
```

### 🛡️ Configuración de Seguridad

```bash
enable secret cisco123
service password-encryption

interface Ethernet0/0
 spanning-tree portfast
 spanning-tree bpduguard enable

interface Ethernet0/1
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation restrict
 switchport port-security mac-address sticky
 spanning-tree portfast
 spanning-tree bpduguard enable

username admin secret cisco123
line vty 0 4
 login local
 transport input ssh
line con 0
 login local

end
write
```

---

## 💻 PC2 — Consola VPCS

### ⚙️ Configuración de Interfaz

```bash
ip 20.13.67.10 255.255.255.0 20.13.67.1
save
```

---

## 🪟 Windows10-1 — Configuración del túnel (vía Interfaz Gráfica)

| Paso | Acción |
|---|---|
| 1 | Abrir **Configuración → Red e Internet → VPN → Agregar una conexión VPN** |
| 2 | Proveedor de VPN: **Windows (integrado)** |
| 3 | Nombre de la conexión: `VPN-R3-L2TP` |
| 4 | Nombre o dirección del servidor: **`200.13.67.6`** *(IP pública de R3)* |
| 5 | Tipo de VPN: **L2TP/IPsec con clave previamente compartida** |
| 6 | Clave precompartida: **`cisco123`** |
| 7 | Tipo de información de inicio de sesión: **Nombre de usuario y contraseña** → Usuario `vpnuser` / Contraseña `cisco123` |
| 8 | **Guardar** y presionar **Conectar** |

<details>
<summary>🧩 Alternativa por PowerShell</summary>

```powershell
Add-VpnConnection -Name "VPN-R3-L2TP" -ServerAddress "200.13.67.6" `
  -TunnelType L2tp -L2tpPsk "cisco123" -AuthenticationMethod MSChapv2 `
  -EncryptionLevel Required -AllUserConnection

rasdial "VPN-R3-L2TP" vpnuser cisco123
```

</details>

---

## 🐧 Cliente Linux — Alternativa (NetworkManager-l2tp / strongSwan + xl2tpd)

<details>
<summary>Opción A — GUI (NetworkManager-l2tp)</summary>

```bash
sudo apt install network-manager-l2tp network-manager-l2tp-gnome
```

Crear conexión VPN tipo **"Layer 2 Tunneling Protocol (L2TP)"**, apuntando a `200.13.67.6`, con **IPsec pre-shared key** `cisco123` y credenciales PPP `vpnuser` / `cisco123`.

</details>

<details>
<summary>Opción B — Manual (strongSwan + xl2tpd)</summary>

**`/etc/ipsec.conf`**
```bash
conn L2TP-PSK-R3
    keyexchange=ikev1
    authby=secret
    pfs=no
    rekey=no
    forceencaps=yes
    left=%defaultroute
    leftprotoport=17/1701
    right=200.13.67.6
    rightprotoport=17/1701
    auto=add
```

**`/etc/ipsec.secrets`**
```bash
%any 200.13.67.6 : PSK "cisco123"
```

**`/etc/xl2tpd/xl2tpd.conf`**
```bash
[lac r3-vpn]
lns = 200.13.67.6
ppp debug = yes
pppoptfile = /etc/ppp/options.l2tpd.client
length bit = yes
```

**`/etc/ppp/options.l2tpd.client`**
```bash
ipparam r3-vpn
require-mschap-v2
noccp
noauth
idle 1800
mtu 1410
mru 1410
defaultroute
usepeerdns
user "vpnuser"
password "cisco123"
```

**Levantar el túnel:**
```bash
sudo ipsec restart
sudo ipsec up L2TP-PSK-R3
sudo systemctl restart xl2tpd
echo "c r3-vpn" | sudo tee /var/run/xl2tpd/l2tp-control
```

</details>

---

## ✅ Verificación final — el túnel L2TP/IPsec funciona

![Fase1](https://img.shields.io/badge/Fase%201-QM__IDLE-2ea043?style=flat-square)
![Fase2](https://img.shields.io/badge/Fase%202-SA%20Activa-2ea043?style=flat-square)
![L2TP](https://img.shields.io/badge/Sesión%20L2TP-Establecida-2ea043?style=flat-square)
![NAT](https://img.shields.io/badge/NAT-Overload%20Activo-2ea043?style=flat-square)

### 1️⃣ Verificar NAT — en R2

```bash
show ip nat translations
show ip nat statistics
```
Debe mostrarse la traducción de `10.13.67.10` hacia `200.13.67.2` en el momento en que el cliente intenta negociar.

### 2️⃣ Verificar Fase 1 (ISAKMP SA) — en R3

```bash
show crypto isakmp sa
```
Debe mostrar el estado **QM_IDLE** con la IP pública de R2 (`200.13.67.2`) como peer — no la IP privada del cliente, ya que viene traducida.

### 3️⃣ Verificar Fase 2 (IPsec SA)

```bash
show crypto ipsec sa
```
Debe verse tráfico cifrado (`encaps`/`decaps` incrementando) sobre el par UDP 1701 (y UDP 4500 si hay NAT-T activo).

### 4️⃣ Verificar la sesión L2TP / PPP

```bash
show vpdn session all
show vpdn tunnel all
show caller ip
show interface virtual-access 1
```
`show caller ip` debe listar al usuario `vpnuser` con una IP asignada del pool `192.168.100.10–20`.

### 5️⃣ Verificar enrutamiento

```bash
show ip route
```
En R1 confirma que **no hay ninguna ruta configurada** (solo las dos conectadas). En R2 y R3, confirma las rutas hacia el otro extremo `/30`.

### 6️⃣ Prueba de Conectividad End-to-End

**Desde Windows10-1 (VPN conectada):**
```bash
ping 20.13.67.10
```

**Desde PC2 (VPCS), hacia la IP asignada por R3:**
```bash
ping 192.168.100.10
```

---

<div align="center">

**TSI-203 — Seguridad de Redes** · ITLA — Instituto Tecnológico de las Américas

</div>
