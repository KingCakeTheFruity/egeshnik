#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from threading import Thread
from random import randint, choice, shuffle
from time import time, sleep
import telebot


TELEBOT_TOKEN = open('tg.tkn').read()
TeleBot = telebot.TeleBot(TELEBOT_TOKEN)
ADMIN_ID = [150486866]

USERS = {}
ROOMS = {}
EVENTS = set()

HELP = open('help.txt', 'r').read()


class Event:
    def __init__(self, init_time, length, target, *args):
        self.init_time = init_time
        self.end_time = init_time + length
        self.target = target
        self.args = args

    def check(self, cur_time):
        if cur_time > self.end_time:
            self.target(*self.args)
            return True
        else:
            return False


class Room:
    def __init__(self, room_id, round_time, bonus_time, admin):
        self.id = room_id
        self.admin = admin
        self.users = []

    def add_player(self, player):
        self.users.append(player)

    def send_msg(self, message):
        for user in self.users:
            user.send_msg(message)


class User:
    def __init__(self, telegram_id, name):
        self.tg_id = telegram_id
        self.name = name
        self.room = None

    def set_name(self, name):
        self.name = name
        return 'Имя успешно изменено на ' + name

    def join_room(self, room_id):
        room = room_by_id(room_id)
        if not room:
            return 'Такой комнаты не существует'
        else:
            if self in room.users:
                return 'Вы уже находитесь в этой комнате'
            else:
                self.leave_room()
                room.users.append(self)
                self.room = room
                return 'Вы успешно присоединились к комнате'

    def leave_room(self):
        if not self.room:
            return 'Чтобы покинуть комнату, в нее вначале надо зайти'
        else:
            room = self.room
            if self in room.users:
                del room.users[room.users.index(self)]
            self.room = None
            return 'Вы успешно покинули комнату {}'.format(room.id)

    def send_msg(self, message):
        TeleBot.send_message(self.tg_id, message)


def user_by_id(user_id):
    if user_id in USERS:
        return USERS[user_id]
    else:
        return None


def room_by_id(room_id):
    if room_id in ROOMS:
        return ROOMS[room_id]
    else:
        return None


# -----------------------------------------------------------------------------
def get_args(text, command_len, sep='_'):
    return text[command_len:].split(sep)

def polish_args(args, requirements):
    ret = args[::]
    if len(args) != len(requirements):
        return None
    try:
        for i in range(len(args)):
            ret[i] = type(requirements[i])(ret[i])
    except Exception:
        return None
    return ret


def warn_invalid_args(chat_id):
    TeleBot.send_message(chat_id, 'Некоректные аргументы. /commands_help для помощи')
# -----------------------------------------------------------------------------


@TeleBot.message_handler(func=lambda x: True)
def message_handler(message):
    chat = message.chat
    text = message.text
    user = user_by_id(chat.id)
    print('Got message from {}: {}'.format(chat.first_name, text))

    if user is None and text != '/start':
        TeleBot.send_message(chat.id, 'Напишите мне, пожалуйста, /start, чтобы я добавил вас в список пользователей')
        return

    if text == '/start':
        TeleBot.send_message(chat.id, 'Привет! Помощь по командам доступна по /help')
        USERS[chat.id] = User(chat.id, chat.first_name)

    if text == '/help':
        ret = HELP
        user.send_msg(ret)

    if text.startswith('/setname'):
        args = get_args(text, len('/setname') + 1)
        name = args[0]
        ret = user.set_name(name)
        user.send_msg(ret)

    if text.startswith('/join'):
        args = get_args(text, len('/join') + 1)
        args = polish_args(args, [''])
        if not args:
            warn_invalid_args(user.tg_id)
            return

        room_id = args[0]
        ret = user.join_room(room_id)
        user.send_msg(ret)

    if text == '/leave':
        ret = user.leave_room()
        user.send_msg(ret)

    if text == '/text':
        pass

    if text.startswith('/some_text'):
        pass


def event_check():
    while True:
        t = time()
        events_to_delete = []
        for event in EVENTS:
            if event.check(t):
                events_to_delete.append(event)
        for event in events_to_delete:
            EVENTS.remove(event)

        sleep(0.1)


event_check_thread = Thread(target=event_check)


def main():
    global ROOMS
    global USERS
    ROOMS = {}
    USERS = {}
    print('Le go')
    event_check_thread.start()
    TeleBot.polling(interval=0.5)


if __name__ == "__main__":
    main()