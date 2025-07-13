import pandas as pd
from datetime import datetime, time, timedelta
import jpholiday
import numpy as np # np.nan を使うため

# --- 1. ヘルパー関数の定義 ---

def is_weekday_jp(date_str: str) -> bool:
    """
    指定された日付文字列が日本の平日かどうかを判定します。
    土日祝日を休日と見なします。
    Args:
        date_str (str): 判定したい日付文字列 (例: 'YYYY-MM-DD')。
    Returns:
        bool: 日本の平日であれば True、休日（土日祝日）であれば False。
    """
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        # 日付形式が不正な場合のハンドリング
        print(f"Warning: Invalid date format '{date_str}'. Returning False (assuming not weekday).")
        return False

    is_weekend = (target_date.weekday() >= 5) # 5:土曜日, 6:日曜日
    is_holiday = jpholiday.is_holiday(target_date)

    return not is_weekend and not is_holiday

def parse_time_str(time_str):
    """
    時刻文字列を datetime.time オブジェクトに変換します。
    無効な形式の場合は None を返します。
    """
    if pd.isna(time_str): # NaN値のチェック
        return None
    try:
        # 秒まである場合とない場合に対応
        if time_str.count(':') == 2: # HH:MM:SS
            return datetime.strptime(str(time_str), '%H:%M:%S').time()
        elif time_str.count(':') == 1: # HH:MM (秒がない場合)
            return datetime.strptime(str(time_str), '%H:%M').time()
        else:
            return None # その他の不正な形式
    except ValueError:
        return None

def find_closest_train_time(passenger_data_row, timetable_weekday_df, timetable_weekend_df):
    """
    乗降記録の曜日と時刻に基づき、最も近い（直後の）列車の出発時刻を時刻表から見つけます。
    
    Args:
        passenger_data_row (pd.Series): df_nakamozu_passengers の1行データ。
        timetable_weekday_df (pd.DataFrame): 平日の時刻表データフレーム（時刻でソート済み）。
        timetable_weekend_df (pd.DataFrame): 休日の時刻表データフレーム（時刻でソート済み）。
                                     
    Returns:
        str or None: 最も近い列車の出発時刻の文字列 ('HH:MM:SS')、見つからない場合は None。
    """
    p_date_str = passenger_data_row['data_date']
    p_boarding_time_obj = passenger_data_row['depature_station_time_obj']
    
    if p_boarding_time_obj is None: # 時刻の変換に失敗した場合
        return None

    # 日付から平日/休日を判定
    is_weekday = is_weekday_jp(p_date_str)

    if is_weekday:
        target_timetable = timetable_weekday_df
    else:
        target_timetable = timetable_weekend_df

    # 乗車時刻以降の列車に絞り込む
    # departure_time_obj は既に time オブジェクト
    after_boarding_trains = target_timetable[
        target_timetable['departure_time_obj'] > p_boarding_time_obj
    ]

    if not after_boarding_trains.empty:
        # 最も早い列車（ソート済みなので最初の行）の出発時刻文字列を返す
        return after_boarding_trains.iloc[0]['departure_time']
    else:
        # 該当する列車がない場合
        return None

# --- 2. データ読み込みと前処理 ---

'''

# 改札データの読み込み
# CSV読み込み時のエラーを防ぐため、encodingを指定することが多いです (例: encoding='utf-8')
df_passengers = pd.read_csv("./data/202504-Nakamozu-OD-Romaji.csv", encoding='utf-8')

# 'data_number' 列を追加
df_passengers['data_number'] = df_passengers.index

# df_nakamozu_passengers を作成 (SettingWithCopyWarning 回避のため .copy() を使用)
df_nakamozu_passengers = df_passengers.loc[df_passengers['depature_station'] == 'Nakamozu'].copy()

# 時刻表データの読み込み
df_timetable = pd.read_csv("./data/timetable_nakamozu.csv", encoding='utf-8')

# df_timetable にも data_number を追加（今回は使わないが、元のコードに倣って残す）
df_timetable['data_number'] = df_timetable.index

# 平日・休日の時刻表をフィルタリング (SettingWithCopyWarning 回避のため .copy() を使用)
df_weekday_timetable = df_timetable.loc[df_timetable['schedule_type'] == 'weekday'].copy()
df_weekend_timetable = df_timetable.loc[df_timetable['schedule_type'] == 'weekend'].copy()

# 時刻データを datetime.time オブジェクトに変換 (重要)
df_nakamozu_passengers['depature_station_time_obj'] = df_nakamozu_passengers['depature_station_time'].apply(parse_time_str)
df_weekday_timetable['departure_time_obj'] = df_weekday_timetable['departure_time'].apply(parse_time_str)
df_weekend_timetable['departure_time_obj'] = df_weekend_timetable['departure_time'].apply(parse_time_str)

# 時刻表を時刻でソートしておく (検索効率化のため)
df_weekday_timetable_sorted = df_weekday_timetable.sort_values(by='departure_time_obj').reset_index(drop=True)
df_weekend_timetable_sorted = df_weekend_timetable.sort_values(by='departure_time_obj').reset_index(drop=True)

# 新しい列 'train_time' を df_nakamozu_passengers に事前に作成・初期化 (KeyError 回避)
df_nakamozu_passengers['train_time'] = None # None で初期化

# --- 3. メイン処理: 列車時刻の割り当て ---

# df_nakamozu_passengers の各行に対して find_closest_train_time 関数を適用
# `axis=1` は、行全体（Series）が関数に渡されることを意味します
df_nakamozu_passengers['train_time'] = df_nakamozu_passengers.apply(
    lambda row: find_closest_train_time(row, df_weekday_timetable_sorted, df_weekend_timetable_sorted),
    axis=1
)

# --- 4. 結果の表示 ---
print("\n--- 処理後の df_nakamozu_passengers （先頭10行） ---")
print(df_nakamozu_passengers.head(10))

# --- 5. 結果をCSVファイルに保存 ---
output_filename = "./data/nakamozu_passengers_with_train_times.csv" # 保存先のパスとファイル名を指定
df_nakamozu_passengers.to_csv(output_filename, index=False, encoding='utf-8')

print(f"\n処理結果を '{output_filename}' に保存しました。")
'''




