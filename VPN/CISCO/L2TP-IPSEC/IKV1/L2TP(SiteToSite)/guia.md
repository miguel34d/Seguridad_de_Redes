# 🔐 VPN Site-to-Site — IPsec (IKEv1)

![Materia](https://img.shields.io/badge/Materia-TSI--203-1E1E1E?style=flat-square)
![Estado](https://img.shields.io/badge/Estado-Completado-2ea043?style=flat-square)
![Protocolo](https://img.shields.io/badge/Protocolo-IPsec%20IKEv1-red?style=flat-square)
![Topología](https://img.shields.io/badge/Topología-Site--to--Site-blue?style=flat-square)
![Fase1](https://img.shields.io/badge/Fase%201-ISAKMP%20PSK-orange?style=flat-square)
![Fase2](https://img.shields.io/badge/Fase%202-Modo%20Túnel-orange?style=flat-square)

![Herramientas](https://img.shields.io/badge/Herramientas-GNS3%20%7C%20Cisco%20IOS%20%7C%20VPCS-6f42c1?style=flat-square)

**Sitio A (LAN cliente):** R2 → red `10.13.67.0/24` &nbsp;↔&nbsp; **Sitio B (LAN protegida):** R3 → red `20.13.67.0/24`

---

## 📑 Tabla de contenido

- [Resumen de la topología](#-resumen-de-la-topología)
- [Diferencias vs. Client-to-Site (L2TP)](#-diferencias-vs-client-to-site-l2tp)
- [Direccionamiento IP](#️-direccionamiento-ip)
- [R1 — Nodo de tránsito (ISP)](#-r1--nodo-de-tránsito--isp)
- [R2 — Extremo VPN Sitio A](#️-r2--extremo-vpn-sitio-a)
- [R3 — Extremo VPN Sitio B](#️-r3--extremo-vpn-sitio-b)
- [Switch1 — VLAN 10](#-switch1--lado-cliente--vlan-10)
- [Switch2 — VLAN 20](#-switch2--lan-protegida--vlan-20)
- [PC2 — VPCS](#-pc2--consola-vpcs)
- [Verificación final](#-verificación-final--el-túnel-ipsec-funciona)

---

## 🗺️ Resumen de la topología

```
       (Sitio A)                                            (Sitio B)
  10.13.67.0/24 ── R2 ── R1 (ISP/Tránsito) ── R3 ── 20.13.67.0/24
   LAN cliente     Extremo VPN            Extremo VPN     LAN protegida
                   (crypto map)            (crypto map)
```

| Rol | Dispositivo |
|---|---|
| Nodo central de tránsito (ISP) | **R1** |
| Extremo VPN — Sitio A | **R2** |
| Extremo VPN — Sitio B | **R3** |
| Switch Sitio A (VLAN 10) | **Switch1** |
| Switch Sitio B (VLAN 20) | **Switch2** |
| Host en Sitio A | (opcional, VLAN 10) |
| Host en Sitio B | **PC2** (VPCS) |

---

## 📌 Diferencias vs. Client-to-Site (L2TP)

| Aspecto | Client-to-Site (L2TP/IPsec) | Site-to-Site (IPsec puro) |
|---|---|---|
| Extremos del túnel | Host remoto (PC) ↔ Router | **Router ↔ Router** (red a red) |
| Encapsulamiento | L2TP sobre PPP, cifrado con IPsec | **Solo IPsec**, sin L2TP ni PPP |
| Modo IPsec | Transporte (L2TP ya encapsula) | **Túnel** (IPsec encapsula el paquete IP completo) |
| Autenticación de usuario | Sí (AAA/PPP, usuario y contraseña) | No aplica — autentica el router (PSK) |
| Tráfico interesante | Todo el tráfico UDP 1701/500/4500 hacia la IP del LNS | Definido por **ACL** (solo `10.13.67.0/24 ⇄ 20.13.67.0/24`) |
| Asignación de IP | Pool PPP al cliente remoto | No aplica — las LANs ya tienen direccionamiento fijo |
| NAT necesario en el ISP | No aplicable (client-to-site no cambia esto) | **No** — el ISP nunca ve las IPs privadas en ninguno de los dos casos |

---

## 🗺️ Direccionamiento IP

| Dispositivo | Interfaz | Dirección IP | Descripción |
|---|---|---|---|
| R1 | Fa0/0 | `200.13.67.1/30` | Enlace a R2 (IP pública) |
| R1 | Fa0/1 | `200.13.67.5/30` | Enlace a R3 (IP pública) |
| R2 | Fa0/0 | `200.13.67.2/30` | WAN — extremo VPN Sitio A |
| R2 | Fa0/1 | `10.13.67.1/24` | LAN Sitio A — VLAN 10 |
| R3 | Fa0/0 | `200.13.67.6/30` | WAN — extremo VPN Sitio B |
| R3 | Fa0/1 | `20.13.67.1/24` | LAN Sitio B — VLAN 20 |
| PC2 | NIC | `20.13.67.10/24` GW `20.13.67.1` | Host destino en Sitio B |

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

---

## 🛡️ R2 — Extremo VPN Sitio A

### ⚙️ Configuración de Interfaz

```bash
configure terminal
hostname R2

interface FastEthernet0/0
 description WAN_HACIA_ISP_R1
 ip address 200.13.67.2 255.255.255.252
 no shutdown

interface FastEthernet0/1
 description LAN_SITIO_A_VLAN10
 ip address 10.13.67.1 255.255.255.0
 no shutdown

end
```

### 🧭 Configuración de Enrutamiento

```bash
ip route 0.0.0.0 0.0.0.0 200.13.67.1

end
```

### 🔑 Fase 1 — IKEv1 (crypto isakmp)

```bash
crypto isakmp policy 10
 encr aes 256
 hash sha
 authentication pre-share
 group 5
 lifetime 86400

crypto isakmp key cisco123 address 200.13.67.6
```

### 🔒 Fase 2 — IPsec (Transform-Set, modo túnel)

```bash
crypto ipsec transform-set TSET_SITE2SITE esp-aes 256 esp-sha-hmac
 mode tunnel
```

### 🎯 ACL de tráfico interesante

```bash
ip access-list extended ACL_VPN_SITIO_A
 permit ip 10.13.67.0 0.0.0.255 20.13.67.0 0.0.0.255
```

### 🗺️ Crypto Map (estático, apunta directo al peer)

```bash
crypto map CMAP_SITE2SITE 10 ipsec-isakmp
 set peer 200.13.67.6
 set transform-set TSET_SITE2SITE
 set security-association lifetime seconds 3600
 match address ACL_VPN_SITIO_A
```

### 🔗 Aplicación en la interfaz WAN

```bash
interface FastEthernet0/0
 crypto map CMAP_SITE2SITE

end
write
```

---

## 🛡️ R3 — Extremo VPN Sitio B

### ⚙️ Configuración de Interfaz

```bash
configure terminal
hostname R3

interface FastEthernet0/0
 description WAN_HACIA_ISP_R1
 ip address 200.13.67.6 255.255.255.252
 no shutdown

interface FastEthernet0/1
 description LAN_SITIO_B_VLAN20
 ip address 20.13.67.1 255.255.255.0
 no shutdown

end
```

### 🧭 Configuración de Enrutamiento

```bash
ip route 0.0.0.0 0.0.0.0 200.13.67.5

end
```

### 🔑 Fase 1 — IKEv1 (crypto isakmp)

```bash
crypto isakmp policy 10
 encr aes 256
 hash sha
 authentication pre-share
 group 5
 lifetime 86400

crypto isakmp key cisco123 address 200.13.67.2
```

### 🔒 Fase 2 — IPsec (Transform-Set, modo túnel)

```bash
crypto ipsec transform-set TSET_SITE2SITE esp-aes 256 esp-sha-hmac
 mode tunnel
```

### 🎯 ACL de tráfico interesante (espejo de la de R2)

```bash
ip access-list extended ACL_VPN_SITIO_B
 permit ip 20.13.67.0 0.0.0.255 10.13.67.0 0.0.0.255
```

### 🗺️ Crypto Map (estático, apunta directo al peer)

```bash
crypto map CMAP_SITE2SITE 10 ipsec-isakmp
 set peer 200.13.67.2
 set transform-set TSET_SITE2SITE
 set security-association lifetime seconds 3600
 match address ACL_VPN_SITIO_B
```

### 🔗 Aplicación en la interfaz WAN

```bash
interface FastEthernet0/0
 crypto map CMAP_SITE2SITE

end
write
```

---

## 🖧 Switch1 — Sitio A (VLAN 10)

```bash
configure terminal
hostname Switch1

vlan 10
 name VLAN_SITIO_A

interface Ethernet0/0
 description ENLACE_A_R2
 switchport mode access
 switchport access vlan 10
 switchport nonegotiate

interface range Ethernet0/1 - 3
 switchport mode access
 switchport access vlan 999
 shutdown

vlan 999
 name VLAN_APAGADA_NO_USAR

enable secret cisco123
service password-encryption

interface Ethernet0/0
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

## 🖧 Switch2 — Sitio B (VLAN 20)

```bash
configure terminal
hostname Switch2

vlan 20
 name VLAN_SITIO_B

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

```bash
ip 20.13.67.10 255.255.255.0 20.13.67.1
save
```

---

## ✅ Verificación final — el túnel IPsec funciona

![Fase1](https://img.shields.io/badge/Fase%201-QM__IDLE-2ea043?style=flat-square)
![Fase2](https://img.shields.io/badge/Fase%202-SA%20Activa-2ea043?style=flat-square)

### 1️⃣ Verificar Fase 1 (ISAKMP SA) — en R2 y en R3

```bash
show crypto isakmp sa
```

### 2️⃣ Verificar Fase 2 (IPsec SA)

```bash
show crypto ipsec sa
```

### 3️⃣ Verificar el crypto map aplicado

```bash
show crypto map
```

### 4️⃣ Verificar enrutamiento

```bash
show ip route
```

### 5️⃣ Prueba de Conectividad End-to-End

**Desde un host en la LAN de R2 (Sitio A, `10.13.67.0/24`):**
```bash
ping 20.13.67.10
```

**Desde PC2 (VPCS, Sitio B):**
```bash
ping 10.13.67.1
```

---

<div align="center">

**TSI-203 — Seguridad de Redes** · ITLA — Instituto Tecnológico de las Américas

</div>
