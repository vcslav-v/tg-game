import json
import os
import re
from typing import Union
from zipfile import ZipFile

from tg_engine import db, models, schemas


async def is_user_exist(tg_id: int):
    with db.SessionLocal() as session:
        return bool(
            session.query(models.User).filter_by(telegram_id=tg_id).count()
        )


async def add_user(tg_id: int, parent_tg_id: Union[int, None] = None):
    with db.SessionLocal() as session:
        user = models.User(telegram_id=tg_id)
        session.add(user)
        if parent_tg_id:
            db_parent = session.query(models.User).filter_by(telegram_id=parent_tg_id).first()
            if db_parent:
                db_parent.num_referals += 1

        session.commit()


async def get_cur_message_link(tg_id: int):
    with db.SessionLocal() as session:
        db_user = session.query(models.User).filter_by(telegram_id=tg_id).first()
        return db_user.cur_message_link


async def get_num_referals(tg_id: int) -> int:
    with db.SessionLocal() as session:
        db_user = session.query(models.User).filter_by(telegram_id=tg_id).first()
        return db_user.num_referals


async def get_message(message_link: str) -> schemas.Message:
    with db.SessionLocal() as session:
        db_message = session.query(models.Message).filter_by(link=message_link).first()
        if not db_message:
            db_message = session.query(models.Message).filter_by(start_msg=True).first()
        buttons = []
        for button in db_message.buttons:
            buttons.append(schemas.Button(
                text=button.text,
                number=button.number,
                next_message_link=button.next_message_link
            ))
        message = schemas.Message(
            link=db_message.link,
            content_type=db_message.content_type,
            time_typing=db_message.time_typing,
            start_of_chapter_name=db_message.start_of_chapter_name,
            timeout=db_message.timeout,
            text=db_message.message,
            media_id=db_message.media.id if db_message.media else None,
            next_msg=db_message.next_msg,
            buttons=buttons,
            wait_reaction=[
                react.text for react in db_message.wait_reaction.reactions
            ] if db_message.wait_reaction else None,
            referal_block=db_message.referal_block,
        )
    return message


async def set_cur_message(tg_id: int, msg_link: str, chapter_start: bool = False) -> None:
    with db.SessionLocal() as session:
        db_user = session.query(models.User).filter_by(telegram_id=tg_id).first()
        db_user.cur_message_link = msg_link
        if chapter_start:
            if db_user.chapter_message_links and msg_link not in db_user.chapter_message_links:
                db_user.chapter_message_links += f'|{msg_link}'
            elif not db_user.chapter_message_links:
                db_user.chapter_message_links = msg_link
        session.commit()


async def get_tg_id_media(media_id: int) -> Union[str, None]:
    with db.SessionLocal() as session:
        db_media = session.query(models.Media).filter_by(id=media_id).first()
        return db_media.tg_id


async def get_media(media_id: int) -> bytes:
    with db.SessionLocal() as session:
        db_media = session.query(models.Media).filter_by(id=media_id).first()
        return db_media.file_data


async def update_media_tg_id(media_id: int, media_tg_id: str) -> None:
    with db.SessionLocal() as session:
        db_media = session.query(models.Media).filter_by(id=media_id).first()
        db_media.tg_id = media_tg_id
        session.commit()


async def get_started_chapters(tg_id: int) -> list[tuple[str]]:
    started_chapters = []
    with db.SessionLocal() as session:
        db_user = session.query(models.User).filter_by(telegram_id=tg_id).first()
        if db_user.chapter_message_links:
            for message_link in db_user.chapter_message_links.split('|'):
                db_message = session.query(models.Message).filter_by(link=message_link).first()
                if not db_message or not db_message.start_of_chapter_name:
                    continue
                started_chapters.append(
                    (db_message.start_of_chapter_name, db_message.link)
                )
    return started_chapters


async def add_story(zip_file):
    zip_value = ZipFile(zip_file)
    with zip_value.open('story.json') as story_file:
        story = json.loads(story_file.read())
    with zip_value.open('reactions.json') as reactions_file:
        wait_reactions = json.loads(reactions_file.read())
    with db.SessionLocal() as session:
        session.query(models.Button).delete()
        session.query(models.Media).delete()
        session.query(models.Reaction).delete()
        session.commit()
        session.query(models.Message).delete()
        session.query(models.WaitReaction).delete()
        session.commit()

    for name_react, reactions in wait_reactions.items():
        db_wait_reactions = models.WaitReaction(name=name_react)
        session.add(db_wait_reactions)
        for reaction in reactions:
            db_reaction = models.Reaction(text=reaction)
            session.add(db_reaction)
            db_wait_reactions.reactions.append(db_reaction)
    session.commit()

    for link in story['data']['stitches'].keys():
        new_msg = models.Message(link=link)
        session.add(new_msg)
        session.commit()

    for link, message in story['data']['stitches'].items():
        db_msg = session.query(models.Message).filter_by(link=link).first()
        text, *options = message['content']
        if re.match(r'^\[.*\]$', text.strip()):
            msg_info = text.strip('[] ').split(',')
            msg_info = list(map(lambda x: x.strip().split('='), msg_info))
            for field, value in msg_info:
                value = value.strip('\"\'')
                if field == 'photo':
                    db_msg.content_type = field
                    with zip_value.open(os.path.join('media', value), 'r') as media_file:
                        new_media = models.Media(
                            file_data=media_file.read(),
                            parrent_message=db_msg,
                        )
                        session.add(new_media)
                elif field == 'voice':
                    db_msg.content_type = field
                    with zip_value.open(os.path.join('media', value), 'r') as media_file:
                        new_media = models.Media(
                            file_data=media_file.read(),
                            parrent_message=db_msg,
                        )
                        session.add(new_media)
                elif field == 'cap':
                    db_msg.message = value
        else:
            db_msg.message = text
            db_msg.content_type = 'text'
        but_num = 0
        for option in options:
            next_msg_link = option.get('divert')
            button_text = option.get('option')
            marker = option.get('flagName')
            chapter_name = option.get('pageLabel')
            if chapter_name:
                db_msg.start_of_chapter_name = chapter_name
            if next_msg_link:
                db_msg.next_msg = next_msg_link
            elif button_text:
                new_button = models.Button(
                    text=button_text,
                    parrent_message=db_msg,
                    number=but_num,
                    next_message_link=option['linkPath']
                )
                session.add(new_button)
                but_num += 1
            if marker and re.match(r'.+=.+', marker.strip()):
                field, value = map(lambda x: x.strip('\'\" '), marker.strip().split('='))
                if field == 'referal_block':
                    db_msg.referal_block = int(value)
                elif field == 'wait_reaction':
                    db_wait_reaction = session.query(
                        models.WaitReaction
                    ).filter_by(name=value).first()
                    if db_wait_reaction:
                        db_msg.wait_reaction = db_wait_reaction
                elif field == 'timeout':
                    db_msg.timeout = float(value)
                elif field == 'time_typing':
                    db_msg.time_typing = float(value)
            elif marker:
                # TODO markers
                pass

        if not db_msg.wait_reaction:
            db_wait_reaction = session.query(models.WaitReaction).filter_by(name='std').first()
            db_msg.wait_reaction = db_wait_reaction
        session.commit()

    db_start_msg = session.query(models.Message).filter_by(link=story['data']['initial']).first()
    db_start_msg.start_msg = True
    session.commit()
    zip_value.close()
