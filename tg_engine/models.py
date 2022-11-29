from sqlalchemy import (Boolean, Column, Float, ForeignKey, Integer,
                        LargeBinary, Table, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

user_flags = Table(
    'user_flags',
    Base.metadata,
    Column('users_id', ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
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

button_condition_flags = Table(
    'button_condition_flags',
    Base.metadata,
    Column('flag_id', ForeignKey('flags.id', ondelete='CASCADE'), primary_key=True),
    Column('button_id', ForeignKey('buttons.id', ondelete='CASCADE'), primary_key=True),
)


class User(Base):
    """Telegram users."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    telegram_id = Column(Text, unique=True)
    cur_message_link = Column(Text)
    num_referals = Column(Integer, default=0)
    chapter_message_links = Column(Text, default='{}')
    flags = relationship(
        'Flag', secondary=user_flags, back_populates='users', cascade="all, delete",
    )


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

    condition_flags = relationship(
        'Flag', secondary=button_condition_flags, back_populates='buttons', cascade="all, delete",
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
    buttons = relationship(
        'Button',
        secondary=button_condition_flags,
        back_populates='condition_flags',
        passive_deletes=True,
    )
