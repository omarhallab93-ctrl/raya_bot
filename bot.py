import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# 1. Dummy Port HTTP Server (فحص الصحة لـ Render)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_check, daemon=True).start()

# 2. إعدادات البوت وقواعد البيانات
TOKEN = os.environ.get("BOT_TOKEN", "8697226305:AAGxUICqrnQa0p3Ww54dNE1QZ2PYWfFGcy0")

users_db = {}
muted_users = set()
restricted_users = set()
warns_db = {}

def init_db():
    pass

def get_user_data(user_id, name):
    if user_id not in users_db:
        users_db[user_id] = {
            "name": name,
            "account_num": "60929472334683232",
            "bank": "الأهلي",
            "type": "فيزا",
            "balance": 4776523806865234528,
            "transfer_temp": None
        }
    return users_db[user_id]

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if chat.type == "private":
        return True
    member = await context.bot.get_chat_member(chat.id, user.id)
    return member.status in ["administrator", "creator"]

# 3. دوال الإشراف
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("• هذا الأمر للمشرفين فقط!")
        return
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("• يرجى الرد على رسالة العضو المراد طرده.")
        return
    await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=reply.from_user.id)
    await context.bot.unban_chat_member(chat_id=update.effective_chat.id, user_id=reply.from_user.id)
    await update.message.reply_text(f"• تم طرد العضو [{reply.from_user.first_name}] بنجاح.")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("• هذا الأمر للمشرفين فقط!")
        return
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("• يرجى الرد على رسالة العضو لإنذاره.")
        return
    u_id = reply.from_user.id
    count = warns_db.get(u_id, 0) + 1
    warns_db[u_id] = count
    if count >= 3:
        await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=u_id)
        warns_db[u_id] = 0
        await update.message.reply_text(f"• تم حظر [{reply.from_user.first_name}] لوصوله لـ 3 إنذارات.")
    else:
        await update.message.reply_text(f"• تم إنذار [{reply.from_user.first_name}]. عدد الإنذارات: ({count}/3)")

async def clear_muted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    count = len(muted_users)
    for u_id in list(muted_users):
        try:
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=u_id,
                permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True)
            )
        except Exception:
            pass
    muted_users.clear()
    await update.message.reply_text(f"• تم مسح المكتومين وفك الكتم عن ({count}) عضو.")

async def clear_restricted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    count = len(restricted_users)
    for u_id in list(restricted_users):
        try:
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=u_id,
                permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True)
            )
        except Exception:
            pass
    restricted_users.clear()
    await update.message.reply_text(f"• تم مسح المقيدين وفك التقييد عن ({count}) عضو.")

