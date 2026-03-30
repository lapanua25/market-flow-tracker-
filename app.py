import os
import io
import base64
import json
import matplotlib
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import datetime

matplotlib.use('Agg')
app = Flask(__name__)
CORS(app)

SYMBOLS = {
    '原油': 'CL=F',
    'ゴールド': 'GC=F',
    '日経平均': '^N225',
    '日経平均先物': 'NIY=F',
    'S&P 500': '^GSPC',
    '米ドル/円': 'JPY=X',
    'ビットコイン': 'BTC-USD'
}

import requests

def fetch_and_calculate():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    df = yf.download(list(SYMBOLS.values()), period="1y", interval="1d", session=session)
    
    if df is None or df.empty:
        raise Exception("大変申し訳ありません。現在Yahooのサーバー側で無料クラウドからの通信が一時的にブロックされています。")
        
    if isinstance(df.columns, pd.MultiIndex):
        close_df = df.xs('Close', level='Price', axis=1) if 'Price' in df.columns.names else df['Close']
    else:
        close_df = df

    common_index = pd.date_range(start=close_df.index.min(), end=close_df.index.max(), freq='D')
    close_df_reindexed = close_df.reindex(common_index).ffill()
    last_date = close_df_reindexed.index[-1]
    
    timeframes = {
        '1D': {'label': '対前日比', 'start_date': last_date - pd.Timedelta(days=1)},
        '1W': {'label': '対前週', 'start_date': last_date - pd.Timedelta(days=7)},
        '1M': {'label': '対前月', 'start_date': last_date - pd.DateOffset(months=1)},
        '1Y': {'label': '対前年', 'start_date': close_df_reindexed.index[0]}
    }
    
    all_data = {}
    
    try:
        plt.rcParams['font.family'] = ['Noto Sans CJK JP', 'Meiryo', 'sans-serif']
    except:
        pass

    for tf_key, tf_info in timeframes.items():
        stats = []
        tf_start_date = tf_info['start_date']
        
        slice_df = close_df_reindexed[close_df_reindexed.index >= tf_start_date]
        if len(slice_df) < 2 and tf_key != '1D':
            slice_df = close_df_reindexed
            
        normalized_df = pd.DataFrame()
        for name, ticker in SYMBOLS.items():
            if ticker not in close_df.columns: continue
            series = close_df[ticker].dropna()
            if len(series) < 2: continue
            
            current_price = float(series.iloc[-1])
            if tf_key == '1D':
                price_ago = float(series.iloc[-2])
            else:
                available_past = series[series.index <= tf_start_date]
                price_ago = float(available_past.iloc[-1]) if len(available_past) > 0 else float(series.iloc[0])
            
            high_1y = float(series.max())
            low_1y = float(series.min())
            
            return_rate = (current_price / price_ago - 1) * 100
            pos_1y = (current_price - low_1y) / (high_1y - low_1y) * 100 if high_1y != low_1y else 0
            
            stats.append({
                'name': name,
                'current_price': current_price,
                'return_rate': return_rate,
                'position_1y': pos_1y
            })
            
            s_slice = slice_df[ticker].dropna()
            if len(s_slice) > 0:
                normalized_df[name] = s_slice / s_slice.iloc[0] * 100

        plt.style.use('default')
        plt.figure(figsize=(10, 5))
        if tf_key == '1D':
            plot_df = close_df_reindexed[close_df_reindexed.index >= last_date - pd.Timedelta(days=7)]
            norm_plot_df = pd.DataFrame()
            for col in plot_df.columns:
                s = plot_df[col].dropna()
                if len(s)>0: norm_plot_df[col] = s / s.iloc[0] * 100
            for col in norm_plot_df.columns:
                plt.plot(norm_plot_df.index, norm_plot_df[col], label=col, linewidth=2)
            plt.title('直近1週間の推移 (1Dリターン選択中)', color='#1e293b', fontweight='bold')
        else:
            for col in normalized_df.columns:
                plt.plot(normalized_df.index, normalized_df[col], label=col, linewidth=2)
            plt.title(f'{tf_info["label"]}の騰落比較 (起点=100)', color='#1e293b', fontweight='bold')

        plt.legend(facecolor='#ffffff', edgecolor='#e2e8f0', labelcolor='#1e293b')
        plt.grid(color='#cbd5e1', linestyle='--', linewidth=0.5)
        ax = plt.gca()
        ax.set_facecolor('#ffffff')
        plt.gcf().patch.set_facecolor('#ffffff')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#ffffff', transparent=True)
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        all_data[tf_key] = {
            'stats': stats,
            'image_url': f'data:image/png;base64,{img_base64}'
        }

    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    analysis = [
        "ビットコインなどの投機資産を中心としたリスクオフの資金流出が継続中。",
        "実物資産（ゴールド・原油）などの安全資産へのシフトが顕著。",
        "ドル高円安の進行から、米国株よりも日本株に資金が流入しやすい環境を形成。"
    ]

    return {
        'timeframes': all_data,
        'analysis': analysis,
        'last_updated': time_str
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    try:
        data = fetch_and_calculate()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
