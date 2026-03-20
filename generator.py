import os
import json
import matplotlib
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import datetime

matplotlib.use('Agg')

SYMBOLS = {
    '原油': 'CL=F',
    'ゴールド': 'GC=F',
    '日経平均': '^N225',
    'S&P 500': '^GSPC',
    '米ドル/円': 'JPY=X',
    'ビットコイン': 'BTC-USD'
}

def generate_static_files():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(base_dir, 'docs')
    os.makedirs(docs_dir, exist_ok=True)

    df = yf.download(list(SYMBOLS.values()), period="1y", interval="1d")
    if isinstance(df.columns, pd.MultiIndex):
        close_df = df.xs('Close', level='Price', axis=1) if 'Price' in df.columns.names else df['Close']
    else:
        close_df = df

    stats = []
    for name, ticker in SYMBOLS.items():
        if ticker not in close_df.columns: continue
        series = close_df[ticker].dropna()
        if len(series) == 0: continue
        current_price = float(series.iloc[-1])
        price_1y_ago = float(series.iloc[0])
        high_1y = float(series.max())
        low_1y = float(series.min())
        
        return_1y = (current_price / price_1y_ago - 1) * 100
        pos_1y = (current_price - low_1y) / (high_1y - low_1y) * 100 if high_1y != low_1y else 0
        stats.append({
            'name': name,
            'current_price': current_price,
            'return_1y': return_1y,
            'position_1y': pos_1y
        })

    common_index = pd.date_range(start=close_df.index.min(), end=close_df.index.max(), freq='D')
    close_df_reindexed = close_df.reindex(common_index).ffill()
    normalized_df = pd.DataFrame()
    for name, ticker in SYMBOLS.items():
        if ticker in close_df_reindexed.columns:
            series = close_df_reindexed[ticker].dropna()
            if len(series) > 0:
                normalized_df[name] = series / series.iloc[0] * 100

    try:
        # Noto Sans for Github Actions Linux, Meiryo for Local Windows
        plt.rcParams['font.family'] = ['Noto Sans CJK JP', 'Meiryo', 'sans-serif']
    except:
         pass
    
    plt.style.use('dark_background')
    plt.figure(figsize=(10, 5))
    for col in normalized_df.columns:
        plt.plot(normalized_df.index, normalized_df[col], label=col, linewidth=2)

    plt.title('1 Year Performance (1yr Ago = 100)', color='white')
    plt.legend(facecolor='#1e1e24', edgecolor='none', labelcolor='white')
    plt.grid(color='#333333', linestyle='--', linewidth=0.5)
    ax = plt.gca()
    ax.set_facecolor('#0d0d12')
    plt.gcf().patch.set_facecolor('#0d0d12')
    plt.tight_layout()

    image_path = os.path.join(docs_dir, 'chart.png')
    plt.savefig(image_path, facecolor='#0d0d12', transparent=True)
    plt.close()

    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    analysis = [
        "ビットコインなどの投機資産を中心としたリスクオフの資金流出が継続中。",
        "実物資産（ゴールド・原油）などの安全資産へのシフトが顕著。",
        "ドル高円安の進行から、米国株よりも日本株に資金が流入しやすい環境を形成。"
    ]

    data = {
        'success': True,
        'data': {
            'stats': stats,
            'image_url': f'./chart.png?t={int(datetime.datetime.now().timestamp())}',
            'analysis': analysis,
            'last_updated': time_str
        }
    }

    with open(os.path.join(docs_dir, 'data.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Static files generated successfully in docs/")

if __name__ == '__main__':
    generate_static_files()
