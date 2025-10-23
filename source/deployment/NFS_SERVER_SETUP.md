# Configuración del Servidor NFS para ANB Rising Stars

## Resumen
Esta instancia EC2 actuará como servidor de almacenamiento compartido (NFS) para los videos entre Backend y Worker.

---

## 1. Requisitos de la Instancia EC2

### Especificaciones Mínimas:
- **AMI**: Ubuntu Server 22.04 LTS
- **Tipo**: t2.small o t2.medium (mínimo 20GB almacenamiento)
- **Storage**:
  - Root volume: 8GB (gp3)
  - Additional EBS volume: **50GB - 100GB** (gp3) para videos
- **Security Group**: Ver sección de configuración

### Security Group - NFS Server

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | Your IP | Administración |
| NFS | TCP | 2049 | Backend Security Group | NFS desde Backend |
| NFS | TCP | 2049 | Worker Security Group | NFS desde Worker |
| Custom TCP | TCP | 111 | Backend Security Group | RPC Portmapper |
| Custom TCP | TCP | 111 | Worker Security Group | RPC Portmapper |

---

## 2. Instalación y Configuración del Servidor NFS

### Paso 2.1: Conectar a la instancia

```bash
ssh -i "your-key.pem" ubuntu@<NFS_SERVER_PUBLIC_IP>
```

### Paso 2.2: Actualizar el sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### Paso 2.3: Instalar el servidor NFS

```bash
sudo apt install nfs-kernel-server -y
```

### Paso 2.4: Verificar que el volumen EBS adicional está montado

```bash
# Ver discos disponibles
lsblk

# Deberías ver algo como:
# NAME    MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
# xvda    202:0    0    8G  0 disk
# └─xvda1 202:1    0    8G  0 part /
# xvdf    202:80   0   50G  0 disk
```

### Paso 2.5: Formatear y montar el volumen EBS

```bash
# Formatear el disco (SOLO LA PRIMERA VEZ)
sudo mkfs.ext4 /dev/xvdf

# Crear punto de montaje
sudo mkdir -p /mnt/nfs_share

# Montar el disco
sudo mount /dev/xvdf /mnt/nfs_share

# Verificar
df -h | grep nfs_share
```

### Paso 2.6: Hacer el montaje permanente

```bash
# Obtener el UUID del disco
sudo blkid /dev/xvdf

# Editar /etc/fstab
sudo nano /etc/fstab

# Agregar esta línea al final (reemplaza UUID con el tuyo):
# UUID=tu-uuid-aqui /mnt/nfs_share ext4 defaults,nofail 0 2

# Ejemplo:
# UUID=12345678-1234-1234-1234-123456789abc /mnt/nfs_share ext4 defaults,nofail 0 2

# Probar la configuración
sudo umount /mnt/nfs_share
sudo mount -a

# Verificar
df -h | grep nfs_share
```

### Paso 2.7: Crear estructura de directorios para videos

```bash
# Crear directorios
sudo mkdir -p /var/nfs/shared_folder/uploads/original
sudo mkdir -p /var/nfs/shared_folder/uploads/processed
sudo mkdir -p /var/nfs/shared_folder/uploads/temp

# Dar permisos amplios (importante para que Backend y Worker puedan escribir)
sudo chmod -R 777 /var/nfs/shared_folder/uploads

# Verificar
ls -la /var/nfs/shared_folder/
```

### Paso 2.8: Configurar las exportaciones NFS

```bash
# Editar el archivo de exportaciones
sudo nano /etc/exports

# Agregar estas líneas (reemplaza con las IPs privadas de Backend y Worker):
# IMPORTANTE: Obtén las IPs privadas de tus instancias Backend y Worker desde la consola AWS

# Ejemplo (reemplaza con TUS IPs privadas):
/var/nfs/shared_folder/uploads 172.31.XXX.XXX(rw,sync,no_subtree_check,no_root_squash) 172.31.YYY.YYY(rw,sync,no_subtree_check,no_root_squash)

# Formato:
# /var/nfs/shared_folder/uploads <BACKEND_PRIVATE_IP>(rw,sync,no_subtree_check,no_root_squash) <WORKER_PRIVATE_IP>(rw,sync,no_subtree_check,no_root_squash)

# Opciones explicadas:
# rw                  - Lectura/escritura
# sync                - Sincronización inmediata
# no_subtree_check    - Mejora rendimiento
# no_root_squash      - Permite root desde clientes
```

### Paso 2.9: Aplicar la configuración y reiniciar NFS

