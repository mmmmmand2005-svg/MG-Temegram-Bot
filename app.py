import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN ="8897589222:AAGVfPw75tiG3__W17p3qqpO_MwaykpvDc8"
ADMIN_ID ="8446946673"
DB = "bot.db"


def db():
    con = sqlite3.connect(DB)

    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            username TEXT,
            title TEXT,
            target INTEGER DEFAULT 0,
            funded INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        )
    """)

    con.commit()
    return con


def ensure_user(user):
    con = db()

    con.execute(
        "INSERT OR IGNORE INTO users(id, username) VALUES(?, ?)",
        (user.id, user.username or "")
    )

    con.execute(
        "UPDATE users SET username=? WHERE id=?",
        (user.username or "", user.id)
    )

    con.commit()
    con.close()


def main_keyboard(user_id):
    buttons = [
        [
            InlineKeyboardButton("💰 رصيدي", callback_data="balance"),
            InlineKeyboardButton("📢 القنوات", callback_data="channels")
        ],
        [
            InlineKeyboardButton("➕ إضافة قناة", callback_data="add"),
            InlineKeyboardButton("📊 إحصائياتي", callback_data="stats")
        ]
    ]

    if user_id == ADMIN_ID:
        buttons.append([
            InlineKeyboardButton("🛠 لوحة المدير", callback_data="admin")
        ])

    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user)

    await update.message.reply_text(
        "أهلاً بك في بوت التمويل 📢\n\n"
        "اختار من القائمة:",
        reply_markup=main_keyboard(update.effective_user.id)
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    ensure_user(query.from_user)

    if query.data == "balance":

        con = db()

        result = con.execute(
            "SELECT balance FROM users WHERE id=?",
            (user_id,)
        ).fetchone()

        con.close()

        balance = result[0] if result else 0

        text = (
            "💰 رصيدك الحالي\n\n"
            f"الرصيد: {balance} نقطة"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ الرئيسية", callback_data="home")]
        ])

    elif query.data == "channels":

        con = db()

        rows = con.execute("""
            SELECT id, username, title, target, funded
            FROM channels
            WHERE active=1
            ORDER BY id DESC
            LIMIT 20
        """).fetchall()

        con.close()

        if rows:
            text = "📢 الحملات المتاحة:\n\n"

            for row in rows:
                channel_id, username, title, target, funded = row

                text += (
                    f"#{channel_id} "
                    f"{title or username}\n"
                    f"💰 {funded}/{target}\n\n"
                )
        else:
            text = "📢 لا توجد حملات متاحة حالياً."

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ الرئيسية", callback_data="home")]
        ])

    elif query.data == "add":

        text = (
            "➕ إضافة قناة\n\n"
            "أرسل الأمر بهذا الشكل:\n\n"
            "/addchannel @channelusername | اسم القناة | 100\n\n"
            "الرقم الأخير هو هدف التمويل."
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ الرئيسية", callback_data="home")]
        ])

    elif query.data == "stats":

        con = db()

        channels_count = con.execute(
            "SELECT COUNT(*) FROM channels WHERE owner_id=?",
            (user_id,)
        ).fetchone()[0]

        balance = con.execute(
            "SELECT balance FROM users WHERE id=?",
            (user_id,)
        ).fetchone()[0]

        con.close()

        text = (
            "📊 إحصائياتك\n\n"
            f"📢 القنوات المضافة: {channels_count}\n"
            f"💰 الرصيد: {balance} نقطة"
        )

       
