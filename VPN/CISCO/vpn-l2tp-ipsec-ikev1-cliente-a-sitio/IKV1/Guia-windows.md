# 🔐 GUÍA DE CONFIGURACIÓN — VPN CLIENT-TO-SITE L2TP/IPsec (IKEv1)

**Materia:** TSI-203 — Seguridad de Redes
**Topología:** Windows10-1 (Cliente VPN) ←→ Switch1 ←→ R2 ←→ R1 (ISP/Tránsito) ←→ R3 (Servidor VPN / LNS) ←→ Switch2 ←→ PC2
**Modalidad:** VPN Client-to-Site (punto a multipunto) — **L2TP sobre IPsec**
**Fase 1 (IKE):** IKEv1 (`crypto isakmp`), clave precompartida — **Fase 2 (IPsec):** Transform-Set en **modo transporte** (protege el UDP 1701 de L2TP)
**Servidor L2TP (LNS):** R3, mediante `vpdn` + `Virtual-Template` + PPP (MS-CHAPv2)
**Cliente:** nativo de Windows 10/11 (o Linux con NetworkManager-l2tp / strongSwan + xl2tpd)

| Rol | Nombre Asignado |
|---|---|
| Nodo central de tránsito (ISP) | **R1** |
| Gateway/ISP del lado Cliente | **R2** |
| Servidor VPN — LNS (L2TP/IPsec) | **R3** |
| Switch lado Cliente (VLAN 10) | **Switch1** |
| Switch lado LAN protegida (VLAN 20) | **Switch2** |
| Cliente VPN (Windows) | **Windows10-1** (NIC1) |
| Host destino en la LAN protegida | **PC2** (VPCS) |

---

## 📌 ¿Por qué L2TP/IPsec y no un site-to-site clásico?

| Aspecto | Site-to-Site (DMVPN/GRE+IPsec) | Client-to-Site (L2TP/IPsec) |
|---|---|---|
| Extremos del túnel | Dos routers (red a red) | Un **host remoto** (PC/laptop) y un router (LNS) |
| Protocolo de transporte | GRE multipunto (mGRE) | **L2TP** (UDP 1701) sobre **PPP** |
| Autenticación de usuario | No aplica (autentica el router) | **Sí** — usuario/contraseña vía PPP (MS-CHAPv2) |
| Modo IPsec | Puede ser túnel o transporte | **Transporte** (L2TP ya encapsula, IPsec solo cifra el UDP) |
| Asignación de IP al remoto | Ruta estática/dinámica normal | **Pool de direcciones** entregado por PPP (`peer default ip address pool`) |
| Versión de IKE típica | IKEv2 (moderno) | **IKEv1** — es el único soportado por el cliente nativo L2TP/IPsec de Windows |

> 💡 El cliente VPN incorporado de Windows para "L2TP/IPsec con clave precompartida" **solo negocia IKEv1**. Por eso R3 usa `crypto isakmp` (Fase 1 clásica) y no `crypto ikev2`.

---

## 🗺️ Direccionamiento IP

| Dispositivo | Interfaz | Dirección IP | Descripción |
|---|---|---|---|
| R1 | Fa0/0 | 200.13.67.1/30 | Enlace a R2 |
| R1 | Fa0/1 | 200.13.67.5/30 | Enlace a R3 |
| R2 | Fa0/0 | 200.13.67.2/30 | WAN hacia R1 (ISP) |
| R2 | Fa0/1 | 10.10.10.1/24 | LAN cliente — VLAN 10 |
| R3 | Fa0/0 | 200.13.67.6/30 | WAN hacia R1 (ISP) — **IP pública del servidor VPN** |
| R3 | Fa0/1 | 10.20.20.1/24 | LAN protegida — VLAN 20 |
| R3 | Virtual-Template1 | *(unnumbered a Fa0/1)* | Interfaz virtual PPP para clientes L2TP |
| Windows10-1 | NIC1 | 10.10.10.10/24 GW 10.10.10.1 | Cliente VPN (equipo remoto) |
| PC2 | NIC | 10.20.20.10/24 GW 10.20.20.1 | Host destino protegido |
| Pool VPN (clientes remotos) | — | 192.168.100.10 – 192.168.100.20 | Asignado por PPP al conectar el túnel |

