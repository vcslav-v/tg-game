from sqlalchemy import (Boolean, Column, Float, ForeignKey, Integer,
                        LargeBinary, Table, Text, DateTime)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

user_flags = Table(
    'user_flags',
    Base.metadata,
    Column('users_id', ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('flag_id', ForeignKey('flags.id', ondelete='CASCADE'), primary_key=True),
)

save_user_flags = Table(
    'save_user_flags',
    Base.metadata,
    Column(
        'save_user_datas_id',
        ForeignKey('save_user_datas.id', ondelete='CASCADE'),
        primary_key=True
    ),
    Column('flag_id', ForeignKey('flags.id', ondelete='CASCADE'), primary_key=True),
)

message_set_flags = Table(
    'message_set_flags',
    Base.metadata,
    Column('flag_id', ForeignKey('flags.id', ondelete='CASCADE'), primary_key=True),
    Column('message_id', ForeignKey('messages.id', ondelete='CASCADE'), primary_key=True),
)

message_rm_flags = Table(
    'message_rm_flags',
    Base.metadata,
    Column('flag_id', ForeignKey('flags.id', ondelete='CASCADE'), primary_key=True),
    Column('message_id', ForeignKey('messages.id', ondelete='CASCADE'), primary_key=True),
)

button_condition_flags_up = Table(
    'button_condition_flags_up',
    Base.metadata,
    Column('flag_id', ForeignKey('flags.id', ondelete='CASCADE'), primary_key=True),
    Column('button_id', ForeignKey('buttons.id', ondelete='CASCADE'), primary_key=True),
)

button_condition_flags_down = Table(
    'button_condition_flags_down',
    Base.metadata,
    Column('flag_id', ForeignKey('flags.id', ondelete='CASCADE'), primary_key=True),
    Column('button_id', ForeignKey('buttons.id', ondelete='CASCADE'), primary_key=True),
)

addition_text_up_flags = Table(
    'addition_text_up_flags',
    Base.metadata,
    Column('flag_id', ForeignKey('flags.id', ondelete='CASCADE'), primary_key=True),
    Column(
        'addition_text_id',
        ForeignKey('addition_texts.id', ondelete='CASCADE'),
        primary_key=True
    ),
)

addition_text_down_flags = Table(
    'addition_text_down_flags',
    Base.metadata,
    Column('flag_id', ForeignKey('flags.id', ondelete='CASCADE'), primary_key=True),
    Column(
        'addition_text_id',
        ForeignKey('addition_texts.id', ondelete='CASCADE'),
        primary_key=True
    ),
)


class User(Base):
    """Telegram users."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    telegram_id = Column(Text, unique=True)
    cur_message_link = Column(Text)
    num_referals = Column(Integer, default=0)
    is_blocked = Column(Boolean, default=False)
    flags = relationship(
        'Flag', secondary=user_flags, back_populates='users', cascade="all, delete",
    )
    save_user_data = relationship('SaveUserData', back_populates='user')


class SaveUserData(Base):
    """Telegram users."""
    __tablename__ = 'save_user_datas'
    id = Column(Integer, primary_key=True)
    message_link = Column(Text)
    flags = relationship(
        'Flag', secondary=save_user_flags, back_populates='save_user_datas', cascade="all, delete",
    )
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='save_user_data')
    date = Column(DateTime)


class Message(Base):
    """Story."""

    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    link = Column(Text, unique=True)
    start_of_chapter_name = Column(Text)
    start_msg = Column(Boolean, default=False)
    timeout = Column(Float, default=0.0)
    time_typing = Column(Float, default=4.0)
    content_type = Column(Text)
    message = Column(Text)
    addition_text = relationship('AdditionText', back_populates='message')

    media = relationship(
        'Media',
        uselist=False,
        back_populates='parrent_message',
        cascade='delete-orphan,delete',
        foreign_keys='[Media.parrent_message_link]',
    )
    next_msg = Column(Text, ForeignKey('messages.link'))
    buttons = relationship(
        'Button',
        back_populates='parrent_message',
        cascade='delete-orphan,delete',
        foreign_keys='[Button.parrent_message_link]',
    )
    wait_reaction_id = Column(Integer, ForeignKey('wait_reactions.id'))
    wait_reaction = relationship('WaitReaction')
    referal_block = Column(Integer, default=0)
    set_flags = relationship(
        'Flag', secondary=message_set_flags, back_populates='messages_set', cascade="all, delete"
    )
    rm_flags = relationship(
        'Flag', secondary=message_rm_flags, back_populates='messages_rem', cascade="all, delete"
    )


class AdditionText(Base):
    """Condition text for message"""
    __tablename__ = 'addition_texts'

    id = Column(Integer, primary_key=True)
    tag = Column(Text)
    text = Column(Text)
    up_flags = relationship(
        'Flag',
        secondary=addition_text_up_flags,
        back_populates='addition_text_up',
        cascade="all, delete",
    )
    down_flags = relationship(
        'Flag',
        secondary=addition_text_down_flags,
        back_populates='addition_text_down',
        cascade="all, delete",
    )
    message_id = Column(Integer, ForeignKey('messages.id'))
    message = relationship('Message', back_populates='addition_text')


class Button(Base):
    """Buttons."""

    __tablename__ = 'buttons'

    id = Column(Integer, primary_key=True)

    text = Column(Text, nullable=False)
    parrent_message_link = Column(
        Text,
        ForeignKey('messages.link'),
        nullable=False,
    )
    parrent_message = relationship(
        'Message',
        back_populates='buttons',
        foreign_keys=[parrent_message_link],
    )
    number = Column(Integer)

    next_message_link = Column(Text, ForeignKey('messages.link'))
    next_message = relationship(
        'Message',
        foreign_keys=[next_message_link],
    )

    up_flags = relationship(
        'Flag',
        secondary=button_condition_flags_up,
        back_populates='buttons_up',
        cascade="all, delete",
    )

    down_flags = relationship(
        'Flag',
        secondary=button_condition_flags_down,
        back_populates='buttons_down',
        cascade="all, delete",
    )


class Media(Base):
    """Media."""

    __tablename__ = 'media'

    id = Column(Integer, primary_key=True)

    file_data = Column(LargeBinary, nullable=False)
    tg_id = Column(Text)
    parrent_message_link = Column(
        Text,
        ForeignKey('messages.link'),
        nullable=False,
    )
    parrent_message = relationship(
        'Message',
        back_populates='media',
        foreign_keys=[parrent_message_link]
    )


class WaitReaction(Base):
    """Wait reactions."""

    __tablename__ = 'wait_reactions'

    id = Column(Integer, primary_key=True)

    name = Column(Text)

    reactions = relationship(
        'Reaction',
        back_populates='wait_reaction',
        cascade='delete-orphan,delete',
    )


class Reaction(Base):
    """Reactions."""

    __tablename__ = 'reactions'

    id = Column(Integer, primary_key=True)

    text = Column(Text)

    wait_reaction_id = Column(
        Integer,
        ForeignKey('wait_reactions.id'),
    )

    wait_reaction = relationship(
        'WaitReaction',
        back_populates='reactions',
        passive_deletes=True,
    )


class Flag(Base):
    """Flags."""

    __tablename__ = 'flags'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    users = relationship('User', secondary=user_flags, back_populates='flags', passive_deletes=True)
    messages_set = relationship(
        'Message',
        secondary=message_set_flags,
        back_populates='set_flags',
        passive_deletes=True,
    )
    messages_rem = relationship(
        'Message',
        secondary=message_rm_flags,
        back_populates='rm_flags',
        passive_deletes=True
    )
    buttons_up = relationship(
        'Button',
        secondary=button_condition_flags_up,
        back_populates='up_flags',
        passive_deletes=True,
    )
    buttons_down = relationship(
        'Button',
        secondary=button_condition_flags_down,
        back_populates='down_flags',
        passive_deletes=True,
    )
    save_user_datas = relationship(
        'SaveUserData',
        secondary=save_user_flags,
        back_populates='flags',
        passive_deletes=True,
    )
    addition_text_up = relationship(
        'AdditionText',
        secondary=addition_text_up_flags,
        back_populates='up_flags',
        passive_deletes=True,
    )

    addition_text_down = relationship(
        'AdditionText',
        secondary=addition_text_down_flags,
        back_populates='down_flags',
        passive_deletes=True,
    )
