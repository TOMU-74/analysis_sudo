import pandas as pd
from datetime import datetime, timedelta

# 改札データの読み込み
df_passengers = pd.read_csv("./data/202504-Nakamozu-OD-Romaji.csv")
df_passengers['data_number'] = df_passengers.index
#print(df_passengers['data_number'].head())
print(df_passengers.head())

'''
# 時刻表データの読み込み
df_timetable = pd.read_csv("timetable.csv")
df_timetable['通過時刻'] = pd.to_datetime(df_timetable['通過時刻'])

# 仮想的な例：A駅→D駅の移動の場合
for i, row in df_passengers.iterrows():
    乗車駅 = row['乗車駅']
    降車駅 = row['降車駅']
    入時刻 = row['改札入時刻']
    出時刻 = row['改札出時刻']

    # 乗車駅・降車駅を通る列車を抽出
    df_candidate = df_timetable[(df_timetable['駅'].isin([乗車駅, 降車駅]))]

    # 同じ列車IDで、乗車駅が入時刻に近く、降車駅が出時刻に近いものを探す
    for 列車ID in df_candidate['列車ID'].unique():
        stops = df_candidate[df_candidate['列車ID'] == 列車ID].sort_values('通過時刻')
        if (乗車駅 in stops['駅'].values) and (降車駅 in stops['駅'].values):
            t_in = stops[stops['駅'] == 乗車駅]['通過時刻'].values[0]
            t_out = stops[stops['駅'] == 降車駅]['通過時刻'].values[0]
            if 入時刻 <= t_in + timedelta(minutes=5) and 出時刻 >= t_out - timedelta(minutes=5):
                # この列車と判断
                区間リスト = stops[stops['駅'].isin([乗車駅, 降車駅])]
                # 区間ごとに乗車人数カウントに加算
                # ...

'''