---

# 🌐 ROUTER: R1 *(Nodo de tránsito / ISP)*

## ► Aplicación de Interfaces

```
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

> 📌 R1 solo cumple el rol de **tránsito** (equivalente al ISP): ambos enlaces /30 quedan directamente conectados en su tabla de rutas, por lo que no requiere rutas estáticas adicionales ni participa en el túnel L2TP/IPsec — simplemente reenvía el tráfico IP entre R2 y R3.

---

# 🛡️ ROUTER: R2 *(Gateway del lado Cliente)*

## ► Aplicación de Interfaces

```
configure terminal
hostname R2

interface FastEthernet0/0
 description WAN_HACIA_ISP_R1
 ip address 200.13.67.2 255.255.255.252
 no shutdown

interface FastEthernet0/1
 description LAN_CLIENTE_VLAN10
 ip address 10.10.10.1 255.255.255.0
 no shutdown

end
```

## ► Aplicación de Enrutamiento Estático (alcance WAN)

```
ip route 200.13.67.4 255.255.255.252 200.13.67.1

end
write
```

> 📌 R2 **no participa en la negociación L2TP/IPsec**, solo provee salida a Internet/WAN para el equipo Windows10-1 (rol equivalente al router doméstico/ISP del cliente remoto). El túnel real se establece **directamente entre Windows10-1 y R3** (extremo a extremo, IP pública 200.13.67.6), pasando de forma transparente por R2 y R1.

---

# 🛡️ ROUTER: R3 *(Servidor VPN — LNS L2TP/IPsec)*

## ► Aplicación de Interfaces

```
configure terminal
hostname R3

interface FastEthernet0/0
 description WAN_HACIA_ISP_R1_IP_PUBLICA
 ip address 200.13.67.6 255.255.255.252
 no shutdown

interface FastEthernet0/1
 description LAN_PROTEGIDA_VLAN20
 ip address 10.20.20.1 255.255.255.0
 no shutdown

end
```

## ► Aplicación de IKEv1 — Fase 1 (crypto isakmp)

```
crypto isakmp policy 10
 encr aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400

crypto isakmp policy 20
 encr 3des
 hash sha
 authentication pre-share
 group 2
 lifetime 86400

crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0

crypto isakmp nat-traversal 20
crypto isakmp keepalive 10 3
```

> ⚠️ Se incluyen **dos políticas ISAKMP**: la `policy 10` (AES-256/SHA-256/DH14, más segura) y la `policy 20` (3DES/SHA1/DH2, la que el cliente nativo de Windows propone **por defecto** sin tocar el registro). Si solo se deja la política fuerte, un Windows sin ajustes de registro (`NegotiateDH2048_AES256`) **no podrá negociar Fase 1** y el túnel fallará silenciosamente.

## ► Aplicación de IPsec — Fase 2 (Transform-Set, modo transporte)

```
crypto ipsec transform-set TSET_L2TP esp-aes 256 esp-sha256-hmac
 mode transport

crypto ipsec transform-set TSET_L2TP_LEGACY esp-3des esp-sha-hmac
 mode transport

crypto dynamic-map DYNMAP_L2TP 10
 set transform-set TSET_L2TP TSET_L2TP_LEGACY
 set security-association lifetime seconds 3600

crypto map CMAP_L2TP 10 ipsec-isakmp dynamic DYNMAP_L2TP
```

> 💡 Se usa **modo transporte** (no túnel) porque L2TP ya encapsula el tráfico de usuario en un paquete PPP/UDP 1701; IPsec solo necesita cifrar ese datagrama UDP, no volver a encapsular una IP dentro de otra IP. Además se usa un **crypto map dinámico** (no una ACL fija) porque el cliente remoto puede tener cualquier IP pública — no se conoce de antemano.

## ► Aplicación del Crypto Map en la interfaz WAN

```
interface FastEthernet0/0
 crypto map CMAP_L2TP
```

## ► Aplicación de AAA y Base de Usuarios (autenticación PPP)

```
aaa new-model
aaa authentication ppp default local
aaa authorization network default local

