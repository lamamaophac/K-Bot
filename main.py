# ==========================================
# K-BOT FULL FIXED VERSION
# pip install py-cord ==========================================

import discord
from discord.ext import commands, tasks
import random
import time
import asyncio
import json
import os

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TOKEN")
DATA_FILE = "players.json"

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# =========================
# DATA
# =========================

players = {}
afk_users = {}

BRANCHES = [
    "lucquan",
    "haiquan",
    "khongquan",
    "daccong",
    "phaobinh",
    "congbinh",
    "haucan"
]

UNITS = {
    "tieudoi": 50,
    "trungdoi": 120,
    "daidooi": 220,
    "tieudoan": 330,
    "trungdoan": 500,
    "luudoan": 800,
    "sudoan": 1200,
    "quandoan": 1800
}

UNIT_PRICE = {
    "tieudoi": 100,
    "trungdoi": 250,
    "daidooi": 600,
    "tieudoan": 1500,
    "trungdoan": 3500,
    "luudoan": 8000,
    "sudoan": 15000,
    "quandoan": 30000
}

# =========================
# SHOP STOCK
# =========================

shop_stock = {}

for b in BRANCHES:
    shop_stock[b] = 3600

# =========================
# SAVE / LOAD
# =========================

def load_data():

    global players

    if os.path.exists(DATA_FILE):

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                players = json.load(f)

        except:
            players = {}

    else:
        players = {}

def save_data():

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

# =========================
# PLAYER
# =========================

def get_player(uid):

    uid = str(uid)

    if uid not in players:

        players[uid] = {
            "money": 5000,
            "army_power": 0,
            "territory": 5,
            "daily_time": 0,
            "lottery_tickets": 0,
            "nukes": 0,
            "troops": {}
        }

        for b in BRANCHES:
            players[uid]["troops"][b] = 0

    return players[uid]

# =========================
# READY
# =========================

@bot.event
async def on_ready():

    load_data()

    logistics.start()
    restock_shop.start()

    print("✅ BOT DA ON:", bot.user)
    
# =========================
# KHO ĐỒ / HỒ SƠ QUÂN SỰ
# =========================

@bot.command(name="kho")
async def inventory(ctx, member: discord.Member = None):

    member = member or ctx.author

    p = get_player(member.id)

    # =========================
    # BXH QUÂN SỰ
    # =========================

    ranking = sorted(
        players.items(),
        key=lambda x: x[1]["army_power"],
        reverse=True
    )

    rank_pos = 1

    for i, (uid, data) in enumerate(ranking, start=1):

        if str(uid) == str(member.id):
            rank_pos = i
            break

    # =========================
    # TỔNG QUÂN
    # =========================

    total_troops = sum(p["troops"].values())

    # =========================
    # TEXT
    # =========================

    text = f"""
╔════════════════╗
             📦 KHO ĐỒ
╚════════════════╝

👤 Người chơi: {member.name}

💰 Tiền: {p['money']} Kq pts
⚔️ Sức mạnh quân sự: {p['army_power']}
🏆 BXH quân sự: #{rank_pos}

🏳️ Lãnh thổ: {p['territory']}
☢️ Bom hạt nhân: {p.get('nukes',0)}

🪖 Tổng quân: {total_troops}

━━━━━━━━━━━━━━━━
       📊 BINH CHỦNG
━━━━━━━━━━━━━━━━
"""

    # =========================
    # HIỆN BINH CHỦNG
    # =========================

    branch_names = {
        "lucquan": "🪖 Lục quân",
        "haiquan": "⚓ Hải quân",
        "khongquan": "✈️ Không quân",
        "daccong": "🗡️ Đặc công",
        "phaobinh": "💣 Pháo binh",
        "congbinh": "🛠️ Công binh",
        "haucan": "🚚 Hậu cần"
    }

    for b, v in p["troops"].items():

        text += f"\n{branch_names.get(b,b)}: {v}"

    text += f"""

━━━━━━━━━━━━━━━━
         📈 THỐNG KÊ
━━━━━━━━━━━━━━━━

🎟️ Vé số: {p.get('lottery_tickets',0)}
🗺️ Territory: {p.get('territory',0)}
💵 Thu nhập hậu cần:
+{p['troops'].get('haucan',0)} / 30s
"""

    await ctx.send(text)
    
# =========================
# AFK SYSTEM
# =========================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    uid = str(message.author.id)

    # bỏ afk khi chat
    if uid in afk_users:
        del afk_users[uid]

    # check ping
    for user in message.mentions:

        if str(user.id) in afk_users:

            await message.channel.send(
                f"😴 {user.name} đang AFK\n"
                f"📝 {afk_users[str(user.id)]}"
            )

    await bot.process_commands(message)

# =========================
# CƯỢC XU
# !cuoc <t/d> <số tiền>
# t = trên
# d = dưới
# =========================

