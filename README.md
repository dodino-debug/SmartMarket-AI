# SmartMarket AI

Prototipo académico para consultar ventas e inventario de un supermercado ficticio. Incluye un panel de inteligencia de negocios y un chatbot en español basado en reglas. Los datos son simulados y cubren de enero a diciembre de 2025.

Flask sirve la aplicación, psycopg conecta con PostgreSQL y Gunicorn ejecuta Flask en Render. PostgreSQL reemplaza a SQLite para guardar los datos en Neon independientemente de los reinicios o despliegues del servicio web. Los gráficos usan HTML y JavaScript del repositorio, sin dependencias de un CDN. El asistente tampoco necesita claves de un servicio de IA.

## 1. Preparar el entorno local

Instala Git y Python 3.14. Si ya tienes el repositorio abierto, ejecuta los comandos desde su raíz. Para obtener una copia nueva:

```sh
git clone https://github.com/dodino-debug/SmartMarket-AI.git
cd SmartMarket-AI
python -m venv .venv
```

En Windows PowerShell, puedes usar `\.venv\Scripts\python.exe` en lugar de `python` en los comandos siguientes, o activar el entorno con `.\.venv\Scripts\Activate.ps1`. En macOS o Linux, activa el entorno con `source .venv/bin/activate`.

## 2. Instalar dependencias

```sh
python -m pip install -r requirements.txt
python -m pip check
```

Gunicorn se ejecuta en Linux, incluido Render. Para el desarrollo en Windows se usa el servidor de Flask.

## 3. Crear la base de datos en Neon