username vpnuser secret cisco123

ip local pool POOL_L2TP 192.168.100.10 192.168.100.20
```

## ► Aplicación de L2TP (VPDN + Virtual-Template)

```
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

> 💡 `virtual-template 1` es la plantilla que Cisco IOS clona dinámicamente en una interfaz **Virtual-Access** cada vez que un cliente L2TP se conecta. `ip unnumbered FastEthernet0/1` hace que la interfaz virtual "tome prestada" la subred de la LAN protegida (10.20.20.0/24), de modo que el cliente remoto (con IP del pool 192.168.100.0/24) quede enrutable hacia/desde PC2 sin NAT. `ppp authentication ms-chap-v2` es el método que el cliente nativo de Windows usa por defecto.

## ► Aplicación de Enrutamiento Estático (alcance WAN)

```
ip route 200.13.67.0 255.255.255.252 200.13.67.5

end
write
```

---

# 🖧 SWITCH: Switch1 *(Lado Cliente — VLAN 10)*

## ► Aplicación de VLAN y Seguridad de Puertos

```
configure terminal
hostname Switch1

enable secret cisco123
service password-encryption

vlan 10
 name VLAN_CLIENTE_VPN

interface Ethernet0/0
 description ENLACE_A_R2
 switchport mode access
 switchport access vlan 10
 switchport nonegotiate
 spanning-tree portfast
 spanning-tree bpduguard enable

interface Ethernet0/1
 description PC_WINDOWS10-1_NIC1
 switchport mode access
 switchport access vlan 10
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation restrict
 switchport port-security mac-address sticky
 switchport nonegotiate
 spanning-tree portfast
 spanning-tree bpduguard enable

interface range Ethernet0/2 - 3
 switchport mode access
 switchport access vlan 999
 shutdown

vlan 999
 name VLAN_APAGADA_NO_USAR

username admin secret cisco123
line vty 0 4
 login local
 transport input ssh
line con 0
 login local

end
write
```

> 📌 `switchport port-security maximum 1` + `mac-address sticky` asegura que **solo la NIC1 de Windows10-1** puede usar ese puerto: si alguien desconecta el equipo y conecta otro dispositivo, el puerto entra en modo `restrict` (descarta tráfico ilegítimo y genera log, sin apagar el puerto). Los puertos sin uso se mueven a una VLAN "basurero" (999) y se apagan (`shutdown`) para evitar accesos no autorizados.

---

# 🖧 SWITCH: Switch2 *(LAN Protegida — VLAN 20)*

## ► Aplicación de VLAN y Seguridad de Puertos

```
configure terminal
hostname Switch2

enable secret cisco123
service password-encryption

vlan 20
 name VLAN_LAN_PROTEGIDA

interface Ethernet0/0
 description ENLACE_A_R3
 switchport mode access
 switchport access vlan 20
 switchport nonegotiate
 spanning-tree portfast
 spanning-tree bpduguard enable

interface Ethernet0/1
 description PC2_VPCS
 switchport mode access
 switchport access vlan 20
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation restrict
 switchport port-security mac-address sticky
 switchport nonegotiate
 spanning-tree portfast
 spanning-tree bpduguard enable

interface range Ethernet0/2 - 3
 switchport mode access
 switchport access vlan 999
 shutdown

vlan 999
 name VLAN_APAGADA_NO_USAR

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

# 💻 TERMINAL: PC2 (Consola VPCS)

## ► Aplicación de Direccionamiento IP

```
ip 10.20.20.10 255.255.255.0 10.20.20.1
save
```

---

# 🪟 CLIENTE: Windows10-1 — Configuración del túnel L2TP/IPsec

## ► Opción A — Interfaz gráfica

1. **Configuración → Red e Internet → VPN → Agregar una conexión VPN**
2. Proveedor de VPN: **Windows (integrado)**
3. Nombre de la conexión: `VPN-R3-L2TP`
4. Nombre o dirección del servidor: **`200.13.67.6`** *(IP pública de R3)*
5. Tipo de VPN: **L2TP/IPsec con clave previamente compartida**
6. Clave precompartida: **`cisco123`**
7. Tipo de información de inicio de sesión: **Nombre de usuario y contraseña**
   - Usuario: `vpnuser`
   - Contraseña: `cisco123`
8. Guardar y **Conectar**

## ► Opción B — PowerShell

```powershell
Add-VpnConnection -Name "VPN-R3-L2TP" -ServerAddress "200.13.67.6" `
  -TunnelType L2tp -L2tpPsk "cisco123" -AuthenticationMethod MSChapv2 `
  -EncryptionLevel Required -AllUserConnection

