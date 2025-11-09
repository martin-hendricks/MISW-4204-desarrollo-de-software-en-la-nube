## 4.1 Escenario 1: Capacidad de la Capa Web (Usuarios Concurrentes)

### 4.1.1 Estrategia de Implementación
- **Desacoplamiento del Worker**: Los endpoints de carga devuelven 202 y redirigen a un mock de cola que acepta mensajes en memoria
- **Simulación de Carga Real**: Uso de archivos de video reales para simular condiciones de producción
- **Modo de Prueba**: Activación de `TEST_MODE=true` para deshabilitar el procesamiento real

### 4.1.2 Escenarios de Prueba

#### 4.1.2.1 **Prueba de Sanidad (Smoke Test)**
- **Usuarios**: 5 usuarios concurrentes
- **Duración**: 1 minuto
- **Objetivo**: Validar que el sistema responde correctamente y la telemetría está activa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"`
- **Evidencias**: 
  - **Smoke Test**
    <img width="1363" height="278" alt="image" src="https://github.com/user-attachments/assets/64452718-366e-47fc-bb37-5429e84d89e2" />
  - **ClaudWatch**
      <img width="1198" height="628" alt="image" src="https://github.com/user-attachments/assets/ebf11b4e-52f6-48b1-9ed5-2c133179bff4" />
      <img width="1246" height="589" alt="image" src="https://github.com/user-attachments/assets/3e5c5a1d-1aaf-4215-8a86-4dbb92c7293a" />
      <img width="1248" height="606" alt="image" src="https://github.com/user-attachments/assets/e9e2e7a0-50bb-4109-b8d9-65e9b713a3c1" />
 #### **Concluciones - Prueba de Sanidad (Smoke Test)**
--------------------------------------------------------------------------------------------------------------------------------------------------
#### 4.1.2.2 **Prueba de Escalamiento (Ramp-up)**
- **Estrategia**: Iniciar en 0 usuarios y aumentar gradualmente hasta X usuarios en 3 minutos, mantener 5 minutos
- **Niveles de Prueba**: 100 → 200 → 300 → 400 → 500 usuarios (se saturo maquina en 300 usuarios)
- **Objetivo**: Encontrar la capacidad máxima sin degradación significativa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_X_users_results.jtl -Jusers=X"`
- **Evidencias**: 
  - **100 Usuarios**
    <img width="1194" height="480" alt="image" src="https://github.com/user-attachments/assets/ab638f5d-e9d8-4b2b-974f-b2f64efb3f08" />
  - **CloudWatch**
    <img width="1186" height="644" alt="image" src="https://github.com/user-attachments/assets/b4dbdc22-c69b-4246-b63d-7ea8056de708" />
    <img width="1232" height="579" alt="image" src="https://github.com/user-attachments/assets/e55d5c9b-13b4-4f03-9b4d-f7c2584177b6" />
    <img width="1257" height="658" alt="image" src="https://github.com/user-attachments/assets/45dcd64d-4451-417d-af1f-cdbeee912cae" />

  - **200 Usuarios**
    <img width="1192" height="608" alt="image" src="https://github.com/user-attachments/assets/ffe341d5-0c16-4390-ba88-73aaeeab57ca" />
  - **CloudWatch**
    <img width="2962" height="1342" alt="image" src="https://github.com/user-attachments/assets/a610a9ee-5e6c-4929-ad55-4063e2397215" />
    <img width="1186" height="792" alt="image" src="https://github.com/user-attachments/assets/54dd0299-d1d2-49ae-8075-fc27dc0a5326" />
    <img width="696" height="581" alt="image" src="https://github.com/user-attachments/assets/8edd65af-9d61-49ae-a313-01a6a2b445be" />
    
  - **300 Usuarios**
    <img width="1201" height="384" alt="image" src="https://github.com/user-attachments/assets/d97a2d87-0b04-474a-848e-388fbf913a90" />
  - **CloudWatch**
    <img width="1348" height="339" alt="image" src="https://github.com/user-attachments/assets/215d1297-ab01-4d0e-ba8b-f5f9472c55cb" />
    <img width="896" height="281" alt="image" src="https://github.com/user-attachments/assets/3f44b6b4-b970-4995-ac31-6ff15bce95b5" />
    <img width="2954" height="1228" alt="image" src="https://github.com/user-attachments/assets/788b7d48-4793-47a7-9824-9dbc38fa7053" />
    <img width="1346" height="320" alt="image" src="https://github.com/user-attachments/assets/4d794a25-b9f8-4309-baa5-c5a4569a1f1b" />
    
