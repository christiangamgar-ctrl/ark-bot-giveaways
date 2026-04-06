import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime
from config import MYSTERY_BOX_PRIZES, PAYPAL_LINK, KEY_PRICE_EUR, ADMIN_ROLE_NAME
import database as db


def is_admin():
    async def predicate(interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=ADMIN_ROLE_NAME)
        if role and role in interaction.user.roles:
            return True
        if interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.send_message(
            "❌ No tienes permisos para usar este comando.", ephemeral=True
        )
        return False
    return app_commands.check(predicate)


def roll_mystery_prize():
    prizes = [p[0] for p in MYSTERY_BOX_PRIZES]
    weights = [p[1] for p in MYSTERY_BOX_PRIZES]
    return random.choices(prizes, weights=weights, k=1)[0]


# ─────────────────────────────────────────────────────────────────────────────
#  VISTAS
# ─────────────────────────────────────────────────────────────────────────────

class ClaimKeyView(discord.ui.View):
    def __init__(self, giveaway_msg_id: int):
        super().__init__(timeout=None)
        self.giveaway_msg_id = giveaway_msg_id

    @discord.ui.button(label="🗝️ ¡Reclamar llave!", style=discord.ButtonStyle.success, custom_id="claim_key")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificar que el key giveaway sigue activo en DB
        kg = db.get_key_giveaway(self.giveaway_msg_id)
        if not kg:
            await interaction.response.send_message("❌ Esta llave ya fue reclamada.", ephemeral=True)
            return

        # Desactivar en DB primero (evita race conditions)
        db.close_key_giveaway(self.giveaway_msg_id)

        db.add_keys(interaction.user.id, 1)
        total_keys = db.get_keys(interaction.user.id)
        claim_time = datetime.now().strftime("%d/%m/%Y %H:%M")

        button.disabled = True
        button.label = "🔒 Llave reclamada"
        button.style = discord.ButtonStyle.secondary

        try:
            msg = await interaction.channel.fetch_message(self.giveaway_msg_id)
            embed = msg.embeds[0]
            embed.color = 0x555555
            embed.title = "🗝️ LLAVE RECLAMADA"
            embed.add_field(name="🥇 Reclamada por", value=interaction.user.mention, inline=True)
            embed.add_field(name="🕔 Reclamada el", value=claim_time, inline=True)
            await msg.edit(embed=embed, view=self)
        except Exception as e:
            print(f"Error editando: {e}")

        await interaction.response.send_message(
            f"🎉 {interaction.user.mention} ¡Has conseguido la llave! Ahora tienes **{total_keys}** llave(s)."
        )

        db.log_event("key_claimed", {
            "msg_id": self.giveaway_msg_id,
            "claimer_id": interaction.user.id,
            "claim_time": claim_time
        })


class OpenBoxView(discord.ui.View):
    def __init__(self, box_msg_id: int):
        super().__init__(timeout=None)
        self.box_msg_id = box_msg_id

    @discord.ui.button(label="🔑 Usar llave para abrir", style=discord.ButtonStyle.primary, custom_id="open_box")
    async def open_box(self, interaction: discord.Interaction, button: discord.ui.Button):
        box = db.get_mystery_box(self.box_msg_id)
        if not box:
            await interaction.response.send_message("❌ Esta mystery box ya no está disponible.", ephemeral=True)
            return

        if box["pending_user_id"] is not None:
            await interaction.response.send_message(
                "⏳ Ya hay alguien esperando aprobación de admin para esta caja.", ephemeral=True
            )
            return

        keys = db.get_keys(interaction.user.id)
        if keys < 1:
            await interaction.response.send_message(
                f"❌ No tienes llaves. Compra una aquí: {PAYPAL_LINK}\nPrecio: **€{KEY_PRICE_EUR}** por llave.",
                ephemeral=True
            )
            return

        db.set_box_pending_user(self.box_msg_id, interaction.user.id)

        approve_view = AdminApproveView(
            box_msg_id=self.box_msg_id,
            requester=interaction.user,
            box_channel=interaction.channel
        )

        host_mention = f"<@{box['host_id']}>"
        admin_msg_content = (
            f"🔔 **{interaction.user.mention}** quiere usar una llave para abrir la **Mystery Box** "
            f"(ID: `{self.box_msg_id}`).\n"
            f"📦 Creada por: {host_mention}\n"
            f"🏆 Contenido: **{box['prize']}** *(solo visible para admins)*\n"
            f"⚙️ Método: {box['prize_method']}\n\n"
            f"¿Apruebas?"
        )

        await interaction.channel.send(admin_msg_content, view=approve_view)
        await interaction.response.send_message(
            "⏳ Solicitud enviada. Un admin debe aprobarla.", ephemeral=True
        )


