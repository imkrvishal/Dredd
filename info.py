"""
Dredd, discord bot
Copyright (C) 2020 Moksej
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
import time
import asyncio
import os
import codecs
import pathlib
import aiohttp
import inspect

from io import BytesIO
from discord.ext import commands, tasks
from discord.utils import escape_markdown
from datetime import datetime

from utils import default, checks
from utils.checks import has_voted
from utils.paginator import Pages, TextPages
from utils.Nullify import clean
from utils.publicflags import UserFlags

from collections import Counter
from db import emotes



class info(commands.Cog, name="Info"):

    def __init__(self, bot):
        self.bot = bot
        self.help_icon = "<:tag:686251889586864145>"
        self.big_icon = "https://cdn.discordapp.com/emojis/686251889586864145.png?v=1"
        self.bot.embed_color = 0x0058D6
        self.bot.help_command.cog = self
    async def bot_check(self, ctx):

        if await ctx.bot.is_owner(ctx.author):
            return True

        cmd = self.bot.get_command(ctx.command.name)
        data = await self.bot.db.fetchval("select * from cmds where command = $1", str(cmd))

        
        if data is not None:
            await ctx.send(f"{emotes.blacklisted} | `{ctx.command.name}` is temporarily disabled for maintenance")
            return False

        if data is None:
            return True

    @commands.command(brief="Pongerino")
    @commands.guild_only()
    async def ping(self, ctx):
        """ See bot's latency to discord """
        discord_start = time.monotonic()
        async with self.bot.session.get("https://discord.com/") as resp:
            if resp.status == 200:
                discord_end = time.monotonic()
                discord_ms = f"{round((discord_end - discord_start) * 1000)}ms"
            else:
                discord_ms = "fucking dead"
        await ctx.send(f"\U0001f3d3 Pong   |   {discord_ms}")

    @commands.command(brief="Information about the bot", aliases=["botinfo"])
    @commands.guild_only()
    async def about(self, ctx):
        """ Displays basic information about the bot """

        version = self.bot.version

        channel_types = Counter(type(c) for c in self.bot.get_all_channels())
        voice = channel_types[discord.channel.VoiceChannel]
        text = channel_types[discord.channel.TextChannel]
        
        te = len([c for c in set(self.bot.walk_commands()) if c.cog_name == "Owner"])
        se = len([c for c in set(self.bot.walk_commands()) if c.cog_name == "Staff"])
        xd = len([c for c in set(self.bot.walk_commands())])
        ts = se + te
        totcmd = xd - ts

        mems = len(self.bot.users)

        file = discord.File("img/dreddthumb.png", filename="dreddthumb.png")
        Moksej = self.bot.get_user(345457928972533773)

        embed = discord.Embed(color=self.bot.embed_color)
        embed.add_field(name="__**General Information:**__", value=f"**Developer:** {Moksej}\n**Library:**\n{emotes.other_python} [Discord.py](https://github.com/Rapptz/discord.py)\n**Version:** {discord.__version__}\n**Last boot:** {default.timeago(datetime.utcnow() - self.bot.uptime)}\n**Bot version:** {version}", inline=True)
        embed.add_field(name="__**Other Information:**__", value=f"**Created:** {default.date(self.bot.user.created_at)}\n({default.timeago(datetime.utcnow() - self.bot.user.created_at)})\n**Total:**\nCommands: **{totcmd:,}**\nMembers: **{mems:,}**\nServers: **{len(self.bot.guilds):,}**\nChannels: {emotes.other_unlocked} **{text:,}** | {emotes.other_vcunlock} **{voice:,}**\n", inline=True)

        embed.set_image(
            url='attachment://dreddthumb.png')     

        await ctx.send(file=file, embed=embed)
    
    @commands.command(aliases=['lc'], brief="Lines count of the code")
    async def linecount(self, ctx):
        """ Lines count of the code used creating Dredd """
        pylines = 0
        pyfiles = 0
        for path, subdirs, files in os.walk('.'):
            for name in files:
                    if name.endswith('.py'):
                        pyfiles += 1
                        with codecs.open('./' + str(pathlib.PurePath(path, name)), 'r', 'utf-8') as f:
                            for i, l in enumerate(f):
                                if l.strip().startswith('#') or len(l.strip()) == 0:  # skip commented lines.
                                    pass
                                else:
                                    pylines += 1


        e = discord.Embed(color=self.bot.embed_color,
                          description=f"{emotes.other_python} I am made of **{pyfiles:,}** files and **{pylines:,}** lines. You can also find my source at: [github](https://github.com/TheMoksej/Dredd)") 
        await ctx.send(embed=e)

    @commands.command(brief="Server moderators", aliases=['guildstaff'])
    @commands.guild_only()
    async def serverstaff(self, ctx):
        """ Check which server mods are online in the server """
        message = ""
        online, idle, dnd, offline = [], [], [], []

        for user in ctx.guild.members:
            if ctx.channel.permissions_for(user).kick_members or \
               ctx.channel.permissions_for(user).ban_members:
                if not user.bot and user.status is discord.Status.online:
                    online.append(f"**{user}**")
                if not user.bot and user.status is discord.Status.idle:
                    idle.append(f"**{user}**")
                if not user.bot and user.status is discord.Status.dnd:
                    dnd.append(f"**{user}**")
                if not user.bot and user.status is discord.Status.offline:
                    offline.append(f"**{user}**")

        if online:
            message += f"{emotes.online_status} {', '.join(online)}\n"
        if idle:
            message += f"{emotes.idle_status} {', '.join(idle)}\n"
        if dnd:
            message += f"{emotes.dnd_status} {', '.join(dnd)}\n"
        if offline:
            message += f"{emotes.offline_status} {', '.join(offline)}\n"

        e = discord.Embed(color=self.bot.embed_color, title=f"{ctx.guild.name} mods", description="This lists everyone who can ban and/or kick.")
        e.add_field(name="Server Staff List:", value=message)

        await ctx.send(embed=e)

    @commands.command(brief="All the server roles")
    @commands.guild_only()
    async def roles(self, ctx):
        """ List of roles in the server """
        allroles = []

        for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
            if role.is_default():
                continue
            allroles.append(f"`[{str(num).zfill(2)}]` {role.mention} | {role.id} | **[ Users : {len(role.members)} ]**\n")

        #data = BytesIO(allroles.encode('utf-8'))
        paginator = Pages(ctx,
                          title=f"{ctx.guild.name} roles list",
                          entries=allroles,
                          thumbnail=None,
                          per_page = 15,
                          embed_color=ctx.bot.embed_color,
                          show_entry_count=True,
                          author=ctx.author)
        await paginator.paginate()


    @commands.command(brief="See server information", aliases=['server', 'si'])
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """ Overview about the information of a server """

            
        if ctx.guild.mfa_level == 0:
            mfa = "Disabled"
        else:
            mfa = "Enabled"

        tot_mem = 0
        for member in ctx.guild.members:
            tot_mem += 1

        unique_members = set(ctx.guild.members)
        unique_online = sum(1 for m in unique_members if m.status is discord.Status.online and not type(m.activity) == discord.Streaming)
        unique_offline = sum(1 for m in unique_members if m.status is discord.Status.offline and not type(m.activity) == discord.Streaming)
        unique_idle = sum(1 for m in unique_members if m.status is discord.Status.idle and not type(m.activity) == discord.Streaming)
        unique_dnd = sum(1 for m in unique_members if m.status is discord.Status.dnd and not type(m.activity) == discord.Streaming )
        unique_streaming = sum(1 for m in unique_members if type(m.activity) == discord.Streaming)
        humann = sum(1 for member in ctx.guild.members if not member.bot)
        botts = sum(1 for member in ctx.guild.members if member.bot)

        nitromsg = f"This server was boosted **{ctx.guild.premium_subscription_count}** times"
        nitromsg += "\n{0}".format(default.next_level(ctx))


        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(icon_url=ctx.guild.icon_url,
                         name=f"Server Information")
        embed.add_field(name="__**General Information**__", value=f"**Guild name:** {ctx.guild.name}\n**Guild ID:** {ctx.guild.id}\n**Guild Owner:** {ctx.guild.owner}\n**Guild Owner ID:** {ctx.guild.owner.id}\n**Created at:** {default.date(ctx.guild.created_at)}\n**Region:** {str(ctx.guild.region).title()}\n**MFA:** {mfa}\n**Verification level:** {str(ctx.guild.verification_level).capitalize()}", inline=True)
        embed.add_field(name="__**Other**__", value=f"**Members:**\n{emotes.online_status} **{unique_online:,}**\n{emotes.idle_status} **{unique_idle:,}**\n{emotes.dnd_status} **{unique_dnd:,}**\n{emotes.streaming_status} **{unique_streaming:,}**\n{emotes.offline_status} **{unique_offline:,}**\n**Total:** {tot_mem:,} ({humann:,} Humans/{botts:,} Bots)\n**Channels:** {emotes.other_unlocked} {len(ctx.guild.text_channels)}/{emotes.other_vcunlock} {len(ctx.guild.voice_channels)}\n**Roles:** {len(ctx.guild.roles)}", inline=True)
        embed.add_field(name='__**Server boost status**__',
                        value=nitromsg, inline=False)
        info = []
        features = set(ctx.guild.features)
        all_features = {
            'PARTNERED': 'Partnered',
            'VERIFIED': 'Verified',
            'DISCOVERABLE': 'Server Discovery',
            'PUBLIC': 'Public server',
            'INVITE_SPLASH': 'Invite Splash',
            'VIP_REGIONS': 'VIP Voice Servers',
            'VANITY_URL': 'Vanity Invite',
            'MORE_EMOJI': 'More Emoji',
            'COMMERCE': 'Commerce',
            'LURKABLE': 'Lurkable',
            'NEWS': 'News Channels',
            'ANIMATED_ICON': 'Animated Icon',
            'BANNER': 'Banner'
        }

        for feature, label in all_features.items():
            if feature in features:
                info.append(label)

        if info:
            embed.add_field(name="__**Features**__", value=', '.join(info))
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon_url_as(format="png"))
        if ctx.guild.banner:
            embed.set_image(url=ctx.guild.banner_url_as(format="png"))

        embed.set_footer(
            text=f'© {self.bot.user}')

        await ctx.send(embed=embed)


    @commands.command(brief="Get user information", aliases=['user'])
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def userinfo(self, ctx, *, user: discord.User = None):
        """ Overview about the information of an user """

        user = user or ctx.author
        
        badges = {
            'hs_brilliance': f'{emotes.discord_brilliance}',
            'discord_employee': f'{emotes.discord_staff}',
            'discord_partner': f'{emotes.discord_partner}',
            'hs_events': f'{emotes.discord_events}',
            'bug_hunter_lvl1': f'{emotes.discord_bug1}',
            'hs_bravery': f'{emotes.discord_bravery}',
            'hs_balance': f'{emotes.discord_balance}',
            'early_supporter': f'{emotes.discord_early}',
            'bug_hunter_lvl2': f'{emotes.discord_bug2}',
            'verified_dev': f'{emotes.discord_dev}'
        }
        
        badge_list = []
        flag_vals = UserFlags((await self.bot.http.get_user(user.id))['public_flags'])
        for i in badges.keys():
            if i in [*flag_vals]:
                badge_list.append(badges[i])
        
        ranks = []

        guild = self.bot.get_guild(671078170874740756)

        if user == self.bot.get_user(345457928972533773):
            owner = f"{emotes.bot_owner}"
            ranks.append(owner)
        
        botadmin_role = guild.get_role(674929900674875413)
        if user in guild.members:
            if user in botadmin_role.members:
                botadmin = f"{emotes.bot_admin}"
                ranks.append(botadmin)

        
        botpartner_role = guild.get_role(683288670467653739)
        if user in guild.members:
            if user in botpartner_role.members:
                botpartner = f"{emotes.bot_partner}"
                ranks.append(botpartner)
    

        bughunter_role = guild.get_role(679643117510459432)
        if user in guild.members:
            if user in bughunter_role.members:
                bughunter = f"{emotes.bot_hunter}"
                ranks.append(bughunter)

        supporter_role = guild.get_role(679642623107137549)
        if user in guild.members:
            if user in supporter_role.members:
                supporter = f"{emotes.bot_early_supporter}"
                ranks.append(supporter)

        booster_role = guild.get_role(686259869874913287)
        if user in guild.members:
            if user in booster_role.members:
                supporter = f"{emotes.bot_booster}"
                ranks.append(supporter)

        if user.bot:
            bot = "Yes"
        elif not user.bot:
            bot = "No"
        
        if badge_list:
            discord_badges = '\n**Discord badges:** ' + ' '.join(badge_list)
        elif not badge_list:
            discord_badges = ''

        usercheck = ctx.guild.get_member(user.id)
        if usercheck:
                
            if usercheck.nick is None:
                nick = "N/A"
            else:
                nick = usercheck.nick

            status = {
            "online": f"{f'{emotes.online_mobile}' if usercheck.is_on_mobile() else f'{emotes.online_status}'}",
            "idle": f"{f'{emotes.idle_mobile}' if usercheck.is_on_mobile() else f'{emotes.idle_status}'}",
            "dnd": f"{f'{emotes.dnd_mobile}' if usercheck.is_on_mobile() else f'{emotes.dnd_status}'}",
            "offline": f"{emotes.offline_status}"
            }

            
            if usercheck.activities:
                ustatus = ""
                for activity in usercheck.activities:
                    if activity.type == discord.ActivityType.streaming:
                        ustatus += f"{emotes.streaming_status}"
            else:
                ustatus = f'{status[str(usercheck.status)]}'

            if not ustatus:
                ustatus = f'{status[str(usercheck.status)]}'
            
            nicknames = []
            for nicks, in await self.bot.db.fetch(f"SELECT nickname FROM nicknames WHERE user_id = $1 AND guild_id = $2 ORDER BY time DESC", user.id, ctx.guild.id):
                nicknames.append(nicks)
                
            nicknamess = ""
            for nickss in nicknames[:5]:
                nicknamess += f"{nickss}, "
            
            if nicknamess == "":
                lnicks = "N/A"
            else:
                lnicks = nicknamess[:-2]
                
            uroles = ''
            for role in usercheck.roles:
                if role.is_default():
                    continue
                uroles += f"{role.mention}, "

            if len(uroles) > 500:
                uroles = "Too many roles ...."

            profile = discord.Profile
            
            emb = discord.Embed(color=self.bot.embed_color)
            if ranks:
                emb.title = ' '.join(ranks)
            emb.set_author(icon_url=user.avatar_url, name=f"{user}'s information")
            emb.add_field(name="__**General Info:**__", value=f"**Full name:** {user}\n**User ID:** {user.id}\n**Account created:** {user.created_at.__format__('%A %d %B %Y, %H:%M')}\n**Bot:** {bot}\n**Avatar URL:** [Click here]({user.avatar_url}){discord_badges}", inline=False)
            emb.add_field(name="__**Activity Status:**__", value=f"**Status:** {ustatus}\n**Activity status:** {default.member_activity(usercheck)}", inline=False)
            emb.add_field(name="__**Server Info:**__", value=f"**Nickname:** {escape_markdown(nick, as_needed=True)}\n**Latest nicknames:** {escape_markdown(lnicks, as_needed=True)}\n**Joined at:** {default.date(usercheck.joined_at)}\n**Roles: ({len(usercheck.roles) - 1})** {uroles[:-2]}", inline=True)    
            if user.is_avatar_animated() == False:
                emb.set_thumbnail(url=user.avatar_url_as(format='png'))
            elif user.is_avatar_animated() == True:
                emb.set_thumbnail(url=user.avatar_url_as(format='gif'))
            else:
                emb.set_thumbnail(url=user.avatar_url)
                
            await ctx.send(embed=emb)

        elif not usercheck:
            emb = discord.Embed(color=self.bot.embed_color)
            if ranks:
                emb.title = ' '.join(ranks)
            emb.set_author(icon_url=user.avatar_url, name=f"{user}'s information")
            emb.add_field(name="__**General Info:**__", value=f"**Full name:** {user}\n**User ID:** {user.id}\n**Account created:** {user.created_at.__format__('%A %d %B %Y, %H:%M')}\n**Bot:** {bot}\n**Avatar URL:** [Click here]({user.avatar_url}){discord_badges}", inline=False)
            if user.is_avatar_animated() == False:
                emb.set_thumbnail(url=user.avatar_url_as(format='png'))
            elif user.is_avatar_animated() == True:
                emb.set_thumbnail(url=user.avatar_url_as(format='gif'))
            else:
                emb.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=emb)

    @commands.command(aliases=['source'], brief="View the bot source code")
    async def sourcecode(self, ctx):
        await ctx.send(f"{emotes.other_python} You can find my source code at: https://github.com/TheMoksej/Dredd")

    @commands.command(aliases=['pfp'], brief="Users avatar")
    @commands.guild_only()
    async def avatar(self, ctx, user: discord.User = None):
        """ Displays what avatar user is using """

        user = user or ctx.author

        Zenpa = self.bot.get_user(373863656607318018)
        if user is self.bot.user:
            embed = discord.Embed(color=self.bot.embed_color,
                                  title=f'{self.bot.user}\'s Profile Picture!')
            embed.set_image(url=self.bot.user.avatar_url_as(static_format='png'))
            embed.set_footer(text=f'Huge thanks to {Zenpa} for this avatar')
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(color=self.bot.embed_color,
                                  title=f'{user}\'s Profile Picture!')
            embed.set_image(url=user.avatar_url_as(static_format='png'))
            # embed.set_footer(text=f'© {self.bot.user}')
            await ctx.send(embed=embed)
        
    @commands.command(brief="Check someone's latest nicknames", aliases=['nicks'])
    @commands.guild_only()
    async def nicknames(self, ctx, member: discord.Member = None):
        """ Tells you last 10 nicknames that member had """

        member = member or ctx.author

        nick = []
        for nicks, in await self.bot.db.fetch(f"SELECT nickname FROM nicknames WHERE user_id = $1 AND guild_id = $2 ORDER BY time DESC", member.id, ctx.guild.id):
            nick.append(nicks)
        
        if len(nick) == 0:
            return await ctx.send(f"{member} has had no nicknames in this server.")

        if len(nick) > 10:
            nicks = '10'
        else:
            nicks = len(nick)
        
        nicknames = ""
        for num, nickss in enumerate(nick[:10], start=0):
            nicknames += f"`[{num + 1}]` **{escape_markdown(nickss, as_needed=True)}**\n"

        e = discord.Embed(color=self.bot.embed_color, description=f"**{member}** last {nicks} nickname(s) in the server:\n{nicknames}")

        await ctx.send(embed=e)

    @commands.command(brief="Support server invite")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def support(self, ctx):
        """ A link to this bot's support server """

        if ctx.guild.id == 671078170874740756:
            return await ctx.send("You are in the support server, dummy.")

        else:
            support = await self.bot.db.fetchval("SELECT * FROM support")
            embed = discord.Embed(color=self.bot.embed_color, description=f"{emotes.social_discord} Join my support server [here]({support})")
            await ctx.send(embed=embed)

    @commands.command(description="Invite of the bot", brief="Invite bot")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def invite(self, ctx):
        """ Invite bot to your server """

        invite = await self.bot.db.fetchval("SELECT * FROM invite")
        embed = discord.Embed(color=self.bot.embed_color, description=f"{emotes.pfp_normal} You can invite me by clicking [here]({invite})")
        await ctx.send(embed=embed)
    
    @commands.command(brief='Vote for the bot')
    async def vote(self, ctx):
        """ Give me a vote, please. Thanks... """

        e = discord.Embed(color=self.bot.embed_color, description=f"{emotes.pfp_normal} You can vote for me [here](https://top.gg/bot/667117267405766696/vote)")
        await ctx.send(embed=e)
    
    @commands.command(brief="Credits to people helped", description="All the people who helped with creating this bot are credited")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.guild_only()
    async def credits(self, ctx):
        """ Credits for all the people that worked with this bot """
        # return await ctx.send("test")
        Zenpa = self.bot.get_user(373863656607318018)
        xhigh = self.bot.get_user(315539924155891722)
        Dutchy = self.bot.get_user(171539705043615744)
        # ! alt 200 for ╚

        semb = discord.Embed(color=self.bot.embed_color,
                             title="I'd like to say huge thanks to these people for their help with Dredd")
        semb.add_field(name="__**Graphic designers:**__\n", value=f"• **{Zenpa}**\n╠ {emotes.social_discord} [Discord Server](https://discord.gg/A6p9tep)\n╚ {emotes.social_instagram} [Instagram](https://www.instagram.com/donatas.an/)", inline=False)
        semb.set_footer(text=f"Also thanks to {xhigh} for the image")
        semb.add_field(name="__**Bug Hunter(s)**__", value='\n'.join(f"• **{x}**" for x in self.bot.get_guild(671078170874740756).get_role(679643117510459432).members), inline=True)
                       
        semb.add_field(name="__**Programming:**__\n",
                       value=f"• **{Dutchy}**\n╚ {emotes.social_discord} [Discord Server](https://discord.gg/ZFuwq2v)", inline=True)

        await ctx.send(embed=semb)
    
    @commands.command(brief="Get server emotes", aliases=['se', 'emotes'])
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def serveremotes(self, ctx):
        """ Get a list of emotes in the server """

        _all = []
        for num, e in enumerate(ctx.guild.emojis, start=0):
            _all.append(f"`[{num + 1}]` {e} **{e.name}** | {e.id}\n")
        
        paginator = Pages(ctx,
                          title=f"{ctx.guild.name} emotes list",
                          entries=_all,
                          thumbnail=None,
                          per_page = 15,
                          embed_color=ctx.bot.embed_color,
                          show_entry_count=True,
                          author=ctx.author)
        await paginator.paginate()
    
    @commands.command(brief='Disabled commands list', aliases=['disabledcmds', 'discmd'])
    @commands.guild_only()
    async def disabledcommands(self, ctx):
        """ List of globally disabled commands and guild disabled commands """
        cmmd = []
        for command, in await self.bot.db.fetch("SELECT command FROM cmds"):
            cmmd.append(command)

        comd = ''
        for commands in cmmd:
            comd += f"{commands}, "
        cmmds = []
        for command, in await self.bot.db.fetch("SELECT command FROM guilddisabled WHERE guild_id = $1", ctx.guild.id):
            cmmds.append(command)

        comds = ''
        for commands in cmmds:
            comds += f"{commands}, "
            
        e = discord.Embed(color=self.bot.embed_color, description=f"List of all disabled commands")
        if comd:
            e.add_field(name='**Globally disabled commands:**', value=f"{comd[:-2]}", inline=False)
        if comds:
            e.add_field(name=f"**Disabled commands in this server:**", value=f'{comds[:-2]}')
        await ctx.send(embed=e)
    
    @commands.command(brief='User permissions in the guild', aliases=['perms'])
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def permissions(self, ctx, member: discord.Member = None):
        """ See what permissions member has in the guild. """

        member = member or ctx.author
        
        sperms = dict(member.guild_permissions)

        perm = []
        for p in sperms.keys():
            if sperms[p] == True and member.guild_permissions.administrator == False:
                perm.append(f"{emotes.white_mark} {p}\n")
            if sperms[p] == False and member.guild_permissions.administrator == False:
                perm.append(f"{emotes.red_mark} {p}\n")

        if member.guild_permissions.administrator == True:
            perm = [f'{emotes.white_mark} Administrator']

        
        paginator = Pages(ctx,
                          title=f"{member.name} guild permissions",
                          entries=perm,
                          thumbnail=None,
                          per_page = 20,
                          embed_color=ctx.bot.embed_color,
                          show_entry_count=False,
                          author=ctx.author)
        await paginator.paginate()
    



def setup(bot):
    bot.add_cog(info(bot))