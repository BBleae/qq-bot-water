from nonebot import on_command, CommandSession
from nonebot import on_natural_language, NLPSession, IntentCommand
from nonebot import message_preprocessor
from nonebot import CQHttpError
from nonebot.log import logger

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

@singleton
class Grass(object):
    def __init__(self, *args, **kwargs):
        self.last_grass = {}
        super().__init__(*args, **kwargs)

    async def send_grass(self, bot, group):
        if group not in self.last_grass or time.time() - self.last_grass[group] > config.grass_delay:
            try:
                await bot.send_group_msg(group_id=group,message='草')
            except CQHttpError as e:
                logger.exception(e.retcode)
            self.last_grass[group] = time.time()
            

@message_preprocessor
async def funcname(bot, msg):
    if msg['self_id'] != msg['sender']['user_id'] and msg['sender']['user_id'] not in config.ignore_list and msg['message_type'] == 'group':
        db.watertop.insert(msg)
        if msg['raw_message'] == '草':
            grass = Grass()
            await grass.send_grass(bot, msg['group_id'])


@on_command('top', aliases=('watertop', '水群排行'), only_to_me=False)
async def top(session: CommandSession):
    if session.ctx['message_type'] == 'group':
        command = session.get('command', prompt='?')
        
        if command == 'today':
            time_before = time.time()
            today_query = {'$and': [
                {'time': {'$gte': today_start_time()}},
                {'group_id': session.ctx['group_id']}
            ]}
            today_sender = {}
            today_qqlist = []
            today_rank = []

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
                except CQHttpError as eo:
                    logger.exception(eo)
                    try:
                        ranker = await session.bot.get_stranger_info(user_id=today_qqlist[i])
                        ranker['card'] = ranker['nickname']+'(已退群)'
                    except CQHttpError as e:
                        logger.exception(e)
                        ranker = {'card': str(today_qqlist[i])+'(名称获取失败)'}
                today_rank.append(
                    f'第{cn_number[i]}名：{ranker["card"] if ranker["card"] != "" and "card" in ranker else ranker["nickname"]}---{today_sender[today_qqlist[i]]}条\n')
            water_report = f'你群今日水群排行\n{"".join(today_rank)}本次查询花费{str(time.time() - time_before)}秒'

        
        elif command == 'help':
            water_report = 'top\n从机器人开始记录的第一条消息起开始计算\ntop today\n只显示今天发言排行\ntop myself\n查看自己当前在本群的排名和发言条数(从有记录开始)\ntop BaseOnMe\n以自己被机器人第一次记录的发言开始计算排名\ntop today-myself\n今日你的排名'

        
        elif command == 'myself':
            time_before = time.time()
            self_query = {'group_id': session.ctx['group_id']}
            self_sender = {}
            self_qqlist = []
            self_rank = []

            for x in db.watertop.find(self_query, {'_id': 0, 'sender': 1}):
                # print(x)
                if x['sender']['user_id'] in self_sender:
                    self_sender[x['sender']['user_id']] += 1
                else:
                    self_sender[x['sender']['user_id']] = 1

            for k in sorted(self_sender, key=self_sender.__getitem__, reverse=True):
                self_qqlist.append(k)
                if k == session.ctx['sender']['user_id']:
                    break
            if self_qqlist[-1] == session.ctx['sender']['user_id']:

                try:
                    ranker = await session.bot.get_group_member_info(group_id=session.ctx['group_id'], user_id=session.ctx['sender']['user_id'])
                except CQHttpError:
                    try:
                        ranker = await session.bot.get_stranger_info(user_id=session.ctx['sender']['user_id'])
                        ranker['card'] = ranker['nickname']
                    except CQHttpError:
                        ranker = {'card': str(self_qqlist[i])+'(名称获取失败)'}
                water_report = f"你在本群排第{str(len(self_qqlist))}名:共{self_sender[session.ctx['sender']['user_id']]}条\n本次查询花费{str(time.time() - time_before)}秒"
            else:
                water_report = '你已被加入bot忽略名单'
        
        
        elif command == 'BaseOnMe':
            time_before = time.time()
            bom_start = 0
            for r in db.watertop.find({'sender': {'user_id': session.ctx['sender']['user_id']}}, {'_id': 0, 'sender': 1}).limit(1).sort('time'):
                bom_start = r['time']
                break
            bom_query = {'$and': [
                {'time': {'$gte': bom_start}},
                {'group_id': session.ctx['group_id']}
            ]}
            bom_sender = {}
            bom_qqlist = []
            bom_rank = []
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

        
        elif command == 'today-myself':
            time_before = time.time()
            today_self_query = {'$and': [
                {'time': {'$gte': today_start_time()}},
                {'group_id': session.ctx['group_id']}
            ]}
            today_self_sender = {}
            today_self_qqlist = []
            today_self_rank = []

            for x in db.watertop.find(today_self_query, {'_id': 0, 'sender': 1}):
                # print(x)
                if x['sender']['user_id'] in today_self_sender:
                    today_self_sender[x['sender']['user_id']] += 1
                else:
                    today_self_sender[x['sender']['user_id']] = 1

            for k in sorted(today_self_sender, key=today_self_sender.__getitem__, reverse=True):
                today_self_qqlist.append(k)
                if k == session.ctx['sender']['user_id']:
                    break
            try:
                ranker = await session.bot.get_group_member_info(group_id=session.ctx['group_id'], user_id=session.ctx['sender']['user_id'])
            except CQHttpError:
                try:
                    ranker = await session.bot.get_stranger_info(user_id=session.ctx['sender']['user_id'])
                    ranker['card'] = ranker['nickname']
                except CQHttpError:
                    ranker = {'card': str(today_self_qqlist[i])+'(名称获取失败)'}
            water_report = f"你今天在本群排第{str(len(today_self_qqlist))}名:共{today_self_sender[session.ctx['sender']['user_id']]}条\n本次查询花费{str(time.time() - time_before)}秒"

        
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
        
        
        await session.bot.send_group_msg(group_id=session.ctx['group_id'], message=water_report)


@top.args_parser
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    # print(stripped_arg)

    if session.is_first_run:
        if stripped_arg == 'today' or stripped_arg == 'help' or stripped_arg == 'myself' or stripped_arg == 'BaseOnMe' or stripped_arg == 'today-myself':
            session.state['command'] = stripped_arg
        else:
            session.state['command'] = 'all'
        return

    if not stripped_arg:
        session.state['command'] = 'all'

    session.state[session.current_key] = stripped_arg
