import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import telegram
import pandahouse
from datetime import date
import io
from read_db.CH import Getch
import sys
import os

def check_anomaly(df, metric, a = 3, n = 5):
    # алгоритм поиска аномалий с помощью межквартильного размаха
    
    df['q25'] = df[metric].shift(1).rolling(n).quantile(0.25)
    df['q75'] = df[metric].shift(1).rolling(n).quantile(0.75)
    df['iqr'] = df['q75'] - df['q25']
    df['up'] = df['q75'] + a*df['iqr']
    df['low'] = df['q25'] - a*df['iqr']
    current_value = df[metric].iloc[-1]
    lower =  df['low'].iloc[-1]
    upper = df['up'].iloc[-1]
    
    if current_value > upper or current_value < lower:
        is_alert = 1
    else: 
        is_alert = 0
            
    return is_alert, df

def run_alerts(chat=None):
    chat_id = chat or -1001706798154
    bot = telegram.Bot(token='5201590178:AAF13m9D__06QZxQ8CtwdJ_Qxp6p1b0cfUE') 
    
    data = Getch(''' SELECT
                        toStartOfFifteenMinutes(time) as ts
                        , toDate(ts) as date
                        , formatDateTime(ts, '%R') as hm
                        , count(user_id) messages
                        , countif(DISTINCT user_id, os='IOS') ios
                        , countif(DISTINCT user_id, os='Android') android
                    FROM simulator_20220320.message_actions
                    WHERE ts >=  today() - 1 and ts < toStartOfFifteenMinutes(now())
                    GROUP BY ts, date, hm
                    ORDER BY ts ''').df

    

    metrics = ['messages', 'ios', 'Android']
    
    for metric in metrics:
        is_alert, df = check_anomaly(data, metric, a=3, n=5) 
    
        if is_alert: 
            chart = 'https://superset.lab.karpov.courses/superset/dashboard/616/'
            msg = f'Метрика {metric}:\nтекущее значение: {current_value:.2f}\nВерхняя граница {upper}/nНижняя граница{lower}/nДашборд: {chart}/nЗагляни @sent_kate' 
            
           
            sns.set(rc={'figure.figsize': (16, 10)})
            plt.tight_layout()
            ax = sns.lineplot(x=data['ts'], y=data[metric], label='metric')
            ax = sns.lineplot(x=data['ts'], y=data['up'], label='up_qn')
            ax = sns.lineplot(x=data['ts'], y=data['low'], label='low_qn')

            ax.set(xlabel='time')
            ax.set_title(metric)

            plot_object = io.BytesIO()
            ax.figure.savefig(plot_object)
            plot_object.seek(0)
            plot_object.name = '{0}.png'.format(metric)
            plt.close()
            bot.sendMessage(chat_id=chat_id, text=msg)
            bot.sendPhoto(chat_id=chat_id, photo=plot_object)            
     
try:
    run_alerts()
except Exception as e:
    print(e)
