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

LOTTERY SERVER ( Quay so sever )
!lottery

😴 AFK
!afk <lý do>

🚨 ADMIN HELP ( chinh quyen )
use: !adminhelp

📢 CHAT
!nh <nội dung>
""")

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

@bot.command(name="d