#### **Concluciones - Prueba de Escalamiento (Ramp-up)**
------------------------------------------------------------------------------------------------------------------------------------------
#### 4.1.2.3 **Prueba Sostenida**

- **Usuarios**: 80% de la capacidad máxima encontrada (cap maxima 300 usuarios, se realizo prueba con 240 usuarios)
- **Duración**: 5 minutos
- **Objetivo**: Confirmar estabilidad del sistema bajo carga sostenida

- **Evidencias**:
  - **Prueba sostenida**
    <img width="1171" height="424" alt="image" src="https://github.com/user-attachments/assets/d42f0f3b-1368-4c3d-b7a7-c2dd66b145af" />
  - **CloudWatch**
    <img width="1357" height="405" alt="image" src="https://github.com/user-attachments/assets/026f0360-1a97-4fa8-b6a7-d2283a0e6172" />
    <img width="931" height="290" alt="image" src="https://github.com/user-attachments/assets/430068e1-d172-4f60-bc1a-54133d9f3be2" />
    <img width="1234" height="569" alt="image" src="https://github.com/user-attachments/assets/46530c6f-263e-42e8-809d-7147772c30cf" />
    <img width="1238" height="578" alt="image" src="https://github.com/user-attachments/assets/ff0b29d4-ff46-4522-bdf9-dc0a505bf723" />
    <img width="1244" height="590" alt="image" src="https://github.com/user-attachments/assets/b25bf460-bf0c-4ed5-b2e4-135eb728f1a8" />

#### **Concluciones - Prueba Sostenida**

#### 4.1.3 Endpoints a Probar
- `POST /auth/login` - Autenticación
- `POST /videos/upload` - Subida de videos
- `GET /videos` - Lista de videos del usuario
- `GET /public/videos` - Videos públicos
- `POST /public/videos/{video_id}/vote` - Votación

## 4.2 Escenario 2: Rendimiento de la Capa Worker (Videos/Minuto)

### 4.2.1 Estrategia de Implementación
- **Bypass de la Web**: Inyección directa de mensajes en la cola de AWS SQS
- **Payloads Realistas**: Uso de archivos de video de diferentes tamaños (50MB)
- **Configuraciones Variables**: 1, 2, 4 procesos/hilos por nodo

### 4.2.2 Escenarios de Prueba

#### 4.2.2.1 **Pruebas de Saturación**
- **Objetivo**: Envio de 20 videos
- **Estrategia**: Aumentar progresivamente la cantidad de tareas en la cola
- **Tamaños de Video**: 50MB
- **Concurrencia de Worker**: 1, 2, 4 procesos/hilos por nodo
- **Tiempo de Espera**: Envio de 20 videos
- **Evidencias**:
  - ##Pruebas de saturacion Worker
      ###Inyeccion 100 videos en la cola
      <img width="1249" height="648" alt="image" src="https://github.com/user-attachments/assets/387e535b-a3fb-4391-857d-96e6f5f586de" />

      ## Monitoreo de la maquina directamente con las herramientas de linux htop
      <img width="1234" height="947" alt="image" src="https://github.com/user-attachments/assets/93a9b05f-944b-438c-87e5-3a095305757d" />

      ## Monitoreo de la maquina mediante la herramienta CloudWatch
      <img width="1133" height="1345" alt="image" src="https://github.com/user-attachments/assets/bbb85982-12f4-4b06-976a-4a6f4578a459" />
      <img width="1151" height="607" alt="image" src="https://github.com/user-attachments/assets/8cca0986-519b-4443-a51d-e39992033c2a" />
      <img width="1112" height="637" alt="image" src="https://github.com/user-attachments/assets/c85417b9-10ad-45e9-ad4b-416e3acd3658" />


      

#### **Concluciones - Pruebas de Saturación**
---------------------------------------------------------------------------------------------------------------------------------




