# 🔐 GUÍA DE CONFIGURACIÓN — VPN SITE-TO-SITE IPSec (IKEv2)

**Materia:** TSI-203 — Seguridad de Redes
**Topología:** PC1 → Switch-A → PearA ←→ ISP ←→ PearB ← Switch-B ← PC2
**Direccionamiento privado:** 10.13.67.x
**Direccionamiento público:** 200.13.67.x

| Nombre en Topología | Rol | Nombre Asignado |
|---|---|---|
| Router1 | Nodo central de tránsito | **ISP** |
| Router2 | Sitio izquierdo (VLAN 10) | **PearA** |
| Router3 | Sitio derecho (VLAN 20) | **PearB** |
| Switch1 | Switch sitio izquierdo | **Switch-A** |
| Switch2 | Switch sitio derecho | **Switch-B** |

---

# 🌐 ROUTER: ISP

> Rol de tránsito. No participa en la VPN, solo enruta entre los dos sitios.

## ► Aplicación de Interfaces

```
configure terminal
hostname ISP

interface Ethernet0/0
 description ENLACE_A_PEARA
 ip address 200.13.67.1 255.255.255.252
 no shutdown

interface Ethernet0/1
 description ENLACE_A_PEARB
 ip address 200.13.67.5 255.255.255.252
 no shutdown

end
write
```
🔚 *Cierre del bloque de interfaces.*

---

# 🛡️ ROUTER: PearA *(Sitio Izquierdo — VLAN 10)*

## ► Aplicación de Interfaces

```
configure terminal
hostname PearA

interface Ethernet0/0
 description WAN_HACIA_ISP
 ip address 200.13.67.2 255.255.255.252
 no shutdown

interface Ethernet0/1
 description LAN_VLAN10
 ip address 10.13.67.1 255.255.255.128
 no shutdown

end
```
🔚 *Cierre del bloque de interfaces.*

## ► Aplicación de Enrutamiento

```
ip route 0.0.0.0 0.0.0.0 200.13.67.1
```
🔚 *Cierre del bloque de enrutamiento.*

## ► Aplicación de ACL (Tráfico Interesante)

```
access-list 102 permit ip 10.13.67.0 0.0.0.127 10.13.67.128 0.0.0.127
```
🔚 *Cierre del bloque de ACL. Define qué tráfico entra al túnel.*

## ► Aplicación de IKEv2 — Fase 1

```
crypto ikev2 proposal PROP_IKEv2_TOP
 encryption aes-cbc-256
 integrity sha256
 group 14

crypto ikev2 policy POL_IKEv2_TOP
 proposal PROP_IKEv2_TOP
```
🔚 *Cierre del bloque de propuesta y política IKEv2.*

## ► Aplicación de Keyring y Perfil IKEv2

```
crypto ikev2 keyring KEYRING_PEAR
 peer PearB
  address 200.13.67.6
  pre-shared-key local cisco123
  pre-shared-key remote cisco123

crypto ikev2 profile PERFIL_IKEv2_PEAR
 match identity remote address 200.13.67.6 255.255.255.255
 identity local address 200.13.67.2
 authentication remote pre-share
 authentication local pre-share
 keyring local KEYRING_PEAR
```
🔚 *Cierre del bloque de autenticación (Fase 1 completa).*

## ► Aplicación de IPsec — Fase 2 (Transform-Set)

```
crypto ipsec transform-set TSET_IKEv2 esp-aes 256 esp-sha256-hmac
 mode tunnel
```
🔚 *Cierre del bloque de transform-set.*

## ► Aplicación de Crypto Map

```
crypto map MAPA_IKEv2_POL 10 ipsec-isakmp
 set peer 200.13.67.6
 set transform-set TSET_IKEv2
 set ikev2-profile PERFIL_IKEv2_PEAR
 match address 102

interface Ethernet0/0
 crypto map MAPA_IKEv2_POL

end
write
```
🔚 *Cierre del bloque de crypto map. Túnel activado en la interfaz WAN.*

---

# 🛡️ ROUTER: PearB *(Sitio Derecho — VLAN 20)*

## ► Aplicación de Interfaces

```
configure terminal
hostname PearB

interface Ethernet0/0
 description WAN_HACIA_ISP
 ip address 200.13.67.6 255.255.255.252
 no shutdown

interface Ethernet0/1
 description LAN_VLAN20
 ip address 10.13.67.129 255.255.255.128
 no shutdown

end
```
🔚 *Cierre del bloque de interfaces.*

## ► Aplicación de Enrutamiento

```
ip route 0.0.0.0 0.0.0.0 200.13.67.5
```
🔚 *Cierre del bloque de enrutamiento.*

## ► Aplicación de ACL (Tráfico Interesante — Espejo)

```
access-list 102 permit ip 10.13.67.128 0.0.0.127 10.13.67.0 0.0.0.127
```
🔚 *Cierre del bloque de ACL.*

## ► Aplicación de IKEv2 — Fase 1

```
crypto ikev2 proposal PROP_IKEv2_TOP
 encryption aes-cbc-256
 integrity sha256
 group 14

crypto ikev2 policy POL_IKEv2_TOP
 proposal PROP_IKEv2_TOP
```
🔚 *Cierre del bloque de propuesta y política IKEv2.*

## ► Aplicación de Keyring y Perfil IKEv2

