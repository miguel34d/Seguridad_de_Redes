# 🔐 GUÍA DE CONFIGURACIÓN — DMVPN FASE 3 (1 Hub, 2 Spokes)

**Materia:** TSI-203 — Seguridad de Redes
**Topología:** Spoke1 ←→ ISP ←→ Hub ←→ ISP ←→ Spoke2
**Modalidad:** DMVPN Fase 3 — mGRE en Hub y Spokes, IPsec con `tunnel protection ipsec profile`
**Fase 1 (IKE):** IKEv2 (crypto ikev2), clave precompartida comodín — **Fase 2 (IPsec):** Transform-Set + IPsec Profile
**Enrutamiento dinámico:** EIGRP AS 100, con `ip nhrp redirect` en el Hub e `ip nhrp shortcut` en los Spokes para permitir túneles Spoke-a-Spoke directos (característica distintiva de la Fase 3)

| Rol | Nombre Asignado |
|---|---|
| Nodo central de tránsito | **ISP** |
| Hub DMVPN | **Hub** |
| Spoke 1 (VLAN 10) | **Spoke1** (Router2 en el diagrama) |
| Spoke 2 (VLAN 20) | **Spoke2** (Router4 en el diagrama) |

---

## 📌 ¿Qué cambia respecto a Fase 2?

| Aspecto | Fase 2 | Fase 3 |
|---|---|---|
| IKE | IKEv1 (`crypto isakmp`) | **IKEv2** (`crypto ikev2`) |
| Túnel Spoke-a-Spoke | NHRP dinámico "clásico" | NHRP con **redirect/shortcut** (más escalable) |
| `next-hop-self` en el Hub | Deshabilitado | **Habilitado (default)** — no se toca |
| `split-horizon` en el Hub | Deshabilitado | **Sigue deshabilitado** — el split-horizon de EIGRP opera por interfaz (no por vecino), así que en mGRE hay que deshabilitarlo igual que en Fase 2, o el Hub no reenvía entre spokes las rutas aprendidas por Tunnel0 |
| Comando clave en Hub | — | `ip nhrp redirect` en Tunnel0 |
| Comando clave en Spokes | — | `ip nhrp shortcut` en Tunnel0 |
| Resumen de rutas en Hub | No recomendado | **Permitido/recomendado** (ventaja de Fase 3) |

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

## ► Aplicación de IKEv2 — Fase 1

```
crypto ikev2 proposal PROP_DMVPN
 encryption aes-cbc-256
 integrity sha256
 group 14

crypto ikev2 policy POL_DMVPN
 proposal PROP_DMVPN

crypto ikev2 keyring KEYRING_DMVPN
 peer SPOKES
  address 0.0.0.0 0.0.0.0
  pre-shared-key cisco123

crypto ikev2 profile PROF_DMVPN
 match identity remote address 0.0.0.0 0.0.0.0
 authentication remote pre-share
 authentication local pre-share
 keyring local KEYRING_DMVPN
```

## ► Aplicación de IPsec — Fase 2 (Transform-Set + IPsec Profile)

```
crypto ipsec transform-set TSET_DMVPN esp-aes 256 esp-sha256-hmac
 mode transport

crypto ipsec profile IPSEC_PROF_DMVPN
 set transform-set TSET_DMVPN
 set ikev2-profile PROF_DMVPN
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
 ip nhrp redirect
 tunnel source Ethernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 tunnel protection ipsec profile IPSEC_PROF_DMVPN
 no shutdown
```

> 💡 `ip nhrp redirect` es el comando distintivo de Fase 3 en el Hub: le indica que envíe mensajes NHRP de redirección cuando detecta tráfico entre spokes que está pasando por él, para que los spokes construyan un atajo directo.

## ► Aplicación de EIGRP

```
router eigrp 100
 network 172.13.67.0 0.0.0.255
 no auto-summary

interface Tunnel0
 no ip split-horizon eigrp 100
```

> 📌 A diferencia de Fase 2, **no se deshabilita** `next-hop-self` (queda habilitado/default: el Hub sigue siendo el next-hop anunciado, y es NHRP —redirect/shortcut— quien construye el camino directo Spoke-a-Spoke, no el enrutamiento).
>
> Sin embargo, **`split-horizon` sí debe deshabilitarse**, igual que en Fase 2: como `Tunnel0` es una interfaz mGRE compartida por ambos spokes, EIGRP por defecto no reenvía por la misma interfaz una ruta que aprendió por ella — así el Hub jamás le pasaría a Spoke2 la ruta de Spoke1 (y viceversa), aunque la vecindad EIGRP esté establecida con ambos.

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

## ► Aplicación de IKEv2 — Fase 1

