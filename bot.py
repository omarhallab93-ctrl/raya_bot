import os
import sqlite3
import logging

from dotenv import load_dotenv
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("لم يتم العثور على BOT_TOKEN في ملف .env")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

DB = "raya.db"


# =========================
# قاعدة البيانات
# =========================

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            PRIMARY KEY (chat_id, user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            chat_id INTEGER,
            user_id INTEGER,
            action TEXT,
            PRIMARY KEY (chat_id, user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            chat_id INTEGER,
            user_id INTEGER,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, user_id)
        )
    """)

    conn.commit()
    conn.close()


def save_user(chat_id, user):
    conn = sqlite3.connect(DB)
    conn.execute("""
        INSERT OR REPLACE INTO users
        (chat_id, user_id, username, first_name)
        VALUES (?, ?, ?, ?)
    """, (
        chat_id,
        user.id,
        user.username.lower() if user.username else None,
        user.first_name or ""
    ))
    conn.commit()
    conn.close()


def save_action(chat_id, user_id, action):
    conn = sqlite3.connect(DB)
    conn.execute("""
        INSERT OR REPLACE INTO actions
        (chat_id, user_id, action)
        VALUES (?, ?, ?)
    """, (chat_id, user_id, action))
    conn.commit()
    conn.close()


def remove_action(chat_id, user_id):
    conn = sqlite3.connect(DB)
    conn.execute(
        "DELETE FROM actions WHERE chat_id=? AND user_id=?",
        (chat_id, user_id)
    )
    conn.commit()
    conn.close()


def get_user_by_username(chat_id, username):
    username = username.replace("@", "").lower()

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, first_name
        FROM users
        WHERE chat_id=? AND username=?
    """, (chat_id, username))

    result = cur.fetchone()
    conn.close()

    return result


def get_actions(chat_id, action):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id
        FROM actions
        WHERE chat_id=? AND action=?
    """, (chat_id, action))

    result = [row[0] for row in cur.fetchall()]
    conn.close()

    return result


# =========================
# المشرف
# =========================

async def is_admin(update):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        return False

    member = await chat.get_member(user.id)

    return member.status in ("administrator", "creator")


# =========================
# الشخص المستهدف
# =========================

async def get_target(update, context):

    message = update.message
    chat_id = update.effective_chat.id

    # الرد على رسالة
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        save_user(chat_id, target)
        return target

    # استخدام @username
    if context.args:

        username = context.args[0]

        result = get_user_by_username(chat_id, username)

        if result:
            user_id, first_name = result

            class Target:
                pass

            target = Target()
            target.id = user_id
            target.first_name = first_name
            target.username = username.replace("@", "")

            return target

        await message.reply_text(
            "⚠️ لم أتعرف على هذا المستخدم.\n"
            "استخدم الأمر بالرد على رسالته أول مرة."
        )

    return None


# =========================
# الصلاحيات
# =========================

async def can_manage(update, target):

    chat = update.effective_chat

    try:
        member = await chat.get_member(target.id)

        if member.status in ("administrator", "creator"):
            return False

        return True

    except:
        return True


# =========================
# الكتم
# =========================

async def mute(update, context):

    if not await is_admin(update):
        return

    target = await get_target(update, context)

    if not target:
        await update.message.reply_text(
            "⚠️ رد على رسالة العضو واكتب:\nكتم"
        )
        return

    if not await can_manage(update, target):
        await update.message.reply_text(
            "❌ لا يمكنني تنفيذ الأمر على مشرف."
        )
        return

    try:
        permissions = ChatPermissions(
            can_send_messages=False
        )

        await update.effective_chat.restrict_member(
            target.id,
            permissions=permissions
        )

        save_action(
            update.effective_chat.id,
            target.id,
            "muted"
        )

        await update.message.reply_text(
            f"🔇 تم كتم {target.first_name}"
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text(
            "❌ لم أستطع كتم العضو."
        )


# =========================
# فك الكتم
# =========================

async def unmute(update, context):

    if not await is_admin(update):
        return

    target = await get_target(update, context)

    if not target:
        return

    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )

        await update.effective_chat.restrict_member(
            target.id,
            permissions=permissions
        )

        remove_action(
            update.effective_chat.id,
            target.id
        )

        await update.message.reply_text(
            f"🔊 تم فك الكتم عن {target.first_name}"
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text(
            "❌ حدث خطأ أثناء فك الكتم."
        )


# =========================
# الحظر
# =========================

async def ban(update, context):

    if not await is_admin(update):
        return

    target = await get_target(update, context)

    if not target:
        return

    if not await can_manage(update, target):
        await update.message.reply_text(
            "❌ لا يمكنني حظر مشرف."
        )
        return

    try:
        await update.effective_chat.ban_member(target.id)

        await update.message.reply_text(
            f"🚫 تم حظر {target.first_name}"
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text(
            "❌ لم أستطع حظر العضو."
        )


# =========================
# فك الحظر
# =========================

async def unban(update, context):

    if not await is_admin(update):
        return

    target = await get_target(update, context)

    if not target:
        return

    try:
        await update.effective_chat.unban_member(
            target.id,
            only_if_banned=True
        )

        await update.message.reply_text(
            f"✅ تم فك الحظر عن {target.first_name}"
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text(
            "❌ حدث خطأ أثناء فك الحظر."
        )


# =========================
# التقييد
# =========================

async def restrict(update, context):

    if not await is_admin(update):
        return

    target = await get_target(update, context)

    if not target:
        return

    if not await can_manage(update, target):
        await update.message.reply_text(
            "❌ لا يمكنني تقييد مشرف."
        )
        return

    try:
        permissions = ChatPermissions(
            can_send_messages=False
        )

        await update.effective_chat.restrict_member(
            target.id,
            permissions=permissions
        )

        save_action(
            update.effective_chat.id,
            target.id,
            "restricted"
        )

        await update.message.reply_text(
            f"⛔ تم تقييد {target.first_name}"
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text(
            "❌ لم أستطع تقييد العضو."
        )


# =========================
# الطرد
# =========================

async def kick(update, context):

    if not await is_admin(update):
        return

    target = await get_target(update, context)

    if not target:
        return

    if not await can_manage(update, target):
        await update.message.reply_text(
            "❌ لا يمكنني طرد مشرف."
        )
        return

    try:
        await update.effective_chat.ban_member(target.id)
        await update.effective_chat.unban_member(target.id)

        await update.message.reply_text(
            f"👢 تم طرد {target.first_name}"
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text(
            "❌ لم أستطع طرد العضو."
        )


# =========================
# الإنذار
# =========================

async def warn(update, context):

    if not await is_admin(update):
        return

    target = await get_target(update, context)

    if not target:
        return

    chat_id = update.effective_chat.id

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT count FROM warnings
        WHERE chat_id=? AND user_id=?
    """, (chat_id, target.id))

    row = cur.fetchone()

    count = (row[0] if row else 0) + 1

    cur.execute("""
        INSERT OR REPLACE INTO warnings
        (chat_id, user_id, count)
        VALUES (?, ?, ?)
    """, (chat_id, target.id, count))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"⚠️ تم إعطاء {target.first_name} إنذارًا.\n"
        f"عدد الإنذارات: {count}"
    )


