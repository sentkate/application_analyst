import telegram
import matplotlib.pyplot as plt
import io
import pandas as pd
import pandahouse
from read_db.CH import Getch
import os
from datetime import datetime, timedelta


def report_auto(chat=None):
    chat_id = chat or -1001539201117
    bot = telegram.Bot(token='5201590178:AAF13m9D__06QZxQ8CtwdJ_Qxp6p1b0cfUE')
        
    data_for_metrics = Getch('''
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
                       
    DAU = data_for_metrics.DAU.values[0]
    CTR = data_for_metrics.CTR.values[0]
    likes = data_for_metrics.Likes.values[0]
    views = data_for_metrics.Views.values[0]
    day = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')

    msg = ((f"Данные {day} по ленте новостей:") + "\n" + (f"DAU: {DAU}") 
    + "\n" + (f"CTR: {CTR} %") + "\n" + (f"Views: {views}")
    + "\n" + (f"Likes: {likes}"))
    bot.sendMessage(chat_id=chat_id,text=msg)

          
    data_for_metrics.plot(x='Дата', y='CTR', figsize=(12, 8))
    plt.title('Информация за неделю по CTR')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'ctr_plot.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
    data_for_metrics.plot(x='Дата', y=['Likes', 'Views', 'DAU'], figsize=(12, 8))
    plt.title('Информация за неделю по лайкам, просмотрам и DAU')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'full_plot.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)
                       
                       
try:
    report_auto()
except Exception as e:
    print(e)

                       
                       
                       

