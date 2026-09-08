import os
import random
import asyncio
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# TOKEN البوت يقرأه تلقائياً من بيئة التشغيل
TOKEN = os.environ.get("BOT_TOKEN", "ضع_التوكن_الخاص_بك_هنا")

# ----------------- قواعد البيانات في الذاكرة -----------------
users_db = {}  # {user_id: {"name": str, "balance": int}}
lottery_participants = set()  # المشاركون في القرعة
LOTTERY_ENTRY_FEE = 100

# ألعاب التخمين والجروبات
active_guesses = {}

# ----------------- 1. أوامر الإدارة والحماية -----------------

# الترحيب بالأعضاء الجدد
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text("👋 شكراً لإضافتي! يرجى رفعي كمشرف (Admin) بكامل الصلاحيات لكي أعمل بشكل صحيح. 🛡️")
        else:
            await update.message.reply_text(
                f"أهلاً بك يا [{member.first_name}](tg://user?id={member.id}) في المجموعة! 🥳\n"
                f"اكتب /start لمعرفة الأوامر والألعاب المتاحة.",
                parse_mode="Markdown"
            )

# طرد عضو
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("يرجى الرد على رسالة العضو المراد طرده!")
        return
    target_user = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target_user.id)
        await update.message.reply_text(f"🛑 تم طرد العضو {target_user.first_name} بنجاح.")
    except Exception:
        await update.message.reply_text("❌ فشل الطرد! تأكد من إعطائي صلاحية طرد المستخدمين.")

# حظر عضو
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("يرجى الرد على رسالة العضو المراد حظره!")
        return
    target_user = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
        await update.message.reply_text(f"🚫 تم حظر العضو {target_user.first_name} نهائياً.")
    except Exception:
        await update.message.reply_text("❌ فشل الحظر! تأكد من الصلاحيات.")

# كتم عضو
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("يرجى الرد على رسالة العضو المراد كتمه!")
        return
    target_user = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target_user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"🔇 تم كتم العضو {target_user.first_name}.")
    except Exception:
        await update.message.reply_text("❌ فشل الكتم! تأكد من الصلاحيات.")

# الغاء الكتم
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("يرجى الرد على رسالة العضو المراد إلغاء كتمه!")
        return
    target_user = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"🔊 تم إلغاء كتم العضو {target_user.first_name}.")
    except Exception:
        await update.message.reply_text("❌ فشل إلغاء الكتم.")

# ----------------- 2. نظام البنك والمال -----------------

async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    if user_id in users_db:
        await update.message.reply_text(f"لديك حساب بالفعل! رصيدك: {users_db[user_id]['balance']} $")
        return
    users_db[user_id] = {"name": user_name, "balance": 500}
    await update.message.reply_text(f"💳 تم إنشاء حساب بنكي لـ {user_name} برصيد افتتاح 500 $!")

async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users_db:
        await update.message.reply_text("ليس لديك حساب بنكي! اكتب /bank_create لإنشاء حساب.")
        return
    await update.message.reply_text(f"💰 رصيدك الحالي: {users_db[user_id]['balance']} $")

# ----------------- 3. الألعاب (روليت، تخمين، قرعة) -----------------

