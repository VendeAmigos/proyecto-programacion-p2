# Guía de Comandos del Proyecto

## Comandos de Git

### 1. Crear y moverse a una nueva rama (branch)
Crea una nueva rama local y te cambia a ella:
```bash
git checkout -b nombre_de_tu_rama
```

*(Importante: Para que esta nueva rama aparezca en la página web de GitHub, debes subirla ejecutando:)*
```bash
git push -u origin nombre_de_tu_rama
```

### 2. Guardar (comitear) y subir a la rama actual
Agrega los cambios, haz el commit y súbelos a GitHub:
```bash
# Agregar todos los archivos modificados
git add .

# Crear el commit con un mensaje descriptivo
git commit -m "Tu mensaje descriptivo aquí"

# Subir los cambios a tu rama en el repositorio remoto
git push origin nombre_de_tu_rama
```
*(Nota: Si es la primera vez que subes esta rama, usa `git push -u origin nombre_de_tu_rama`)*

### 3. Descargar una rama remota
Si alguien más creó una rama y quieres descargarla a tu computadora:
```bash
# Actualizar la lista de ramas y cambios del repositorio remoto
git fetch

# Moverte a la rama descargada
git checkout nombre_de_la_rama
```
*(Si ya tienes la rama localmente y solo quieres bajar nuevos cambios, colócate en la rama y ejecuta `git pull origin nombre_de_la_rama`)*.

---

## Comandos de SASS

Estos comandos se ejecutan desde la terminal en la raíz del proyecto para procesar tus archivos CSS.

### 1. Instalar dependencias (solo la primera vez)
```bash
cd static/scss
npm install
cd ../..
```

### 2. Compilar SASS de forma manual (una sola vez)
Convierte el código `.scss` a `styles.css`.
```bash
npx sass static/scss/styles.scss static/styles.css
```

### 3. Modo Observador (Watch) - RECOMENDADO
Deja ejecutando SASS en segundo plano. Cada vez que guardes un archivo `.scss`, se compilará automáticamente a `.css`.
```bash
npx sass --watch static/scss/styles.scss static/styles.css
```
*(Para detener este modo, presiona `Ctrl + C` en la terminal)*.
