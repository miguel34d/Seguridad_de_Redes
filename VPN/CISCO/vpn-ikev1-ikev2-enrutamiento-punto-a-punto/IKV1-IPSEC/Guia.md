# 🔐 GUÍA DE CONFIGURACIÓN — VPN SITE-TO-SITE IPSec (IKEv1) *BASADA EN ENRUTAMIENTO*

**Materia:** TSI-203 — Seguridad de Redes
**Topología:** PC1 → Switch-A → PearA ←→ ISP ←→ PearB ← Switch-B ← PC2
**Modalidad:** Route-Based VPN (VTI — Virtual Tunnel Interface), sin crypto map ni ACL de tráfico interesante
**Fase 1:** IKEv1 (crypto isakmp) — **Fase 2:** IPsec Profile aplicado a interfaz Tunnel

> 📌 **Diferencia clave con el laboratorio anterior (policy-based, IKEv2):**
> Aquí **no hay `access-list` ni `crypto map`**. El tráfico que entra al túnel lo decide la **tabla de enrutamiento** (una ruta estática o dinámica apuntando a `Tunnel0`), no una ACL. Esto simplifica el diseño y permite enrutar protocolos dinámicos dentro del túnel si se desea.

| Nombre en Topología | Rol | Nombre Asignado |
|---|---|---|
| Router1 | Nodo central de tránsito | **ISP** |
| Router2 | Sitio izquierdo (VLAN 10) | **PearA** |
| Router3 | Sitio derecho (VLAN 20) | **PearB** |
| Switch1 | Switch sitio izquierdo | **Switch-A** |
| Switch2 | Switch sitio derecho | **Switch-B** |

---

# 🌐 ROUTER: ISP

> Sin cambios respecto al laboratorio anterior. Sigue siendo solo un nodo de tránsito IP; no participa en la VPN.

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

## ► Aplicación de IKEv1 — Fase 1 (ISAKMP)

```
crypto isakmp policy 10
 encryption aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400

crypto isakmp key cisco123 address 200.13.67.6
```
🔚 *Cierre del bloque ISAKMP. Define cifrado, autenticación PSK y el peer remoto (Fase 1 completa).*

## ► Aplicación de IPsec — Fase 2 (Transform-Set + Profile)

```
crypto ipsec transform-set TSET_IKEv1 esp-aes 256 esp-sha256-hmac
 mode tunnel

crypto ipsec profile PERFIL_IPSEC_IKEv1
 set transform-set TSET_IKEv1
```
🔚 *Cierre del bloque de IPsec. A diferencia del laboratorio anterior, aquí se crea un **profile**, no un crypto map — se aplicará directo a la interfaz de túnel.*

## ► Aplicación de Interfaz de Túnel (VTI)

```
interface Tunnel0
 description TUNEL_VTI_HACIA_PEARB
 ip address 172.13.67.1 255.255.255.252
 tunnel source Ethernet0/0
 tunnel destination 200.13.67.6
 tunnel mode ipsec ipv4
 tunnel protection ipsec profile PERFIL_IPSEC_IKEv1
 no shutdown
```
🔚 *Cierre del bloque de interfaz de túnel. El túnel queda como una interfaz lógica más de Capa 3.*

## ► Aplicación de Enrutamiento

```
ip route 10.13.67.128 255.255.255.128 Tunnel0
ip route 200.13.67.4 255.255.255.252 200.13.67.1

end
write
```
🔚 *Cierre del bloque de enrutamiento. La primera ruta envía la LAN remota (VLAN 20) por Tunnel0 — esto es lo que activa el cifrado (route-based). La segunda ruta es indispensable para que PearA alcance la WAN de PearB (200.13.67.6) a través de ISP; sin ella, `Tunnel0` nunca encuentra "output interface" y el ISAKMP se queda en `MM_NO_STATE`.*

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

## ► Aplicación de IKEv1 — Fase 1 (ISAKMP)

```
crypto isakmp policy 10
 encryption aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400

crypto isakmp key cisco123 address 200.13.67.2
```
🔚 *Cierre del bloque ISAKMP (Fase 1 completa).*

## ► Aplicación de IPsec — Fase 2 (Transform-Set + Profile)

```
crypto ipsec transform-set TSET_IKEv1 esp-aes 256 esp-sha256-hmac
 mode tunnel

crypto ipsec profile PERFIL_IPSEC_IKEv1
 set transform-set TSET_IKEv1
```
🔚 *Cierre del bloque de IPsec.*

