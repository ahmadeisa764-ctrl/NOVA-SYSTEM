import discord
from discord.ext import commands
import datetime

# إعداد الصلاحيات الكاملة للبوت
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# تخزين الإعدادات (رومات الفخ، الترحيب، واللوجات)
server_settings = {}

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user.name}")
    print("البوت الشامل يعمل الآن بكلا الأقسام والأنظمة بكفاءة عالية!")
    await bot.change_presence(activity=discord.Game(name="Nova City | Server Management"))

# ==================== أولاً: أوامر الإدارة الأساسية (Ban, Kick, Timeout) ====================

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 تم حظر العضو {member.mention} بنجاح. السبب: {reason}")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_user(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"👢 تم طرد العضو {member.mention} بنجاح. السبب: {reason}")

@bot.command(name="timeout")
@commands.has_permissions(moderate_members=True)
async def timeout_user(ctx, member: discord.Member, minutes: int, *, reason=None):
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f"⏱️ تم إعطاء تايم أوت لـ {member.mention} لمدة {minutes} دقيقة.")

@bot.command(name="join")
async def join_voice(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"🔊 تم الانضمام بنجاح إلى الروم الصوتي: {channel.name}")
    else:
        await ctx.send("❌ يجب أن تكون متواجداً في روم صوتي ليتمكن البوت من الدخول إليه!")

# ==================== ثانياً: نظام الحماية وقناة الفخ (Trap Channel) ====================

@bot.command(name="settrap")
@commands.has_permissions(administrator=True)
async def set_trap(ctx, channel: discord.TextChannel):
    if ctx.guild.id not in server_settings:
        server_settings[ctx.guild.id] = {}
    server_settings[ctx.guild.id]['trap_channel'] = channel.id
    await ctx.send(f"⚠️ تم تعيين {channel.mention} كـ **قناة فخ**! أي رسالة ستُرسل فيها ستؤدي لحظر صاحبها فوراً.")

@bot.command(name="removetrap")
@commands.has_permissions(administrator=True)
async def remove_trap(ctx):
    if ctx.guild.id in server_settings and 'trap_channel' in server_settings[ctx.guild.id]:
        del server_settings[ctx.guild.id]['trap_channel']
        await ctx.send("✅ تم إلغاء تفعيل قناة الفخ بنجاح.")
    else:
        await ctx.send("❌ لا توجد قناة فخ معينة أصلاً في هذا السيرفر.")

# ==================== ثالثاً: نظام الترحيب بالأفاتار (Welcome System) ====================

@bot.command(name="setwelcome")
@commands.has_permissions(administrator=True)
async def set_welcome(ctx, channel: discord.TextChannel):
    if ctx.guild.id not in server_settings:
        server_settings[ctx.guild.id] = {}
    server_settings[ctx.guild.id]['welcome_channel'] = channel.id
    await ctx.send(f"✅ تم تحديد {channel.mention} كقناة رسمية للترحيب بالأعضاء الجدد.")

@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    if guild_id in server_settings and 'welcome_channel' in server_settings[guild_id]:
        channel = member.guild.get_channel(server_settings[guild_id]['welcome_channel'])
        if channel:
            embed = discord.Embed(
                title="👋 أهلاً بك في السيرفر!",
                description=f"مرحباً بك يا {member.mention} في سيرفرنا!\nنتمنى لك قضاء وقت ممتع معنا.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            else:
                embed.set_thumbnail(url=member.default_avatar.url)
            embed.set_footer(text=member.guild.name, icon_url=member.guild.icon.url if member.guild.icon else None)
            await channel.send(embed=embed)

# ==================== رابعاً: نظام اللوجات الشامل (Discord & FiveM Logs) ====================

@bot.command(name="setlogs")
@commands.has_permissions(administrator=True)
async def set_logs(ctx, channel: discord.TextChannel):
    if ctx.guild.id not in server_settings:
        server_settings[ctx.guild.id] = {}
    server_settings[ctx.guild.id]['logs_channel'] = channel.id
    await ctx.send(f"✅ تم تعيين {channel.mention} لاستقبال كافة السجلات (Logs).")

@bot.event
async def on_member_remove(member):
    guild_id = member.guild.id
    if guild_id in server_settings and 'logs_channel' in server_settings[guild_id]:
        channel = member.guild.get_channel(server_settings[guild_id]['logs_channel'])
        if channel:
            embed = discord.Embed(title="📤 مغادرة عضو / Kick", description=f"العضو **{member}** غادر السيرفر أو تم طرده.", color=discord.Color.orange(), timestamp=datetime.datetime.utcnow())
            await channel.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    guild_id = guild.id
    if guild_id in server_settings and 'logs_channel' in server_settings[guild_id]:
        channel = guild.get_channel(server_settings[guild_id]['logs_channel'])
        if channel:
            embed = discord.Embed(title="🔨 حظر عضو (Ban)", description=f"تم حظر العضو: **{user}**", color=discord.Color.dark_red(), timestamp=datetime.datetime.utcnow())
            await channel.send(embed=embed)

# ==================== خامساً: نظام الاستنفار والأمان (Anti-Nuke Audit) ====================

@bot.event
async def on_guild_channel_delete(channel):
    print(f"🚨 تنبيه استنفار: تم حذف روم باسم ({channel.name})!")
    # تستطيع هنا ربط كود لإعادة إنشاء القناة أو تنبيه الإدارة عبر روم اللوجات تلقائياً

# ==================== سادساً: الحدث الرئيسي لمعالجة الرسائل وفحص الفخ ====================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = message.guild.id
    # فحص قناة الفخ للحظر الفوري
    if guild_id in server_settings and 'trap_channel' in server_settings[guild_id]:
        if message.channel.id == server_settings[guild_id]['trap_channel']:
            try:
                await message.delete()
                await message.author.ban(reason="تجاوز قناة الفخ المخصصة للحظر الفوري.")
                return
            except Exception as e:
                print(f"خطأ أثناء حظر المخالف من قناة الفخ: {e}")

    await bot.process_commands(message)

# ==================== تشغيل البوت ====================
# ضع توكن البوت الخاص بك هنا بين علامتي التنصيص
# bot.run("MTUzOTk5MzQxNjM1NDYzNTc4Ng.GCnobd.oF-nnldbLyZXARIl5uDmz31y-y__SM4Qlugy-I")