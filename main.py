#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from threading import Thread
from random import randint, choice, shuffle
from time import time, sleep
import telebot
import saver as SV


TELEBOT_TOKEN = open('tg.tkn').read()
print(TELEBOT_TOKEN)
TeleBot = telebot.TeleBot(TELEBOT_TOKEN)
ADMIN_ID = [150486866]

USERS = {}
ROOMS = {}
EVENTS = set()

HELP = open('help.txt', 'r').read()

OK = '✅'
CROSS = '❌'
STAR = '⭐️'
BAN = '🛑'


T_EASY ="легко" + OK
T_MEDI ="средне" + OK
T_HARD ="сложно" + OK
F_EASY ="легко" + CROSS
F_MEDI ="средне" + CROSS
F_HARD ="сложно" + CROSS

ANS_MARKUP = telebot.types.ReplyKeyboardMarkup()
t_easy = telebot.types.KeyboardButton(text=T_EASY)
t_medi = telebot.types.KeyboardButton(text=T_MEDI)
t_hard = telebot.types.KeyboardButton(text=T_HARD)
f_easy = telebot.types.KeyboardButton(text=F_EASY)
f_medi = telebot.types.KeyboardButton(text=F_MEDI)
f_hard = telebot.types.KeyboardButton(text=F_HARD)
ANS_MARKUP.row(t_easy, t_medi, t_hard)
ANS_MARKUP.row(f_easy, f_medi, f_hard)

OK_MARKUP = telebot.types.ReplyKeyboardMarkup()
OK_MARKUP.row(OK)

