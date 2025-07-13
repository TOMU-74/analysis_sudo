import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, time
import jpholiday # 祝日判定用

# --- ヘルパー関数（再利用） ---
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
    if pd.isna(time_str):
        return None
    try:
        if isinstance(time_str, time): # 既にtimeオブジェクトの場合はそのまま返す
            return time_str
        elif isinstance(time_str, str):
            if time_str.count(':') == 2: # HH:MM:SS
                return datetime.strptime(time_str, '%H:%M:%S').time()
            elif time_str.count(':') == 1: # HH:MM
                return datetime.strptime(time_str, '%H:%M').time()
        return None
    except ValueError:
        return None

# --- 1. 保存したCSVファイルの読み込み ---
input_filename = "./data/nakamozu_passengers_with_train_times.csv"

if not os.path.exists(input_filename):
    print(f"エラー: ファイル '{input_filename}' が見つかりません。先に前回のスクリプトを実行してファイルを作成してください。")
    exit()

df_processed_passengers = pd.read_csv(input_filename, encoding='utf-8')

# 前処理で train_time 列を文字列として保存しているはずなので、
# ここで再度 time オブジェクトに変換すると便利
df_processed_passengers['train_time_obj'] = df_processed_passengers['train_time'].apply(parse_time_str)

# --- 2. 平日・土日祝日の判定列を追加 ---
# data_date 列が YYYY-MM-DD 形式の文字列であることを仮定
df_processed_passengers['is_weekday_traffic'] = df_processed_passengers['data_date'].apply(is_weekday_jp)

# --- 3. 平日データと土日祝日データに分割 ---
df_weekday_traffic = df_processed_passengers[df_processed_passengers['is_weekday_traffic'] == True].copy()
df_weekend_holiday_traffic = df_processed_passengers[df_processed_passengers['is_weekday_traffic'] == False].copy()

print(f"\n平日データ件数: {len(df_weekday_traffic)}件")
print(f"土日祝日データ件数: {len(df_weekend_holiday_traffic)}件")

# --- 4. 集計と出力、グラフ描画を関数化 ---

def process_and_plot_traffic(df_traffic, period_name, output_base_dir):
    """
    指定された交通データフレームを処理し、集計結果をCSVに出力し、グラフを描画します。

    Args:
        df_traffic (pd.DataFrame): 平日または土日祝日の交通データフレーム。
        period_name (str): '平日' または '土日祝日' の文字列。出力ファイル名やグラフタイトルに使用。
        output_base_dir (str): 出力ファイルを保存するベースディレクトリ。
    """
    print(f"\n--- {period_name}のデータ処理を開始 ---")

    # train_time列がNone/NaNでない行に絞る
    df_valid_trains = df_traffic.dropna(subset=['train_time'])

    if df_valid_trains.empty:
        print(f"{period_name}に該当する有効な電車データがありません。")
        return

    # 電車ごとの利用者数集計
    train_passenger_counts = df_valid_trains['train_time'].value_counts().reset_index()
    train_passenger_counts.columns = ['train_time', 'passenger_count']

    # 時刻順にソート（グラフ描画のために重要）
    train_passenger_counts['train_time_obj'] = train_passenger_counts['train_time'].apply(parse_time_str)
    train_passenger_counts = train_passenger_counts.sort_values(by='train_time_obj').reset_index(drop=True)

    print(f"{period_name}の電車ごとの利用者数集計結果（先頭10行）:")
    print(train_passenger_counts.head(10))

    # --- 集計結果のCSV書き出し ---
    output_counts_dir = os.path.join(output_base_dir, "counts")
    os.makedirs(output_counts_dir, exist_ok=True) # フォルダが存在しない場合は作成
    
    output_counts_filename = os.path.join(output_counts_dir, f"train_passenger_counts_{period_name}.csv")
    train_passenger_counts[['train_time', 'passenger_count']].to_csv(output_counts_filename, index=False, encoding='utf-8')
    print(f"電車ごとの利用者数集計結果を '{output_counts_filename}' に保存しました。")

    # --- グラフ描画 ---
    plt.rcParams['font.family'] = 'Hiragino Sans' # Mac
    # plt.rcParams['font.family'] = 'Meiryo' # Windows
    # plt.rcParams['font.family'] = 'TakaoGothic' # Linux
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.unicode_minus'] = False

    plt.figure(figsize=(18, 9))
    sns.barplot(x='train_time', y='passenger_count', data=train_passenger_counts, palette='viridis')

    plt.title(f'電車ごとの利用者数 ({period_name})', fontsize=18)
    plt.xlabel('出発時刻', fontsize=14)
    plt.ylabel('利用者数', fontsize=14)

    num_trains = len(train_passenger_counts)

    # X軸のラベル設定を動的に調整
    if num_trains > 60:
        tick_interval = 10
        plt.xticks(rotation=90, ha='right', fontsize=6)
    elif num_trains > 30:
        tick_interval = 5
        plt.xticks(rotation=75, ha='right', fontsize=8)
    elif num_trains > 15:
        tick_interval = 1
        plt.xticks(rotation=60, ha='right', fontsize=10)
    else:
        tick_interval = 1
        plt.xticks(rotation=45, ha='right', fontsize=12)

    if tick_interval > 1:
        selected_indices = [i for i, _ in enumerate(train_passenger_counts['train_time']) if i % tick_interval == 0]
        selected_labels = [train_passenger_counts['train_time'].iloc[idx] for idx in selected_indices]
        plt.xticks(selected_indices, selected_labels)

    plt.tight_layout()

    output_graph_dir = os.path.join(output_base_dir, "graphs")
    os.makedirs(output_graph_dir, exist_ok=True) # フォルダが存在しない場合は作成
    
    output_graph_filename = os.path.join(output_graph_dir, f"train_passenger_counts_bar_chart_{period_name}.png")
    plt.savefig(output_graph_filename, dpi=300)
    print(f"グラフを '{output_graph_filename}' に保存しました。")

    plt.close() # グラフを表示せずにメモリを解放（ループ内で複数グラフを作成する場合に重要）


# --- 5. 平日と土日祝日それぞれに処理を実行 ---
base_output_dir = "./output/" # ベースとなる出力ディレクトリ

process_and_plot_traffic(df_weekday_traffic, '平日', base_output_dir)
process_and_plot_traffic(df_weekend_holiday_traffic, '土日祝日', base_output_dir)

print("\n全ての処理が完了しました。")