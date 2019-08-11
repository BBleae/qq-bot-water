import time
import datetime
import pymongo
import config

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


db = pymongo.MongoClient(host=config.host, port=config.port)[
    config.db]

daytop_query = {
    '$and': {
        'time':{'$gte': yesterday_start_time()},
        'time':{'$lte': yesterday_end_time()}
    }
}
daymap = {}
for msg in db.watertop.find(daytop_query,{'_id':0,'sender':1,'group_id':1}):
    if msg['group_id'] in daymap:
        if msg['sender']['user_id'] in daymap[msg['group_id']]:
            daymap[msg['group_id']][msg['sender']['user_id']]+=1
        else:
            daymap[msg['group_id']][msg['sender']['user_id']]=1
    else:
        daymap[msg['group_id']] = {msg['sender']['user_id']:1}

yesterday_top = {}

for group in daymap:
    daymax = max(daymap[group], key=daymap[group].get)
    db.daytop.insert({'group_id':group,'user_id':daymax,'count':daymap[group][daymax]})