OKAY_MARKUP = telebot.types.ReplyKeyboardMarkup()
OKAY_MARKUP.row(BAN, STAR)
OKAY_MARKUP.row(OK)

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

        self.words = [[], WORDS[::], []]
        self.words[0] = []
        self.words[1] = WORDS[::]
        self.words[2] = []
        self.stats = {}

        self.last_word = ''
        self.favourite = []
        self.prohibited = []

    def set_name(self, name):
        self.name = name
        return 'Имя успешно изменено на ' + name

    def send_msg(self, message, markup=None):
        if markup:
            TeleBot.send_message(self.tg_id, message, reply_markup=markup, parse_mode="Markdown")
        else:
            TeleBot.send_message(self.tg_id, message, parse_mode="Markdown")

    def del_word(self, word):
        for i in range(len(self.words)):
            if word in self.words[i]:
                self.words[i].remove(word)

    def to_easy(self, word):
        self.del_word(word)
        self.words[0].append(word)

    def to_medi(self, word):
        self.del_word(word)
        self.words[1].append(word)

    def to_hard(self, word):
        self.del_word(word)
        self.words[2].append(word)

    def to_lvl(self, word, level):
        if level == 'easy' or level == 0:
            self.to_easy(word)
        if level == 'medi' or level == 1:
            self.to_medi(word)
        if level == 'hard' or level == 2:
            self.to_hard(word)

    def get_word(self):
        x = randint(1, 10)
        word = 'error'
        if x < 2:
            level_prior = [self.words[0], self.words[1], self.words[2]]
        elif x < 8:
            level_prior = [self.words[2], self.words[1], self.words[0]]
        else:
            level_prior = [self.words[1], self.words[0], self.words[2]]

        for level in level_prior:
            if level:
                word = choice(level)
                break

        self.last_word = word
        return word.lower().replace('ё', 'е')

    def to_favourite(self, word):
        if word in self.favourite:
            self.favourite.remove(word)
            return 'удалено из избранных'
        else:
            self.favourite.append(word)
            return 'добавлено в избранные'

    def to_prohibited(self, word):
        if word in self.prohibited:
            self.prohibited.remove(word)
            self.words[1].append(word)
            return 'удалено из запрещённых'
        else:
            self.prohibited.append(word)
            self.del_word(word)
            return 'добавлено в запрещённые'

    def get_favourite(self):
        return 'Ваши избранные слова:\n' + '\n'.join(self.favourite)

    def get_prohibited(self):
        return 'Ваши запрещённые слова:\n' + '\n'.join(self.prohibited)

    def reset(self):
        self.words[1] = self.words[0] + self.words[1] + self.words[2]
        self.stats = {}
        return 'Статистика успешно сброшена'

    def get_stats(self, cnt=10):
        stats = []
        max_len = 0
        for word in self.stats:
            st = self.stats[word]
            stats.append([word, st[0], st[1], st[2]])
            max_len = max(max_len, len(word))
        stats.sort(key=lambda x: x[2], reverse=True)
        stats = stats[:cnt]
        for i in range(len(stats)):
            stats[i][-1] = {0: 'легко', 1 : 'средне', 2 : 'сложно'}[stats[i][-1]]
            word = stats[i][0]
            stats[i][0] = '`' + word + ' ' * (max_len - len(word)) + '`'
            stats[i] = ' | '.join(map(str, stats[i]))
        ret = '\n'.join(stats)
        if not ret:
            ret = 'Никакой статистики!'
        return ret

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
        TeleBot.send_message(chat.id, 'Привет! Прочти инструкцию: /help')
        USERS[chat.id] = User(chat.id, chat.first_name)

        user = USERS[chat.id]
        word = user.get_word()
        user.send_msg(word, OKAY_MARKUP)

    if text == '/help':
        ret = HELP
        user.send_msg(ret)

    if text == '/word':
        word = user.get_word()
        user.send_msg(word, OKAY_MARKUP)

    if text == OK:
        user.send_msg(user.last_word, ANS_MARKUP)

    if text == STAR:
        ret = user.to_favourite(user.last_word)
        user.send_msg(user.last_word + ' | ' + ret, ANS_MARKUP)

    if text == BAN:
        ret = user.to_prohibited(user.last_word)
        user.send_msg(user.last_word + ' | ' + ret, ANS_MARKUP)

    if text.startswith('/fav_'):
        word = text[5:]
        user.to_favourite(word)
        ret = word + ' | добавлено в запрещённые'
        user.send_msg(ret, OK_MARKUP)

    if text.startswith('/ban_'):
        word = text[5:]
        ret = word + ' | ' + user.to_prohibited(word)
        user.send_msg(ret, OK_MARKUP)

    if text.startswith('/favs'):
        ret = user.get_favourite()
        user.send_msg(ret, OK_MARKUP)

    if text.startswith('/bans'):
        ret = user.get_prohibited()
        user.send_msg(ret, OK_MARKUP)

    if text in [T_EASY, T_MEDI, T_HARD, F_EASY, F_MEDI, F_HARD]:
        mistake = text[-1] == CROSS
        level = {'легко' : 0, 'средне' : 1, 'сложно' : 2}
        word = user.last_word
        user.to_lvl(word, level)
        if not word in user.stats:
            user.stats[word] = [0, 0, 1]
        user.stats[word][mistake] += 1
        user.stats[word][2] = level[''.join(text[:-1])]

        word = user.get_word()
        user.send_msg(word, OKAY_MARKUP)

    if text.startswith('/setname'):
        args = get_args(text, len('/setname') + 1)
        name = args[0]
        ret = user.set_name(name)
        user.send_msg(ret)

    if text == '/stats':
        ret = user.get_stats()
        user.send_msg(ret)

    if text == '/reset':
        ret = user.reset()
        user.send_msg(ret)

    if text.startswith('/admin_'):
        if text[7:] == TELEBOT_TOKEN:
            ADMIN_ID.append(user.tg_id)

    if text in ['/save_state', '/load_state']:
        if user.tg_id in ADMIN_ID:
            ret = admin_command(text)
        else:
            ret = 'Вы не являетесь админом'
        user.send_msg(ret)

    if text.startswith('/tell'):
        if user.tg_id in ADMIN_ID:
            text = text[6:]
            for usr_id in USERS:
                USERS[usr_id].send_msg(text)


def admin_command(command, args=[]):
    global SAVER
    global USERS
    global ROOMS
    global EVENTS

    if command == '/save_state':
        SAVER.save()
        return 'Состояние от \[{}] успешно сохранено'.format(SAVER.last_save_datetime)
    elif command == '/load_state':
        SAVER = SAVER.load()
        USERS, ROOMS, EVENTS = SAVER.data
        return 'Состояние от \[{}] успешно загружено'.format(SAVER.last_save_datetime)


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
    global EVENTS
    global SAVER
    ROOMS = {}
    USERS = {}
    global WORDS
    WORDS = []
    words = open('words.txt').read().splitlines()
    for word in words:
        if word and not word[0] == '#':
            WORDS.append(word)
    print('Le go')
    event_check_thread.start()

    SAVER = SV.Saver([USERS, ROOMS, EVENTS], 30)
    SAVER = SAVER.load()
    USERS, ROOMS, EVENTS = SAVER.data
    SAVER.start()

    TeleBot.polling(interval=0.3)

if __name__ == "__main__":
    main()