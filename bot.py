from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import random
import json
import os

TELEGRAM_TOKEN = "8697226305:AAHbh7I_lpqhIItAt-GNByRJ5OLl60L-trs"

active_games = {}
DATA_FILE = "users_bank.json"

# تحميل وبدء قاعدة بيانات الحسابات البنكية
def load_bank():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_bank(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

bank_data = load_bank()

def get_or_create_account(user):
    user_id = str(user.id)
    if user_id not in bank_data:
        acc_num = f"BANK-{random.randint(100000, 999999)}"
        bank_data[user_id] = {
            "name": user.first_name,
            "account_id": acc_num,
            "balance": 1000  # هدية ترحيبية
        }
        save_bank(bank_data)
    return bank_data[user_id]

# شروح الألعاب
GAME_EXPLANATIONS = {
    "شرح كراج": "🏎 **شرح لعبة كراجي:**\nلعبة تنافسية تقوم فيها بشراء وتطوير السيارات والمشاركة في سباقات سريعة ضد أعضاء المجموعة للوصول لأعلى تصنيف!",
    "شرح المزاد": "💰 **شرح لعبة مزاد البقاء:**\nتعتمد على المزايدة الذكية بأقل وأعلى الأسعار لشراء الموارد والبقاء حياً حتى نهاية الجولات.",
    "شرح العمدة": "🏛 **شرح لعبة العمدة:**\nلعبة إدارة وتكتيك، حيث يتنافس اللاعبون على الفوز بلقب العمدة وجمع أصوات أعضاء المجموعة وإدارة القرية.",
    "شرح الاساطير": "⚔️ **شرح لعبة معركة الأساطير:**\nلعبة قتال وتكتيك اختيار أبطال لمواجهة الفرق الأُخرى وتدمير حصونهم.",
    "شرح الاصطبل": "🐎 **شرح لعبة اسطبلي:**\nلعبة العناية بالخيول وتجهيزها للسباقات والمراهنة على الفائزين بين المشاركين.",
    "شرح تخمين": "🔍 **شرح لعبة تخمين:**\nالبوت يطرح سؤالاً أو صورة وعلى اللاعبين التخمين بأسرع وقت، والأسرع يحصل على النقاط."
}

# قائمة الألعاب الكتابية
GAMES_DATA = {
    "غنيلي": ["🎵 *غنيلي شوية غنيلي.. وخد عينيّ..* 🎤", "🎵 *سلمتك بيد الله.. يا محملني أذية..* 🎶"],
    "بغني": ["🎤 *أنا بغني للأمل.. بغني لليام الجاية!* ✨"],
    "عجلة النجوم": ["🌟 **عجلة النجوم دارت ووقفت عند:** أنت نجم اليوم ورائع جدًا! ⭐"],
    "تخمين": ["❓ **تخمين:** شيء يتكلم جميع لغات العالم ولكنه لا يملك لساناً؟\n\n*(الجواب: الصدى)*"],
    "قنص": ["🎯 **عملية قنص:** قمت بتصويب البندقية ودقة الهدف 99%! إصابة مباشرة! 💥"],
    "حزر": ["🧩 **حزر فزر:** ما هو الشيء الذي يربط اثنين ولكن يلمس شخصاً واحداً فقط؟\n\n*(الجواب: خاتم الزفاف)*"],
    "احكام": ["📜 **حكم:** عليك غناء مقطع قصير بصوتك في ريكورد للمجموعة!"],
    "عقاب": ["⚠️ **عقاب:** لا تتكلم في المجموعة لمدة 10 دقائق إلا باللغة العربية الفصحى!"],
    "حكم": ["👑 **حكمة اليوم:** لا تدع أمس يأخذ الكثير من اليوم."],
    "كرسي اعتراف": ["🪑 **كرسي الاعتراف:** ما هو أكبر سر تحتفظ به ولن تقوله لأحد؟"],
    "كت": ["ما هي أكثر عادة غريبة تقوم بها عندما تكون لوحدك؟"],
    "لو خيروك": ["تأكل وجبتك المفضلة طوال العمر 🍔 أم تسافر كل سنة لبلد جديد ✈️؟"],
    "صراحة": ["ما هو أكثر موقف محرج تعرضت له في حياتك؟"],
    "عواصم": ["🏛 ما هي عاصمة **السعودية**؟\n\n*(الجواب: الرياض)*"],
    "تفكيك": ["فكك الكلمة التالية: **تـلـيـجـرام**"],
    "ترتيب": ["رتب حروف الكلمة التالية للحصول على اسم دولة: **( ر - ص - م )**"]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    acc = get_or_create_account(user)
    await update.message.reply_text(f"أهلاً بك يا {user.first_name}!\nتم فتح حسابك البنكي تلقائياً: `{acc['account_id']}`\nأرسل (الالعاب) لعرض القائمة أو (حسابي) لمعرفة رصيدك.", parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_id = str(user.id)

    # 1. المناداة باسم البوت
    names = ["رايا", "يا رايا", "رؤى", "يا رؤى", "raya"]
    if text.lower() in names:
        await update.message.reply_text("عيون رايا ❤️", reply_to_message_id=update.message.message_id)
        return

    # 2. إنشاء حساب بنكي / حسابي / الفلوس
    if text in ["انشاء حساب بنكي", "إنشاء حساب بنكي", "فتح حساب بنكي"]:
        acc = get_or_create_account(user)
        await update.message.reply_text(f"💳 **حسابك البنكي جاهز بالفعل!**\n\n• **الاسم:** {acc['name']}\n• **رقم الحساب (ID):** `{acc['account_id']}`\n• **الرصيد:** {acc['balance']} 💵", reply_to_message_id=update.message.message_id, parse_mode="Markdown")
        return

    if text in ["حسابي", "الفلوس", "فلوسي", "رصيدي"]:
        acc = get_or_create_account(user)
        msg = (
            f"🏦 **بيانات حسابك البنكي:**\n\n"
            f"👤 **الاسم:** {acc['name']}\n"
            f"💳 **رقم الحساب:** `{acc['account_id']}`\n"
            f"💰 **رصيدك الحالي:** {acc['balance']} 💵"
        )
        await update.message.reply_text(msg, reply_to_message_id=update.message.message_id, parse_mode="Markdown")
        return

    # 3. توب الفلوس والتصنيف
    if text in ["توب الفلوس", "التصنيف", "الأغنياء", "التاپ"]:
        if not bank_data:
            await update.message.reply_text("لا يوجد حسابات registrada بعد!")
            return
        sorted_users = sorted(bank_data.values(), key=lambda x: x["balance"], reverse=True)[:10]
        top_msg = "🏆 **جدول تصنيف أغنى الأعضاء (توب الفلوس):**\n\n"
        for i, u_acc in enumerate(sorted_users, 1):
            top_msg += f"{i}. {u_acc['name']} ← **{u_acc['balance']}** 💵\n"
        await update.message.reply_text(top_msg, parse_mode="Markdown")
        return

    # 4. التحويل البنكي (تحويل المبلغ رقم_الحساب)
    if text.startswith("تحويل"):
        parts = text.split()
        if len(parts) >= 3 and parts[1].isdigit():
            amount = int(parts[1])
            target_acc_id = parts[2].strip()

            sender_acc = get_or_create_account(user)
            if sender_acc["balance"] < amount:
                await update.message.reply_text("❌ رصيدك غير كافي لإتمام التحويل!")
                return

            target_user_id = None
            for uid, acc in bank_data.items():
                if acc["account_id"] == target_acc_id:
                    target_user_id = uid
                    break

            if not target_user_id:
                await update.message.reply_text("❌ لم يتم العثور على رقم الحساب البنكي المكتوب!")
                return

            sender_acc["balance"] -= amount
            bank_data[target_user_id]["balance"] += amount
            save_bank(bank_data)

            await update.message.reply_text(f"✅ **تم التحويل بنجاح!**\n\n• **المبلغ:** {amount} 💵\n• **إلى الحساب:** `{target_acc_id}`\n• **رصيدك المتبقي:** {sender_acc['balance']} 💵", parse_mode="Markdown")
            return
        else:
            await update.message.reply_text("💡 **طريقة التحويل الصحيحة:**\nاكتب: `تحويل المبلغ رقم_الحساب`\nمثال: `تحويل 500 BANK-123456`", parse_mode="Markdown")
            return

    # 5. عرض قائمة الألعاب
    if text in ["الالعاب", "الألعاب", "العاب", "ألعاب"]:
        msg = (
            "🎲 **قائمة الألعاب والخدمات البنكية:**\n\n"
            "💳 **النظام البنكي والمالي:**\n"
            "← حسابي (أو الفلوس)\n"
            "← انشاء حساب بنكي\n"
            "← توب الفلوس (أو التصنيف)\n"
            "← تحويل [المبلغ] [رقم الحساب]\n\n"
            "• **الألعاب الجماعية (بدء وسجل مشاركين):**\n"
            "← كراجي (أو كراج)\n"
            "← مزاد البقاء (أو المزاد)\n"
            "← العمدة\n"
            "← معركة الأساطير (أو الأساطير)\n"
            "← اسطبلي (أو الاصطبل)\n"
            "← روليت\n"
            "← قرعة\n\n"
            "• **الألعاب الكتابية (تحصل منها على مكافأة مالية 💵):**\n"
            "← كت تويت (أو كت)\n"
            "← لو خيروك\n"
            "← صراحة\n"
            "← حزورة\n"
            "← عواصم\n"
            "← غنيلي\n"
            "← عجلة النجوم\n"
            "← تخمين\n"
            "← قنص\n"
            "← احكام\n"
            "← عقاب\n"
            "← كرسي اعتراف\n"
            "← تفكيك\n"
            "← ترتيب\n\n"
            "• **شروح الألعاب الجماعية:**\n"
            "← اكتب (شرح) + اسم اللعبة (مثال: شرح كراج، شرح المزاد)."
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    # 6. شروح الألعاب
    if text in GAME_EXPLANATIONS:
        await update.message.reply_text(GAME_EXPLANATIONS[text], reply_to_message_id=update.message.message_id, parse_mode="Markdown")
        return

    # 7. الألعاب الجماعية
    group_games_triggers = {
        "كراج": "كراجي 🏎", "كراجي": "كراجي 🏎",
        "المزاد": "مزاد البقاء 💰", "مزاد البقاء": "مزاد البقاء 💰",
        "العمدة": "العمدة 🏛",
        "الاساطير": "معركة الأساطير ⚔️", "معركة الاساطير": "معركة الأساطير ⚔️",
        "الاصطبل": "اسطبلي 🐎", "اسطبلي": "اسطبلي 🐎",
        "روليت": "الروليت 🎲", "روليت روسي": "الروليت 🎲"
    }

    if text in group_games_triggers:
        game_name = group_games_triggers[text]
        active_games[chat_id] = {"name": game_name, "participants": []}
        keyboard = [
            [InlineKeyboardButton("مشاركة", callback_data="join_group_game")],
            [InlineKeyboardButton("بدء اللعبة", callback_data="start_group_game")]
        ]
        msg_text = f"🎮 **تم بدء لعبة ({game_name}) بنجاح!**\n\n- اضغط على زر (مشاركة) للانضمام إلى اللعبة.\n\n• **عدد المشاركين:** 0"
        await update.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), reply_to_message_id=update.message.message_id, parse_mode="Markdown")
        return

    # 8. الألعاب الكتابية + كسب الفلوس عند اللعب
    for key, item_list in GAMES_DATA.items():
        if text == key or (key == "كت" and text in ["كت تويت", "كت"]):
            acc = get_or_create_account(user)
            reward = random.randint(50, 200)
            acc["balance"] += reward
            save_bank(bank_data)

            q = random.choice(item_list)
            response = f"🎮 **لعبة {key}:**\n\n{q}\n\n🎁 **ربحت {reward} 💵 لمشاركتك في اللعبة!**\n💰 **رصيدك الحالي:** {acc['balance']} 💵"
            await update.message.reply_text(response, reply_to_message_id=update.message.message_id, parse_mode="Markdown")
            return

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id
    user = query.from_user

    if chat_id not in active_games:
        await query.message.edit_text("• انتهت هذه اللعبة.")
        return

    game = active_games[chat_id]

    if query.data == "join_group_game":
        if user.id not in [u["id"] for u in game["participants"]]:
            game["participants"].append({"id": user.id, "name": user.first_name})
            participants_list = "\n".join([f"- {u['name']}" for u in game["participants"]])
            msg_text = (
                f"🎮 **لعبة ({game['name']}) جارية!**\n\n"
                "- اضغط على زر (مشاركة) للانضمام.\n\n"
                f"• **عدد المشاركين ({len(game['participants'])}):**\n"
                f"{participants_list}"
            )
            keyboard = [
                [InlineKeyboardButton("مشاركة", callback_data="join_group_game")],
                [InlineKeyboardButton("بدء اللعبة", callback_data="start_group_game")]
            ]
            await query.message.edit_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "start_group_game":
        if not game["participants"]:
            await query.answer("لا يوجد مشاركون بعد!", show_alert=True)
            return
        
        winner = random.choice(game["participants"])
        winner_user = type('User', (object,), {'id': winner['id'], 'first_name': winner['name']})
        acc = get_or_create_account(winner_user)
        reward = 500
        acc["balance"] += reward
        save_bank(bank_data)

        participants_list = "\n".join([f"- {u['name']}" for u in game["participants"]])
        final_text = (
            f"🏆 **اكتملت لعبة ({game['name']})!**\n\n"
            f"• **عدد المشاركين:** {len(game['participants'])}\n"
            f"{participants_list}\n\n"
            f"🎉 **الفائز هو:** [{winner['name']}](tg://user?id={winner['id']}) 👑\n"
            f"🎁 **حصل الفائز على جائزة قدرها {reward} 💵!**"
        )
        del active_games[chat_id]
        await query.message.edit_text(final_text, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(CallbackQueryHandler(handle_button))

    print("البوت يعمل بنجاح مع النظام البنكي وكسب الفلوس...")
    app.run_polling()

if __name__ == "__main__":
    main()
