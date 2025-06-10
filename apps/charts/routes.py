# -*- encoding: utf-8 -*-
import numpy as np
import pandas as pd
from flask import Blueprint, request, render_template
from tensorflow.keras.models import load_model
from datetime import datetime
import pymysql
from keras.saving import register_keras_serializable
from tensorflow.keras.layers import Layer
import tensorflow.keras.backend as K
from sklearn.preprocessing import MinMaxScaler
# LSTM + Attention
from keras.saving import register_keras_serializable
from tensorflow.keras.layers import Layer
import tensorflow.keras.backend as K
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Sử dụng non-GUI backend để tránh lỗi thread
import matplotlib.pyplot as plt
import io
import base64

charts_blueprint = Blueprint('charts_blueprint', __name__)

# Kết nối DB
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        db='pbl7',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


@charts_blueprint.route('/charts_statistics', methods=['GET', 'POST'])
def charts():
    conn = get_db_connection()
    industries = []
    chart_data = {'Đà Nẵng': [], 'Hà Nội': [], 'Hồ Chí Minh': []}
    summary_title = ""
    totals = {'Đà Nẵng': 0, 'Hà Nội': 0, 'Hồ Chí Minh': 0}

    try:
        with conn.cursor() as cursor:
            # Lấy danh sách ngành nghề
            cursor.execute("SELECT DISTINCT industry FROM base WHERE industry IS NOT NULL AND industry != ''")
            industries = [row['industry'] for row in cursor.fetchall()]

            # Mặc định ngành nghề là 'Tất cả ngành' và năm là 2025
            industry = request.form.get('industry', '')  # Mặc định là không chọn ngành
            year = request.form.get('time_value_year', '2025')  # Mặc định là năm 2025

            months = list(range(1, 13))
            locations = ['Đà Nẵng', 'Hà Nội', 'Hồ Chí Minh']

            for loc in locations:
                monthly_counts = []
                for month in months:
                    query = """
                        SELECT COUNT(*) AS count FROM base
                        WHERE location = %s AND YEAR(create_at) = %s AND MONTH(create_at) = %s
                    """
                    params = [loc, year, month]

                    if industry:
                        query += " AND industry = %s"
                        params.append(industry)

                    cursor.execute(query, tuple(params))
                    row = cursor.fetchone()
                    monthly_counts.append(row['count'] if row['count'] else 0)

                chart_data[loc] = monthly_counts
                totals[loc] = sum(monthly_counts)

            summary_title = f"Thống kê số lượng công việc ngành {industry or 'Tất cả'} theo năm {year}"

    finally:
        conn.close()

    months_labels = [f"Tháng {i}" for i in range(1, 13)]

    return render_template('charts/statistics.html',
                           industries=industries,
                           chart_data=chart_data,
                           months=months_labels,
                           summary_title=summary_title,
                           totals=totals,
                           segment='charts')