# 🎰 لعبة الروليت الروسي (للمخاطرة والكتم)
async def russian_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id

    outcomes = ["bullet", "blank", "blank", "blank", "blank", "blank"]
    bullet = random.choice(outcomes)

    await update.message.reply_text(f"🔫 {user_name} يسحب الزناد في الروليت الروسي...")
    await asyncio.sleep(1.5)

    if bullet == "bullet":
        try:
            await context.bot.restrict_chat_member(
                chat_id,
                user_id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            await update.message.reply_text(f"💥 **طخ!** أصابتك الرصاصة يا {user_name}! تم كتمك حظاً سعيداً في المرة القادمة. 💀")
        except Exception:
            await update.message.reply_text(f"💥 **طخ!** أصابتك الرصاصة يا {user_name}! (لم أتمكن من كتمك لعدم وجود صلاحيات).")
    else:
        await update.message.reply_text(f"محيط المسدس فارغ! 💨 نجوت بأمان يا {user_name}! 🎉")

# 🎰 لعبة روليت الرهان (مكسب أو خسارة فلوس)
async def roulette_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users_db:
        await update.message.reply_text("يجب أن تملك حساباً بنكياً أولاً عبر /bank_create")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("حدد مبلغ الرهان! مثال: `/روليت_رهان 100`", parse_mode="Markdown")
        return

    amount = int(context.args[0])
    if users_db[user_id]["balance"] < amount:
        await update.message.reply_text("رصيدك لا يكفي لهذا الرهان!")
        return

    win = random.choice([True, False])
    if win:
        users_db[user_id]["balance"] += amount
        await update.message.reply_text(f"🎰 **مبروك!** فزت بالروليت وكسبت {amount} $! رصيدك الجديد: {users_db[user_id]['balance']} $")
    else:
        users_db[user_id]["balance"] -= amount
        await update.message.reply_text(f"💀 **خسرت!** ذهب مبلغ {amount} $ في الروليت. رصيدك الجديد: {users_db[user_id]['balance']} $")

# 🎯 إعداد التخمين المخفي من الخاص
async def set_guess_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.message.reply_text("اكتب هذا الأمر في خاص البوت لتحديد الكلمة السرية!")
        return
    if not context.args:
        await update.message.reply_text("حدد الكلمة! مثال: `/تخمين تفاحة 200`", parse_mode="Markdown")
        return

    secret_word = context.args[0].strip()
    reward = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 200
    context.user_data["pending_guess"] = {"word": secret_word, "reward": reward}
    await update.message.reply_text(f"تم حفظ الكلمة: **{secret_word}**! اذهب للجروب واكتب `/تفعيل_التخمين`", parse_mode="Markdown")

# تفعيل التخمين في الجروب
async def activate_guess_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("هذا الأمر للجروبات فقط!")
        return
    chat_id = update.effective_chat.id
    pending = context.user_data.get("pending_guess")
    if not pending:
        await update.message.reply_text("اذهب للخاص واكتب `/تخمين الكلمة` أولاً!")
        return

    active_guesses[chat_id] = {"word": pending["word"].lower(), "reward": pending["reward"]}
    context.user_data["pending_guess"] = None
    await update.message.reply_text(f"🎯 **بدأت لعبة التخمين!**\n💰 الجائزة: {pending['reward']} $\nخمنوا الكلمة الآن في الشات!")

# 🎟️ القرعة
async def join_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users_db or users_db[user_id]["balance"] < LOTTERY_ENTRY_FEE:
        await update.message.reply_text(f"تحتاج حساب بنكي ورصيد {LOTTERY_ENTRY_FEE}$ على الأقل!")
        return
    if user_id in lottery_participants:
        await update.message.reply_text("أنت مشارك بالفعل في القرعة!")
        return

    users_db[user_id]["balance"] -= LOTTERY_ENTRY_FEE
    lottery_participants.add(user_id)
    await update.message.reply_text(f"🎟️ تم انضمامك للقرعة! عدد المشاركين الحالي: {len(lottery_participants)}")

async def draw_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global lottery_participants
    if not lottery_participants:
        await update.message.reply_text("لا يوجد مشاركون في القرعة!")
        return

    prize = len(lottery_participants) * LOTTERY_ENTRY_FEE
    winner_id = random.choice(list(lottery_participants))
    users_db[winner_id]["balance"] += prize
    await update.message.reply_text(
        f"🎉 **تم إجراء السحب على القرعة!** 🎉\n\n"
        f"🏆 الفائز: {users_db[winner_id]['name']}\n"
        f"💰 الجائزة الكبرى: {prize} $"
    )
    lottery_participants.clear()

# ----------------- 4. معالجة الرسائل والردود التلقائية -----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ **أهلاً بك في بوت إدارة المجموعات والألعاب!**\n\n"
        "🛠️ **أوامر المشرف (بالرد على الرسالة):**\n"
        "▫️ `/طرد` - طرد العضو\n"
        "▫️ `/حظر` - حظر العضو\n"
        "▫️ `/كتم` - كتم العضو\n"
        "▫️ `/الغاء_الكتم` - فك الكتم\n\n"
        "🎰 **الألعاب والقرعة:**\n"
        "▫️ `/روليت` - لعبة الروليت الروسي (كتم عشوائي)\n"
        "▫️ `/روليت_رهان [المبلغ]` - روليت المراهنات بالفلوس\n"
        "▫️ `/تخمين [الكلمة]` - وضع كلمة سرية (في الخاص)\n"
        "▫️ `/تفعيل_التخمين` - بدء التخمين في الشات\n"
        "▫️ `/lottery_join` - دخول القرعة\n"
        "▫️ `/lottery_start` - سحب القرعة\n\n"
        "💳 **البنك:**\n"
        "▫️ `/bank_create` - فتح حساب بنكي\n"
        "▫️ `/balance` - معرفة الرصيد",
        parse_mode="Markdown"
    )

async def process_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    text = update.message.text.strip().lower()

    # 1. الرد التلقائي على السلام عليكم
    salams = ["السلام عليكم", "سلام عليكم", "السلام عليكم ورحمة الله", "السلام عليكم ورحمة الله وبركاته"]
    if any(salam in text for salam in salams):
        await update.message.reply_text("وعليكم السلام ورحمة الله وبركاته 🌺")
        return

    # 2. فحص التخمين في الشات
    if chat_id in active_guesses:
        guess_info = active_guesses[chat_id]
        if text == guess_info["word"]:
            winner_id = update.effective_user.id
            winner_name = update.effective_user.first_name
            reward = guess_info["reward"]

            if winner_id in users_db:
                users_db[winner_id]["balance"] += reward

            await update.message.reply_text(
                f"🎉 **تخمين صحيح!** 🎉\n🏆 الفائز: {winner_name}\n🔑 الكلمة: {guess_info['word']}\n💰 المكافأة: {reward} $"
            )
            del active_guesses[chat_id]

# ----------------- الدالة الرئيسية -----------------

def main():
    app = Application.builder().token(TOKEN).build()

    # الأوامر الرئيسية
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bank_create", create_account))
    app.add_handler(CommandHandler("balance", get_balance))

    # أوامر الإشراف
    app.add_handler(CommandHandler(["طرد", "kick"], kick_user))
    app.add_handler(CommandHandler(["حظر", "ban"], ban_user))
    app.add_handler(CommandHandler(["كتم", "mute"], mute_user))
    app.add_handler(CommandHandler(["الغاء_الكتم", "unmute"], unmute_user))

    # ألعاب الروليت والقرعة والتخمين
    app.add_handler(CommandHandler(["روليت", "roulette"], russian_roulette))
    app.add_handler(CommandHandler(["روليت_رهان", "roulette_bet"], roulette_bet))
    app.add_handler(CommandHandler(["تخمين", "guess"], set_guess_private))
    app.add_handler(CommandHandler(["تفعيل_التخمين", "start_guess"], activate_guess_group))
    app.add_handler(CommandHandler("lottery_join", join_lottery))
    app.add_handler(CommandHandler("lottery_start", draw_lottery))

    # معالجة الأحداث والرسائل والردود التلقائية
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_group_messages))

    app.run_polling()

if __name__ == "__main__":
    main()

