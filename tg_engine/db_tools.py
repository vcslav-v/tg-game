import json
import os
import re
from typing import Union
from zipfile import ZipFile
from bs4 import BeautifulSoup

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
    with zip_value.open('story.html') as story_file:
        story_soup = BeautifulSoup(story_file, 'lxml')
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

    for passagedata in story_soup.body.find('tw-storydata').find_all('tw-passagedata'):
        new_msg = models.Message(link=passagedata.attrs['name'])
        session.add(new_msg)
        session.commit()

    for passagedata in story_soup.body.find('tw-storydata').find_all('tw-passagedata'):
        db_msg = session.query(models.Message).filter_by(link=passagedata.attrs['name']).first()
        db_msg.content_type = 'text'
        passage_vars = re.findall(r'(\(set: )(.*)( to )(.*)(\))', passagedata.text)
        push_msg = False
        text = re.sub(
            r'(\(set:.*?\(dm:.*?\)\))|(\(set:.*?\)|(\[\[.*?\]\])|(\\n))',
            '',
            passagedata.text
        ).strip()
        if text:
            db_msg.message = text
        for p_var in passage_vars:
            field, value = p_var[1], p_var[3]
            if field == '_media':
                iter_data = zip(
                    re.findall(r'(\(dm:)(.*)(\))', value)[0][1].split(',')[::2],
                    re.findall(r'(\(dm:)(.*)(\))', value)[0][1].split(',')[1::2]
                )
                m_data = {}
                for m_key, m_value in iter_data:
                    _value = m_value.strip('"\'\\/')
                    m_data[m_key.strip('"')] = int(_value) if _value.isdigit() else _value
                db_msg.content_type = m_data['media_type']
                with zip_value.open(os.path.join('media', m_data['file']), 'r') as media_file:
                    new_media = models.Media(
                        file_data=media_file.read(),
                        parrent_message=db_msg,
                    )
                    session.add(new_media)
                if m_data.get('caption'):
                    db_msg.message = m_data.get('caption')
            elif field == '_start_chapter':
                _value = value.strip('"\'\\/')
                db_msg.start_of_chapter_name = _value
            elif field == '_push_next' and value.strip('"\'\\/') == 'true':
                push_link = re.search(r'(\[\[)([^|]*?)(\]\])', passagedata.text)
                if push_link:
                    push_msg = True
                    db_msg.next_msg = push_link.group(2)
            elif field == '_referal_block':
                _value = int(value.strip('"\'\\/'))
                db_msg.referal_block = _value
            elif field == '_wait_reaction':
                _value = value.strip('"\'\\/')
                db_wait_reaction = session.query(
                    models.WaitReaction
                ).filter_by(name=_value).first()
                if db_wait_reaction:
                    db_msg.wait_reaction = db_wait_reaction
            elif field == '_timeout':
                _value = float(value.strip('"\'\\/'))
                db_msg.timeout = _value
            elif field == '_time_typing':
                _value = float(value.strip('"\'\\/'))
                db_msg.time_typing = _value

        if not push_msg:
            but_num = 0
            for button_data in re.findall(r'(\[\[)(.*?)(\]\])', passagedata.text):
                raw_button = button_data[1]
                button_text, *button_link = raw_button.split('|')
                if button_link:
                    button_link = button_link[0]
                else:
                    button_link = button_text
                new_button = models.Button(
                    text=button_text,
                    parrent_message=db_msg,
                    number=but_num,
                    next_message_link=button_link
                )
                session.add(new_button)
                but_num += 1

        if not db_msg.wait_reaction:
            db_wait_reaction = session.query(models.WaitReaction).filter_by(name='std').first()
            db_msg.wait_reaction = db_wait_reaction
        session.commit()

    start_node_pid = story_soup.body.find('tw-storydata').attrs['startnode']
    start_node_name = story_soup.body.find('tw-storydata').find(
        'tw-passagedata',
        attrs={'pid': start_node_pid}
    ).attrs['name']
    db_start_msg = session.query(models.Message).filter_by(link=start_node_name).first()
    db_start_msg.start_msg = True
    session.commit()
    zip_value.close()
