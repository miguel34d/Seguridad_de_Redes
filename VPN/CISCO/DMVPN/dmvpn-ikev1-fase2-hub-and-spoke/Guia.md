# 🔐 GUÍA DE CONFIGURACIÓN — DMVPN FASE 2 (1 Hub, 2 Spokes)

**Materia:** TSI-203 — Seguridad de Redes
**Topología:** Spoke1 ←→ ISP ←→ Hub ←→ ISP ←→ Spoke2
**Modalidad:** DMVPN Fase 2 — mGRE en Hub y Spokes, IPsec con `tunnel protection ipsec profile`
**Fase 1 (IKE):** IKEv1 (crypto isakmp), clave precompartida comodín — **Fase 2 (IPsec):** Transform-Set + IPsec Profile
**Enrutamiento dinámico:** EIGRP AS 100, con `no ip next-hop-self` en el Hub para permitir túneles Spoke-a-Spoke directos (característica distintiva de la Fase 2)

| Rol | Nombre Asignado |
|---|---|
| Nodo central de tránsito | **ISP** |
| Hub DMVPN | **Hub** |
| Spoke 1 (VLAN 10) | **Spoke1** |
| Spoke 2 (VLAN 20) | **Spoke2** |

---

# 🌐 ROUTER: ISP

## ► Aplicación de Interfaces

```
configure terminal
hostname ISP

interface Ethernet0/0
 description ENLACE_A_HUB
 ip address 200.13.67.1 255.255.255.252
 no shutdown

interface Ethernet0/1
 description ENLACE_A_SPOKE1
 ip address 200.13.67.5 255.255.255.252
 no shutdown

interface Ethernet0/2
 description ENLACE_A_SPOKE2
 ip address 200.13.67.9 255.255.255.252
 no shutdown

end
write
```

---

# 🛡️ ROUTER: Hub

## ► Aplicación de Interfaces

```
configure terminal
hostname Hub

interface Ethernet0/0
 description WAN_HACIA_ISP
 ip address 200.13.67.2 255.255.255.252
 no shutdown

end
```

## ► Aplicación de IKEv1 — Fase 1 (ISAKMP)

```
crypto isakmp policy 10
 encryption aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400

crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0
```

## ► Aplicación de IPsec — Fase 2 (Transform-Set + IPsec Profile)

```
crypto ipsec transform-set TSET_DMVPN esp-aes 256 esp-sha256-hmac
 mode transport

crypto ipsec profile IPSEC_PROF_DMVPN
 set transform-set TSET_DMVPN
```

## ► Aplicación de Interfaz de Túnel mGRE (Hub)

```
interface Tunnel0
 description TUNEL_DMVPN_HUB
 ip address 172.13.67.1 255.255.255.0
 no ip redirects
 ip nhrp authentication cisco123
 ip nhrp map multicast dynamic
 ip nhrp network-id 100
 no ip next-hop-self eigrp 100
 no ip split-horizon eigrp 100
 tunnel source Ethernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 tunnel protection ipsec profile IPSEC_PROF_DMVPN
 no shutdown
```

## ► Aplicación de EIGRP

```
router eigrp 100
 network 172.13.67.0 0.0.0.255
 no auto-summary
```

## ► Aplicación de Enrutamiento Estático (alcance WAN)

```
ip route 200.13.67.0 255.255.255.0 200.13.67.1

end
write
```

---

# 🛡️ ROUTER: Spoke1 *(VLAN 10)*

## ► Aplicación de Interfaces

```
configure terminal
hostname Spoke1

interface Ethernet0/0
 description WAN_HACIA_ISP
 ip address 200.13.67.6 255.255.255.252
 no shutdown

interface Ethernet0/1
 description LAN_VLAN10
 ip address 10.13.67.1 255.255.255.128
 no shutdown

end
```

## ► Aplicación de IKEv1 — Fase 1 (ISAKMP)

```
crypto isakmp policy 10
 encryption aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400

crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0
```

## ► Aplicación de IPsec — Fase 2 (Transform-Set + IPsec Profile)

```
crypto ipsec transform-set TSET_DMVPN esp-aes 256 esp-sha256-hmac
 mode transport

crypto ipsec profile IPSEC_PROF_DMVPN
 set transform-set TSET_DMVPN
```

## ► Aplicación de Interfaz de Túnel mGRE (Spoke1)

```
interface Tunnel0
 description TUNEL_DMVPN_SPOKE1
 ip address 172.13.67.2 255.255.255.0
 no ip redirects
 ip nhrp authentication cisco123
 ip nhrp map 172.13.67.1 200.13.67.2
 ip nhrp map multicast 200.13.67.2
 ip nhrp network-id 100
 ip nhrp nhs 172.13.67.1
 tunnel source Ethernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 tunnel protection ipsec profile IPSEC_PROF_DMVPN
 no shutdown
```