@charts_blueprint.route('/predict', methods=['GET', 'POST'])
def predict():
    conn = get_db_connection()
    real_data, predicted_data, categories = [], [], []
    summary_title = ""
    industry = request.form.get('industry')
    location = request.form.get('location')
    time_type = request.form.get('time_type') or 'month'

    with conn.cursor() as cursor:
        cursor.execute("SELECT DISTINCT industry FROM base WHERE industry IS NOT NULL AND industry != ''")
        industries = [row['industry'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT location FROM base WHERE location IS NOT NULL AND location != ''")
        locations = [row['location'] for row in cursor.fetchall()]

        if request.method == 'POST':
            query = """
                        SELECT DATE_FORMAT(create_at, '%%Y-%%m-01') AS period, COUNT(*) AS total 
                        FROM base 
                        WHERE create_at <= CURDATE()
                    """

            params = []
            if industry:
                query += " AND industry = %s"
                params.append(industry)
            if location:
                query += " AND location = %s"
                params.append(location)
            query += " GROUP BY period ORDER BY period"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

    conn.close()

    if request.method == 'GET':
        return render_template('charts/predict.html',
                               industries=industries,
                               locations=locations,
                               real_data=[],
                               predicted_data=[],
                               categories=[],
                               segment='charts')

    if not rows:
        summary_title = "Không có dữ liệu phù hợp."
        return render_template('charts/predict.html',
                               industries=industries,
                               locations=locations,
                               real_data=[],
                               predicted_data=[],
                               categories=[],
                               summary_title=summary_title,
                               segment='charts',
                               selected_industry=industry,
                               selected_location=location,
                               time_type=time_type)

    df = pd.DataFrame(rows)
    df['period'] = pd.to_datetime(df['period'])

    if time_type == 'quarter':
        # Chuyển từ quý thành tháng, chia đều công việc trong mỗi quý cho 3 tháng
        df['quarter'] = df['period'].dt.to_period('Q')
        grouped = df.groupby('quarter')['total'].sum()  # Tính tổng công việc theo quý

        # Chuyển đổi quý thành tháng, mỗi quý có 3 tháng
        monthly_data = []
        for total in grouped:
            monthly_data.extend([total / 3] * 3)  # Mỗi quý chia đều cho 3 tháng

        # Tạo lại dữ liệu theo tháng
        df = pd.DataFrame({'period': pd.date_range(start=df['period'].min(), periods=len(monthly_data), freq='M'),
                           'total': monthly_data})
        offset = pd.DateOffset(months=1)
        window_size = 12  # 12 tháng
    else:
        df['period'] = df['period'].dt.to_period('M').dt.to_timestamp()
        grouped = df.groupby('period')['total'].sum()  # Tổng công việc theo tháng
        offset = pd.DateOffset(months=1)
        window_size = 12  # 12 tháng

    grouped = grouped[-window_size:]
    real_data = [round(x) for x in grouped.values.tolist()]
    real_dates = list(grouped.index)

    # Cập nhật để đảm bảo các giá trị trong real_dates là Timestamp, không phải Period
    real_dates = [d.to_timestamp() if isinstance(d, pd.Period) else d for d in real_dates]

    # Tính toán các ngày tương lai bằng cách cộng `offset` vào `Timestamp`
    future_dates = [real_dates[-1] + offset * i for i in range(1, window_size + 1)]

    # Tạo lớp AttentionLayer
    @register_keras_serializable()
    class AttentionLayer(Layer):
        def __init__(self, **kwargs): super().__init__(**kwargs)
        def build(self, input_shape):
            self.W = self.add_weight(name="att_weight", shape=(input_shape[-1], 1), initializer="random_normal", trainable=True)
            self.b = self.add_weight(name="att_bias", shape=(input_shape[1], 1), initializer="zeros", trainable=True)
            super().build(input_shape)
        def call(self, x):
            e = K.tanh(K.dot(x, self.W) + self.b)
            a = K.softmax(e, axis=1)
            return x * a

    scaler = MinMaxScaler((0, 1))
    scaled = scaler.fit_transform(np.array(real_data).reshape(-1, 1))
    X_input = scaled.reshape(1, window_size, 1)

    # Load mô hình
    model = load_model(r"D:\My folder\HK8\PBL7\SRC\apps\charts\models\Model_BiLSTM_Attention_Trend.keras", 
                       custom_objects={'AttentionLayer': AttentionLayer})

    predicted = []
    for _ in range(window_size):
        pred = model.predict(X_input, verbose=0)
        predicted.append(pred[0][0])
        X_input = np.append(X_input[:, 1:, :], pred.reshape(1, 1, 1), axis=1)

    predicted_data = scaler.inverse_transform(np.array(predicted).reshape(-1, 1)).flatten()
    predicted_data = [round(x) for x in predicted_data]

    # Vẽ biểu đồ
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(real_dates, real_data, marker='o', label='Thực tế')
    ax.plot([real_dates[-1]] + future_dates, [real_data[-1]] + predicted_data, marker='o', linestyle='--', color='orange', label='Dự đoán')
    for x, y in zip(real_dates, real_data):
        ax.text(x, y + 1, f'{y}', ha='center')
    for x, y in zip(future_dates, predicted_data):
        ax.text(x, y + 1, f'{y}', ha='center')
    ax.set_title(f'Xu hướng tuyển dụng {industry.upper() if industry else "TẤT CẢ NGÀNH"} {window_size} kỳ tới ({time_type})')
    ax.set_xlabel('Thời gian')
    ax.set_ylabel('Số lượng công việc')
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    summary_title = f"Dự đoán {industry or 'Tất cả ngành'} - {location or 'Tất cả địa điểm'} ({'theo tháng' if time_type == 'month' else 'theo quý'})"

    return render_template('charts/predict.html',
                           industries=industries,
                           locations=locations,
                           real_data=real_data,
                           predicted_data=predicted_data,
                           categories=[d.strftime('%Y-%m') if time_type == 'month' else f"{d.year}-Q{(d.month - 1)//3 + 1}" for d in real_dates + future_dates],
                           chart_image=chart_base64,
                           summary_title=summary_title,
                           selected_industry=industry,
                           selected_location=location,
                           time_type=time_type,
                           segment='charts')