```bash
# Exportar los directorios
sudo exportfs -a

# Reiniciar el servicio NFS
sudo systemctl restart nfs-kernel-server

# Verificar estado
sudo systemctl status nfs-kernel-server

# Ver exportaciones activas
sudo exportfs -v
```

### Paso 2.10: Verificar que el firewall permite NFS

```bash
# En Ubuntu, ufw suele estar desactivado por defecto
# Pero por si acaso, verifica:
sudo ufw status

# Si está activo, permite NFS:
sudo ufw allow from <BACKEND_PRIVATE_IP> to any port nfs
sudo ufw allow from <WORKER_PRIVATE_IP> to any port nfs
```

---

## 3. Verificación desde el Servidor NFS

### Verificar que NFS está escuchando:

```bash
sudo netstat -tuln | grep 2049
# Deberías ver: tcp  0  0 0.0.0.0:2049  0.0.0.0:*  LISTEN
```

### Ver logs en caso de problemas:

```bash
sudo journalctl -u nfs-kernel-server -f
```

### Verificar montajes:

```bash
showmount -e localhost
# Deberías ver:
# Export list for localhost:
# /var/nfs/shared_folder/uploads 172.31.XXX.XXX,172.31.YYY.YYY
```

---

## 4. Información para las demás instancias

### Datos que necesitarás para Backend y Worker:

```bash
# 1. IP PRIVADA del servidor NFS
hostname -I
# Ejemplo: 172.31.XXX.XXX

# 2. Ruta del export
# /var/nfs/shared_folder/uploads
```

### Guardar esta información:

```
NFS_SERVER_PRIVATE_IP=172.31.XXX.XXX
NFS_EXPORT_PATH=/var/nfs/shared_folder/uploads
```

---

## 5. Troubleshooting

### Problema: "Permission denied" al montar desde cliente

```bash
# En el servidor NFS, verificar permisos:
ls -la /mnt/nfs_share/uploads

# Dar permisos completos temporalmente para probar:
sudo chmod -R 777 /mnt/nfs_share/uploads
```

### Problema: "No route to host"

```bash
# Verificar Security Groups en AWS Console
# Asegúrate de que el puerto 2049 está abierto para las IPs privadas de Backend y Worker
```

### Problema: Cambios en /etc/exports no se aplican

```bash
# Re-exportar y reiniciar:
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server
```

### Verificar conectividad desde Backend/Worker:

```bash
# Desde Backend o Worker, probar conectividad:
ping <NFS_PRIVATE_IP>
telnet <NFS_PRIVATE_IP> 2049
```

---

## 6. Monitoreo y Mantenimiento

### Ver clientes conectados:

```bash
sudo showmount -a
```

### Ver espacio en disco:

```bash
df -h /mnt/nfs_share
```

### Limpiar archivos temporales viejos (opcional):

```bash
# Crear un cron job para limpiar archivos temp mayores a 7 días
sudo crontab -e

# Agregar:
# 0 2 * * * find /mnt/nfs_share/uploads/temp -type f -mtime +7 -delete
```

---

## 7. Backup Recommendations

### Crear snapshot del volumen EBS:

```bash
# Desde AWS Console:
# EC2 > Elastic Block Store > Volumes
# Seleccionar el volumen de 50GB
# Actions > Create Snapshot
# Programar snapshots automáticos semanales
```

---

## Resumen de Comandos Rápidos

```bash
# Instalación completa (copia y pega):
sudo apt update && sudo apt install nfs-kernel-server -y
sudo mkfs.ext4 /dev/xvdf  # SOLO SI ES DISCO NUEVO
sudo mkdir -p /mnt/nfs_share
sudo mount /dev/xvdf /mnt/nfs_share
sudo mkdir -p /mnt/nfs_share/uploads/{original,processed,temp}
sudo chmod -R 777 /mnt/nfs_share/uploads

# Configurar /etc/exports (editar con tus IPs):
echo "/mnt/nfs_share/uploads <BACKEND_IP>(rw,sync,no_subtree_check,no_root_squash) <WORKER_IP>(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# Aplicar:
sudo exportfs -a
sudo systemctl restart nfs-kernel-server

# Verificar:
sudo exportfs -v
showmount -e localhost
```

---

## Próximos Pasos

Una vez que el servidor NFS esté configurado:
1. ✅ Anotar la IP privada del servidor NFS
2. ⏭️ Configurar Backend para montar NFS
3. ⏭️ Configurar Worker para montar NFS
4. ⏭️ Probar subida de archivos desde Backend
5. ⏭️ Probar procesamiento desde Worker
