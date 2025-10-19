# Configuración de CI/CD Pipeline

Este repositorio incluye un pipeline de Integración Continua (CI) que se ejecuta automáticamente en GitHub Actions.

## 🚀 Características del Pipeline

El pipeline incluye tres etapas fundamentales:

### 1. **Ejecución de Pruebas Unitarias** (`test`)
- Ejecuta todas las pruebas unitarias del backend y worker
- Configura servicios de PostgreSQL y Redis para las pruebas
- Genera reportes de cobertura de código
- Sube los reportes a Codecov

### 2. **Construcción Automática** (`build`)
- Construye todas las imágenes Docker del proyecto
- Valida la configuración de docker-compose
- Utiliza cache de Docker para optimizar el tiempo de construcción

### 3. **Análisis de Calidad con SonarCloud** (`sonarcloud`)
- Analiza la calidad del código Python usando SonarCloud
- Detecta vulnerabilidades, code smells y problemas de mantenibilidad
- Genera reportes de cobertura para SonarCloud
- Bloquea el merge si no pasa el quality gate

## ⚙️ Configuración Requerida

### ✅ **Configuración Requerida para SonarCloud**

Para que el pipeline funcione completamente, necesitas configurar:

#### **1. SonarCloud Token (Requerido)**
1. Ve a [SonarCloud.io](https://sonarcloud.io)
2. Inicia sesión con tu cuenta de GitHub
3. Ve a **Account > Security > Generate Tokens**
4. Crea un token con nombre "GitHub Actions"
5. Copia el token generado
6. En GitHub, ve a **Settings > Secrets and variables > Actions**
7. Crea un nuevo secret llamado `SONAR_TOKEN` con el token copiado

#### **2. Configuración Automática**
- **Base de datos**: Se configura automáticamente para las pruebas (SQLite)
- **Servicios**: Redis se configura automáticamente
- **SonarCloud**: Se conecta automáticamente usando el token

## 🔧 Configuración Local (Opcional)

Si quieres ejecutar las pruebas localmente:

```bash
# Instalar dependencias
cd backend && pip install -r requirements.txt && pip install pytest-cov
cd ../worker && pip install -r requirements.txt

# Ejecutar pruebas del backend
cd backend
export DATABASE_URL="sqlite:///./test.db"
export REDIS_URL="redis://localhost:6379/0"
export TEST_MODE=true
export UPLOAD_DIR="/tmp/test_uploads"
mkdir -p /tmp/test_uploads/original /tmp/test_uploads/processed
pytest tests/ -v --cov=app --cov-report=xml

# Ejecutar pruebas del worker
cd ../worker
export DATABASE_URL="sqlite:///./test.db"
export REDIS_URL="redis://localhost:6379/0"
export UPLOAD_DIR="/tmp/test_uploads"
pytest tests/ -v --cov=tasks --cov-report=xml
```

## 📊 Triggers del Pipeline

El pipeline se ejecuta automáticamente en:

- **Push** a las ramas `main` y `develop`
- **Pull Requests** hacia las ramas `main` y `develop`

## 🎯 Criterios de Éxito

Para que un PR pueda ser mergeado, todas las etapas deben pasar:

- ✅ **Tests**: Todas las pruebas unitarias deben pasar
- ✅ **Build**: Todas las imágenes Docker deben construirse correctamente
- ✅ **SonarCloud**: El análisis de calidad debe pasar el quality gate

## 🐛 Solución de Problemas

### Error de SonarCloud
- Verifica que el secret `SONAR_TOKEN` esté configurado correctamente
- Asegúrate de que el token tenga permisos de análisis
- El proyecto se crea automáticamente con la clave `misw4204-cloud`

### Error de Tests
- Revisa que las variables de entorno estén configuradas correctamente
- Verifica que las dependencias estén instaladas

### Error de Build
- Revisa que los Dockerfiles estén correctamente configurados
- Verifica que docker-compose.yml sea válido

## 📈 Monitoreo

- **Logs detallados**: Revisa la pestaña "Actions" en GitHub
- **Cobertura de código**: Los reportes se suben automáticamente a Codecov
- **Calidad de código**: SonarCloud se ejecuta automáticamente en cada pipeline

## 🔧 **Pipelines Disponibles**

### **Pipeline Principal** (`ci.yml`)
- **Triggers**: Push y PRs a `main` y `develop`
- **Incluye**: Tests (SQLite), Build, SonarCloud
- **Duración**: ~5-7 minutos
- **Base de datos**: SQLite (más confiable en CI)

### **Pipeline de Backend** (`test-backend-only.yml`)
- **Triggers**: Cambios solo en `backend/`
- **Incluye**: Solo tests del backend
- **Duración**: ~2-3 minutos
- **Ventaja**: Más rápido para cambios solo en backend
- **Base de datos**: SQLite (más confiable en CI)

## 🚀 **Próximos Pasos**

1. **Haz un push** a cualquier rama para activar el pipeline automáticamente
2. **Revisa los resultados** en la pestaña "Actions" de GitHub
3. **El pipeline se ejecutará** sin configuración adicional

## 🐛 **Solución de Problemas Actualizada**

### Error de Base de Datos
- ✅ **Solucionado**: Uso exclusivo de SQLite (más confiable en CI)
- ✅ **Eliminado**: Dependencias de PostgreSQL que causaban fallos
- ✅ **Mejorado**: Configuración simplificada y robusta

### Error de SonarCloud
- ✅ **Solucionado**: Uso de SonarCloud en lugar de SonarQube local
- ✅ **Mejorado**: Configuración automática con GitHub Actions
- ✅ **Estable**: Sin problemas de contenedores o recursos

### Error de Tests
- ✅ **Solucionado**: Variables de entorno configuradas correctamente
- ✅ **Mejorado**: Solo Redis como dependencia externa
- ✅ **Simplificado**: Menos puntos de fallo