```
crypto ikev2 proposal PROP_DMVPN
 encryption aes-cbc-256
 integrity sha256
 group 14

crypto ikev2 policy POL_DMVPN
 proposal PROP_DMVPN

crypto ikev2 keyring KEYRING_DMVPN
 peer ANY
  address 0.0.0.0 0.0.0.0
  pre-shared-key cisco123

crypto ikev2 profile PROF_DMVPN
 match identity remote address 0.0.0.0 0.0.0.0
 authentication remote pre-share
 authentication local pre-share
 keyring local KEYRING_DMVPN
```

> ⚠️ El `match identity remote address` y el `peer` del keyring van con **0.0.0.0 0.0.0.0** (cualquier IP), **no** solo la del Hub. En Fase 3 el spoke necesita poder negociar IKEv2 directo contra **otro spoke** cuando NHRP arma el shortcut — si el profile solo acepta al Hub, el mapeo NHRP dinámico se crea pero queda marcado `X` (No Socket) porque no hay forma de levantar IPsec entre los dos spokes.

## ► Aplicación de IPsec — Fase 2 (Transform-Set + IPsec Profile)

```
crypto ipsec transform-set TSET_DMVPN esp-aes 256 esp-sha256-hmac
 mode transport

crypto ipsec profile IPSEC_PROF_DMVPN
 set transform-set TSET_DMVPN
 set ikev2-profile PROF_DMVPN
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
 ip nhrp shortcut
 tunnel source Ethernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 tunnel protection ipsec profile IPSEC_PROF_DMVPN
 no shutdown
```

> 💡 `ip nhrp shortcut` es el comando distintivo de Fase 3 en los Spokes: le permite instalar en su tabla CEF una ruta directa hacia otro spoke cuando recibe el mensaje de redirección del Hub.

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

## ► Aplicación de IKEv2 — Fase 1

```
crypto ikev2 proposal PROP_DMVPN
 encryption aes-cbc-256
 integrity sha256
 group 14

crypto ikev2 policy POL_DMVPN
 proposal PROP_DMVPN

crypto ikev2 keyring KEYRING_DMVPN
 peer ANY
  address 0.0.0.0 0.0.0.0
  pre-shared-key cisco123

crypto ikev2 profile PROF_DMVPN
 match identity remote address 0.0.0.0 0.0.0.0
 authentication remote pre-share
 authentication local pre-share
 keyring local KEYRING_DMVPN
```

> ⚠️ Igual que en Spoke1: **0.0.0.0 0.0.0.0**, no solo la IP del Hub — Spoke2 también debe poder negociar IKEv2 directo contra Spoke1 cuando se arme el shortcut.

## ► Aplicación de IPsec — Fase 2 (Transform-Set + IPsec Profile)

```
crypto ipsec transform-set TSET_DMVPN esp-aes 256 esp-sha256-hmac
 mode transport

crypto ipsec profile IPSEC_PROF_DMVPN
 set transform-set TSET_DMVPN
 set ikev2-profile PROF_DMVPN
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
 ip nhrp shortcut
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

## ► 1. Verificar Fase 1 (IKEv2 SA) — en Hub, Spoke1 y Spoke2

```
show crypto ikev2 sa
```

## ► 2. Verificar Fase 2 (IPsec SA)

```
show crypto ipsec sa
```

## ► 3. Verificar la Nube DMVPN

```
show dmvpn
show ip nhrp
show ip nhrp shortcut
```
En el Hub debe verse `#Ent` con dos spokes registrados. En cada Spoke debe verse el NHS (Hub) resuelto; tras cursar tráfico entre spokes, debe aparecer una entrada de tipo **shortcut** en `show ip nhrp` (propio de la Fase 3, distinto al mapeo dinámico "clásico" de Fase 2).

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
Al inicio, cada Spoke ve la ruta EIGRP hacia la LAN del otro Spoke con next-hop **el Hub** (a diferencia de Fase 2). Eso es normal: en Fase 3 el camino directo no depende de la ruta EIGRP, sino de NHRP.

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

> 💡 En el primer `ping`, el tráfico pasa inicialmente por el Hub. El Hub detecta el flujo, envía un **NHRP redirect** a Spoke1, y Spoke1 solicita un **shortcut** directo hacia Spoke2. Repitiendo el `trace` tras la convergencia, el paquete debería viajar directo Spoke1↔Spoke2 sin pasar por el Hub — esa es la diferencia central entre Fase 2 y Fase 3 de DMVPN: en Fase 2 el atajo se construye por NHRP "resolution request/reply" ligado al enrutamiento manipulado; en Fase 3 se construye por **redirect/shortcut** independientemente del next-hop anunciado por EIGRP.
