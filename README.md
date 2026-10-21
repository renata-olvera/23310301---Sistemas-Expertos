# Intérprete de proposiciones y reglas

Programa en Python para extraer proposiciones (X1, X2...) y expresar reglas (R1, R2...) a partir de texto en español.

## Uso

1. Escribe o pega el problema en `problema.txt` (puede ser un párrafo completo o varias líneas).
2. Ejecuta en la terminal, desde esta carpeta:

```bash
python ejecutar.py problema.txt
```

Para otro problema, crea otro archivo `.txt` y cambia su nombre en el comando.

## Operaciones

Admite estructuras como `Si P, entonces Q`, `P y Q`, `P o Q`, `P no ...`, `No es cierto que P` y agrupaciones con paréntesis. Las oraciones que no se puedan interpretar se muestran para revisión.

La aplicación únicamente identifica proposiciones y reglas. No calcula todavía satisfacibilidad ni convierte a FNC. Funciona con Python estándar, sin instalaciones adicionales.
