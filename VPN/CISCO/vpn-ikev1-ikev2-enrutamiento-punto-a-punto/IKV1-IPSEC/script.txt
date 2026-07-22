# Guía de Configuración: VPN Site-to-Site (Policy-Based) IPsec IKEv1

## 0. Topología y direccionamiento

```
        PC1 --- Switch1 --- Router2 --- Router1 --- Router3 --- Switch2 --- PC2
      (VPCS)              (PEAR-A)      (ISP)     (PEAR-B)              (VPCS)
```

| Dispositivo | Interfaz | IP                  | Rol                     |
|--------------|----------|---------------------|--------------------------|
| Router1      | e0/0     | 200.13.67.1/30       | Tránsito ISP hacia R2   |
| Router1      | e0/1     | 200.13.67.5/30       | Tránsito ISP hacia R3   |
| Router2      | e0/0     | 200.13.67.2/30       | WAN (peer VPN)          |
| Router2      | e0/1     | 10.13.67.1/25        | LAN local (Switch1)     |
| Router3      | e0/0     | 200.13.67.6/30       | WAN (peer VPN)          |
| Router3      | e0/1     | 10.13.67.129/25      | LAN local (Switch2)     |
| PC1          | e0       | 10.13.67.10/25       | Gateway 10.13.67.1      |
| PC2          | e0       | 10.13.67.140/25      | Gateway 10.13.67.129    |

> **Nota:** Router1 solo enruta tráfico entre las WAN de Router2 y Router3, simulando un ISP. La VPN se levanta **entre Router2 y Router3** usando sus IPs públicas 200.13.67.2 y 200.13.67.6.

---

## 1. Configuración base — Router1 (ISP / tránsito)

```
configure terminal
hostname Router1
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

Router1 no necesita rutas estáticas adicionales porque solo conecta dos redes /30 directamente conectadas entre sí (actúa como el "internet" entre los dos sitios).

---

## 2. Configuración base — Router2 (PEAR-A)

```
configure terminal
hostname Router2
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

## 3. Configuración base — Router3 (PEAR-B)

```
configure terminal
hostname Router3
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

En este punto, antes de tocar la VPN, verifica conectividad básica: `ping 200.13.67.6` desde Router2 debe responder a través de Router1.

---

## 4. Aplicación de IKE (Fase 1 — ISAKMP)

Esta fase negocia cómo se autentican y protegen los dos routers entre sí (el "canal seguro de control").

**En Router2:**
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

**En Router3 (simétrico):**
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

> Cierro aquí la fase de IKEv1. Ambos routers ya pueden autenticarse mutuamente.

---

## 5. Aplicación de IPsec (Fase 2 — Transform-Set)

Define cómo se va a cifrar y garantizar la integridad del tráfico real de datos.

**En Router2 y Router3 (idéntico en ambos):**
```
configure terminal
crypto ipsec transform-set TSET_IKEv1 esp-aes 256 esp-sha256-hmac
 mode tunnel
end
write memory
```

> Cierro aquí la fase de IPsec (transform-set). El "cómo" del cifrado ya quedó definido.

---

## 6. Aplicación de ACL (tráfico interesante)

Esta ACL define **qué tráfico** debe viajar cifrado por el túnel (solo LAN-a-LAN).

**En Router2:**
```
configure terminal
ip access-list extended VPN-TRAFFIC
 permit ip 10.13.67.0 0.0.0.127 10.13.67.128 0.0.0.127
end
write memory
```

**En Router3 (espejo/inverso):**
```
configure terminal
ip access-list extended VPN-TRAFFIC
 permit ip 10.13.67.128 0.0.0.127 10.13.67.0 0.0.0.127
end
write memory
```

> Cierro aquí la ACL. Ya está definido el "qué" se cifra.

---

## 7. Aplicación de Crypto Map (Policy-Based VPN)

Aquí se amarra todo: ACL + transform-set + peer, y se aplica a la interfaz WAN.

**En Router2:**
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

**En Router3:**
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

> Cierro aquí el crypto map. La VPN site-to-site policy-based queda operativa en la interfaz WAN de ambos routers.

---

## 8. Seguridad en los Switches

### 8.1 Aplicación de VLAN

**Switch1:**
```
configure terminal
hostname Switch1
vlan 10
 name LAN_PEAR_A
end
write memory
```

**Switch2:**
```
configure terminal
hostname Switch2
vlan 20
 name LAN_PEAR_B
end
write memory
```

> Cierro aquí la aplicación de VLAN.

### 8.2 Aplicación de modo acceso (switchport mode access)

**Switch1 (puerto a Router2 y puerto a PC1):**
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

**Switch2 (puerto a Router3 y puerto a PC2):**
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

> Cierro aquí la aplicación de modo acceso.

### 8.3 Aplicación de Port-Security

Restringe cuántas MAC pueden conectarse por puerto y protege contra flooding/spoofing (aplica sobre todo al puerto conectado a la PC).

**Switch1 — Ethernet0/1 (hacia PC1):**
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

**Switch2 — Ethernet0/1 (hacia PC2):**
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

> Cierro aquí la aplicación de port-security.

### 8.4 Aplicación de Spanning-Tree PortFast

Evita retrasos de convergencia en puertos de acceso hacia hosts finales.

**Switch1:**
```
configure terminal
interface Ethernet0/1
 spanning-tree portfast
end
write memory
```

**Switch2:**
```
configure terminal
interface Ethernet0/1
 spanning-tree portfast
end
write memory
```

> Cierro aquí PortFast.

---

## 9. Configuración de las PCs (VPCS)

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

## 10. Verificación de que todo funciona

### 10.1 Verificar Fase 1 (ISAKMP/IKEv1)
```
show crypto isakmp policy
show crypto isakmp sa
```
El estado de la SA debe mostrar `QM_IDLE` una vez haya tráfico interesante circulando.

### 10.2 Verificar Fase 2 (IPsec)
```
show crypto ipsec sa
```
Debes ver contadores de paquetes encapsulados (`#pkts encaps`) y desencapsulados (`#pkts decaps`) incrementando después de generar tráfico.

### 10.3 Verificar el Crypto Map aplicado
```
show crypto map
```

### 10.4 Verificar enrutamiento
```
show ip route
```

### 10.5 Prueba de conectividad extremo a extremo
Desde **PC1**:
```
ping 10.13.67.140
```
Desde **PC2**:
```
ping 10.13.67.10
```

Ambos ping deben responder exitosamente. Justo después de lanzar el primer ping, vuelve a Router2 o Router3 y corre nuevamente `show crypto ipsec sa`: los contadores de paquetes cifrados deben haber aumentado, confirmando que el tráfico realmente está viajando **por el túnel IPsec** y no en texto claro.

### 10.6 Verificación de seguridad en switches
```
show port-security
show port-security address
show vlan brief
show spanning-tree interface e0/1
```

---

## Resumen del orden de aplicación

1. Direccionamiento IP básico (routers)
2. Enrutamiento (rutas estáticas hacia el ISP)
3. **Aplicación de IKE** (isakmp policy + key)
4. **Aplicación de IPsec** (transform-set)
5. **Aplicación de ACL** (tráfico interesante)
6. **Aplicación de Crypto Map** (amarre + aplicación a interfaz WAN)
7. **Aplicación de VLAN** (switches)
8. **Aplicación de modo acceso** (switchport)
9. **Aplicación de Port-Security**
10. **Aplicación de PortFast**
11. Configuración de hosts (VPCS)
12. Verificación final