# 4. معالج الرسائل
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"أهلاً بك يا {user_name}! 🌹\nبوت الإدارة والألعاب جاهز للمناداة بـ (رايا).")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    user = update.effective_user
    user_data = get_user_data(user.id, user.first_name)

    # المناداة
    if text == "رايا":
        await update.message.reply_text("عيون رايا 🌹")
        return

    # أوامر الإشراف
    elif text == "طرد":
        await kick(update, context)
        return
    elif text in ["إنذار", "انذار"]:
        await warn(update, context)
        return
    elif text == "مسح المكتومين":
        await clear_muted(update, context)
        return
    elif text == "مسح المقيدين":
        await clear_restricted(update, context)
        return

    # قائمة الألعاب الجديدة
    elif text in ["الالعاب", "الألعاب"]:
        games_list = (
            "الرئيسية 🌟\n\n"
            "العاب صور 🫰🏻\n"
            "👈🏻 ميكب\n"
            "👈🏻 زوم\n"
            "👈🏻 صور\n"
            "👈🏻 شاعر\n"
            "👈🏻 جدول\n"
            "👈🏻 طبخات\n"
            "👈🏻 مسلسل\n"
            "👈🏻 المختلف\n"
            "👈🏻 صور فنانين\n"
            "👈🏻 شخصيات انمي\n\n"
            "العاب كتابية 🫰🏻\n"
            "👈🏻 اسالني\n"
            "👈🏻 عواصم\n"
            "👈🏻 خمن\n"
            "👈🏻 كلمات\n"
            "👈🏻 عربي\n"
            "👈🏻 اكمل\n"
            "👈🏻 خلوه مع ذاتك\n"
            "👈🏻 انقليزي\n"
            "👈🏻 تفكيك\n"
            "👈🏻 الاسرع\n"
            "👈🏻 العكس\n"
            "👈🏻 حزوره\n"
            "👈🏻 ترتيب\n"
            "👈🏻 علم دول\n"
            "👈🏻 دين\n"
            "👈🏻 عامه\n"
            "👈🏻 كبو العشاء\n"
            "👈🏻 رياضيات\n"
            "👈🏻 مصطلح\n"
            "👈🏻 تركيب\n"
            "👈🏻 كت تويت\n"
            "👈🏻 لو خيروك\n"
            "👈🏻 سرعه\n"
            "👈🏻 صراحه\n"
            "👈🏻 اعرف المثل\n"
            "👈🏻 اختر حرف\n"
            "👈🏻 حروف\n"
            "👈🏻 خلينا نهوجس\n"
            "👈🏻 ايموجي\n\n"
            "العاب مُضافة 🫰🏻\n"
            "👈🏻 ضحكيني عنود\n"
            "👈🏻 غنيلي\n"
            "👈🏻 بغني\n"
            "👈🏻 عجلة النجوم\n"
            "👈🏻 قرعة\n"
            "👈🏻 تخمين\n\n"
            "العاب الجماعية 🫰🏻\n"
            "👈🏻 قنص\n"
            "👈🏻 روليت روسي\n"
            "👈🏻 كراجي - شرح كراج\n"
            "👈🏻 مزاد البقاء - شرح المزاد\n"
            "👈🏻 العمدة - شرح العمدة\n"
            "👈🏻 روليت دول\n"
            "👈🏻 روليت\n"
            "👈🏻 معركة الاساطير-شرح الاساطير\n"
            "👈🏻 بدء تخمين - شرح تخمين\n"
            "👈🏻 اسطبلي - شرح الاسطبل\n"
            "👈🏻 جوابك جوابهم\n"
            "👈🏻 المعركة - اوامر المعارك\n"
            "👈🏻 صراع العقول - اوامر صراع العقول\n"
            "👈🏻 حزر\n"
            "👈🏻 احكام\n"
            "👈🏻 عقاب\n"
            "👈🏻 حكم\n"
            "👈🏻 تحديات\n"
            "👈🏻 كرسي اعتراف"
        )
        await update.message.reply_text(games_list)
        return

    elif text == "توب الفلوس":
        top_text = (
            "28 ) 🪙 9,223,370,927,194,901,235\n"
            "قسورة 🇮🇶☝️\n"
            "29 ) 🪙 9,223,368,167,820,361,160\n"
            "أسَاهِيـّكْ .؟ 🇮🇶\n"
            "30 ) 🪙 9,223,365,817,977,976,980\n"
            "💲! AHMED 💎\n"
            "• you )\n"
            "4,776,523,806,865,234,528 🪙 | 🛡️⚜️القَيصَر⚜️\n\n"
            "ملاحظة : اي شخص مخالف للعبة بالفلش او خاط يوزر ينحظر من اللعبه وتتصفر فلوسه"
        )
        await update.message.reply_text(top_text)
        return

    elif text == "فلوسي":
        await update.message.reply_text(f"فلوسك {user_data['balance']} ريال 🪙")
        return

    elif text == "حسابي":
        account_info = (
            f"حسابي\n"
            f"• الاسم .. 🛡️⚜️{user.first_name}⚜️\n"
            f"• الحساب .. {user_data['account_num']}\n"
            f"• بنك .. ( الاهلي )\n"
            f"• نوع .. ( فيزا )\n"
            f"• الرصيد ..\n"
            f"( {user_data['balance']} ريال )\n"
            f"• الزرف .. ( 17910 ريال 🪙 )\n"
            f"• التصنيف .. ( 2050 🏅 )"
        )
        await update.message.reply_text(account_info)
        return

    elif text == "روليت":
        keyboard = [
            [InlineKeyboardButton("🌙 روليت مخفية", callback_data="roulette_hidden")],
            [InlineKeyboardButton("😎 روليت مكشوفة", callback_data="roulette_open")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🏠 لعبة الروليت\n\n• اختر نوع اللعبة ..", reply_markup=reply_markup)
        return

    elif text == "قرعة":
        keyboard = [
            [InlineKeyboardButton("1", callback_data="lottery_1"), InlineKeyboardButton("2", callback_data="lottery_2")],
            [InlineKeyboardButton("3", callback_data="lottery_3"), InlineKeyboardButton("4", callback_data="lottery_4")],
            [InlineKeyboardButton("5", callback_data="lottery_5")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🏠 قرعة\n• اختر عدد الفائزين ..", reply_markup=reply_markup)
        return

# 5. تشغيل البوت
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ البوت يعمل بنجاح!")
    app.run_polling()

if __name__ == "__main__":
    main()
