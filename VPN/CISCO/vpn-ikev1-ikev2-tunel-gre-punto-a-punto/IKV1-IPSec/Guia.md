# 🔐 GUÍA DE CONFIGURACIÓN — VPN SITE-TO-SITE GRE sobre IPsec (IKEv1)

**Materia:** TSI-203 — Seguridad de Redes
**Topología:** PC1 → Switch-A → PearA ←→ ISP ←→ PearB ← Switch-B ← PC2
**Modalidad:** GRE sobre IPsec (crypto map + ACL, **modo transporte**), sin VTI
**Fase 1:** IKEv1 (crypto isakmp) — **Fase 2:** IPsec Transform-Set + Crypto Map aplicado a la interfaz física

> 📌 **Diferencia clave con los laboratorios route-based (VTI):**
> Aquí sí existe una interfaz `Tunnel0`, pero es **GRE puro** (`tunnel mode gre ip`), no una VTI de IPsec. La encriptación no la aplica el túnel — la aplica un **crypto map clásico sobre la interfaz física** (`Ethernet0/0`), usando una **ACL** que reconoce el tráfico GRE entre las dos IPs públicas como "tráfico interesante". El GRE se encarga de encapsular (y permite rutas dinámicas o multicast dentro del túnel); el IPsec en modo transporte solo cifra ese GRE ya encapsulado — por eso `mode transport` es correcto aquí y no `mode tunnel`.

| Nombre en Topología | Rol | Nombre Asignado |
|---|---|---|
| Router1 | Nodo central de tránsito | **ISP** |
| Router2 | Sitio izquierdo (VLAN 10) | **PearA** |
| Router3 | Sitio derecho (VLAN 20) | **PearB** |
| Switch1 | Switch sitio izquierdo | **Switch-A** |
| Switch2 | Switch sitio derecho | **Switch-B** |

---

# 🌐 ROUTER: ISP

> Sin cambios respecto a los laboratorios anteriores. Sigue siendo solo un nodo de tránsito IP; no participa en la VPN.

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

## ► Aplicación de ACL — Tráfico Interesante (solo GRE)

```
access-list 100 remark CIFRAR_UNICAMENTE_EL_GRE_ENTRE_LOS_PUBLICOS
access-list 100 permit gre host 200.13.67.2 host 200.13.67.6
```
🔚 *Cierre del bloque de ACL. Ojo: esta ACL no menciona las LAN (10.13.67.0/25) — solo protege el GRE entre las IPs públicas, porque las redes internas viajan **encapsuladas dentro** del GRE y no necesitan aparecer aquí.*

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

## ► Aplicación de IPsec — Fase 2 (Transform-Set + Crypto Map)

```
crypto ipsec transform-set TSET_GRE esp-aes 256 esp-sha256-hmac
 mode transport

crypto map CMAP_GRE 10 ipsec-isakmp
 description CRIPTOMAPA_HACIA_PEARB
 set peer 200.13.67.6
 set transform-set TSET_GRE
 match address 100
```
🔚 *Cierre del bloque de IPsec. `mode transport` es correcto aquí porque GRE ya agrega su propio encabezado IP — no hace falta el encabezado extra de `mode tunnel`. A diferencia de los laboratorios VTI, aquí sí se usa `crypto map` (no `ipsec profile`), porque se aplicará a la interfaz física, no a una interfaz de túnel IPsec.*

## ► Aplicación del Crypto Map en la Interfaz Física

```
interface Ethernet0/0
 crypto map CMAP_GRE
```
🔚 *Cierre del bloque. Esto activa el cifrado: todo el tráfico que salga por `Ethernet0/0` y coincida con la ACL 100 (el GRE hacia 200.13.67.6) se cifra antes de salir.*

## ► Aplicación de Interfaz de Túnel (GRE puro)

```
interface Tunnel0
 description TUNEL_GRE_HACIA_PEARB
 ip address 172.16.0.1 255.255.255.252
 tunnel source Ethernet0/0
 tunnel destination 200.13.67.6
 tunnel mode gre ip
 no shutdown
```
🔚 *Cierre del bloque de interfaz de túnel. Nótese que aquí NO hay `tunnel protection ipsec profile` — este túnel es GRE simple; la protección viene del crypto map en la interfaz física, no de la interfaz de túnel.*

## ► Aplicación de Enrutamiento

```
ip route 200.13.67.4 255.255.255.252 200.13.67.1
ip route 10.13.67.128 255.255.255.128 172.16.0.2

end
write
```
🔚 *Cierre del bloque de enrutamiento. La primera ruta lleva el tráfico hacia la WAN de PearB a través de ISP — indispensable para que el GRE (y por tanto el crypto map) tenga a quién llegar. La segunda ruta envía la LAN remota (VLAN 20) por el túnel GRE — el direccionamiento del túnel usa `/30` (172.16.0.1 y 172.16.0.2), solo 2 IPs, igual que en los laboratorios anteriores.*

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

## ► Aplicación de ACL — Tráfico Interesante (solo GRE)

```
access-list 100 remark CIFRAR_UNICAMENTE_EL_GRE_ENTRE_LOS_PUBLICOS
access-list 100 permit gre host 200.13.67.6 host 200.13.67.2
```
🔚 *Cierre del bloque de ACL (espejo de PearA, orden fuente/destino invertido).*

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

## ► Aplicación de IPsec — Fase 2 (Transform-Set + Crypto Map)