# =========================
# مسح المكتومين
# =========================

async def clear_muted(update, context):

    if not await is_admin(update):
        return

    chat = update.effective_chat
    users = get_actions(chat.id, "muted")

    count = 0

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

    for user_id in users:
        try:
            await chat.restrict_member(
                user_id,
                permissions=permissions
            )

            remove_action(chat.id, user_id)
            count += 1

        except:
            pass

    await update.message.reply_text(
        f"🔊 تم فك كتم {count} عضو."
    )


# =========================
# مسح المقيدين
# =========================

async def clear_restricted(update, context):

    if not await is_admin(update):
        return

    chat = update.effective_chat
    users = get_actions(chat.id, "restricted")

    count = 0

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

    for user_id in users:
        try:
            await chat.restrict_member(
                user_id,
                permissions=permissions
            )

            remove_action(chat.id, user_id)
            count += 1

        except:
            pass

    await update.message.reply_text(
        f"🔊 تم فك تقييد {count} عضو."
    )


# =========================
# استقبال الرسائل
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    chat = update.effective_chat
    user = update.effective_user

    # حفظ كل مستخدم تحدث رايا معه
    if chat.type != "private":
        save_user(chat.id, user)

    text = update.message.text.strip()

    if text == "كتم":
        await mute(update, context)

    elif text == "فك كتم":
        await unmute(update, context)

    elif text == "حظر":
        await ban(update, context)

    elif text == "فك حظر":
        await unban(update, context)

    elif text == "تقييد":
        await restrict(update, context)

    elif text == "طرد":
        await kick(update, context)

    elif text == "إنذار":
        await warn(update, context)

    elif text == "مسح المكتومين":
        await clear_muted(update, context)

    elif text == "مسح المقيدين":
        await clear_restricted(update, context)


# =========================
# تشغيل رايا
# =========================

def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("رايا تعمل الآن ✅")

    app.run_polling()


if __name__ == "__main__":
    main()

