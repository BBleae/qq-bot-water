from nonebot import on_command, CommandSession
from nonebot import on_natural_language, NLPSession, IntentCommand
from nonebot import message_preprocessor

from bson import json_util
import pymongo
import plugins.watertop.config as config
import time
import datetime

# 今天日期
today = datetime.date.today


# 昨天时间
def yesterday(): return today() - datetime.timedelta(days=1)


# 明天时间
def tomorrow(): return today() + datetime.timedelta(days=1)


def acquire(): return today() + datetime.timedelta(days=2)


# 昨天开始时间戳
def yesterday_start_time(): return int(time.mktime(
    time.strptime(str(yesterday()), '%Y-%m-%d')))


# 昨天结束时间戳
def yesterday_end_time(): return int(time.mktime(
    time.strptime(str(today()), '%Y-%m-%d'))) - 1


# 今天开始时间戳
def today_start_time(): return int(time.mktime(
    time.strptime(str(datetime.date.today()), '%Y-%m-%d')))


# 今天结束时间戳
def today_end_time(): return int(time.mktime(
    time.strptime(str(tomorrow()), '%Y-%m-%d'))) - 1


# 明天开始时间戳
def tomorrow_start_time(): return int(time.mktime(
    time.strptime(str(tomorrow()), '%Y-%m-%d')))


# 明天结束时间戳
def tomorrow_end_time(): return int(time.mktime(
    time.strptime(str(acquire()), '%Y-%m-%d'))) - 1


cn_number = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']


def singleton(cls):
    _instance = {}

    def inner(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]
    return inner


