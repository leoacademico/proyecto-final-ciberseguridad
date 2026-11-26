# TecnoHogar MTY — Proyecto final de Ciberseguridad

Integrantes: Leonardo, Rodrigo y Nelida.

Aplicación académica Flask y SQLite, con datos ficticios. Uso exclusivo en localhost (127.0.0.1). No apta para producción. La base de datos se crea localmente y las cuentas precargadas son únicamente de demostración. La clave de sesión de respaldo y las contraseñas de demostración en texto plano no son controles de producción.

## Instalación en Windows (PowerShell)

Ejecutar desde la carpeta del repositorio, un comando a la vez:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Abrir http://127.0.0.1:5000. Detener con Ctrl+C.

## Controles implementados

- SQL Injection: consultas parametrizadas en `/login` y `/buscar`.
- XSS: escapado HTML de la búsqueda y de autor/comentario en reseñas.
- IDOR/BOLA: comprobación de propiedad del pedido en la página y API; respuesta 403 si no corresponde al usuario autenticado.
- Registro de solicitudes y eventos en `app.log` (archivo local excluido del repositorio).

## Validación

Repetir las pruebas de la guía del equipo en el entorno local. Ejecutar OWASP ZAP antes y después de las correcciones. Las pruebas manuales de autorización son necesarias aunque ZAP no detecte IDOR. Documentar resultados reales; no confundir los resultados esperados con los observados.

## Mejora de recuperación (actividad 7, opción C)

Con la aplicación detenida y la base ficticia creada, ejecutar, por ejemplo (ajustar E: a la unidad disponible):

```powershell
python respaldo.py --destino E:\RespaldoTecnoHogar
```

Sin otra unidad, es posible usar una carpeta separada, por ejemplo `$HOME\RespaldoTecnoHogar`, siempre que esté fuera del directorio del proyecto. Documentar que no hay separación física si comparte disco. El script verifica SHA-256 del origen, respaldo y restauración de una copia temporal, además de `PRAGMA integrity_check` de SQLite. No borra el original. Conserva el respaldo y el manifiesto SHA256.txt. El manifiesto no sustituye una firma o almacenamiento inmutable; para ransomware se recomienda copia desconectada o inmutable y pruebas periódicas.

## Archivos

- `app.py`: aplicación integrada de laboratorio.
- `requirements.txt`: dependencia Flask.
- `respaldo.py`: demostración de recuperación sin eliminación del origen.
- `.gitignore`: excluye archivos locales, entornos, bases y registros.

No publicar credenciales reales, claves privadas, bases de datos ni registros que contengan datos sensibles. Si un archivo ya está versionado, `.gitignore` no lo elimina del historial.