## ► Aplicación de Interfaz de Túnel (VTI)

```
interface Tunnel0
 description TUNEL_VTI_HACIA_PEARA
 ip address 172.13.67.2 255.255.255.252
 tunnel source Ethernet0/0
 tunnel destination 200.13.67.2
 tunnel mode ipsec ipv4
 tunnel protection ipsec profile PERFIL_IPSEC_IKEv1
 no shutdown
```
🔚 *Cierre del bloque de interfaz de túnel.*

## ► Aplicación de Enrutamiento

```
ip route 10.13.67.0 255.255.255.128 Tunnel0
ip route 200.13.67.0 255.255.255.252 200.13.67.5

end
write
```
🔚 *Cierre del bloque de enrutamiento. Espejo de PearA: la primera ruta envía la VLAN 10 remota por Tunnel0; la segunda le da a PearB la ruta hacia la WAN de PearA (200.13.67.2) a través de ISP.*

---

# 🔧 SWITCH: Switch-A *(Lado Izquierdo)*

> Sin cambios respecto al laboratorio anterior — la seguridad de acceso es independiente del tipo de VPN usado en los routers.

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
🔚 *Cierre del bloque de port-security.*

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
🔚 *Cierre del bloque de port-security.*

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
🔚 *Cierre del bloque de direccionamiento. Sin cambios respecto al laboratorio anterior.*

---

# ✅ VERIFICACIÓN FINAL — EL TÚNEL FUNCIONA

## ► 1. Verificar Fase 1 (ISAKMP SA) — en PearA y PearB

```
show crypto isakmp sa
```
Debe mostrar `QM_IDLE` entre 200.13.67.2 ↔ 200.13.67.6 (estado establecido en Modo Rápido).

## ► 2. Verificar Fase 2 (IPsec SA) — en PearA y PearB

```
show crypto ipsec sa
```
Verificar SPIs activos y que `#pkts encaps`/`#pkts decaps` incrementan tras tráfico.

## ► 3. Verificar la Interfaz de Túnel

```
show interface Tunnel0
show ip interface brief
```
`Tunnel0` debe estar `up/up` con **protocol status: protected** una vez que el IPsec Profile la asegura.

## ► 4. Verificar la Tabla de Enrutamiento

```
show ip route
```
Debe existir la ruta hacia la LAN remota apuntando a `Tunnel0`, **y también** la ruta hacia la WAN del peer remoto (200.13.67.4/30 en PearA, 200.13.67.0/30 en PearB) — sin esta última, `Tunnel0` no encuentra "output interface" y el túnel nunca levanta.

## ► 5. Verificar VLANs y puertos — en Switch-A y Switch-B

```
show vlan brief
show port-security interface Ethernet0/1
```

## ► 6. Prueba de Conectividad End-to-End

**Desde PC1:**
```
ping 10.13.67.140
```

**Desde PC2:**
```
ping 10.13.67.10
```

> 💡 **Nota:** a diferencia del modelo policy-based, aquí también puedes hacer `ping 10.13.67.140` directo desde `PearA#` y funcionará, porque el enrutamiento (no una ACL) es quien decide meter el paquete al túnel — la interfaz de salida ya es `Tunnel0`.

✔️ El ping debe responder correctamente y los contadores en `show crypto ipsec sa` deben aumentar, confirmando que el tráfico viaja cifrado dentro del túnel VTI.

---

### 📌 Resumen de Nombres Finales

| Dispositivo Original | Nombre en Configuración |
|---|---|
| Router1 | ISP |
| Router2 | PearA |
| Router3 | PearB |
| Switch1 | Switch-A |
| Switch2 | Switch-B |

### 📌 Comparación Rápida con el Laboratorio Anterior

| Aspecto | Anterior (Policy-Based, IKEv2) | Este Laboratorio (Route-Based, IKEv1) |
|---|---|---|
| Fase 1 | `crypto ikev2` | `crypto isakmp` |
| Fase 2 | `crypto ipsec transform-set` + `crypto map` | `crypto ipsec transform-set` + `crypto ipsec profile` |
| Selección de tráfico | Access-list 102 (tráfico interesante) | Tabla de enrutamiento hacia `Tunnel0` |
| Interfaz aplicada | Ethernet0/0 (física, vía crypto map) | Tunnel0 (virtual, VTI) |
| Soporta rutas dinámicas | No directamente | Sí, se puede correr un IGP sobre Tunnel0 |