@bot.command()
async def cuoc(ctx, side="t", amount: int = 0):

    p = get_player(ctx.author.id)

    # =========================
    # CHECK TIỀN
    # =========================

    if amount <= 0:
        return await ctx.send("❌ Số tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    # =========================
    # FIX SIDE
    # =========================

    side = side.lower()

    if side not in ["t", "d"]:
        side = "t"

    # =========================
    # TRỪ TIỀN CƯỢC
    # =========================

    p["money"] -= amount

    # =========================
    # ANIMATION
    # =========================

    msg = await ctx.send("🪙 Đang tung xu...")

    frames = [
        "🪙",
        "⬆️",
        "🪙",
        "⬇️",
        "🪙"
    ]

    for f in frames:

        await msg.edit(content=f)

        await asyncio.sleep(0.4)

    # =========================
    # RANDOM KẾT QUẢ
    # =========================

    result = random.choice(["t", "d"])

    if result == "t":
        result_text = "🔺 MẶT TRÊN"
    else:
        result_text = "🔻 MẶT DƯỚI"

    # =========================
    # THẮNG / THUA
    # =========================

    if side == result:

        reward = amount * 2

        p["money"] += reward

        save_data()

        return await msg.edit(
            content=
            f"{result_text}\n\n"
            f"🎉 THẮNG CƯỢC\n"
            f"💰 +{reward}"
        )

    else:

        save_data()

        return await msg.edit(
            content=
            f"{result_text}\n\n"
            f"💀 THUA CƯỢC, Cược thêm đi mày, lỡ lượt sau trúng thì sao\n"
            f"💸 -{amount}"
        )
        
        
#===\\\==\\\==\\\==\\\========
# KHU VUC NHIEU LENH CASINO
#لا اله الا الله محمد رسول الله!
#==========================

# =========================
# 🐎 ĐUA NGỰA NHIỀU NGƯỜI
# =========================

horse_race = {
    "started": False,
    "bets": {}
}

# =========================
# BET HORSE
# !duangua <1-3> <tiền>
# =========================

@bot.command()
async def duangua(ctx, horse: int, amount: int):

    global horse_race

    p = get_player(ctx.author.id)

    if horse not in [1,2,3]:
        return await ctx.send("❌ Chọn ngựa 1-3")

    if amount <= 0:
        return await ctx.send("❌ Tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= amount

    horse_race["bets"][str(ctx.author.id)] = {
        "horse": horse,
        "amount": amount
    }

    save_data()

    await ctx.send(
        f"🐎 {ctx.author.name} cược ngựa {horse}\n"
        f"💰 {amount} Kpts"
    )

# =========================
# START HORSE RACE
# admin only
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def startngua(ctx):

    global horse_race

    if len(horse_race["bets"]) <= 0:
        return await ctx.send("❌ Chưa ai cược")

    msg = await ctx.send("🐎 ĐUA NGỰA BẮT ĐẦU")

    pos = [0,0,0]

    while max(pos) < 20:

        for i in range(3):
            pos[i] += random.randint(1,3)

        text = ""

        for i in range(3):
            text += f"\n🐎 {i+1}: {'=' * pos[i]}"

        await msg.edit(content=text)

        await asyncio.sleep(1)

    winner = pos.index(max(pos)) + 1

    result = f"\n🏆 NGỰA {winner} THẮNG\n"

    for uid, bet in horse_race["bets"].items():

        if bet["horse"] == winner:

            reward = bet["amount"] * 2

            players[uid]["money"] += reward

            result += f"\n💰 <@{uid}> +{reward}"

    save_data()

    horse_race["bets"] = {}

    await msg.edit(content=result)

# =========================
# 🃏 BÀI CÀO PVP
# !baicaopvp @user tiền
# =========================

@bot.command()
async def baicaopvp(ctx, member: discord.Member, amount: int):

    p1 = get_player(ctx.author.id)
    p2 = get_player(member.id)

    if amount <= 0:
        return await ctx.send("❌ Tiền không hợp lệ")

    if p1["money"] < amount:
        return await ctx.send("❌ Bạn không đủ tiền")

    if p2["money"] < amount:
        return await ctx.send("❌ Đối thủ không đủ tiền")

    p1["money"] -= amount
    p2["money"] -= amount

    cards1 = [
        random.randint(1,10),
        random.randint(1,10),
        random.randint(1,10)
    ]

    cards2 = [
        random.randint(1,10),
        random.randint(1,10),
        random.randint(1,10)
    ]

    score1 = sum(cards1) % 10
    score2 = sum(cards2) % 10

    msg = await ctx.send("🃏 ĐANG CHIA BÀI...")

    await asyncio.sleep(2)

    if score1 > score2:

        reward = amount * 2

        p1["money"] += reward

        result = f"🏆 {ctx.author.name} THẮNG +{reward}"

    elif score2 > score1:

        reward = amount * 2

        p2["money"] += reward

        result = f"🏆 {member.name} THẮNG +{reward}"

    else:

        p1["money"] += amount
        p2["money"] += amount

        result = "🤝 HÒA"

    save_data()

    await msg.edit(
        content=
        f"""
🧍 {ctx.author.name}
{cards1}
➡️ {score1} nút

🧍 {member.name}
{cards2}
➡️ {score2} nút

━━━━━━━━━━
{result}
"""
    )

# =========================
# 🎣 FISHING
# !fish <tiền>
# =========================

@bot.command()
async def fish(ctx, amount: int):

    p = get_player(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ Tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= amount

    msg = await ctx.send("🎣 ĐANG CÂU CÁ...")

    await asyncio.sleep(2)

    roll = random.randint(1,100)

    # =========================
    # RANDOM
    # =========================

    if roll <= 40:

        reward = int(amount * 1.2)

        fish_name = "🐟 Cá thường"

    elif roll <= 70:

        reward = int(amount * 2)

        fish_name = "🐠 Cá hiếm"

    elif roll <= 90:

        reward = int(amount * 5)

        fish_name = "🦈 Cá mập"

    else:

        reward = 0

        fish_name = "💀 Câu trúng rác"

    p["money"] += reward

    save_data()

    await msg.edit(
        content=
        f"""
🎣 KẾT QUẢ CÂU CÁ

{fish_name}

💰 +{reward}
"""
    )
    
# =========================
# TÀI XỈU
# !taixiu tai/xiu số_tiền
# =========================

@bot.command()
async def taixiu(ctx, choice, amount: int):

    p = get_player(ctx.author.id)

    choice = choice.lower()

    if choice not in ["tai", "xiu"]:
        return await ctx.send("❌ Chọn tai hoặc xiu")

    if amount <= 0:
        return await ctx.send("❌ Tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= amount

    msg = await ctx.send("🎲 ĐANG LẮC...")

    await asyncio.sleep(1)

    d1 = random.randint(1,6)
    d2 = random.randint(1,6)
    d3 = random.randint(1,6)

    total = d1+d2+d3

    result = "tai" if total >= 11 else "xiu"

    if choice == result:

        reward = amount * 2

        p["money"] += reward

        text = f"🎉 THẮNG +{reward}"

    else:

        text = f"💀 THUA -{amount}"

    save_data()

    await msg.edit(
        content=
        f"""
🎲 {d1} | {d2} | {d3}

📊 Tổng: {total}
🏆 Kết quả: {result.upper()}

{text}
"""
    )

# =========================
# 🌍 AUTO EVENTS SYSTEM
# =========================

EVENTS = [
    {
        "name": "🛢️ OIL CRISIS",
        "text": "🛢️ Giá dầu tăng mạnh!\n💰 Tất cả oil rig +2000 Kpts",
        "type": "oil"
    },

    {
        "name": "☪️ RAMADAN",
        "text": "☪️ Ramadan Mubarak!\n💰 Tất cả nhận 5000 Kpts",
        "type": "money"
    },

    {
        "name": "💥 NUCLEAR WAR",
        "text": "💥 Chiến tranh hạt nhân!\n⚔️ Mọi người mất 10% quân lực",
        "type": "army"
    },

    {
        "name": "🎁 JACKPOT RAIN",
        "text": "🎁 Mưa tiền từ casino!\n💰 Tất cả nhận random Kpts",
        "type": "jackpot"
    },

    {
        "name": "🐪 DESERT FESTIVAL",
        "text": "🐪 Lễ hội sa mạc!\n💰 Đua lạc đà x3 tiền thưởng",
        "type": "camel"
    }
]

# =========================
# ⏰ AUTO EVENT LOOP
# =========================

@tasks.loop(minutes=30)
async def auto_events():

    await bot.wait_until_ready()

    # =========================
    # RANDOM EVENT
    # =========================

    event = random.choice(EVENTS)

    # =========================
    # APPLY EVENT
    # =========================

    if event["type"] == "money":

        for p in players.values():

            p["money"] += 5000

    elif event["type"] == "army":

        for p in players.values():

            loss = int(p["army_power"] * 0.1)

            p["army_power"] -= loss

    elif event["type"] == "oil":

        for p in players.values():

            oilrigs = p.get("oilrig",0)

            if oilrigs > 0:

                p["money"] += oilrigs * 2000

    elif event["type"] == "jackpot":

        for p in players.values():

            p["money"] += random.randint(1000,10000)

    elif event["type"] == "camel":

        global camel_bonus

        camel_bonus = 3

    save_data()

    # =========================
    # SEND EVENT
    # =========================

    for guild in bot.guilds:

        for channel in guild.text_channels:

            try:

                await channel.send(
                    f"""
🌍 EVENT TOÀN SERVER

{event['text']}
"""
                )

                break

            except:

                pass

# =========================
# READY
# =========================

@bot.event
async def on_ready():

    load_data()

    if not auto_events.is_running():

        auto_events.start()

    print(f"✅ BOT ONLINE: {bot.user}")
    
# =========================
# ROULETTE
# !roulette red/black số_tiền
# =========================

@bot.command()
async def roulette(ctx, color, amount: int):

    p = get_player(ctx.author.id)

    color = color.lower()

    if color not in ["red","black"]:
        return await ctx.send("❌ Chọn red hoặc black")

    if amount <= 0:
        return await ctx.send("❌ Tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= amount

    msg = await ctx.send("🎡 ĐANG QUAY ROULETTE...")

    await asyncio.sleep(2)

    result = random.choice(["red","black"])

    if result == color:

        reward = amount * 2

        p["money"] += reward

        text = f"🎉 THẮNG +{reward}"

    else:

        text = f"💀 THUA -{amount}"

    save_data()

    await msg.edit(
        content=
        f"""
🎡 Roulette: {result.upper()}

{text}
"""
    )

# =========================
# BLACKJACK
# !bj số_tiền
# =========================

@bot.command()
async def bj(ctx, amount: int):

    p = get_player(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ Tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= amount

    player = random.randint(15,23)
    botv = random.randint(15,23)

    msg = await ctx.send("🃏 ĐANG CHIA BÀI...")

    await asyncio.sleep(2)

    # =========================
    # CHECK
    # =========================

    if player > 21:

        result = f"💀 BÙ 21\n-{amount}"

    elif botv > 21 or player > botv:

        reward = amount * 2

        p["money"] += reward

        result = f"🎉 THẮNG +{reward}"

    elif player == botv:

        p["money"] += amount

        result = "🤝 HÒA"

    else:

        result = f"💀 THUA -{amount}"

    save_data()

    await msg.edit(
        content=
        f"""
🧍 Ông: {player}
🤖 Bot: {botv}

{result}
"""
    )

# =========================
# ĐÁ GÀ
# !daga số_tiền
# =========================

@bot.command()
async def daga(ctx, amount: int):

    p = get_player(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ Tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= amount

    msg = await ctx.send("🐔 ĐÁ GÀ BẮT ĐẦU")

    hp1 = 100
    hp2 = 100

    while hp1 > 0 and hp2 > 0:

        hp1 -= random.randint(5,20)
        hp2 -= random.randint(5,20)

        await msg.edit(
            content=
            f"""
🐔 GÀ 1: {max(hp1,0)} HP
🐔 GÀ 2: {max(hp2,0)} HP
"""
        )

        await asyncio.sleep(1)

    if hp1 > hp2:

        reward = amount * 2

        p["money"] += reward

        result = f"🐔 GÀ 1 THẮNG\n🎉 +{reward}"

    else:

        result = f"🐔 GÀ 2 THẮNG\n💀 -{amount}"

    save_data()

    await msg.edit(content=result)

# =========================
# RUSSIAN ROULETTE
# !rr số_tiền
# =========================

@bot.command()
async def rr(ctx, amount: int):

    p = get_player(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ Tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= amount

    msg = await ctx.send("🔫 ĐANG XOAY...")

    await asyncio.sleep(2)

    bullet = random.randint(1,6)

    if bullet == 1:

        save_data()

        return await msg.edit(
            content=
            f"""
💥 BÙM

💀 ÔNG CHẾT
💸 -{amount}
"""
        )

    reward = amount * 5

    p["money"] += reward

    save_data()

    await msg.edit(
        content=
        f"""
😎 SỐNG SÓT

💰 +{reward}
"""
    )

# =========================
# CRASH
# !crash số_tiền
# =========================

crash_games = {}

@bot.command()
async def crash(ctx, amount: int):

    p = get_player(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ Tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    uid = str(ctx.author.id)

    p["money"] -= amount

    multi = 1.0

    crash_point = round(random.uniform(1.5,5.0),1)

    msg = await ctx.send("🚀 CRASH START")

    while True:

        await asyncio.sleep(1)

        multi += round(random.uniform(0.2,0.8),1)

        if multi >= crash_point:

            del crash_games[uid]

            save_data()

            return await msg.edit(
                content=
                f"""
💥 CRASH tại x{crash_point}

💀 Mất sạch
"""
            )

        crash_games[uid] = {
            "bet": amount,
            "multi": multi
        }

        await msg.edit(
            content=
            f"""
🚀 x{multi}

👉 !cashout
"""
        )

# =========================
# CASHOUT
# =========================

@bot.command()
async def cashout(ctx):

    uid = str(ctx.author.id)

    if uid not in crash_games:
        return await ctx.send("❌ Không có game crash")

    game = crash_games[uid]

    p = get_player(ctx.author.id)

    reward = int(game["bet"] * game["multi"])

    p["money"] += reward

    del crash_games[uid]

    save_data()

    await ctx.send(
        f"""
🏦 CASHOUT

💰 +{reward}
"""
    )



# =========================
# HELP
# =========================

@bot.command(name="help")
async def help_command(ctx):

    await ctx.send("""
╔════════════════╗
         🤖 K-BOT HELP
╚════════════════╝

💰 KINH TẾ
!daily
!kho
!bxhtien
!bxhquan
!vtt <user> <sotien> ( Vien Tro co thue )
!bank
!gui <số tiền>
!rutbank <số tiền>

⚔️ QUÂN ĐỘI
!shop
!buy < Ten binh chung > < Quy mo >
vi du: !buy haucan trungdoan
!war @user

🎰 MAY RỦI
!vongquay
!veso
!quayso do tat ca ve so da mua
!cuoc < tung xu co 2 mat (t va d) t la tren d la duoi> <so tien> 
!duangua <ngua so 1/2/3> <so tien>
!jackpot <so tien>
!mines
    #Nó sẽ hiênh ra các cô từ 1-9 bạn sẽ chọn ô bằng "!dao <ô 1-9>" ( chọn r mà chọn lại t chửi m chết ), nếu thấy lấy tiền đủ r thì "!rut" tham lam quá bị الله اكبر hồi nào k hay
!taixiu tai <sotien>
!taixiu xiu <sotien>
!roulette red <sotien>
!roulette black 1000 <sotien>
!bj 1000 <sotien>
!daga <sotien>
!rr <sotien>
!crash <sotien>
!cashout (rut)
!baicao <sotien>
!fish <tiền>

!baicaopvp @user tiền
!duanguamuti <1-3> <tiền>

!cuop @user ( Nguy co bi cong an bat )
!muaden tank
!choden

🛢️DAU MO - KAABA
!daumo (xay gian khoan dau)
!oil (xem thu nhap dau)
!cuopdau (cuop dau)
!kaaba (hanh huong)
!ramadan
!thanhduong
!caliphate

Sự kiện sever 
!lottery (mua vé số sever)
Một số event mỗi 30P như: Oil crisis, Ramadan, Nuclear war, Jackpot rain, Desert Festival. Đặc biệt là KhungBo.

😴 AFK
!afk <lý do>

🚨 ADMIN HELP ( chinh quyen )
use: !adminhelp

📢 CHAT
!nh <nội dung>
""")

# =========================
# ☢️ KHUNG BO EVENT
# =========================

zone_active = False
zone_multiplier = 1

# =========================
# ⏰ KHUNG BO
# =========================

@tasks.loop(minutes=45)
async def khungbo_event():

    global zone_active
    global zone_multiplier

    await bot.wait_until_ready()

    # =========================
    # START EVENT
    # =========================

    zone_active = True

    # random giá tăng
    zone_multiplier = random.randint(2,5)

    msg = f"""
☢️ KHỦNG HOẢNG KHUNG BO ☢️

💥 Chiến tranh và hỗn loạn xảy ra!

📈 Giá:
🛢️ Dầu mỏ x{zone_multiplier}
🎰 Casino x{zone_multiplier}
📦 Box x{zone_multiplier}

⏰ Thời gian:
15 phút
"""

    # =========================
    # SEND ALL SERVER
    # =========================

    for guild in bot.guilds:

        for channel in guild.text_channels:

            try:

                await channel.send(msg)

                break

            except:
                pass

    # =========================
    # EVENT TIME
    # =========================

    await asyncio.sleep(900)

    # =========================
    # END EVENT
    # =========================

    zone_active = False
    zone_multiplier = 1

    for guild in bot.guilds:

        for channel in guild.text_channels:

            try:

                await channel.send(
                    """
☢️ KHUNG BO ĐÃ KẾT THÚC

📉 Giá cả đã trở lại bình thường 😭
"""
                )

                break

            except:
                pass
                
# =========================
# ADMIN SECURITY SYSTEM
# !dongbang @user
# !mobang @user
# !cam @user
# !gocam @user
# =========================

# =========================
# UPDATE PLAYER DATA
# thêm vào get_player()
# =========================

"""
"banned": False,
"frozen": False,
"""

# ví dụ:

"""
players[uid] = {
    "money": 5000,
    "bank": 0,
    "banned": False,
    "frozen": False
}
"""

# =========================
# CHECK BAN / FREEZE
# =========================

def is_blocked(uid):

    p = get_player(uid)

    if p.get("banned", False):
        return "banned"

    if p.get("frozen", False):
        return "frozen"

    return None

# =========================
# BLOCK COMMANDS
# =========================

@bot.check
async def global_check(ctx):

    # admin vẫn dùng được
    if ctx.author.guild_permissions.administrator:
        return True

    status = is_blocked(ctx.author.id)

    if status == "banned":

        await ctx.send(
            "⛔ Tài khoản của bạn đã bị cấm, Nếu muốn kháng cáo mời bạn ib @notilike"
        )

        return False

    if status == "frozen":

        await ctx.send(
            "❄️ Tài khoản của bạn đã bị đóng băng"
        )

        return False

    return True

# =========================
# ĐÓNG BĂNG
# !dongbang @user
# =========================

@bot.command(name="dongbang")
@commands.has_permissions(administrator=True)
async def freeze_account(ctx, member: discord.Member):

    p = get_player(member.id)

    p["frozen"] = True

    save_data()

    await ctx.send(
        f"❄️ Đã đóng băng tài khoản {member.name}"
    )

# =========================
# MỞ ĐÓNG BĂNG
# !mobang @user
# =========================

@bot.command(name="mobang")
@commands.has_permissions(administrator=True)
async def unfreeze_account(ctx, member: discord.Member):

    p = get_player(member.id)

    p["frozen"] = False

    save_data()

    await ctx.send(
        f"✅ Đã mở đóng băng {member.name}"
    )

# =========================
# CẤM VĨNH VIỄN
# !cam @user
# =========================

@bot.command(name="cam")
@commands.has_permissions(administrator=True)
async def ban_account(ctx, member: discord.Member):

    p = get_player(member.id)

    p["banned"] = True

    save_data()

    await ctx.send(
        f"⛔ Đã cấm vĩnh viễn {member.name}"
    )

# =========================
# GỠ CẤM
# !gocam @user
# =========================

@bot.command(name="gocam")
@commands.has_permissions(administrator=True)
async def unban_account(ctx, member: discord.Member):

    p = get_player(member.id)

    p["banned"] = False

    save_data()

    await ctx.send(
        f"✅ Đã gỡ cấm {member.name}"
    )
    
# =========================
# ADMIN HELP
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def adminhelp(ctx):

    await ctx.send("""
🛡️ ADMIN COMMANDS

━━━━━━━━━━━━━━
⛔ QUẢN LÍ TÀI KHOẢN
━━━━━━━━━━━━━━

!dongbang @user
→ Đóng băng tài khoản
→ User không dùng được lệnh

!mobang @user
→ Mở đóng băng tài khoản

!cam @user
→ Cấm vĩnh viễn tài khoản

!gocam @user
→ Gỡ cấm tài khoản

━━━━━━━━━━━━━━
🎟️ LOTTERY
━━━━━━━━━━━━━━

!quaylottery
→ Quay lottery server

━━━━━━━━━━━━━━
🐎 ĐUA NGỰA
━━━━━━━━━━━━━━

!startngua
→ Bắt đầu đua ngựa
""")

# =========================
# 🛒 CHỢ ĐEN
# !choden
# =========================

BLACK_MARKET = {
    "tank": [5000,12000],
    "fighter": [15000,30000],
    "nuke": [50000,120000],
    "spy": [2000,7000]
}

@bot.command()
async def choden(ctx):

    text = "🛒 CHỢ ĐEN\n\n"

    for item, price in BLACK_MARKET.items():

        rand_price = random.randint(price[0], price[1])

        text += f"""
🔹 {item}
💰 Giá: {rand_price}

"""

    text += "\nMua bằng:\n!muaden <item>"

    await ctx.send(text)

# =========================
# 💰 MUA CHỢ ĐEN
# !muaden tank
# =========================

@bot.command()
async def muaden(ctx, item):

    p = get_player(ctx.author.id)

    item = item.lower()

    if item not in BLACK_MARKET:
        return await ctx.send("❌ Item không tồn tại")

    # =========================
    # RANDOM PRICE
    # =========================

    price = random.randint(
        BLACK_MARKET[item][0],
        BLACK_MARKET[item][1]
    )

    if p["money"] < price:
        return await ctx.send(
            f"❌ Không đủ tiền\n💰 Giá: {price}"
        )

    p["money"] -= price

    # =========================
    # REWARD
    # =========================

    if item == "tank":

        p["army_power"] += 500

    elif item == "fighter":

        p["army_power"] += 1500

    elif item == "nuke":

        p["nukes"] = p.get("nukes",0) + 1

    elif item == "spy":

        p["spies"] = p.get("spies",0) + 1

    save_data()

    await ctx.send(
        f"""
🛒 MUA THÀNH CÔNG

📦 Item: {item}
💸 -{price} Kpts
"""
    )
    
# =========================
# 🕵️ CƯỚP + CÔNG AN
# !cuop @user
# =========================

@bot.command()
async def cuop(ctx, member: discord.Member):

    robber = get_player(ctx.author.id)
    victim = get_player(member.id)

    # =========================
    # CHECK
    # =========================

    if member.id == ctx.author.id:
        return await ctx.send("❌ Không thể tự cướp mình")

    if victim["money"] < 500:
        return await ctx.send("❌ Nó nghèo quá 😭")

    # =========================
    # CHECK JAIL
    # =========================

    if robber.get("jail", 0) > time.time():

        remain = int(
            (robber["jail"] - time.time()) / 60
        )

        return await ctx.send(
            f"🚔 Bạn đang ở tù\n⏳ Còn {remain} phút"
        )

    msg = await ctx.send("🕵️ ĐANG CƯỚP...")

    await asyncio.sleep(2)

    chance = random.randint(1,100)

    # =========================
    # THÀNH CÔNG
    # =========================

    if chance <= 45:

        stolen = random.randint(
            int(victim["money"] * 0.05),
            int(victim["money"] * 0.2)
        )

        victim["money"] -= stolen
        robber["money"] += stolen

        save_data()

        return await msg.edit(
            content=
            f"""
🤑 CƯỚP THÀNH CÔNG

🎯 Nạn nhân: {member.name}

💰 +{stolen} Kpts
"""
        )

    # =========================
    # BỊ CÔNG AN BẮT
    # =========================

    elif chance <= 80:

        fine = random.randint(1000,5000)

        robber["money"] = max(
            0,
            robber["money"] - fine
        )

        # tù 5 phút
        robber["jail"] = time.time() + 300

        save_data()

        return await msg.edit(
            content=
            f"""
🚔 BỊ CÔNG AN BẮT

💸 Phạt: {fine} Kpts
⛓️ Ngồi tù: 5 phút
"""
        )

    # =========================
    # BỊ BẮN
    # =========================

    else:

        loss = random.randint(5000,15000)

        robber["money"] = max(
            0,
            robber["money"] - loss
        )

        robber["army_power"] = max(
            0,
            robber["army_power"] - 100
        )

        save_data()

        return await msg.edit(
            content=
            f"""
💀 BỊ CẢNH SÁT BẮN

💸 Mất: {loss} Kpts
⚔️ -100 sức mạnh quân đội
"""
        )
        
# =========================
# JACKPOT
# !jackpot <số tiền>
# =========================

@bot.command()
async def jackpot(ctx, amount: int):

    p = get_player(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ Đéo có tiền thì cút m")

    if p["money"] < amount:
        return await ctx.send("❌ Đéo có tiền thì cút m")

    p["money"] -= amount

    msg = await ctx.send("🎰 ĐANG QUAY JACKPOT...")

    slots = ["💰","🕋","👑","🔥","⚔️"]

    for _ in range(10):

        s1 = random.choice(slots)
        s2 = random.choice(slots)
        s3 = random.choice(slots)

        await msg.edit(
            content=f"[ {s1} ] [ {s2} ] [ {s3} ]"
        )

        await asyncio.sleep(0.2)

    # =========================
    # RANDOM TRÚNG
    # =========================

    chance = random.randint(1, 100)

    if chance == 1:

        reward = amount * 20

        p["money"] += reward

        save_data()

        return await msg.edit(
            content=
            f"💎 ALLAHU AKBAR!!!! 💎\n\n"
            f"[ 🕋 ] [ 🕋 ] [ 🕋 ]\n\n"
            f"💰 +{reward}"
        )

    elif chance <= 10:

        reward = amount * 5

        p["money"] += reward

        save_data()

        return await msg.edit(
            content=
            f"🔥 AHIHI CHUC MUNG 🔥\n\n"
            f"💰 +{reward}"
        )

    else:

        save_data()

        return await msg.edit(
            content=
            f"💀 Xui, Cược thêm đi lỡ trúng thì sao😁\n\n"
            f"💸 -{amount}"
        )

# =========================
# JACKPOT
# !jackp0t <số tiền>
# =========================

@bot.command()
async def jackp0t(ctx, amount: int):

    p = get_player(ctx.author.id)

    # =========================
    # CHECK
    # =========================

    if amount <= 0:
        return await ctx.send("❌ Đéo có tiền bày đặt vậy ông cố")

    if p["money"] < amount:
        return await ctx.send("❌ Không có tiền hả cút")

    # =========================
    # TRỪ TIỀN
    # =========================

    p["money"] -= amount

    # =========================
    # ANIMATION
    # =========================

    msg = await ctx.send("🎰 ĐANG QUAY JACKPOT...")

    icons = ["💰","💎","🕋","🔥","👑"]

    a=b=c="❔"

    for _ in range(8):

        a = random.choice(icons)
        b = random.choice(icons)
        c = random.choice(icons)

        await msg.edit(
            content=
            f"""
🎰 JACKPOT 🎰

[{a}] [{b}] [{c}]
"""
        )

        await asyncio.sleep(0.3)

    # =========================
    # RANDOM GIẢI
    # =========================

    roll = random.randint(1,100)

    # luôn thắng ít nhất chút tiền 😎
    if roll <= 10:

        reward = int(amount * 1.2)
        text = "🙂 THẮNG NHẸ"

    elif roll <= 10:

        reward = int(amount * 2)
        text = "😎 THẮNG TO"

    elif roll <= 10:

        reward = int(amount * 5)
        text = "🔥 SIÊU THẮNG"

    else:

        reward = int(amount * 20)
        text = "👑 JACKPOT MEGA"

    # =========================
    # CỘNG TIỀN
    # =========================

    p["money"] += reward

    save_data()

    # =========================
    # RESULT
    # =========================

    await msg.edit(
        content=
        f"""
🎰 JACKPOT 🎰

[{a}] [{b}] [{c}]

{text}

💰 +{reward} Kpts
"""
    )
    
# =========================
# BÀI CÀO
# !baicao <số tiền>
# =========================

@bot.command()
async def baicao(ctx, amount: int):

    p = get_player(ctx.author.id)

    # =========================
    # CHECK
    # =========================

    if amount <= 0:
        return await ctx.send("❌ Đéo có tiền bày đặt vậy ông cố")

    if p["money"] < amount:
        return await ctx.send("❌ Không có tiền hả cút")

    p["money"] -= amount

    # =========================
    # RÚT BÀI
    # =========================

    player_cards = [
        random.randint(1, 10),
        random.randint(1, 10),
        random.randint(1, 10)
    ]

    bot_cards = [
        random.randint(1, 10),
        random.randint(1, 10),
        random.randint(1, 10)
    ]

    # =========================
    # TÍNH ĐIỂM
    # =========================

    player_score = sum(player_cards) % 10
    bot_score = sum(bot_cards) % 10

    # =========================
    # ANIMATION
    # =========================

    msg = await ctx.send("🃏 Đang chia bài...")

    await asyncio.sleep(1)

    await msg.edit(
        content=
        "🃏 Đang mở bài.\n"
        "⬜ ⬜ ⬜"
    )

    await asyncio.sleep(1)

    await msg.edit(
        content=
        f"""
🧍 BÀI CỦA MAY
{player_cards[0]} | {player_cards[1]} | {player_cards[2]}

🤖 BÀI CỦA K-Bot cute
⬜ | ⬜ | ⬜
"""
    )

    await asyncio.sleep(1)

    # =========================
    # KẾT QUẢ
    # =========================

    if player_score > bot_score:

        reward = amount * 2

        p["money"] += reward

        result = (
            f"🎉 MAY THẮNG\n"
            f"💰 +{reward}"
        )

    elif player_score < bot_score:

        result = (
            f"💀 MAY THUA\n"
            f"💸 -{amount}"
        )

    else:

        p["money"] += amount

        result = (
            "🤝 HÒA\n"
            "💵 Hoàn tiền"
        )

    save_data()

    await msg.edit(
        content=
        f"""
🧍 BÀI CỦA MAY
{player_cards[0]} | {player_cards[1]} | {player_cards[2]}
➡️ {player_score} nút

🤖 BÀI CỦA K-BOT cute
{bot_cards[0]} | {bot_cards[1]} | {bot_cards[2]}
➡️ {bot_score} nút

━━━━━━━━━━━━
{result}
"""
    )
    
    
# =========================
# LOTTERY SERVER
# !lottery
# !quaylottery
# =========================

lottery_pool = 0
lottery_players = []

# =========================
# MUA VÉ LOTTERY
# =========================

@bot.command()
async def lottery(ctx):

    global lottery_pool
    global lottery_players

    p = get_player(ctx.author.id)

    ticket_price = 1000

    if p["money"] < ticket_price:
        return await ctx.send("❌ Không đủ tiền mua vé")

    p["money"] -= ticket_price

    # 30% bot giữ lại chống lạm phát 😭
    add_pool = int(ticket_price * 0.7)

    lottery_pool += add_pool

    lottery_players.append(ctx.author.id)

    save_data()

    await ctx.send(
        f"🎟️ {ctx.author.name} đã mua vé lottery\n"
        f"💰 Jackpot hiện tại: {lottery_pool}"
    )

# =========================
# QUAY LOTTERY
# admin only
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def quaylottery(ctx):

    global lottery_pool
    global lottery_players

    if len(lottery_players) <= 0:
        return await ctx.send("❌ Chưa có ai mua vé, ngu v")

    winner_id = random.choice(lottery_players)

    winner = get_player(winner_id)

    reward = lottery_pool

    winner["money"] += reward

    member = await bot.fetch_user(winner_id)

    await ctx.send(
        f"""
🎉 LOTTERY WINNER 🎉

👑 Người thắng:
{member.name}

💰 Giải thưởng:
{reward} Kpts
"""
    )

    lottery_pool = 0
    lottery_players = []

    save_data()

# =========================
# THUẾ GIAO DỊCH
# 5%
# =========================

TRADE_TAX = 0.05

# =========================
# VIỆN TRỢ CÓ THUẾ
# sửa lệnh vt
# =========================

@bot.command()
async def vtt(ctx, member: discord.Member, amount: int):

    sender = get_player(ctx.author.id)
    target = get_player(member.id)

    if amount <= 0:
        return await ctx.send("❌ Số tiền không hợp lệ")

    if sender["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    if member.id == ctx.author.id:
        return await ctx.send("❌ Không thể tự gửi")

    # =========================
    # THUẾ
    # =========================

    tax = int(amount * TRADE_TAX)

    final_amount = amount - tax

    sender["money"] -= amount

    target["money"] += final_amount

    save_data()

    await ctx.send(
        f"""
💸 GIAO DỊCH THÀNH CÔNG

👤 Gửi:
{ctx.author.name}

🎯 Nhận:
{member.name}

💰 Gửi:
{amount}

🏦 Thuế:
{tax}

✅ Thực nhận:
{final_amount}
"""
    )
    
# =========================
# ĐUA NGỰA
# !duanguamuti <1-3> <số tiền>
# =========================

@bot.command()
async def duanguamuti(ctx, horse: int, amount: int):

    p = get_player(ctx.author.id)

    if horse not in [1,2,3]:
        return await ctx.send("❌ Chọn ngựa từ 1-3")

    if amount <= 0:
        return await ctx.send("❌ Tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= amount

    pos = [0,0,0]

    msg = await ctx.send("🏁 ĐUA NGỰA BẮT ĐẦU")

    winner = None

    while winner is None:

        for i in range(3):

            pos[i] += random.randint(1,3)

            if pos[i] >= 20:
                winner = i + 1

        track = ""

        for i in range(3):

            track += (
                f"\n🐎 {i+1} "
                + "-" * pos[i]
                + "🏇"
            )

        await msg.edit(
            content=
            f"🏁 ĐUA NGỰA 🏁\n"
            f"{track}"
        )

        await asyncio.sleep(1)

    # =========================
    # KẾT QUẢ
    # =========================

    if horse == winner:

        reward = amount * 2

        p["money"] += reward

        result = (
            f"🏆 NGỰA {winner} THẮNG\n\n"
            f"🎉 ÔNG THẮNG\n"
            f"💰 +{reward}"
        )

    else:

        result = (
            f"🏆 NGỰA {winner} THẮNG\n\n"
            f"💀 ÔNG THUA\n"
            f"💸 -{amount}"
        )

    save_data()

    await msg.edit(content=result)
    
# =========================
# MINES GAME
# !mines <tiền>
# !dao <ô>
# !rut
# =========================

mines_games = {}

# =========================
# START MINES
# =========================

@bot.command()
async def mines(ctx, amount: int):

    p = get_player(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ Đéo có tiền thì cút m😂😂")

    if p["money"] < amount:
        return await ctx.send("❌ 😂😂Đéo có tiền thì cút m")

    uid = str(ctx.author.id)

    # trừ tiền cược
    p["money"] -= amount

    # random bom
    bombs = random.sample(range(1, 10), 3)

    mines_games[uid] = {
        "bet": amount,
        "bombs": bombs,
        "opened": [],
        "multi": 1.0
    }

    save_data()

    board = """
1️⃣ 2️⃣ 3️⃣
4️⃣ 5️⃣ 6️⃣
7️⃣ 8️⃣ 9️⃣
"""

    await ctx.send(
        f"💣 MINES STARTED\n"
        f"💰 Cược: {amount}\n"
        f"💎 Có 3 quả bom\n\n"
        f"{board}\n"
        f"👉 Dùng: !dao <ô>"
    )

# =========================
# DAO O
# =========================

@bot.command()
async def dao(ctx, slot: int):

    uid = str(ctx.author.id)

    if uid not in mines_games:
        return await ctx.send("❌ Chưa chơi mines")

    game = mines_games[uid]

    if slot < 1 or slot > 9:
        return await ctx.send("❌ Chọn ô từ 1-9")

    if slot in game["opened"]:
        return await ctx.send("❌ Mẹ m chưa đọc hướng dẫn à con chó")

    game["opened"].append(slot)

    # =========================
    # TRÚNG BOM
    # =========================

    if slot in game["bombs"]:

        bombs_text = ""

        for i in range(1, 10):

            if i in game["bombs"]:
                bombs_text += "💣 "
            else:
                bombs_text += "💎 "

            if i % 3 == 0:
                bombs_text += "\n"

        del mines_games[uid]

        return await ctx.send(
            f"💥 الله اكبر !!!!\n"
            f"💸 Mất sạch cược😂😂\n\n"
            f"{bombs_text}"
        )

    # =========================
    # TRÚNG KIM CƯƠNG
    # =========================

    game["multi"] += 0.5

    reward = int(game["bet"] * game["multi"])

    board = ""

    for i in range(1, 10):

        if i in game["opened"]:
            board += "💎 "
        else:
            board += "⬜ "

        if i % 3 == 0:
            board += "\n"

    await ctx.send(
        f"💎 AN TOÀN\n"
        f"📈 Nhân: x{game['multi']}\n"
        f"💰 Nếu rút: {reward}\n\n"
        f"{board}\n"
        f"👉 !dao <ô>\n"
        f"👉 !rut"
    )

# =========================
# RÚT TIỀN
# =========================

@bot.command()
async def rut(ctx):

    uid = str(ctx.author.id)

    if uid not in mines_games:
        return await ctx.send("❌ Không có game mines")

    game = mines_games[uid]

    p = get_player(ctx.author.id)

    reward = int(game["bet"] * game["multi"])

    p["money"] += reward

    save_data()

    del mines_games[uid]

    await ctx.send(
        f"🏦 CASH OUT\n"
        f"💰 +{reward}"
    )
    
# =========================
# NGÂN HÀNG
# !bank
# !gui <số tiền>
# !rutbank <số tiền>
# =========================

# =========================
# UPDATE PLAYER DATA
# thêm vào get_player()
# =========================

# "bank": 0,

# ví dụ:
"""
players[uid] = {
    "money": 5000,
    "bank": 0,
    ...
}
"""

# =========================
# XEM NGÂN HÀNG
# =========================

@bot.command()
async def bank(ctx):

    p = get_player(ctx.author.id)

    await ctx.send(
        f"""
🏦 NGÂN HÀNG

👤 {ctx.author.name}

💵 Tiền mặt: {p.get('money',0)}
🏦 Tiền ngân hàng: {p.get('bank',0)}

📈 Lãi suất:
+5% mỗi 1 giờ
"""
    )

# =========================
# GỬI TIỀN
# =========================

@bot.command()
async def gui(ctx, amount: int):

    p = get_player(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ Số tiền không hợp lệ")

    if p["money"] < amount:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= amount
    p["bank"] = p.get("bank",0) + amount

    save_data()

    await ctx.send(
        f"🏦 Gửi thành công\n"
        f"💵 -{amount}"
    )

# =========================
# RÚT TIỀN
# =========================

@bot.command()
async def rutbank(ctx, amount: int):

    p = get_player(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ Số tiền không hợp lệ")

    if p.get("bank",0) < amount:
        return await ctx.send("❌ Không đủ tiền trong bank")

    p["bank"] -= amount
    p["money"] += amount

    save_data()

    await ctx.send(
        f"🏦 Rút thành công\n"
        f"💰 +{amount}"
    )

# =========================
# 🛢️ DẦU MỎ SYSTEM
# =========================

# =========================
# MUA GIÀN KHOAN DẦU
# !daumo
# =========================

@bot.command()
async def daumo(ctx):

    p = get_player(ctx.author.id)

    cost = 30000

    if p["money"] < cost:
        return await ctx.send(
            f"❌ Cần {cost} Kpts"
        )

    p["money"] -= cost

    p["oilrig"] = p.get("oilrig",0) + 1

    save_data()

    await ctx.send(
        f"""
🛢️ XÂY GIÀN KHOAN THÀNH CÔNG

🛢️ Tổng giàn khoan: {p['oilrig']}
💸 -{cost} Kpts
"""
    )

# =========================
# 💰 DẦU SINH TIỀN
# mỗi 60s
# =========================

@tasks.loop(seconds=60)
async def oil_income():

    for p in players.values():

        rigs = p.get("oilrig",0)

        if rigs > 0:

            income = rigs * random.randint(300,700)

            p["money"] += income

    save_data()

# =========================
# READY
# nhớ thêm:
# oil_income.start()
# =========================

"""
@bot.event
async def on_ready():

    load_data()

    logistics.start()
    oil_income.start()

    print("BOT ONLINE")
"""

# =========================
# 📊 XEM DẦU
# !oil
# =========================

@bot.command()
async def oil(ctx):

    p = get_player(ctx.author.id)

    rigs = p.get("oilrig",0)

    income = rigs * 500

    await ctx.send(
        f"""
🛢️ DẦU MỎ QUỐC GIA

🛢️ Giàn khoan: {rigs}

💰 Thu nhập ~ {income}/phút
"""
    )

# =========================
# 💥 CƯỚP DẦU
# !cuopdau @user
# =========================

@bot.command()
async def cuopdau(ctx, member: discord.Member):

    atk = get_player(ctx.author.id)
    vic = get_player(member.id)

    if vic.get("oilrig",0) <= 0:
        return await ctx.send(
            "❌ Nó không có dầu 😭"
        )

    msg = await ctx.send(
        "🛢️ ĐANG TẤN CÔNG MỎ DẦU..."
    )

    await asyncio.sleep(3)

    chance = random.randint(1,100)

    # =========================
    # THÀNH CÔNG
    # =========================

    if chance <= 40:

        stolen = 1

        vic["oilrig"] -= stolen

        atk["oilrig"] = atk.get("oilrig",0) + stolen

        save_data()

        return await msg.edit(
            content=
            f"""
🛢️ CƯỚP DẦU THÀNH CÔNG

🔥 +1 giàn khoan
"""
        )

    # =========================
    # FAIL
    # =========================

    atk["army_power"] = max(
        0,
        atk["army_power"] - 2000
    )

    save_data()

    await msg.edit(
        content=
        f"""
💀 CƯỚP DẦU THẤT BẠI, BẠN ĐÃ BỊ الله اكبر 🔥🤣🤣😂

⚔️ -2000 quân lực
"""
    )
    
# =========================
# 🕋 KAABA SYSTEM
# !kaaba
# =========================

KAABA_COOLDOWN = 86400  # 24h

@bot.command()
async def kaaba(ctx):

    p = get_player(ctx.author.id)

    now = time.time()

    # =========================
    # COOLDOWN
    # =========================

    if now - p.get("kaaba_time", 0) < KAABA_COOLDOWN:

        remain = int(
            (KAABA_COOLDOWN - (now - p["kaaba_time"])) / 3600
        )

        return await ctx.send(
            f"🕋 Bạn đã hành hương rồi\n⏳ Còn {remain} giờ"
        )

    p["kaaba_time"] = now

    msg = await ctx.send("🕋 ĐANG HÀNH HƯƠNG KAABA...")

    await asyncio.sleep(3)

    # =========================
    # REWARD
    # =========================

    reward = random.randint(3000,10000)

    morale = random.randint(5,20)

    p["money"] += reward

    p["morale"] = p.get("morale", 50) + morale

    # =========================
    # LUCK CASINO
    # =========================

    p["luck"] = time.time() + 3600

    save_data()

    await msg.edit(
        content=
        f"""
🕋 HÀNH HƯƠNG THÀNH CÔNG

☪️ Morale +{morale}
🕋 اللهُ أَكْبَرُ، اللهُ أَكْبَرُ، اللهُ أَكْبَرُ
لَا إِلَهَ إِلَّا اللهُ
اللهُ أَكْبَرُ، اللهُ أَكْبَرُ
وَلِلهِ الْحَمْدُ
​اللهُ أَكْبَرُ كَبِيرًا، وَالْحَمْدُ لِلهِ كَثِيرًا، وَسُبْحَانَ اللهِ بُكْرَةً وَأَصِيلًا
لَا إِلَهَ إِلَّا اللهُ وَحْدَهُ، صَدَقَ وَعْدَهُ، وَنَصَرَ عَبْدَهُ، وَأَعَزَّ جُنْدَهُ وَهَزَمَ الْأَحْزَابَ وَحْدَهُ
لَا إِلَهَ إِلَّا اللهُ، وَلَا نَعْبُدُ إِلَّا إِيَّاهُ، مُخْلِصِينَ لَهُ الدِّينَ وَلَوْ كَرِهَ الْكَافِرُونَ
اللَّهُمَّ صَلِّ عَلَى سَيِّدِنَا مُحَمَّدٍ، وَعَلَى آلِ سَيِّدِنَا مُحَمَّدٍ، وَعَلَى أَصْحَابِ سَيِّدِنَا مُحَمَّدٍ، وَعَلَى أَنْصَارِ سَيِّدِنَا مُحَمَّدٍ، وَعَلَى أَزْوَاجِ سَيِّدِنَا مُحَمَّدٍ، وَعَلَى ذُرِّيَّةِ سَيِّدِنَا مُحَمَّدٍ وَسَلِّمْ تَسْلِيمًا كَثِيرًا
🍀 Luck: 1h
💰 +{reward} Kpts
"""
    )

# =========================
# 🌙 RAMADAN
# !ramadan
# =========================

RAMADAN_CD = 43200  # 12h

@bot.command()
async def ramadan(ctx):

    p = get_player(ctx.author.id)

    now = time.time()

    if now - p.get("ramadan_time",0) < RAMADAN_CD:

        return await ctx.send(
            "🌙 Bạn vừa tổ chức Ramadan rồi"
        )

    p["ramadan_time"] = now

    msg = await ctx.send("🌙 ĐANG TỔ CHỨC RAMADAN...")

    await asyncio.sleep(2)

    morale = random.randint(10,30)

    reward = random.randint(2000,7000)

    p["morale"] = p.get("morale",50) + morale

    p["money"] += reward

    save_data()

    await msg.edit(
        content=
        f"""
🌙 RAMADAN THÀNH CÔNG

☪️ Morale +{morale}
💰 Quyên góp +{reward}
😎 Crime giảm nhẹ
"""
    )

# =========================
# 🕌 XÂY THÁNH ĐƯỜNG
# !thanhduong
# =========================

@bot.command()
async def thanhduong(ctx):

    p = get_player(ctx.author.id)

    cost = 50000

    if p["money"] < cost:
        return await ctx.send(
            f"❌ Cần {cost} Kpts"
        )

    p["money"] -= cost

    p["mosque"] = p.get("mosque",0) + 1

    p["morale"] = p.get("morale",50) + 15

    save_data()

    await ctx.send(
        f"""
🕌 XÂY THÁNH ĐƯỜNG THÀNH CÔNG

☪️ Morale +15
🕌 Tổng thánh đường: {p['mosque']}
💸 -{cost}
"""
    )

# =========================
# ☪️ CALIPHATE
# !caliphate
# =========================

@bot.command()
async def caliphate(ctx):

    p = get_player(ctx.author.id)

    morale = p.get("morale",50)

    army = p.get("army_power",0)

    # =========================
    # REQUIREMENTS
    # =========================

    if morale < 100:
        return await ctx.send(
            "❌ Cần 100 morale"
        )

    if army < 5000:
        return await ctx.send(
            "❌ Cần 5000 sức mạnh quân đội"
        )

    if p.get("caliphate",False):
        return await ctx.send(
            "☪️ Bạn đã lập Caliphate rồi"
        )

    p["caliphate"] = True

    p["army_power"] += 2000

    save_data()

    await ctx.send(
        f"""
☪️ CALIPHATE THÀNH LẬP

⚔️ +2000 quân lực
🔥 Morale toàn quốc tăng mạnh
😈 Nguy cơ bị cấm vận tăng
"""
    )
    
# =========================
# LÃI SUẤT
# +5% / 1H
# =========================

@tasks.loop(hours=1)
async def bank_interest():

    for p in players.values():

        bank_money = p.get("bank",0)

        if bank_money > 0:

            interest = int(bank_money * 0.05)

            p["bank"] += interest

    save_data()

    print("🏦 Đã cộng lãi ngân hàng")
    
# =========================
# BOT CHAT
# =========================

@bot.command()
async def nh(ctx, *, text):

    try:
        await ctx.message.delete()
    except:
        pass

    await ctx.send(text)

# =========================
# AFK
# =========================

@bot.command()
async def afk(ctx, *, reason="AFK"):

    afk_users[str(ctx.author.id)] = reason

    await ctx.send(
        f"😴 {ctx.author.name} đã AFK\n"
        f"📝 {reason}"
    )

# =========================
# DAILY
# =========================

DAILY_COOLDOWN = 86400

@bot.command()
async def daily(ctx):

    p = get_player(ctx.author.id)

    now = time.time()

    if now - p["daily_time"] < DAILY_COOLDOWN:

        remain = DAILY_COOLDOWN - (now - p["daily_time"])

        hours = int(remain // 3600)
        mins = int((remain % 3600) // 60)

        return await ctx.send(
            f"⏳ Tham lam cái lồn nha m còn {hours}h {mins}m"
        )

    reward = random.randint(3000, 6000)

    p["money"] += reward
    p["daily_time"] = now

    save_data()

    await ctx.send(f"💰 +{reward} Kq pts")

# =========================
# SHOP
# =========================

@bot.command()
async def shop(ctx):

    text = "🛒 SHOP QUÂN ĐỘI\n━━━━━━━━━━━━"

    for u in UNITS:

        text += (
            f"\n\n{u}"
            f"\n💰 {UNIT_PRICE[u]}"
            f"\n👥 +{UNITS[u]}"
        )

    text += "\n\n📦 STOCK"

    for b, v in shop_stock.items():
        text += f"\n{b}: {v}"

    await ctx.send(text)

# =========================
# BUY
# =========================

@bot.command()
async def buy(ctx, branch, unit, amount: int = 1):

    p = get_player(ctx.author.id)

    if branch not in BRANCHES:
        return await ctx.send("❌ Sai binh chủng")

    if unit not in UNITS:
        return await ctx.send("❌ Sai đơn vị")

    if amount <= 0:
        return await ctx.send("❌ Số lượng sai")

    troops = UNITS[unit] * amount

    if shop_stock[branch] < troops:
        return await ctx.send(
            f"❌ Không đủ stock\n"
            f"📦 Còn: {shop_stock[branch]}"
        )

    cost = UNIT_PRICE[unit] * amount

    if p["money"] < cost:
        return await ctx.send("❌ Không đủ tiền")

    shop_stock[branch] -= troops

    p["money"] -= cost
    p["army_power"] += troops
    p["troops"][branch] += troops

    save_data()

    await ctx.send(
        f"⚔️ Mua thành công\n"
        f"👥 +{troops}\n"
        f"💸 -{cost}"
    )

# =========================
# RESTOCK SHOP
# =========================

@tasks.loop(hours=1)
async def restock_shop():

    global shop_stock

    for b in BRANCHES:
        shop_stock[b] = 2000

    print("✅ SHOP RESTOCK")

# =========================
# HAU CAN
# =========================

@tasks.loop(seconds=30)
async def logistics():

    for p in players.values():

        if p["troops"].get("haucan", 0) > 0:

            p["money"] += p["troops"]["haucan"]

    save_data()

# =========================
# WAR
# =========================

@bot.command()
async def war(ctx, enemy: discord.Member):

    a = get_player(ctx.author.id)
    d = get_player(enemy.id)

    atk = a["army_power"] * random.uniform(0.8, 1.2)
    deff = d["army_power"] * random.uniform(0.8, 1.2)

    if atk > deff:

        win = int(d["money"] * 0.2)

        a["money"] += win
        d["money"] = max(0, d["money"] - win)

        result = f"🏆 THẮNG +{win}"

    else:

        loss = int(a["money"] * 0.1)

        a["money"] = max(0, a["money"] - loss)

        result = f"💀 THUA -{loss}"

    save_data()

    await ctx.send(result)

# =========================
# SLOT
# =========================

@bot.command(name="vongquay")
async def vongquay(ctx):

    p = get_player(ctx.author.id)

    if p["money"] < 500:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= 500

    symbols = ["💰","💀","⚔️","🎯","🔥","👑"]

    msg = await ctx.send("🎰 Đang quay...")

    c1=c2=c3="❔"

    for _ in range(8):

        c1 = random.choice(symbols)
        c2 = random.choice(symbols)
        c3 = random.choice(symbols)

        await msg.edit(
            content=f"[{c1}] [{c2}] [{c3}]"
        )

        await asyncio.sleep(0.2)

    if c1 == c2 == c3:
        reward = 2000

    elif c1 == c2 or c2 == c3 or c1 == c3:
        reward = 800

    else:
        reward = random.randint(0, 200)

    p["money"] += reward

    save_data()

    await msg.edit(
        content=f"[{c1}] [{c2}] [{c3}]\n💰 +{reward}"
    )

# =========================
# VE SO
# =========================

@bot.command()
async def veso(ctx, amount: int = 1):

    p = get_player(ctx.author.id)

    cost = 200 * amount

    if p["money"] < cost:
        return await ctx.send("❌ Không đủ tiền")

    p["money"] -= cost
    p["lottery_tickets"] += amount

    save_data()

    await ctx.send(f"🎟️ Mua {amount} vé")

# =========================
# QUAY SO
# =========================

@bot.command()
async def quayso(ctx):

    p = get_player(ctx.author.id)

    if p["lottery_tickets"] <= 0:
        return await ctx.send("❌ Không có vé")

    total = 0

    for _ in range(p["lottery_tickets"]):

        roll = random.randint(1, 1000)

        if roll == 1:
            reward = 50000

        elif roll <= 10:
            reward = 5000

        elif roll <= 100:
            reward = 800

        else:
            reward = 0

        total += reward

    p["lottery_tickets"] = 0
    p["money"] += total

    save_data()

    await ctx.send(f"🎟️ +{total} Kq pts")

# =========================
# HO SO
# =========================

@bot.command()
async def do(ctx, member: discord.Member = None):

    member = member or ctx.author

    p = get_player(member.id)

    total_troops = sum(p["troops"].values())

    text = f"""
📦 HỒ SƠ QUÂN SỰ
━━━━━━━━━━━━

👤 {member.name}

💰 Tiền: {p['money']}
⚔️ Sức mạnh: {p['army_power']}
🏳️ Lãnh thổ: {p['territory']}
☢️ Nuclear: {p['nukes']}

🪖 Tổng quân: {total_troops}
"""

    for b, v in p["troops"].items():
        text += f"\n- {b}: {v}"

    await ctx.send(text)

# =========================
# BXH TIEN
# =========================

@bot.command()
async def bxhtien(ctx):

    ranking = sorted(
        players.items(),
        key=lambda x: x[1]["money"],
        reverse=True
    )

    text = "💰 BXH TIỀN\n━━━━━━━━━━━━"

    for i, (uid, data) in enumerate(ranking[:10], start=1):

        try:
            user = await bot.fetch_user(int(uid))
            name = user.name
        except:
            name = "Unknown"

        text += f"\n{i}. {name} — {data['money']}"

    await ctx.send(text)

# =========================
# BXH QUAN
# =========================

@bot.command()
async def bxhquan(ctx):

    ranking = sorted(
        players.items(),
        key=lambda x: x[1]["army_power"],
        reverse=True
    )

    text = "⚔️ BXH QUÂN SỰ\n━━━━━━━━━━━━"

    for i, (uid, data) in enumerate(ranking[:10], start=1):

        try:
            user = await bot.fetch_user(int(uid))
            name = user.name
        except:
            name = "Unknown"

        text += f"\n{i}. {name} — {data['army_power']}"

    await ctx.send(text)

# =========================
# RUN
# =========================

bot.run(TOKEN)
