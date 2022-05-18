import telegram
import matplotlib.pyplot as plt
import io
import pandas as pd
import pandahouse
from read_db.CH import Getch
import os
from datetime import datetime, timedelta

def full_report(chat=None):
    chat_id = chat or -1001539201117
    bot = telegram.Bot(token='5201590178:AAF13m9D__06QZxQ8CtwdJ_Qxp6p1b0cfUE')
        
    feeds = Getch('''
    SELECT toStartOfDay(time) "Дата",
    count(DISTINCT user_id) DAU,
    round((countIf(user_id, action='like')/countIf(user_id, action='view'))*100, 0) CTR,
    countIf(user_id, action='like') "Likes",
    countIf(user_id, action='view') "Views"
    FROM simulator_20220320.feed_actions
    WHERE toStartOfDay(time) > today() - 8 AND toStartOfDay(time) < today()
    GROUP BY toStartOfDay(time)
    ORDER BY toStartOfDay(time) desc
    ''').df

    messages = Getch('''
    SELECT toStartOfDay(time) "Дата",
    count(DISTINCT user_id) DAU, 
    count(user_id) count_users
    FROM simulator_20220320.message_actions
    WHERE toStartOfDay(time) > today() - 8 AND toStartOfDay(time) < today()
    GROUP BY toStartOfDay(time)
    ORDER BY toStartOfDay(time) desc
    ''').df
    
    all_events = Getch('''
    SELECT toStartOfDay(toDateTime(time)) AS __timestamp,
    count(action) AS "События",
    countIf(action='feed') AS "Лента новостей",
    countIf(action='message') AS "Сообщения"
    FROM
    (SELECT user_id, time, action
    FROM
    (SELECT *
    FROM
    (SELECT user_id,time, 'feed' AS action
    FROM simulator_20220320.feed_actions)
    UNION ALL
    (SELECT user_id, time, 'message' AS actiom
    FROM simulator_20220320.message_actions))) AS virtual_table
    WHERE toStartOfDay(time) > today() - 8 AND toStartOfDay(time) < today()
    GROUP BY toStartOfDay(toDateTime(time))
    ORDER BY __timestamp DESC
    ''').df

    DAU = feeds.DAU.values[0]
    CTR = feeds.CTR.values[0]
    likes = feeds.Likes.values[0]
    views = feeds.Views.values[0]
    DAU_msg = messages.DAU.values[0]
    count_msg = messages.count_users.values[0]
    day = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')
    full_events = all_events['События'].values[0]
    
    msg = ((f"Данные за {day}.") + "\n" + "\n" + (f"Всего событий в приложении: {full_events}") + 
    "\n" +  (f"По ленте новостей:") + "\n" + (f"DAU: {DAU}") 
    + "\n" + (f"CTR: {CTR} %") + "\n" + (f"Views: {views}")
    + "\n" + (f"Likes: {likes}") + "\n" + "\n"  + (f"По сообщениям:") + "\n" + 
    (f"DAU: {DAU_msg}") + "\n" + (f"Общее кол-во сообщений: {count_msg}"))
    bot.sendMessage(chat_id=chat_id,text=msg)

    all_events.plot(x='__timestamp', y=['События', 'Лента новостей', 'Сообщения'],            
    figsize=(12, 8))
    plt.title('Динамика событий в приложении')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'events_plot.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
    all_events['% все события'] = round(all_events['События'].pct_change(periods=-1) 
    * 100, 1)
    all_events['% лента новостей'] = round(all_events['Лента новостей'].pct_change(periods=-1) 
    * 100, 1)
    all_events['% сообщения'] = round(all_events['Сообщения'].pct_change(periods=-1) 
    * 100, 1)
    info_msg = (f"Файл содержит в себе все события за неделюс процентной динамикой изменений")
    bot.sendMessage(chat_id=chat_id,text=info_msg)

    file_object = io.StringIO()
    all_events.to_csv(file_object)
    file_object.name = 'chenge_file.csv'
    file_object.seek(0)
    bot.sendDocument(chat_id=chat_id, document=file_object)


try:
    full_report()
except Exception as e:
    print(e)
