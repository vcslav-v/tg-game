from pydantic import BaseModel
from typing import Optional
from typing import Union


class Button(BaseModel):
    text: str
    number: int
    next_message_link: str


class Var(BaseModel):
    name: str
    value: Union[bool, int, str]


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
    set_flags: Optional[set]
    rm_flags: Optional[set]


class WaitReactions(BaseModel):
    name: str
    uid: str
    messages: list[str]


class UserContext(BaseModel):
    next_message: Optional[Message]
    flags: set[str] = set()


class SaveUserData(BaseModel):
    chapter_name: str
    flags: set[str] = set()