rasdial "VPN-R3-L2TP" vpnuser cisco123
```

> ⚠️ Si el servidor VPN (R3) estuviera detrás de NAT (no es el caso en esta topología, ya que 200.13.67.6 es una IP pública/directa), sería necesario el ajuste de registro `AssumeUDPEncapsulationContextOnSendRule` en el cliente Windows para permitir NAT-T. En este laboratorio **no aplica**.

---

# 🐧 CLIENTE: Linux — Alternativa (NetworkManager-l2tp o strongSwan + xl2tpd)

## ► Opción A — GUI (NetworkManager-l2tp)

```
sudo apt install network-manager-l2tp network-manager-l2tp-gnome
```
Crear conexión VPN tipo **"Layer 2 Tunneling Protocol (L2TP)"**, apuntando a `200.13.67.6`, con **IPsec pre-shared key** `cisco123` y credenciales PPP `vpnuser` / `cisco123`.

## ► Opción B — Manual (strongSwan + xl2tpd)

**`/etc/ipsec.conf`**
```
conn L2TP-PSK-R3
    keyexchange=ikev1
    authby=secret
    pfs=no
    rekey=no
    left=%defaultroute
    leftprotoport=17/1701
    right=200.13.67.6
    rightprotoport=17/1701
    auto=add
```

**`/etc/ipsec.secrets`**
```
%any 200.13.67.6 : PSK "cisco123"
```

**`/etc/xl2tpd/xl2tpd.conf`**
```
[lac r3-vpn]
lns = 200.13.67.6
ppp debug = yes
pppoptfile = /etc/ppp/options.l2tpd.client
length bit = yes
```

**`/etc/ppp/options.l2tpd.client`**
```
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

Levantar el túnel:
```
sudo ipsec restart
sudo ipsec up L2TP-PSK-R3
sudo systemctl restart xl2tpd
echo "c r3-vpn" | sudo tee /var/run/xl2tpd/l2tp-control
```

---

# ✅ VERIFICACIÓN FINAL — EL TÚNEL L2TP/IPsec FUNCIONA

## ► 1. Verificar Fase 1 (ISAKMP SA) — en R3

```
show crypto isakmp sa
```
Debe mostrar el estado **QM_IDLE** con la IP pública/actual de Windows10-1 (o su NAT/ISP) como peer.

## ► 2. Verificar Fase 2 (IPsec SA)

```
show crypto ipsec sa
```
Debe verse tráfico cifrado (`encaps`/`decaps` incrementando) sobre el par UDP 1701.

## ► 3. Verificar la sesión L2TP / PPP

```
show vpdn session all
show vpdn tunnel all
show caller ip
show interface virtual-access 1
```
`show caller ip` debe listar al usuario `vpnuser` con una IP asignada del pool `192.168.100.10–20`.

## ► 4. Verificar enrutamiento

```
show ip route
```
La red del pool VPN debe verse alcanzable a través de la interfaz Virtual-Access clonada.

## ► 5. Prueba de Conectividad End-to-End

**Desde Windows10-1 (una vez conectada la VPN):**
```
ping 10.20.20.10
```

**Desde PC2 (VPCS), hacia la IP que R3 asignó al cliente:**
```
ping 192.168.100.10
```

> 💡 Si el `ping` desde Windows10-1 falla pero la Fase 1/Fase 2 muestran SA activas, revisar el firewall de Windows (puede bloquear ICMP de salida) y confirmar que la ruta por defecto de la VPN no esté forzando todo el tráfico por el túnel de forma que rompa la resolución DNS local (desmarcar *"Usar la puerta de enlace predeterminada de la red remota"* si solo se necesita acceso dividido/split-tunnel a la LAN protegida).