1. Inicia sesión en Neon y crea un proyecto para SmartMarket.
2. Crea o selecciona una base de datos de demostración y una rama. Para probar cambios sin afectar la entrega, usa una rama de Neon distinta de la que conectes a Render.
3. Abre **Connect**, selecciona la rama, base de datos y rol. El rol configurado debe poder crear tablas y escribir los datos de demostración en el esquema `public`.
4. Copia la URI PostgreSQL. Puedes mantener activado el *pooling*. Conserva los parámetros de conexión que entregue Neon, incluido `sslmode=require`, y copia la URI completa sin modificar la codificación de la contraseña. [Guía de conexión de Neon](https://neon.com/docs/connect/connect-from-any-app)

También puedes desarrollar con un servidor PostgreSQL local. Crea una base dedicada llamada `smartmarket`, con un rol propietario, y usa su URI en el paso siguiente.

## 4. Configurar las variables de entorno

En PowerShell, ejecuta `Copy-Item .env.example .env`. En macOS o Linux, ejecuta `cp .env.example .env`. Edita `.env` en tu equipo.

| Variable | Desarrollo local | Producción |
| --- | --- | --- |
| `DATABASE_URL` | URI de Neon o de PostgreSQL local | URI de Neon guardada en Render |
| `APP_ENV` | `development` | `production` |
| `FLASK_DEBUG` | Opcional con el servidor local | `0`, definido en el Blueprint |
| `PORT` | Flask usa 5000 de forma predeterminada | Render lo proporciona a Gunicorn |

Una URI local tiene la forma `postgresql://USUARIO:CONTRASEÑA_CODIFICADA@127.0.0.1:5432/smartmarket`, con tus propios valores. En producción, la conexión exige TLS y toma la configuración del entorno del servicio. `.env` y sus variantes están excluidos de Git. `.env.example` se versiona con el valor de conexión vacío.

## 5. Inicializar y ejecutar

```sh
python -m database.init
python -m flask --app app run
```

Abre `http://127.0.0.1:5000`. Para cargar únicamente el esquema, usa `python -m database.init --schema-only`. Ejecuta después el comando sin la opción para agregar los datos.

La inicialización crea el esquema y carga una semilla reproducible con 30 productos, 5 categorías, 5 proveedores y 12 meses de ventas. Las claves estables y `ON CONFLICT DO NOTHING` conservan los registros existentes. Un bloqueo transaccional de PostgreSQL serializa inicializaciones simultáneas y la transacción revierte un intento fallido.

```sh
python scripts/smoke.py http://127.0.0.1:5000
```

Los ingresos corresponden a la suma del precio unitario histórico por la cantidad de cada detalle, en pesos colombianos. Las transacciones cuentan tickets con al menos un detalle y las unidades suman las cantidades vendidas. Las alertas se activan cuando las existencias bajan del mínimo. Un producto con existencias por debajo del mínimo y al menos 30 unidades vendidas en el último mes registrado recibe prioridad de reposición. La recomendación comercial se activa con dos caídas consecutivas de ingresos en tres meses de calendario. Para «¿Cuánto vendimos este mes?», el chatbot contrasta el mes calendario de Bogotá con las fechas registradas y señala el último mes disponible si corresponde.

## 6. Publicar en GitHub

El remoto del proyecto es `dodino-debug/SmartMarket-AI`. Si usas un repositorio propio, créalo vacío y apunta `origin` a su URL con `git remote add origin URL` o, si ya existe `origin`, `git remote set-url origin URL`.

```sh
git remote -v
git status --short
git check-ignore .env
git add .env.example .gitignore .python-version README.md requirements.txt render.yaml app.py analytics.py chatbot.py database scripts static templates
git diff --cached --stat
git commit -m "Prepara SmartMarket AI para Render y Neon"
git push -u origin main
```

Estos comandos de *commit* y *push* aplican al publicar cambios locales por primera vez. En GitHub, comprueba que la rama `main` contenga `render.yaml`, `requirements.txt` y el código. Si el repositorio es privado, concede acceso a Render mediante la integración de GitHub.

## 7. Desplegar en Render

1. Abre el panel de Render y elige **New > Blueprint**.
2. Conecta GitHub, selecciona el repositorio y la rama `main`, y usa el archivo `render.yaml` de la raíz.
3. Cuando Render solicite `DATABASE_URL`, pega la URI de la base de demostración de Neon. Para un Blueprint existente, edita el valor en **Environment** del servicio web.
4. Aplica el Blueprint. Render instala las dependencias en la compilación. En cada arranque ejecuta primero `python -m database.init` y, si termina correctamente, inicia Gunicorn en `0.0.0.0:$PORT`. Esta secuencia permite inicializar en el plan gratuito sin un comando de predespliegue. Gunicorn sirve la aplicación con debug desactivado.
5. Revisa los registros del despliegue, confirma que Render habilite el servicio y copia la URL HTTPS que aparezca en el panel. Los datos permanecen en Neon. Los archivos CSS y JavaScript se sirven desde las rutas `/static/` generadas por Flask.

[Guía de Flask en Render](https://render.com/docs/deploy-flask) · [Referencia del Blueprint](https://render.com/docs/blueprint-spec)

## 8. Verificar la URL pública

1. Abre `https://TU-SERVICIO.onrender.com/health`. Debe responder HTTP 200 con `{"database":"ok","status":"ok"}`. Un HTTP 503 indica que falló el acceso a PostgreSQL o alguna tabla del esquema.
2. Ejecuta la prueba HTTP desde un equipo con acceso a internet.

   ```sh
   python scripts/smoke.py https://TU-SERVICIO.onrender.com
   ```

   Comprueba la página, los archivos estáticos, la salud de PostgreSQL, los totales de los gráficos, las reglas de negocio y 21 consultas del chatbot.
3. Abre la raíz de la URL en una ventana privada. Comprueba que aparezcan las barras de 12 meses y 5 categorías, las alertas de inventario y las recomendaciones. Envía «¿Qué productos necesitan reposición?» y «¿Qué categoría genera mayores ingresos?». Prueba una pregunta sugerida y el botón **Limpiar conversación**.
4. Comparte con el docente la URL de la página principal cuando pasen las verificaciones. El docente solo necesita un navegador. En el plan gratuito, el primer acceso tras un período de inactividad puede tardar mientras se inicia el servicio. [Servicios gratuitos en Render](https://render.com/docs/free)

**Estado de verificación:** prueba HTTP ejecutada contra PostgreSQL 18 local. La verificación de Neon, de Gunicorn en Render y de una URL pública depende de completar el despliegue.