```
crypto ikev2 keyring KEYRING_PEAR
 peer PearA
  address 200.13.67.2
  pre-shared-key local cisco123
  pre-shared-key remote cisco123

crypto ikev2 profile PERFIL_IKEv2_PEAR
 match identity remote address 200.13.67.2 255.255.255.255
 identity local address 200.13.67.6
 authentication remote pre-share
 authentication local pre-share
 keyring local KEYRING_PEAR
```
🔚 *Cierre del bloque de autenticación (Fase 1 completa).*

## ► Aplicación de IPsec — Fase 2 (Transform-Set)

```
crypto ipsec transform-set TSET_IKEv2 esp-aes 256 esp-sha256-hmac
 mode tunnel
```
🔚 *Cierre del bloque de transform-set.*

## ► Aplicación de Crypto Map

```
crypto map MAPA_IKEv2_POL 10 ipsec-isakmp
 set peer 200.13.67.2
 set transform-set TSET_IKEv2
 set ikev2-profile PERFIL_IKEv2_PEAR
 match address 102

interface Ethernet0/0
 crypto map MAPA_IKEv2_POL

end
write
```
🔚 *Cierre del bloque de crypto map. Túnel activado en la interfaz WAN.*

---

# 🔧 SWITCH: Switch-A *(Lado Izquierdo)*

## ► Aplicación de VLAN

```
configure terminal
hostname Switch-A

vlan 10
 name LAN_PEARA
exit
```
🔚 *Cierre del bloque de VLAN.*

## ► Aplicación de Modo Acceso

```
interface Ethernet0/0
 switchport mode access
 switchport access vlan 10

interface Ethernet0/1
 switchport mode access
 switchport access vlan 10
```
🔚 *Cierre del bloque de modo acceso.*

## ► Aplicación de Seguridad de Puerto (Port-Security)

```
interface Ethernet0/1
 switchport port-security
 switchport port-security maximum 1
 switchport port-security mac-address sticky
 switchport port-security violation restrict
```
🔚 *Cierre del bloque de port-security. Limita el puerto de PC1 a una sola MAC.*

## ► Aplicación de STP (Protección de Borde)

```
interface Ethernet0/0
 spanning-tree portfast
 spanning-tree bpduguard enable

interface Ethernet0/1
 spanning-tree portfast
 spanning-tree bpduguard enable

end
write
```
🔚 *Cierre del bloque de STP. Portfast + BPDU Guard evita ataques de manipulación de STP.*

---

# 🔧 SWITCH: Switch-B *(Lado Derecho)*

## ► Aplicación de VLAN

```
configure terminal
hostname Switch-B

vlan 20
 name LAN_PEARB
exit
```
🔚 *Cierre del bloque de VLAN.*

## ► Aplicación de Modo Acceso

```
interface Ethernet0/0
 switchport mode access
 switchport access vlan 20

interface Ethernet0/1
 switchport mode access
 switchport access vlan 20
```
🔚 *Cierre del bloque de modo acceso.*

## ► Aplicación de Seguridad de Puerto (Port-Security)

```
interface Ethernet0/1
 switchport port-security
 switchport port-security maximum 1
 switchport port-security mac-address sticky
 switchport port-security violation restrict
```
🔚 *Cierre del bloque de port-security. Limita el puerto de PC2 a una sola MAC.*

## ► Aplicación de STP (Protección de Borde)

```
interface Ethernet0/0
 spanning-tree portfast
 spanning-tree bpduguard enable

interface Ethernet0/1
 spanning-tree portfast
 spanning-tree bpduguard enable

end
write
```
🔚 *Cierre del bloque de STP.*

---

# 💻 TERMINALES: PC1 y PC2 (Consolas VPCS)

## ► Aplicación de Direccionamiento IP

```
* En PC1:
ip 10.13.67.10 255.255.255.128 10.13.67.1
save

* En PC2:
ip 10.13.67.140 255.255.255.128 10.13.67.129
save
```
🔚 *Cierre del bloque de direccionamiento.*

---

# ✅ VERIFICACIÓN FINAL — EL TÚNEL FUNCIONA

## ► 1. Verificar Fase 1 (IKEv2 SA) — en PearA y PearB

```
show crypto ikev2 sa
```
Debe mostrar el estado **READY** entre 200.13.67.2 ↔ 200.13.67.6.

## ► 2. Verificar Fase 2 (IPsec SA) — en PearA y PearB

```
show crypto ipsec sa
```
Verificar que `#pkts encaps` y `#pkts decaps` incrementan tras el tráfico.

## ► 3. Verificar la Crypto Map

```
show crypto map
```

## ► 4. Verificar VLANs y puertos — en Switch-A y Switch-B

```
show vlan brief
show port-security interface Ethernet0/1
show spanning-tree interface Ethernet0/1 detail
```

## ► 5. Prueba de Conectividad End-to-End

**Desde PC1:**
```
ping 10.13.67.140
```

**Desde PC2:**
```
ping 10.13.67.10
```
✔️ El ping debe responder correctamente y, al revisar `show crypto ipsec sa` en PearA o PearB, los contadores de paquetes cifrados deben haber aumentado — confirmando que el tráfico viaja **dentro del túnel IPsec**, no en texto plano.

---

### 📌 Resumen de Nombres Finales

| Dispositivo Original | Nombre en Configuración |
|---|---|
| Router1 | ISP |
| Router2 | PearA |
| Router3 | PearB |
| Switch1 | Switch-A |
| Switch2 | Switch-B |
