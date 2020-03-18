# -*- coding: utf-8 -*-
#

import sys
import arrow
import datetime
import traceback

import config
from .utils import meta
from .utils.rr import ReactionRole

import discord
from discord.utils import get
from discord.ext import commands
from discord.ext.commands import errors


class Events(commands.Cog):
    """The description for Events goes here."""

    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        # Çağrılan komutda eksik yada hatalı argüman var ise yardım mesajı gönderilir.
        if isinstance(err, errors.MissingRequiredArgument) or isinstance(
            err, errors.BadArgument
        ):
            helper = (
                str(ctx.invoked_subcommand)
                if ctx.invoked_subcommand
                else str(ctx.command)
            )
            await ctx.send_help(helper)

        elif isinstance(err, errors.CommandOnCooldown):
            await ctx.send(
                f"Bu komut bekleme modunda... {err.retry_after:.1f}s sonra tekrar dene!"
            )
        elif isinstance(err, commands.CommandInvokeError):
            original = err.original

            if not isinstance(original, discord.HTTPException):
                print(f"In {ctx.command.qualified_name}:", file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                print(f"{original.__class__.__name__}: {original}", file=sys.stderr)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await meta.update_activity_name(self.bot)
        
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await meta.update_activity_name(self.bot)

    @commands.Cog.listener()
    async def on_message(self, message):
        author = message.author

        if author.bot:
            return
        
        if message.guild is None:
            dmlog = self.bot.get_channel(687804890860486762)
            embed = discord.Embed(color=self.bot.embed_color)
            embed.description = message.content
            embed.set_author(name=author, icon_url=author.avatar_url)
            embed.set_footer(text=f"ID: {message.author.id}")

            if message.attachments:
                attachment_url = message.attachments[0].url
                embed.set_image(url=attachment_url)

            await dmlog.send(embed=embed)

        if self.bot.user.mentioned_in(message) and message.mention_everyone is False:
            mentionlog = self.bot.get_channel(687805076857028671)
            embed = discord.Embed(color=self.bot.embed_color)
            embed.description = message.content
            embed.set_author(name=author, icon_url=author.avatar_url)
            embed.set_footer(text=f"ID: {message.author.id}")

            embed.add_field(
                name="Bahsetme Bilgisi",
                value=f"Sunucu: {author.guild}\n"
                f"ID: `{author.guild.id}`\n"
                f"Kanal: #{message.channel.name}\n"
                f"ID: `{message.channel.id}`",
            )

            if message.attachments:
                attachment_url = message.attachments[0].url
                embed.set_image(url=attachment_url)

            return await mentionlog.send(embed=embed)

    async def add_member(self, payload, standby_limit):
        """
        Kullanıcı #beni-oku kanalındaki mesaja tepki bırakarak 
        YMY Üyesi rolü alabilmesi için en az 3 dakika sunucuda kayıtlı  
        olması gerekli. Bu zaman farkını kontrol eden ve rolü veren fonksiyon.
        """

        guild = self.bot.get_guild(id=payload.guild_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = guild.get_member(payload.user_id)
        
        role = get(guild.roles, name="YMY Üyesi")
        
        ist_now = arrow.now("Europe/Istanbul").datetime
        # datetime.timedelta(hours=3)
        joined_at = (member.joined_at + datetime.timedelta(hours=3)).astimezone()
        
        # Sunucuya giriş zaman 3 dakika ekleyip limit değişkenine atıyoruz.
        # Eğer limit zamanı tepki eklediği zamandan küçük ise kullanıcı rolü alabilir.
        limit = joined_at + datetime.timedelta(minutes=standby_limit)
        
        if limit > ist_now:
            await message.remove_reaction(emoji=payload.emoji, member=member)
            await member.send("\N{SPEECH BALLOON} "
                              "Hadi ama dostum cidden bu kadar kısa sürede okudun mu?")
        else:
            await member.add_roles(role)
            
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild_id = payload.guild_id
        channel_id = payload.channel_id
        
        reaction_role = ReactionRole(self.bot, payload)
        
        if guild_id == config.ymy_guild_id:
            if channel_id == config.reaction_role_channel_id:
                await reaction_role.add_or_remove()
            
            if channel_id == config.beni_oku_channel_id:
                await self.add_member(payload, standby_limit=3)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        pass


def setup(bot):
    bot.add_cog(Events(bot))
