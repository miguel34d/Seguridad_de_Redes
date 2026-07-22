# 🔐 VPN Site-to-Site (Policy-Based) — IPsec IKEv1

---

## 📡 0. TOPOLOGÍA Y DIRECCIONAMIENTO

```
        PC1 --- Swich-A --- PearA --- Isp --- PearB --- Swich-b --- PC2
      (VPCS)              (PEAR-A)      (ISP)     (PEAR-B)              (VPCS)
```

| Dispositivo | Interfaz | IP                  | Rol                     |
|--------------|----------|---------------------|--------------------------|
| Isp      | e0/0     | 200.13.67.1/30       | Tránsito ISP hacia PearA   |
| Isp      | e0/1     | 200.13.67.5/30       | Tránsito ISP hacia PearB   |
| PearA      | e0/0     | 200.13.67.2/30       | WAN (peer VPN)          |
| PearA      | e0/1     | 10.13.67.1/25        | LAN local (Swich-A)     |
| PearB      | e0/0     | 200.13.67.6/30       | WAN (peer VPN)          |
| PearB      | e0/1     | 10.13.67.129/25      | LAN local (Swich-b)     |
| PC1          | e0       | 10.13.67.10/25       | Gateway 10.13.67.1      |
| PC2          | e0       | 10.13.67.140/25      | Gateway 10.13.67.129    |

> **Nota:** Isp solo enruta tráfico entre las WAN de PearA y PearB, simulando un ISP. La VPN se levanta **entre PearA y PearB**, usando sus IPs públicas 200.13.67.2 y 200.13.67.6.

---
---

# 🖥️ ISP (TRÁNSITO)

```
configure terminal
hostname Isp
!
interface Ethernet0/0
 ip address 200.13.67.1 255.255.255.252
 no shutdown
!
interface Ethernet0/1
 ip address 200.13.67.5 255.255.255.252
 no shutdown
!
end
write memory
```

Isp no necesita rutas estáticas adicionales porque solo conecta dos redes /30 directamente conectadas entre sí (actúa como el "internet" entre los dos sitios).

---
---

# 🖥️ PEARA

## 🧱 Direccionamiento y Ruta Base

```
configure terminal
hostname PearA
!
interface Ethernet0/0
 ip address 200.13.67.2 255.255.255.252
 no shutdown
!
interface Ethernet0/1
 ip address 10.13.67.1 255.255.255.128
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 200.13.67.1
end
write memory
```

## 🔑 APLICACIÓN DE IKE (Fase 1 — ISAKMV)

```
configure terminal
crypto isakmp policy 10
 encryption aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400
!
crypto isakmp key Cisco123! address 200.13.67.6
end
write memory
```
> ✅ Cierro aquí la fase de **IKEv1**. PearA ya puede autenticarse con PearB.

## 🛡️ APLICACIÓN DE IPSEC (Fase 2 — Transform-Set)

```
configure terminal
crypto ipsec transform-set TSET_IKEv1 esp-aes 256 esp-sha256-hmac
 mode tunnel
end
write memory
```
> ✅ Cierro aquí la fase de **IPsec** (transform-set).

## 📋 APLICACIÓN DE ACL (Tráfico Interesante)

```
configure terminal
ip access-list extended VPN-TRAFFIC
 permit ip 10.13.67.0 0.0.0.127 10.13.67.128 0.0.0.127
end
write memory
```
> ✅ Cierro aquí la **ACL**. Ya está definido qué tráfico se cifra.

## 🗺️ APLICACIÓN DE CRYPTO MAP

```
configure terminal
crypto map CMAP_VPN 10 ipsec-isakmp
 set peer 200.13.67.6
 set transform-set TSET_IKEv1
 match address VPN-TRAFFIC
!
interface Ethernet0/0
 crypto map CMAP_VPN
end
write memory
```
> ✅ Cierro aquí el **Crypto Map**. La VPN queda activa en la interfaz WAN de PearA.

---
---

# 🖥️ PEARB

## 🧱 Direccionamiento y Ruta Base

```
configure terminal
hostname PearB
!
interface Ethernet0/0
 ip address 200.13.67.6 255.255.255.252
 no shutdown
!
interface Ethernet0/1
 ip address 10.13.67.129 255.255.255.128
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 200.13.67.5
end
write memory
```

## 🔑 APLICACIÓN DE IKE (Fase 1 — ISAKMP)

```
configure terminal
crypto isakmp policy 10
 encryption aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400
!
crypto isakmp key Cisco123! address 200.13.67.2
end
write memory
```
> ✅ Cierro aquí la fase de **IKEv1**. PearB ya puede autenticarse con PearA.

## 🛡️ APLICACIÓN DE IPSEC (Fase 2 — Transform-Set)

```
configure terminal
crypto ipsec transform-set TSET_IKEv1 esp-aes 256 esp-sha256-hmac
 mode tunnel
end
write memory
```
> ✅ Cierro aquí la fase de **IPsec** (transform-set).

## 📋 APLICACIÓN DE ACL (Tráfico Interesante — espejo)

