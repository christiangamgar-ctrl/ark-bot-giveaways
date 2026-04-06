# 🎮 ArkStar Legacy Bot — Giveaways & Mystery Box

Bot de Discord con sistema completo de **Giveaways** y **Mystery Box** con llaves.

---

## 📁 Estructura de archivos

```
bot/
├── main.py              # Archivo principal
├── config.py            # Premios, precios, configuración
├── requirements.txt     # Dependencias
├── .env.example         # Plantilla de variables de entorno
└── cogs/
    ├── giveaways.py     # Sistema de giveaways
    └── mysterybox.py    # Sistema de mystery box y llaves
```

---

## ⚙️ Configuración inicial

### 1. Variables de entorno en Railway
En Railway, ve a tu servicio → **Variables** y añade:
```
DISCORD_TOKEN = tu_token_de_discord
```

### 2. Configurar el rol de admin
Abre `config.py` y cambia esta línea con el nombre exacto de tu rol de admin en Discord:
```python
ADMIN_ROLE_NAME = "Admin"  # ← Cambia esto
```

### 3. Subir a GitHub y deployar en Railway
- Sube todos los archivos a tu repositorio de GitHub
- Railway detectará automáticamente Python y usará `requirements.txt`
- Asegúrate de que el **Start Command** en Railway sea: `python main.py`

---

## 🎉 Comandos de Giveaway

| Comando | Quién | Descripción |
|---|---|---|
| `/giveaway` | Admin | Crear un nuevo giveaway |
| `/endgiveaway <message_id>` | Admin | Finalizar giveaway y elegir ganador |
| `/listgiveaways` | Admin | Ver todos los giveaways activos |

### Cómo funciona:
1. Admin usa `/giveaway` → elige descripción + premio secreto
2. El bot publica un embed con botón **Enter**
3. Los usuarios pulsan Enter para inscribirse (contador en tiempo real)
4. Admin usa `/endgiveaway` con el ID del mensaje → el bot elige ganador aleatorio
5. El embed se actualiza con el ganador, el premio (ahora visible), fechas y el admin que lo finalizó
6. El botón Enter queda **deshabilitado y oscuro**

---

## 📦 Comandos de Mystery Box

| Comando | Quién | Descripción |
|---|---|---|
| `/buykey` | Cualquiera | Ver cómo comprar una llave (muestra PayPal) |
| `/mykeys` | Cualquiera | Ver cuántas llaves tienes |
| `/givekey` | Admin | Regalar llave: el primero en pulsar se la lleva |
| `/mysterybox` | Admin | Crear una mystery box |
| `/addkey <usuario> <cantidad>` | Admin | Añadir llaves a un usuario (tras confirmar pago) |
| `/removekey <usuario> <cantidad>` | Admin | Quitar llaves a un usuario |
| `/checkkeys <usuario>` | Admin | Ver cuántas llaves tiene un usuario |

### Cómo funciona la Mystery Box:
1. Admin usa `/mysterybox`:
   - **Modo Aleatorio**: el bot elige el premio con probabilidades ponderadas
   - **Modo Manual**: el admin elige el premio (el jugador NO sabe si fue manual o aleatorio)
2. El bot publica el embed con botón **"Usar llave para abrir"**
3. El usuario pulsa el botón (necesita ≥1 llave)
4. Los admins reciben una notificación con el premio secreto y botones Aprobar/Rechazar
5. Si aprueban: se descuenta la llave, el premio se envía al usuario **por DM** (privado)
6. El embed público solo muestra que fue abierta, sin revelar el premio

### Probabilidades de Mystery Box:
Los items raros (Private Map) tienen mucho menos probabilidad que los comunes.
Puedes ajustar los pesos en `config.py` en la sección `MYSTERY_BOX_PRIZES`.

---

## 💡 Notas importantes

- **Las llaves se guardan en memoria**: si el bot se reinicia, se pierden los datos.
  Si quieres persistencia, avísame y añadimos una base de datos SQLite.
- El bot usa **Slash Commands** (`/comando`), no prefijo `!`
- Los comandos de admin comprueban el rol por nombre (`ADMIN_ROLE_NAME` en config.py)
  o si el usuario tiene permisos de administrador en el servidor
- El premio de la mystery box se envía por **DM** al ganador para que sea privado

---

## 🛠️ Solución de problemas

**Los slash commands no aparecen:**
- El bot necesita unos minutos para sincronizar los comandos con Discord
- Asegúrate de que el bot tiene permisos de `applications.commands` al invitarlo

**Error de token:**
- Comprueba que `DISCORD_TOKEN` está correctamente configurado en Railway

**El bot no detecta el rol de admin:**
- El nombre del rol en `ADMIN_ROLE_NAME` debe ser exactamente igual (mayúsculas incluidas)