class AdminApproveView(discord.ui.View):
    def __init__(self, box_msg_id: int, requester: discord.Member, box_channel: discord.TextChannel):
        super().__init__(timeout=300)
        self.box_msg_id = box_msg_id
        self.requester = requester
        self.box_channel = box_channel

    async def _check_admin(self, interaction: discord.Interaction) -> bool:
        role = discord.utils.get(interaction.guild.roles, name=ADMIN_ROLE_NAME)
        return (role and role in interaction.user.roles) or interaction.user.guild_permissions.administrator

    @discord.ui.button(label="✅ Aprobar", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_admin(interaction):
            await interaction.response.send_message("❌ Solo admins pueden aprobar.", ephemeral=True)
            return

        box = db.get_mystery_box(self.box_msg_id)
        if not box:
            await interaction.response.send_message("❌ La mystery box ya no existe.", ephemeral=True)
            return

        prize = box["prize"]
        open_time = datetime.now().strftime("%d/%m/%Y %H:%M")

        db.remove_keys(self.requester.id, 1)
        db.close_mystery_box(self.box_msg_id)

        # Editar mensaje original
        try:
            msg = await self.box_channel.fetch_message(self.box_msg_id)
            embed = msg.embeds[0]
            embed.color = 0x555555
            embed.title = "📦 MYSTERY BOX ABIERTA"
            embed.add_field(name="🥇 Abierta por", value=self.requester.mention, inline=True)
            embed.add_field(name="✅ Aprobado por", value=interaction.user.mention, inline=True)
            embed.add_field(name="🕔 Abierta el", value=open_time, inline=True)

            disabled_view = discord.ui.View()
            btn = discord.ui.Button(label="🔒 Cerrada", style=discord.ButtonStyle.secondary, disabled=True)
            disabled_view.add_item(btn)
            await msg.edit(embed=embed, view=disabled_view)
        except Exception as e:
            print(f"Error editando box: {e}")

        # Enviar premio al usuario por DM
        try:
            await self.requester.send(
                f"🎉 ¡Tu Mystery Box ha sido abierta!\n"
                f"🏆 Tu premio es: **{prize}**\n"
                f"Contacta con un admin para reclamarlo."
            )
        except Exception:
            await self.box_channel.send(
                f"🎉 {self.requester.mention} tu mystery box fue abierta. Revisa tus DMs para ver tu premio.",
                delete_after=15
            )

        await self.box_channel.send(
            f"📦 {self.requester.mention} ha abierto la Mystery Box. ¡Contacta con un admin para reclamar tu premio!"
        )

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=f"✅ Aprobado por {interaction.user.mention}. Premio enviado al usuario por DM.",
            view=self
        )

        db.log_event("box_opened", {
            "box_id": self.box_msg_id,
            "opener_id": self.requester.id,
            "prize": prize,
            "approved_by": interaction.user.id,
            "open_time": open_time
        })

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_admin(interaction):
            await interaction.response.send_message("❌ Solo admins pueden rechazar.", ephemeral=True)
            return

        db.clear_box_pending_user(self.box_msg_id)

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=f"❌ Solicitud rechazada por {interaction.user.mention}.",
            view=self
        )
        await self.box_channel.send(
            f"❌ {self.requester.mention} tu solicitud para abrir la mystery box fue rechazada."
        )


# ─────────────────────────────────────────────────────────────────────────────
#  COG
# ─────────────────────────────────────────────────────────────────────────────

class MysteryBoxCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buykey", description="Ver cómo comprar una llave de Mystery Box")
    async def buykey(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🗝️ Comprar Llave de Mystery Box",
            description=(
                f"Cada llave cuesta **€{KEY_PRICE_EUR}**.\n\n"
                f"Realiza el pago y muestra el comprobante a un admin para recibir tu llave.\n\n"
                f"🔗 **[Pagar con PayPal]({PAYPAL_LINK})**"
            ),
            color=0xFFD700
        )
        embed.set_footer(text="ArkStar Legacy · Mystery Box")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mykeys", description="Ver cuántas llaves tienes")
    async def mykeys(self, interaction: discord.Interaction):
        keys = db.get_keys(interaction.user.id)
        await interaction.response.send_message(
            f"🗝️ Tienes **{keys}** llave(s) disponible(s).", ephemeral=True
        )

    @app_commands.command(name="givekey", description="[ADMIN] Regalar una llave: el primero en pulsar se la lleva")
    @is_admin()
    async def givekey(self, interaction: discord.Interaction):
        start_time = datetime.now().strftime("%d/%m/%Y %H:%M")

        embed = discord.Embed(
            title="🗝️ LLAVE GRATIS",
            description="¡Un admin está regalando una llave de Mystery Box!\n**¡El primero que pulse el botón se la lleva!**",
            color=0x00FF88
        )
        embed.add_field(name="🕐 Iniciado el", value=start_time, inline=True)
        embed.add_field(name="👑 Regalado por", value=interaction.user.mention, inline=True)
        embed.set_footer(text="ArkStar Legacy · Mystery Box")

        await interaction.response.defer()
        msg = await interaction.channel.send(embed=embed)

        db.create_key_giveaway(message_id=msg.id, host_id=interaction.user.id)

        view = ClaimKeyView(giveaway_msg_id=msg.id)
        await msg.edit(view=view)

        await interaction.followup.send("✅ Llave gratis publicada.", ephemeral=True)

    @app_commands.command(name="mysterybox", description="[ADMIN] Crear una Mystery Box")
    @app_commands.describe(
        modo="random = el bot elige el premio | admin = tú eliges el premio",
        premio_manual="Si modo=admin, selecciona el premio aquí"
    )
    @app_commands.choices(
        modo=[
            app_commands.Choice(name="🎲 Aleatorio (el bot elige)", value="random"),
            app_commands.Choice(name="👑 Manual (el admin elige)", value="admin"),
        ],
        premio_manual=[
            app_commands.Choice(name=p[0], value=p[0]) for p in MYSTERY_BOX_PRIZES
        ]
    )
    @is_admin()
    async def mysterybox(
        self,
        interaction: discord.Interaction,
        modo: app_commands.Choice[str],
        premio_manual: app_commands.Choice[str] = None
    ):
        if modo.value == "random":
            prize = roll_mystery_prize()
            prize_method = "🎲 Aleatorio (bot)"
        else:
            if not premio_manual:
                await interaction.response.send_message(
                    "❌ En modo admin debes seleccionar el premio en `premio_manual`.", ephemeral=True
                )
                return
            prize = premio_manual.value
            prize_method = "👑 Elegido por admin"

        start_time = datetime.now().strftime("%d/%m/%Y %H:%M")

        embed = discord.Embed(
            title="📦 MYSTERY BOX",
            description=(
                "Un admin ha abierto una **Mystery Box**.\n"
                "¿Tienes una llave? ¡Úsala para abrirla y descubrir tu premio!\n\n"
                f"🗝️ Precio de llave: **€{KEY_PRICE_EUR}** · [Comprar aquí]({PAYPAL_LINK})"
            ),
            color=0xFF6600
        )
        embed.add_field(name="🏆 Premio", value="*Secreto — se revelará al abrirla*", inline=False)
        embed.add_field(name="🕐 Publicada el", value=start_time, inline=True)
        embed.add_field(name="👑 Creada por", value=interaction.user.mention, inline=True)
        embed.set_footer(text="ArkStar Legacy · Mystery Box")

        await interaction.response.defer()
        msg = await interaction.channel.send(embed=embed)

        db.create_mystery_box(
            message_id=msg.id,
            channel_id=interaction.channel.id,
            guild_id=interaction.guild.id,
            prize=prize,
            prize_method=prize_method,
            host_id=interaction.user.id,
            start_time=start_time
        )

        view = OpenBoxView(box_msg_id=msg.id)
        await msg.edit(view=view)

        await interaction.followup.send(
            f"✅ Mystery Box creada.\n"
            f"🏆 Premio secreto: **{prize}**\n"
            f"⚙️ Método: {prize_method}",
            ephemeral=True
        )

    @app_commands.command(name="addkey", description="[ADMIN] Añadir llaves a un usuario (pago confirmado)")
    @app_commands.describe(usuario="Usuario", cantidad="Número de llaves a añadir")
    @is_admin()
    async def addkey(self, interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
        db.add_keys(usuario.id, cantidad)
        total = db.get_keys(usuario.id)
        await interaction.response.send_message(
            f"✅ Se añadieron **{cantidad}** llave(s) a {usuario.mention}. Total: **{total}**.",
            ephemeral=True
        )

    @app_commands.command(name="removekey", description="[ADMIN] Quitar llaves a un usuario")
    @app_commands.describe(usuario="Usuario", cantidad="Número de llaves a quitar")
    @is_admin()
    async def removekey(self, interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
        new_qty = db.remove_keys(usuario.id, cantidad)
        await interaction.response.send_message(
            f"✅ Se quitaron **{cantidad}** llave(s) a {usuario.mention}. Total: **{new_qty}**.",
            ephemeral=True
        )

    @app_commands.command(name="checkkeys", description="[ADMIN] Ver cuántas llaves tiene un usuario")
    @app_commands.describe(usuario="Usuario a consultar")
    @is_admin()
    async def checkkeys(self, interaction: discord.Interaction, usuario: discord.Member):
        keys = db.get_keys(usuario.id)
        await interaction.response.send_message(
            f"🗝️ {usuario.mention} tiene **{keys}** llave(s).", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(MysteryBoxCog(bot))
