import io
import os
from random import choice

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, Update, constants, error, helpers)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from tg_engine import db_tools, schemas

ADMIN_ID = int(os.environ.get('ADMIN_ID', 2601798))
BOOSTY_GROUP_ID = int(os.environ.get('BOOSTY_GROUP_ID', 0))
BOT_TOKEN = os.environ.get('BOT_TOKEN', '414349423:AAEPc431lxLuf5RVe_pgqlBbZcrzP65L45k')
BOOSTY_URL = os.environ.get('BOOSTY_URL', 'boosty url')
TIME_RESEND_STATUS = 6


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Send a message when the command /start is issued."""
    if not await db_tools.is_user_exist(update.effective_message.chat_id):
        try:
            parent = int(context.args[0])
        except Exception:
            parent = None
        await db_tools.add_user(update.effective_message.chat_id, parent)

    await add_to_queue(update.effective_message.chat_id, context)


async def get_user_context(
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    force_link: str = None
) -> schemas.UserContext:
    user_context: schemas.UserContext = context.user_data.get('user_context')
    if not user_context:
        user_context = schemas.UserContext()
    if force_link:
        next_message = await db_tools.get_message(
            force_link,
            user_context.flags
        )
        next_message.timeout = 0
        user_context.next_message = next_message
        context.user_data['user_context'] = user_context
        return user_context

    if not user_context.next_message:
        cur_message = await db_tools.get_cur_message_link(chat_id)
        user_context.next_message = await db_tools.get_message(cur_message, user_context.flags)
        context.user_data['user_context'] = user_context
    return user_context


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_context = await get_user_context(update.effective_message.chat_id, context)
    if context.job_queue.get_jobs_by_name(str(update.effective_message.chat_id)):
        await context.bot.send_message(
            update.effective_message.chat_id,
            choice(user_context.next_message.wait_reaction),
            reply_to_message_id=update.effective_message.message_id,
        )
        return

    if user_context.next_message.referal_block:
        boosty_group_member = await context.bot.getChatMember(
            BOOSTY_GROUP_ID, update.effective_message.chat_id
        )
        if boosty_group_member.status is not constants.ChatMemberStatus.MEMBER:
            num_referals = await db_tools.get_num_referals(update.effective_message.chat_id)
            if user_context.next_message.referal_block > num_referals:
                await add_to_queue(update.effective_message.chat_id, context)
                return

    for button in user_context.next_message.buttons:
        if update.message.text != button.text:
            continue
        user_context.next_message = await db_tools.get_message(
            button.next_message_link,
            user_context.flags
        )
        context.user_data['user_context'] = user_context
        break
    else:
        await context.bot.send_message(
            update.effective_message.chat_id,
            choice(user_context.next_message.wait_reaction),
            reply_to_message_id=update.effective_message.message_id,
        )
        return

    await add_to_queue(update.effective_message.chat_id, context)


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE):
    current_jobs = context.job_queue.get_jobs_by_name(name)

    for job in current_jobs:
        job.schedule_removal()


async def send_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    message: schemas.Message = context.job.data.user_data['user_context'].next_message
    data = {
        'chat_id': context.job.chat_id,
    }
    if message.referal_block:
        message.text = message.text.format(
            ref_url=helpers.create_deep_linked_url(
                context.bot.username, str(data['chat_id'])
            ),
            boosty_url=BOOSTY_URL,
        )

    if message.buttons:
        reply_keyboard = []
        for button in sorted(message.buttons, key=lambda x: x.number):
            reply_keyboard.append([button.text])
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        data['reply_markup'] = markup

    if message.content_type == 'text':
        data['text'] = message.text
        await context.bot.send_message(**data)
    elif message.content_type == 'photo':
        data['caption'] = message.text
        data['photo'] = await db_tools.get_tg_id_media(message.media_id)

        try:
            await context.bot.send_photo(**data)
        except error.BadRequest:
            data['photo'] = await db_tools.get_media(message.media_id)
            sent_message = await context.bot.send_photo(**data)
            await db_tools.update_media_tg_id(message.media_id, sent_message.photo[-1].file_id)

    elif message.content_type == 'voice':
        data['caption'] = message.text
        data['voice'] = await db_tools.get_tg_id_media(message.media_id)

        try:
            await context.bot.send_voice(**data)
        except error.BadRequest:
            data['voice'] = await db_tools.get_media(message.media_id)
            sent_message = await context.bot.send_voice(**data)
            await db_tools.update_media_tg_id(message.media_id, sent_message.voice.file_id)

    context.job.data.user_data['user_context'].flags = await db_tools.update_user_status(
            context.job.chat_id,
            message,
        )

    if message.next_msg:
        message = await db_tools.get_message(
            message.next_msg,
            context.job.data.user_data['user_context'].flags
            )
        context.job.data.user_data['user_context'].next_message = message
        await add_to_queue(context.job.chat_id, context.job.data)


async def send_status(context: ContextTypes.DEFAULT_TYPE) -> None:
    message: schemas.Message = context.job.data.user_data['user_context'].next_message

    if message.content_type == 'text':
        await context.bot.send_chat_action(
            context.job.chat_id,
            constants.ChatAction.TYPING,
        )
    elif message.content_type == 'photo':
        await context.bot.send_chat_action(
            context.job.chat_id,
            constants.ChatAction.UPLOAD_PHOTO,
        )
    elif message.content_type == 'voice':
        await context.bot.send_chat_action(
            context.job.chat_id,
            constants.ChatAction.RECORD_VOICE,
        )


async def add_to_queue(
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    force_link: str = None
) -> None:
    user_context = await get_user_context(chat_id, context, force_link)
    next_message = user_context.next_message
    if not next_message:
        cur_message_link = await db_tools.get_cur_message_link(chat_id)
        next_message = await db_tools.get_message(cur_message_link, user_context.flags)
        user_context.next_message = next_message
    remove_job_if_exists(str(chat_id), context)

    for time_send_status in range(0, int(next_message.time_typing), TIME_RESEND_STATUS):
        context.job_queue.run_once(
            send_status,
            next_message.timeout + time_send_status,
            chat_id=chat_id,
            name=str(chat_id),
            data=context,
        )
    context.job_queue.run_once(
            send_message,
            next_message.timeout + next_message.time_typing,
            chat_id=chat_id,
            name=str(chat_id),
            data=context,
        )


async def set_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message.chat_id != ADMIN_ID:
        return
    story_file = await context.bot.get_file(update.message.document)
    with io.BytesIO() as zip_file:
        await story_file.download_to_memory(out=zip_file)
        await db_tools.add_story(zip_file)
        await context.bot.send_message(update.effective_message.chat_id, 'done')


async def jump(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    started_chapters = await db_tools.get_started_chapters(str(update.effective_message.chat_id))
    keyboard = []
    for chapter_name, message_link in started_chapters:
        keyboard.append([
            InlineKeyboardButton(chapter_name, callback_data=f'to_save={message_link}')]
        )
    keyboard.append([
            InlineKeyboardButton('Отмена', callback_data='cancel=cancel')]
        )
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Давай повторим:', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    command, value = query.data.split('=')
    if command == 'to_save':
        message_link = await db_tools.open_save(str(update.effective_message.chat_id), value)
        await add_to_queue(update.effective_message.chat_id, context, message_link)
    await query.delete_message()


def main() -> None:

    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start, filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("jump", jump, filters.ChatType.PRIVATE))
    application.add_handler(CallbackQueryHandler(button))

    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, echo
    ))
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.ATTACHMENT, set_story
    ))

    application.run_polling()


if __name__ == "__main__":
    main()
