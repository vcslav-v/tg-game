from pydantic import BaseModel
from typing import Optional


class Button(BaseModel):
    text: str
    number: int
    next_message_link: str


class Message(BaseModel):
    link: str
    content_type: str = 'text'
    time_typing: float
    timeout: float
    start_of_chapter_name: Optional[str]
    text: Optional[str]
    media_id: Optional[int]
    next_msg: Optional[str]
    buttons: Optional[list[Button]] = []
    wait_reaction: Optional[list[str]]
    referal_block: Optional[int]


class WaitReactions(BaseModel):
    name: str
    uid: str
    messages: list[str]


class UserContext(BaseModel):
    next_message: Optional[Message]