## ► Aplicación de EIGRP

```
router eigrp 100
 network 172.13.67.0 0.0.0.255
 network 10.13.67.0 0.0.0.127
 no auto-summary
```

## ► Aplicación de Enrutamiento Estático (alcance WAN)

```
ip route 200.13.67.0 255.255.255.0 200.13.67.5

end
write
```

---

# 🛡️ ROUTER: Spoke2 *(VLAN 20)*

## ► Aplicación de Interfaces

```
configure terminal
hostname Spoke2

interface Ethernet0/0
 description WAN_HACIA_ISP
 ip address 200.13.67.10 255.255.255.252
 no shutdown

interface Ethernet0/1
 description LAN_VLAN20
 ip address 10.13.67.129 255.255.255.128
 no shutdown

end
```

## ► Aplicación de IKEv1 — Fase 1 (ISAKMP)

```
crypto isakmp policy 10
 encryption aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400

crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0
```

## ► Aplicación de IPsec — Fase 2 (Transform-Set + IPsec Profile)

```
crypto ipsec transform-set TSET_DMVPN esp-aes 256 esp-sha256-hmac
 mode transport

crypto ipsec profile IPSEC_PROF_DMVPN
 set transform-set TSET_DMVPN
```

## ► Aplicación de Interfaz de Túnel mGRE (Spoke2)

```
interface Tunnel0
 description TUNEL_DMVPN_SPOKE2
 ip address 172.13.67.3 255.255.255.0
 no ip redirects
 ip nhrp authentication cisco123
 ip nhrp map 172.13.67.1 200.13.67.2
 ip nhrp map multicast 200.13.67.2
 ip nhrp network-id 100
 ip nhrp nhs 172.13.67.1
 tunnel source Ethernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 tunnel protection ipsec profile IPSEC_PROF_DMVPN
 no shutdown
```

## ► Aplicación de EIGRP

```
router eigrp 100
 network 172.13.67.0 0.0.0.255
 network 10.13.67.128 0.0.0.127
 no auto-summary
```

## ► Aplicación de Enrutamiento Estático (alcance WAN)

```
ip route 200.13.67.0 255.255.255.0 200.13.67.9

end
write
```

---

# 💻 TERMINALES: PC1 y PC2 (Consolas VPCS)

## ► Aplicación de Direccionamiento IP

```
* En PC1 (detrás de Spoke1):
ip 10.13.67.10 255.255.255.128 10.13.67.1
save

* En PC2 (detrás de Spoke2):
ip 10.13.67.140 255.255.255.128 10.13.67.129
save
```

---

# ✅ VERIFICACIÓN FINAL — EL DMVPN FUNCIONA

## ► 1. Verificar Fase 1 (ISAKMP SA) — en Hub, Spoke1 y Spoke2

```
show crypto isakmp sa
```

## ► 2. Verificar Fase 2 (IPsec SA)

```
show crypto ipsec sa
```

## ► 3. Verificar la Nube DMVPN

```
show dmvpn
show ip nhrp
```
En el Hub debe verse `#Ent` con dos spokes registrados. En cada Spoke debe verse el NHS (Hub) resuelto y, tras tráfico entre spokes, un mapeo dinámico Spoke-a-Spoke (propio de la Fase 2).

## ► 4. Verificar el Túnel

```
show interface Tunnel0
show ip interface brief
```

## ► 5. Verificar EIGRP

```
show ip eigrp neighbors
show ip route eigrp
```
Cada Spoke debe ver la ruta EIGRP hacia la LAN del otro Spoke con next-hop siendo la IP de túnel del otro Spoke (no la del Hub) — eso confirma el spoke-to-spoke de la Fase 2.

## ► 6. Prueba de Conectividad End-to-End

**Desde PC1:**
```
ping 10.13.67.140
trace 10.13.67.140
```

**Desde PC2:**
```
ping 10.13.67.10
```

> 💡 En el `trace`, tras la convergencia de NHRP, el paquete debería viajar directo Spoke1↔Spoke2 (túnel dinámico) sin pasar por el Hub — esa es la diferencia central entre Fase 1 y Fase 2 de DMVPN.

---

### 📌 Comparación Rápida: Fase 1 vs Fase 2 de DMVPN

| Aspecto | Fase 1 | Fase 2 |
|---|---|---|
| Modo de túnel en Spokes | `tunnel mode gre` (punto a punto) | `tunnel mode gre multipoint` |
| Comunicación Spoke-a-Spoke | Siempre pasa por el Hub | Directa, mediante NHRP dinámico |
| `next-hop-self` en el Hub | Habilitado (default) | Deshabilitado (`no ip next-hop-self eigrp 100`) |
| `split-horizon` en el Hub | Sin cambios | Deshabilitado (`no ip split-horizon eigrp 100`) |
| Protección IPsec | `tunnel protection ipsec profile` | `tunnel protection ipsec profile` |
