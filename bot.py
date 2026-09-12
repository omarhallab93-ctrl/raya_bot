import os
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)
from google import genai
from google.genai import types

# 1. خادم فحص الصحة لـ Render
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

# 2. إعداد المفاتيح والذكاء الاصطناعي
TOKEN = os.environ.get("BOT_TOKEN", "8697226305:AAGxUICqrnQa0p3Ww54dNE1QZ2PYWfFGcy0")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        pass

users_db = {}
active_games = {}

def get_user_data(user_id, name):
    if user_id not in users_db:
        users_db[user_id] = {
            "name": name,
            "account_num": "60929472334683232",
            "bank": "الأهلي",
            "type": "فيزا",
            "balance": 4776523806865234528,
        }
    return users_db[user_id]

# 3. معالج الرسائل والألعاب
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_data = get_user_data(user.id, user.first_name)

    # التحقق من إجابات الألعاب
    if chat_id in active_games:
        correct_answer = active_games[chat_id]["answer"]
        if correct_answer in text:
            await update.message.reply_text(f"كفو يا {user.first_name}! 🥳 إجابة صحيحة: ({correct_answer})")
            del active_games[chat_id]
            return

    # المناداة
    if text == "رايا":
        await update.message.reply_text("عيون رايا 🌹")
        return

    # ألعاب التحديات
    elif text in ["لو خيروك", "كت تويت", "حزوره", "اسالني", "خلوه مع ذاتك", "خلينا نهوجس"]:
        if ai_client:
            try:
                response = ai_client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=f"اعطني سؤال محرج أو تحدي ممتع للعبة '{text}' باللغة العربية العامية وبشكل قصير ومباشر.",
                    config=types.GenerateContentConfig(temperature=1.0)
                )
                await update.message.reply_text(response.text)
            except Exception as e:
                await update.message.reply_text(f"حدث خطأ في الذكاء الاصطناعي: {e}")
        else:
            await update.message.reply_text("يرجى إضافة مفتاح GEMINI_API_KEY في Render لتفعيل الذكاء الاصطناعي.")
        return

    # ألعاب التخمين والعواصم
    elif text in ["عواصم", "خمن", "تخمين"]:
        if ai_client:
            try:
                regions = ["آسيا", "أوروبا", "أفريقيا", "أمريكا اللاتينية", "عربية", "أوقيانوسيا"]
                chosen_region = random.choice(regions)
                
                prompt = (
                    f"اختر دولة عشوائية وغير مشهورة من منطقة ({chosen_region}) واسأل عن عاصمتها.\n"
                    "التزم بالتنسيق التالي فقط دون أي مقدمات:\n"
                    "السؤال: ما هي عاصمة [اسم الدولة]؟\n"
                    "الإجابة: [اسم العاصمة فقط]"
                )
                
                response = ai_client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=1.2)
                )
                
                res_text = response.text
                if "الإجابة:" in res_text:
                    parts = res_text.split("الإجابة:")
                    question = parts[0].replace("السؤال:", "").strip()
                    answer = parts[1].strip()
                    active_games[chat_id] = {"answer": answer}
                    await update.message.reply_text(f"🎮 {question}\n\nأول من يكتب الإجابة الصحيحة يفوز!")
                else:
                    await update.message.reply_text(res_text)
            except Exception as e:
                await update.message.reply_text(f"حدث خطأ أثناء توليد السؤال: {e}")
        else:
            await update.message.reply_text("يرجى إضافة مفتاح GEMINI_API_KEY في Render لتفعيل الذكاء الاصطناعي.")
        return

    # قائمة الألعاب
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

# 4. تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ البوت يعمل بنجاح!")
    app.run_polling()

if __name__ == "__main__":
    main()
