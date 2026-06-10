# Git commands

## Status and staging

`git status` muestra qué archivos cambiaron, cuáles están preparados para commit y cuáles no.

```bash
git status
```

`git add .` agrega todos los cambios del directorio actual al staging.

```bash
git add .
```

`git add static/scss/styles.scss` agrega un archivo específico al staging.

```bash
git add static/scss/styles.scss
```

## Commit

`git commit -m "mensaje"` guarda los cambios preparados con un mensaje corto y claro.

```bash
git commit -m "mensaje del commit"
```

## New branch

`git checkout -b nueva-rama` crea una rama nueva y te cambia a ella en un solo paso.

```bash
git checkout -b nueva-rama
```

`git switch -c nueva-rama` hace lo mismo, pero con el comando moderno recomendado.

```bash
git switch -c nueva-rama
```

## Clone a repository

`git clone` descarga un repositorio remoto en tu computadora.

```bash
git clone https://github.com/usuario/repositorio.git
```

## Useful extras

`git branch` lista las ramas locales.

```bash
git branch
```

`git branch -a` muestra ramas locales y remotas.

```bash
git branch -a
```

`git checkout nombre-rama` cambia a una rama existente.

```bash
git checkout nombre-rama
```

`git switch nombre-rama` hace el cambio de rama con el comando moderno.

```bash
git switch nombre-rama
```

`git pull origin main` trae los cambios más recientes del remoto.

```bash
git pull origin main
```

`git push origin nueva-rama` sube tu rama al repositorio remoto.

```bash
git push origin nueva-rama
```

## Run Sass

Primero instala las dependencias del proyecto si todavía no lo hiciste.

```bash
npm install
```

`npm run sass:build` compila `static/scss/styles.scss` y genera `static/styles.css`.

```bash
npm run sass:build
```

`npm run sass:watch` deja Sass observando cambios y recompila automáticamente.

```bash
npm run sass:watch
```

`npm run sass:build:compressed` genera la versión minificada del CSS.

```bash
npm run sass:build:compressed
```