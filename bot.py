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

# ---------------------------------------------------------
# 1. Dummy Port HTTP Server (رضاء فحص الصحة في Render)
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 2. إعدادات البوت والبيانات
# ---------------------------------------------------------
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

users_db = {}
muted_users = set()
restricted_users = set()
warns_db = {}

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

# ---------------------------------------------------------
# 3. الأوامر الأساسية والمناداة وأوامر الإشراف والبنك
# ---------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"أهلاً بك يا {user_name} في البوت! 🌺\n\n"
        "يمكنك مناداة البوت بكلمة (رايا)، واستخدام الأوامر للألعاب والإدارة."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    user = update.effective_user
    chat = update.effective_chat
    user_data = get_user_data(user.id, user.first_name)

    # 1. المناداة ("رايا")
    if text == "رايا":
        await update.message.reply_text("عيون رايا 🌹")
        return

    # ---------------------------------------------------------
    # قسم أوامر الإشراف والإدارة (تحتاج الرد على رسالة المستخدم)
    # ---------------------------------------------------------
    reply = update.message.reply_to_message
    target_user = reply.from_user if reply else None

    # أمر: كتم
    if text == "كتم":
        if not await is_admin(update, context):
            await update.message.reply_text("• هذا الأمر للمشرفين فقط!")
            return
        if not target_user:
            await update.message.reply_text("• يرجى الرد على رسالة العضو المراد كتمه.")
            return
        
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        muted_users.add(target_user.id)
        await update.message.reply_text(f"• تم كتم العضو [{target_user.first_name}] بنجاح.")
        return

    # أمر: إلغاء الكتم / فك الكتم
    elif text in ["إلغاء الكتم", "فك الكتم", "تكلم"]:
        if not await is_admin(update, context):
            return
        if not target_user:
            await update.message.reply_text("• يرجى الرد على رسالة العضو.")
            return
        
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
        )
        muted_users.discard(target_user.id)
        await update.message.reply_text(f"• تم إلغاء كتم العضو [{target_user.first_name}].")
        return

    # أمر: حظر
    elif text == "حظر":
        if not await is_admin(update, context):
            return
        if not target_user:
            await update.message.reply_text("• يرجى الرد على رسالة العضو المراد حظره.")
            return
        
        await context.bot.ban_chat_member(chat_id=chat.id, user_id=target_user.id)
        await update.message.reply_text(f"• تم حظر العضو [{target_user.first_name}] من المجموعة.")
        return

    # أمر: تقييد
    elif text == "تقييد":
        if not await is_admin(update, context):
            return
        if not target_user:
            await update.message.reply_text("• يرجى الرد على رسالة العضو المراد تقييده.")
            return
        
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=False)
        )
        restricted_users.add(target_user.id)
        await update.message.reply_text(f"• تم تقييد العضو [{target_user.first_name}] (منع الوسائط).")
        return

    # أمر: إنذار
    elif text == "إنذار" or text == "انذار":
        if not await is_admin(update, context):
            return
        if not target_user:
            await update.message.reply_text("• يرجى الرد على رسالة العضو لإعطائه إنذار.")
            return
        
        warns = warns_db.get(target_user.id, 0) + 1
        warns_db[target_user.id] = warns
        if warns >= 3:
            await context.bot.ban_chat_member(chat_id=chat.id, user_id=target_user.id)
            warns_db[target_user.id] = 0
            await update.message.reply_text(f"• تم حظر [{target_user.first_name}] لوصوله لـ 3 إنذارات.")
        else:
            await update.message.reply_text(f"• تم إعطاء إنذار لـ [{target_user.first_name}]. عدد الإنذارات: ({warns}/3)")
        return

    # أمر: مسح المكتومين
    elif text == "مسح المكتومين":
        if not await is_admin(update, context):
            return
        count = len(muted_users)
        for u_id in list(muted_users):
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=u_id,
                    permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True)
                )
            except Exception:
                pass
        muted_users.clear()
        await update.message.reply_text(f"• تم مسح قائمة المكتومين وفك الكتم عن ({count}) عضو.")
        return

    # أمر: مسح المقيدين
    elif text == "مسح المقيدين":
        if not await is_admin(update, context):
            return
        count = len(restricted_users)
        for u_id in list(restricted_users):
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=u_id,
                    permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True)
                )
            except Exception:
                pass
        restricted_users.clear()
        await update.message.reply_text(f"• تم مسح قائمة المقيدين وفك التقييد عن ({count}) عضو.")
        return

    # ---------------------------------------------------------
    # قسم الألعاب والبنك
    # ---------------------------------------------------------
    elif text == "الالعاب" or text == "الألعاب":
        games_text = (
            "الألعاب\n"
            "أوامر لعبه البنك:\n"
            "1 - انشاء حساب بنكي ، راتب ، بخشيش ، زرف ، استثمار ، مضاربه ، حظ .\n\n"
            "2 - اضافة العجلة اكتب العجله ب 5 مليون ومن ضمن جوائزها :\n"
            "- سيارة ، ماسة ، X2 = يبديل كلشي تستخدمه لمدة 3 دقائق .. والخ\n\n"
            "3 - ممتلكاتي تستطيع الشراء والبيع واهداء ممتلكاتك أومرها كـمثال :\n"
            "- شراء 2 سيارة\n"
            "- اهداء 2 سيارة بالرد\n"
            "- بيع 2 سيارة\n\n"
            "4 - الاسهم يمكنك شراء اسهم وبيعيها بالطرق التالية :\n"
            "- شراء اسهم 2\n"
            "- بيع اسهم 2\n"
            "كلشي تتغير نسبة الاسهم اكتب ( سعر الاسهم )لمعرفة نسبتها\n\n"
            "5 - اضافة فرض البوت يعطيك عشوائي قرض مع وقت للسداد القرض :\n"
            "- قرض\n"
            "- سجني\n"
            "- ديوني\n"
            "- ديوني بالرد\n"
            "- سداد ديوني\n"
            "- سداد ديونه\n"
            "- اذا اسجنت مستحيل تلعب في أي شيء من البنك حتى تسدد أو يسددون لك .\n\n"
            "6 - اضافة توب الجروبات اكبر 20 عشرين قروبات يلعبون العاب عاديه كثير بالقروب يتصدرون للتوب .\n\n"
            "7 - اضافة توب اكبر 10 متفاعلين بالقروب ."
        )
        await update.message.reply_text(games_text)
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

    elif text.startswith("تحويل "):
        parts = text.split()
        if len(parts) >= 2:
            amount = parts[1]
            user_data["transfer_temp"] = amount
            await update.message.reply_text(
                f"تحويل {amount}\n"
                "• ارسل الحين رقم الحساب البنكي الي تبي تحول له\n-"
            )
        return

    elif text == user_data["account_num"]:
        if user_data.get("transfer_temp"):
            await update.message.reply_text("• مايمديك تحول لنفسك")
            user_data["transfer_temp"] = None
        return

    elif text == "روليت":
        keyboard = [
            [InlineKeyboardButton("🌙 روليت مخفية", callback_data="roulette_hidden")],
            [InlineKeyboardButton("😎 روليت مكشوفة", callback_data="roulette_open")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        roulette_msg = (
            "🏠 لعبة الروليت\n\n"
            "• اختر نوع اللعبة ..\n\n"
            "🌙 روليت مخفية .. لا تظهر اسماء المشاركين\n"
            "😎 روليت مكشوفة .. تظهر اسماء المشاركين"
        )
        await update.message.reply_text(roulette_msg, reply_markup=reply_markup)
        return

    elif text == "قرعة":
        keyboard = [
            [InlineKeyboardButton("1", callback_data="lottery_1"), InlineKeyboardButton("2", callback_data="lottery_2")],
            [InlineKeyboardButton("3", callback_data="lottery_3"), InlineKeyboardButton("4", callback_data="lottery_4")],
            [InlineKeyboardButton("5", callback_data="lottery_5")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        lottery_msg = (
            "🏠 قرعة\n"
            "👤 بواسطة : 🛡️⚜️القَيصَر⚜️\n\n"
            "• اختر عدد الفائزين ..\n"
            "• ملاحظة .. من لا يختار خلال 30 ثانية يتم طرده"
        )
        await update.message.reply_text(lottery_msg, reply_markup=reply_markup)
        return

# ---------------------------------------------------------
# 4. معالجة الأزرار التفاعلية
# ---------------------------------------------------------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data in ["roulette_hidden", "roulette_open"]:
        keyboard = [
            [InlineKeyboardButton("✅ انضمام", callback_data="join_game")],
            [InlineKeyboardButton("🦄 بدء اللعبة", callback_data="start_game")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🌙 تم إنشاء روليت مخفية\n\n"
            "• عدد الفائزين 👈 1\n"
            "• لن تظهر أسماء المشاركين\n"
            "• اضغط على الزر للانضمام",
            reply_markup=reply_markup
        )

    elif query.data == "start_game":
        await query.answer(
            text="• يجب أن يكون هناك 3 لاعبين على الأقل\n(الحالي 👈 1)",
            show_alert=True
        )

# ---------------------------------------------------------
# 5. تشغيل التطبيق
# ---------------------------------------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("✅ تم تشغيل البوت بنجاح مع أوامر الإشراف والمناداة (رايا)!")
    app.run_polling()

if __name__ == "__main__":
    main()