@singleton
class MyMongoClient(pymongo.MongoClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


db = MyMongoClient(host=config.host, port=config.port)[
    config.db]


@message_preprocessor
async def funcname(bot, msg):
    if msg['self_id'] != msg['sender']['user_id'] and msg['sender']['user_id'] != 80000000 and msg['message_type'] == 'group':
        db.watertop.insert(msg)


@on_command('top', aliases=('watertop', '水群排行'), only_to_me=False)
async def top(session: CommandSession):
    if session.ctx['message_type'] == 'group':
        command = session.get('command', prompt='?')
        if command == 'today':
            today_query = {'$and': [
                {'time': {'$gte': today_start_time()}},
                {'time': {'$lte': today_end_time()}},
                {'group_id': session.ctx['group_id']}
            ]}
            today_sender = {}
            today_qqlist = []
            today_rank = []
            time_before = time.time()

            for x in db.watertop.find(today_query, {'_id': 0, 'sender': 1}):
                # print(x)
                if x['sender']['user_id'] in today_sender:
                    today_sender[x['sender']['user_id']] += 1
                else:
                    today_sender[x['sender']['user_id']] = 1

            for k in sorted(today_sender, key=today_sender.__getitem__, reverse=True):
                today_qqlist.append(k)
                if len(today_qqlist) >= 10:
                    break
            for i in range(len(today_qqlist)):
                try:
                    ranker = await session.bot.get_group_member_info(group_id=session.ctx['group_id'], user_id=today_qqlist[i])
                except CQHttpError:
                    try:
                        ranker = await session.bot.get_stranger_info(user_id=today_qqlist[i])
                        ranker['card'] = ranker['nickname']+'(已退群)'
                    except CQHttpError:
                        ranker = {'card': str(today_qqlist[i])+'(名称获取失败)'}
                today_rank.append(
                    f'第{cn_number[i]}名：{ranker["card"] if ranker["card"] != "" and "card" in ranker else ranker["nickname"]}---{today_sender[today_qqlist[i]]}条\n')
            water_report = f'你群今日水群排行\n{"".join(today_rank)}本次查询花费{str(time.time() - time_before)}秒\n你群单日最高记录:{"null"}---{"null"}条'

        elif command == 'help':
            water_report = 'top\n从机器人开始记录的第一条消息起开始计算\ntop today\n只显示今天发言排行\ntop myself\n查看自己当前在本群的排名和发言条数(从有记录开始)\ntop BaseOnMe\n以自己被机器人第一次记录的发言开始计算排名\ntop today-myself\n今日你的排名'
        elif command == 'myself':
            water_report = '你在本群排第114514名:共810条\n本次查询花费0.1145141919810893秒(该功能还未完成)'
        elif command == 'BaseOnMe':
            bom_start = 0
            for r in db.watertop.find({'sender':{'user_id':session.ctx['sender']['user_id']}},{'_id': 0, 'sender': 1}).limit(1).sort('time'):
                bom_start = r['time']
                break
            bom_query = {'$and': [
                {'time': {'$gte': bom_start}},
                {'group_id': session.ctx['group_id']}
            ]}
            bom_sender = {}
            bom_qqlist = []
            bom_rank = []
            time_before = time.time()

            for x in db.watertop.find(bom_query, {'_id': 0, 'sender': 1}):
                # print(x)
                if x['sender']['user_id'] in bom_sender:
                    bom_sender[x['sender']['user_id']] += 1
                else:
                    bom_sender[x['sender']['user_id']] = 1

            for k in sorted(bom_sender, key=bom_sender.__getitem__, reverse=True):
                bom_qqlist.append(k)
                if len(bom_qqlist) >= 10:
                    break
            for i in range(len(bom_qqlist)):
                try:
                    ranker = await session.bot.get_group_member_info(group_id=session.ctx['group_id'], user_id=bom_qqlist[i])
                except CQHttpError:
                    try:
                        ranker = await session.bot.get_stranger_info(user_id=bom_qqlist[i])
                        ranker['card'] = ranker['nickname']+'(已退群)'
                    except CQHttpError:
                        ranker = {'card': str(bom_qqlist[i])+'(名称获取失败)'}
                bom_rank.append(
                    f'第{cn_number[i]}名：{ranker["card"] if ranker["card"] != "" and "card" in ranker else ranker["nickname"]}---{bom_sender[bom_qqlist[i]]}条\n')
            water_report = f'在你第一次(有记录的)发言后本群的水群排名\n{"".join(bom_rank)}本次查询花费{str(time.time() - time_before)}秒'
            # water_report = '在你第一次(有记录的)发言后本群的水群排名\n第一名：新传奇---2936条\n第二名：1446300716(获取名称失败)---1876条\n第三名：Without乄---1125条\n第四名：H17---1096条\n第五名：没玩过东方正作的lhy12138---833条\n第六名：純華落夢---828条\n第七名：久遠澪---646条\n第八名：一个⑨君---600条\n第九名：xiaopanguX---593条\n第十名：花花---577条\n本次查询花费0.9567596912384033秒\n'
        elif command == 'today-myself':
            water_report = '你今天在本群排第114514名:共810条\n本次查询花费0.1145141919810893秒(该功能还未完成)'
        else:  # command == 'all'
            all_query = {'group_id': session.ctx['group_id']}
            all_sender = {}
            all_qqlist = []
            all_rank = []
            time_before = time.time()

            for x in db.watertop.find(all_query, {'_id': 0, 'sender': 1}):
                # print(x)
                if x['sender']['user_id'] in all_sender:
                    all_sender[x['sender']['user_id']] += 1
                else:
                    all_sender[x['sender']['user_id']] = 1

            for k in sorted(all_sender, key=all_sender.__getitem__, reverse=True):
                all_qqlist.append(k)
                if len(all_qqlist) >= 10:
                    break
            for i in range(len(all_qqlist)):
                try:
                    ranker = await session.bot.get_group_member_info(group_id=session.ctx['group_id'], user_id=all_qqlist[i])
                except CQHttpError:
                    try:
                        ranker = await session.bot.get_stranger_info(user_id=all_qqlist[i])
                        ranker['card'] = ranker['nickname']+'(已退群)'
                    except CQHttpError:
                        ranker = {'card': str(all_qqlist[i])+'(名称获取失败)'}
                all_rank.append(
                    f'第{cn_number[i]}名：{ranker["card"] if ranker["card"] != "" and "card" in ranker else ranker["nickname"]}---{all_sender[all_qqlist[i]]}条\n')
            water_report = f'你群水群排行\n{"".join(all_rank)}本次查询花费{str(time.time() - time_before)}秒\n使用top help可以获取top命令更多功能'

            # water_report = '你群水群排行\n第一名：新传奇---3946条\n第二名：Without乄---3453条\n第三名：xiaopanguX---3278条\n第四名：1446300716(获取名称失败)---2800条\n第五名：上瘾---1939条\n第六名：没玩过东方正作的lhy12138---1608条\n第七名：一个⑨君---1459条\n第八名：H17---1173条\n第九名：Floating Hill---1073条\n第十名：忘记的记忆---900条\n本次查询花费0.25286221504211426秒\n使用top help可以获取top命令更多功能\n'

        await session.bot.send_group_msg(group_id=session.ctx['group_id'], message=water_report)


@top.args_parser
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    # print(stripped_arg)

    if session.is_first_run:
        if stripped_arg == 'today' or stripped_arg == 'help' or stripped_arg == 'myself' or stripped_arg == 'BaseOnMe':
            session.state['command'] = stripped_arg
        else:
            session.state['command'] = 'all'
        return

    if not stripped_arg:
        session.state['command'] = 'all'

    session.state[session.current_key] = stripped_arg
