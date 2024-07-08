import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.error import TelegramError

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تحميل البيانات من ملف JSON
def load_data():
    try:
        with open('data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"registered_users": {}, "votes": {}}

# حفظ البيانات في ملف JSON
def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)

data = load_data()
registered_users = data["registered_users"]
votes = data["votes"]
max_participants = 15

# دالة البدء العادية
def start(update: Update, context: CallbackContext) -> None:
    user_id = str(update.message.from_user.id)
    args = context.args
    
    if args:
        target_user_id = args[0]
        custom_start(update, context, target_user_id)
        return
    
    # التحقق من اشتراك المستخدم في القناة
    try:
        member = context.bot.get_chat_member("@Digital_life0", user_id)
        if member.status == ChatMember.MEMBER or member.status == ChatMember.ADMINISTRATOR or member.status == ChatMember.CREATOR:
            if user_id not in registered_users:
                if len(registered_users) < max_participants:
                    registered_users[user_id] = {'username': update.message.from_user.username, 'votes': 0}
                    save_data({"registered_users": registered_users, "votes": votes})
                    reply_text = "هل تود المشاركة في المسابقة؟ العدد المتبقي للمشاركة: {}".format(max_participants - len(registered_users))
                    keyboard = [[InlineKeyboardButton("نعم", callback_data='participate')]]
                    update.message.reply_text(reply_text, reply_markup=InlineKeyboardMarkup(keyboard))
                else:
                    update.message.reply_text("تم تسجيل 15 مشارك بالفعل. لا يمكن التسجيل الآن.")
            else:
                update.message.reply_text("لقد تم تسجيلك بالفعل. رابط الدعوة الخاص بك هو: https://t.me/UC_PUBGTakebot?start={}".format(user_id))
        else:
            update.message.reply_text("يجب عليك الاشتراك في قناتنا أولاً قبل المشاركة في المسابقة.")
    except TelegramError as e:
        update.message.reply_text("حدث خطأ أثناء التحقق من الاشتراك في القناة. يرجى المحاولة لاحقاً.")

# دالة التسجيل
def participate(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = str(query.from_user.id)
    if user_id not in registered_users:
        registered_users[user_id] = {'username': query.from_user.username, 'votes': 0}
        save_data({"registered_users": registered_users, "votes": votes})
    query.edit_message_text(text="تم تسجيلك في المسابقة! رابط الدعوة الخاص بك هو: https://t.me/UC_PUBGTakebot?start={}".format(user_id))

# دالة التصويت
def vote(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = str(query.from_user.id)
    target_user_id = query.data.split('_')[1]
    
    if user_id == target_user_id:
        query.edit_message_text("لا يمكنك التصويت لنفسك.")
        return
    
    if user_id in votes:
        query.edit_message_text("لقد صوتت بالفعل.")
        return
    
    votes[user_id] = target_user_id
    registered_users[target_user_id]['votes'] += 1
    save_data({"registered_users": registered_users, "votes": votes})
    
    query.edit_message_text("شكراً لتصويتك! @{} لديه الآن {} صوت(أصوات).".format(
        registered_users[target_user_id]['username'],
        registered_users[target_user_id]['votes']
    ))

# دالة التعامل مع الروابط المخصصة
def custom_start(update: Update, context: CallbackContext, target_user_id: str) -> None:
    user_id = str(update.message.from_user.id)
    
    if target_user_id not in registered_users:
        update.message.reply_text("رابط غير صالح.")
        return
    
    if user_id == target_user_id:
        update.message.reply_text("لقد تم تسجيلك بالفعل. رابط الدعوة الخاص بك هو: https://t.me/UC_PUBGTakebot?start={}".format(user_id))
        return
    
    reply_text = "قم بالتصويت لـ @{} من خلال الضغط على الزر أدناه.\nلديه حالياً {} صوت(أصوات).".format(
        registered_users[target_user_id]['username'],
        registered_users[target_user_id]['votes']
    )
    keyboard = [[InlineKeyboardButton("تصويت", callback_data='vote_{}'.format(target_user_id))]]
    update.message.reply_text(reply_text, reply_markup=InlineKeyboardMarkup(keyboard))

# دالة عرض النتائج
def results(update: Update, context: CallbackContext) -> None:
    results_text = "النتائج الحالية للمسابقة:\n"
    for user_id, data in registered_users.items():
        results_text += "@{}: {} صوت(أصوات)\n".format(data['username'], data['votes'])
    update.message.reply_text(results_text)

# دالة عرض الأصوات الخاصة بالمستخدم
def my_votes(update: Update, context: CallbackContext) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in registered_users:
        votes = registered_users[user_id]['votes']
        update.message.reply_text("لديك حالياً {} صوت(أصوات).".format(votes))
    else:
        update.message.reply_text("أنت لست مسجلاً في المسابقة.")

def main() -> None:
    # استبدل 'YOUR_BOT_TOKEN' برمز التوكن الخاص بك
    updater = Updater("7017263568:AAE51snSZ96GHFwFtibtBJKRjqmPM1bA-Ek")
    
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(participate, pattern='participate'))
    dispatcher.add_handler(CallbackQueryHandler(vote, pattern='vote_'))
    dispatcher.add_handler(CommandHandler("results", results))
    dispatcher.add_handler(CommandHandler("myvotes", my_votes))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()ain();
