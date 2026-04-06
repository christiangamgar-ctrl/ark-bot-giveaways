import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime
from config import GIVEAWAY_PRIZES, ADMIN_ROLE_NAME
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


class GiveawayEnterButton(discord.ui.View):
    def __init__(self, giveaway_id: int):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(
        label="🎉 Enter",
        style=discord.ButtonStyle.secondary,
        custom_id="giveaway_enter"
    )
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        gw = db.get_giveaway(self.giveaway_id)
        if not gw:
            await interaction.response.send_message("❌ Este giveaway ya no está activo.", ephemeral=True)
            return

        added = db.add_giveaway_entry(self.giveaway_id, interaction.user.id)
        if not added:
            await interaction.response.send_message("⚠️ Ya estás inscrito en este giveaway.", ephemeral=True)
            return

        total = db.get_giveaway_entry_count(self.giveaway_id)
        await interaction.response.send_message(
            f"✅ ¡Te has inscrito! Ahora hay **{total}** participante(s).", ephemeral=True
        )

        try:
            msg = await interaction.channel.fetch_message(self.giveaway_id)
            embed = msg.embeds[0]
            for i, field in enumerate(embed.fields):
                if field.name == "👥 Participantes":
                    embed.set_field_at(i, name="👥 Participantes", value=str(total), inline=True)
                    break
            await msg.edit(embed=embed)
        except Exception:
            pass


class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveaway", description="[ADMIN] Iniciar un nuevo giveaway")
    @app_commands.describe(
        descripcion="Descripción del giveaway",
        premio="Premio secreto (solo admins lo ven hasta finalizar)"
    )
    @app_commands.choices(
        premio=[app_commands.Choice(name=p, value=p) for p in GIVEAWAY_PRIZES]
    )
    @is_admin()
    async def giveaway(
        self,
        interaction: discord.Interaction,
        descripcion: str,
        premio: app_commands.Choice[str]
    ):
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        embed = discord.Embed(
            title="🎉 GIVEAWAY",
            description=f"**{descripcion}**",
            color=0xFFD700
        )
        embed.add_field(name="🏆 Premio", value="*Se revelará al finalizar*", inline=False)
        embed.add_field(name="👥 Participantes", value="0", inline=True)
        embed.add_field(name="🕐 Inicio", value=now, inline=True)
        embed.add_field(name="👑 Organizado por", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Pulsa el botón para participar · ArkStar Legacy")
        embed.set_thumbnail(url="https://i.imgur.com/7V0GSEW.png")

        await interaction.response.defer()
        msg = await interaction.channel.send(embed=embed)

        view = GiveawayEnterButton(giveaway_id=msg.id)
        await msg.edit(view=view)

        db.create_giveaway(
            message_id=msg.id,
            channel_id=interaction.channel.id,
            guild_id=interaction.guild.id,
            prize=premio.value,
            description=descripcion,
            host_id=interaction.user.id,
            start_time=now
        )

        await interaction.followup.send(
            f"✅ Giveaway creado en {interaction.channel.mention}\n"
            f"🔒 Premio secreto: **{premio.value}**\n"
            f"Usa `/endgiveaway {msg.id}` para finalizarlo.",
            ephemeral=True
        )

    @app_commands.command(name="endgiveaway", description="[ADMIN] Finalizar un giveaway y elegir ganador")
    @app_commands.describe(message_id="ID del mensaje del giveaway")
    @is_admin()
    async def endgiveaway(self, interaction: discord.Interaction, message_id: str):
        gw_id = int(message_id)
        gw = db.get_giveaway(gw_id)

        if not gw:
            await interaction.response.send_message("❌ No se encontró un giveaway activo con ese ID.", ephemeral=True)
            return

        entries = db.get_giveaway_entries(gw_id)
        if not entries:
            await interaction.response.send_message("❌ No hay participantes en este giveaway.", ephemeral=True)
            return

        winner_id = random.choice(entries)
        winner = await interaction.guild.fetch_member(winner_id)
        host = await interaction.guild.fetch_member(gw["host_id"])
        end_time = datetime.now().strftime("%d/%m/%Y %H:%M")

        try:
            channel = interaction.guild.get_channel(gw["channel_id"])
            msg = await channel.fetch_message(gw_id)

            embed = discord.Embed(
                title="🎉 GIVEAWAY FINALIZADO",
                description=f"**{gw['description']}**",
                color=0x555555
            )
            embed.add_field(name="🏆 Premio", value=f"**{gw['prize']}**", inline=False)
            embed.add_field(name="🥇 Ganador", value=winner.mention, inline=True)
            embed.add_field(name="👥 Total participantes", value=str(len(entries)), inline=True)
            embed.add_field(name="🕐 Inicio", value=gw["start_time"], inline=True)
            embed.add_field(name="🕔 Fin", value=end_time, inline=True)
            embed.add_field(name="👑 Organizado por", value=host.mention, inline=True)
            embed.add_field(name="⚙️ Finalizado por", value=interaction.user.mention, inline=True)
            embed.set_footer(text="ArkStar Legacy · Giveaway cerrado")
            embed.set_thumbnail(url="https://i.imgur.com/7V0GSEW.png")

            disabled_view = discord.ui.View()
            disabled_btn = discord.ui.Button(
                label="🎉 Enter",
                style=discord.ButtonStyle.secondary,
                disabled=True,
                custom_id="giveaway_enter_disabled"
            )
            disabled_view.add_item(disabled_btn)

            await msg.edit(embed=embed, view=disabled_view)
        except Exception as e:
            print(f"Error editando mensaje: {e}")

        await interaction.channel.send(
            f"🎊 ¡Felicidades {winner.mention}! Has ganado **{gw['prize']}**.\n"
            f"Contacta con un admin para reclamar tu premio."
        )

        await interaction.response.send_message(
            f"✅ Giveaway finalizado. Ganador: **{winner.display_name}** · Premio: **{gw['prize']}**",
            ephemeral=True
        )

        db.close_giveaway(gw_id)
        db.log_event("giveaway_ended", {
            "giveaway_id": gw_id,
            "winner_id": winner_id,
            "prize": gw["prize"],
            "total_entries": len(entries),
            "ended_by": interaction.user.id,
            "end_time": end_time
        })

    @app_commands.command(name="listgiveaways", description="[ADMIN] Ver giveaways activos")
    @is_admin()
    async def listgiveaways(self, interaction: discord.Interaction):
        giveaways = db.get_active_giveaways(interaction.guild.id)
        if not giveaways:
            await interaction.response.send_message("📭 No hay giveaways activos.", ephemeral=True)
            return

        lines = []
        for gw in giveaways:
            count = db.get_giveaway_entry_count(gw["message_id"])
            lines.append(
                f"**ID:** `{gw['message_id']}` | Premio: `{gw['prize']}` | "
                f"Participantes: `{count}` | Host: <@{gw['host_id']}>"
            )

        embed = discord.Embed(title="📋 Giveaways Activos", description="\n".join(lines), color=0xFFD700)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(GiveawayCog(bot))