```
configure terminal
ip access-list extended VPN-TRAFFIC
 permit ip 10.13.67.128 0.0.0.127 10.13.67.0 0.0.0.127
end
write memory
```
> ✅ Cierro aquí la **ACL**.

## 🗺️ APLICACIÓN DE CRYPTO MAP

```
configure terminal
crypto map CMAP_VPN 10 ipsec-isakmp
 set peer 200.13.67.2
 set transform-set TSET_IKEv1
 match address VPN-TRAFFIC
!
interface Ethernet0/0
 crypto map CMAP_VPN
end
write memory
```
> ✅ Cierro aquí el **Crypto Map**. La VPN site-to-site policy-based queda operativa en ambos extremos.

---
---

# 🔌 SWICH-A (LAN PEARA)

## 🏷️ APLICACIÓN DE VLAN

```
configure terminal
hostname Swich-A
vlan 10
 name LAN_PEAR_A
end
write memory
```
> ✅ Cierro aquí la **VLAN**.

## 🔗 APLICACIÓN DE MODO ACCESO

```
configure terminal
interface Ethernet0/0
 switchport mode access
 switchport access vlan 10
!
interface Ethernet0/1
 switchport mode access
 switchport access vlan 10
end
write memory
```
> ✅ Cierro aquí el **modo acceso**.

## 🔒 APLICACIÓN DE PORT-SECURITY

```
configure terminal
interface Ethernet0/1
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation restrict
 switchport port-security mac-address sticky
end
write memory
```
> ✅ Cierro aquí el **port-security**.

## ⚡ APLICACIÓN DE PORTFAST

```
configure terminal
interface Ethernet0/1
 spanning-tree portfast
end
write memory
```
> ✅ Cierro aquí **PortFast**.

---
---

# 🔌 SWICH-B (LAN PEARB)

## 🏷️ APLICACIÓN DE VLAN

```
configure terminal
hostname Swich-b
vlan 20
 name LAN_PEAR_B
end
write memory
```
> ✅ Cierro aquí la **VLAN**.

## 🔗 APLICACIÓN DE MODO ACCESO

```
configure terminal
interface Ethernet0/0
 switchport mode access
 switchport access vlan 20
!
interface Ethernet0/1
 switchport mode access
 switchport access vlan 20
end
write memory
```
> ✅ Cierro aquí el **modo acceso**.

## 🔒 APLICACIÓN DE PORT-SECURITY

```
configure terminal
interface Ethernet0/1
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation restrict
 switchport port-security mac-address sticky
end
write memory
```
> ✅ Cierro aquí el **port-security**.

## ⚡ APLICACIÓN DE PORTFAST

```
configure terminal
interface Ethernet0/1
 spanning-tree portfast
end
write memory
```
> ✅ Cierro aquí **PortFast**.

---
---

# 💻 PC1 Y PC2 (VPCS)

**PC1:**
```
ip 10.13.67.10 255.255.255.128 10.13.67.1
save
```

**PC2:**
```
ip 10.13.67.140 255.255.255.128 10.13.67.129
save
```

---
---

# ✅ VERIFICACIÓN FINAL — ¿TODO FUNCIONA?

## 🔑 Fase 1 (ISAKMP / IKEv1)
```
show crypto isakmp policy
show crypto isakmp sa
```
El estado de la SA debe mostrar `QM_IDLE` una vez haya tráfico interesante circulando.

## 🛡️ Fase 2 (IPsec)
```
show crypto ipsec sa
```
Debes ver contadores de paquetes encapsulados (`#pkts encaps`) y desencapsulados (`#pkts decaps`) incrementando después de generar tráfico.

## 🗺️ Crypto Map aplicado
```
show crypto map
```

## 🧭 Enrutamiento
```
show ip route
```

## 🌐 Prueba de conectividad extremo a extremo

Desde **PC1**:
```
ping 10.13.67.140
```

Desde **PC2**:
```
ping 10.13.67.10
```

Ambos ping deben responder exitosamente. Justo después de lanzar el primer ping, vuelve a PearA o PearB y corre nuevamente `show crypto ipsec sa`: los contadores de paquetes cifrados deben haber aumentado, confirmando que el tráfico realmente está viajando **por el túnel IPsec** y no en texto claro.

## 🔒 Seguridad en los switches
```
show port-security
show port-security address
show vlan brief
show spanning-tree interface e0/1
```

---
---

# 📌 RESUMEN DEL ORDEN DE APLICACIÓN

| # | Paso |
|---|------|
| 1 | Direccionamiento IP básico (routers) |
| 2 | Enrutamiento (rutas estáticas hacia el ISP) |
| 3 | **Aplicación de IKE** (isakmp policy + key) |
| 4 | **Aplicación de IPsec** (transform-set) |
| 5 | **Aplicación de ACL** (tráfico interesante) |
| 6 | **Aplicación de Crypto Map** |
| 7 | **Aplicación de VLAN** (switches) |
| 8 | **Aplicación de modo acceso** (switchport) |
| 9 | **Aplicación de Port-Security** |
| 10 | **Aplicación de PortFast** |
| 11 | Configuración de hosts (VPCS) |
| 12 | Verificación final |