```
crypto ipsec transform-set TSET_GRE esp-aes 256 esp-sha256-hmac
 mode transport

crypto map CMAP_GRE 10 ipsec-isakmp
 description CRIPTOMAPA_HACIA_PEARA
 set peer 200.13.67.2
 set transform-set TSET_GRE
 match address 100
```
🔚 *Cierre del bloque de IPsec.*

## ► Aplicación del Crypto Map en la Interfaz Física

```
interface Ethernet0/0
 crypto map CMAP_GRE
```
🔚 *Cierre del bloque.*

## ► Aplicación de Interfaz de Túnel (GRE puro)

```
interface Tunnel0
 description TUNEL_GRE_HACIA_PEARA
 ip address 172.16.0.2 255.255.255.252
 tunnel source Ethernet0/0
 tunnel destination 200.13.67.2
 tunnel mode gre ip
 no shutdown
```
🔚 *Cierre del bloque de interfaz de túnel.*

## ► Aplicación de Enrutamiento

```
ip route 200.13.67.0 255.255.255.252 200.13.67.5
ip route 10.13.67.0 255.255.255.128 172.16.0.1

end
write
```
🔚 *Cierre del bloque de enrutamiento. Espejo de PearA: ruta hacia la WAN de PearA vía ISP, y la LAN remota (VLAN 10) enviada por el túnel GRE.*

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
🔚 *Cierre del bloque de direccionamiento. Sin cambios respecto a los laboratorios anteriores.*

---

# ✅ VERIFICACIÓN FINAL — EL TÚNEL FUNCIONA

## ► 1. Verificar Fase 1 (ISAKMP SA) — en PearA y PearB

```
show crypto isakmp sa
```
Debe mostrar `QM_IDLE` entre 200.13.67.2 ↔ 200.13.67.6.

## ► 2. Verificar Fase 2 (IPsec SA) — en PearA y PearB

```
show crypto ipsec sa
```
El `interface` mostrado será `Ethernet0/0` (no `Tunnel0`, como en las VTI), porque el crypto map está aplicado a la física. Verifica que `#pkts encaps`/`#pkts decaps` incrementen tras tráfico.

## ► 3. Verificar el Túnel GRE

```
show interface Tunnel0
show ip interface brief
```
`Tunnel0` debe estar `up/up`. A diferencia de las VTI, aquí **no** aparece "protected" en la descripción del túnel — el cifrado ocurre "por fuera", en la física.

## ► 4. Verificar la Tabla de Enrutamiento

```
show ip route
```
Debe existir la ruta hacia la LAN remota apuntando al **siguiente salto dentro del túnel** (172.16.0.2 en PearA / 172.16.0.1 en PearB), y también la ruta hacia la WAN del peer remoto — sin esta última, el GRE nunca encuentra a su destino y el crypto map jamás ve tráfico que cifrar.

## ► 5. Verificar el Crypto Map Aplicado

```
show crypto map
```
Confirma que `CMAP_GRE` esté aplicado a `Ethernet0/0` y que el peer y transform-set sean los correctos.

## ► 6. Verificar VLANs y Puertos — en Switch-A y Switch-B

```
show vlan brief
show port-security interface Ethernet0/1
```

## ► 7. Prueba de Conectividad End-to-End

**Desde PC1:**
```
ping 10.13.67.140
trace 10.13.67.140
```

**Desde PC2:**
```
ping 10.13.67.10
```

> 💡 **Nota:** en el `trace`, el segundo salto debe mostrar `172.16.0.2` (la IP del túnel GRE de PearB) — eso confirma que el paquete viajó por el túnel. Que el ping funcione y `#pkts encaps` aumente en `show crypto ipsec sa` confirma que ese GRE viajó **cifrado**, no en texto plano.

✔️ El ping debe responder correctamente y los contadores en `show crypto ipsec sa` deben aumentar, confirmando que el GRE viaja cifrado dentro del túnel.

---

### 📌 Resumen de Nombres Finales

| Dispositivo Original | Nombre en Configuración |
|---|---|
| Router1 | ISP |
| Router2 | PearA |
| Router3 | PearB |
| Switch1 | Switch-A |
| Switch2 | Switch-B |

### 📌 Comparación Rápida: VTI (Route-Based) vs GRE sobre IPsec

| Aspecto | VTI Route-Based (IKEv1/IKEv2) | GRE sobre IPsec (IKEv1) |
|---|---|---|
| Interfaz de túnel | `tunnel mode ipsec ipv4` | `tunnel mode gre ip` |
| Dónde se aplica la protección | `tunnel protection ipsec profile` (en el propio Tunnel0) | `crypto map` en la interfaz física (`Ethernet0/0`) |
| Selección de tráfico a cifrar | No aplica (todo lo que entra al túnel se cifra) | ACL 100 — solo el GRE entre las IPs públicas |
| Modo de transform-set | `mode tunnel` | `mode transport` (GRE ya encapsula) |
| Verificación de Fase 2 | `interface: Tunnel0` en `show crypto ipsec sa` | `interface: Ethernet0/0` en `show crypto ipsec sa` |
| Soporta rutas dinámicas / multicast | Sí (nativo de VTI) | Sí (GRE lo soporta igual, incluso mejor para multicast) |
| Direccionamiento del túnel | `/30` (2 IPs) | `/30` (2 IPs) |
