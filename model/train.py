import duckdb
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, precision_score, recall_score

# 1. Pull features
con = duckdb.connect("quickbite.duckdb", read_only=True)
df = con.execute("""
    SELECT
        o.order_id,
        o.order_value,
        EXTRACT(HOUR FROM o.order_time) AS order_hour,
        o.delivery_minutes,
        r.rating AS restaurant_rating,
        r.cuisine,
        u.device,
        (o.status = 'cancelled') AS is_cancelled
    FROM mart.orders_fact o
    JOIN mart.restaurants_dim r ON o.restaurant_id = r.restaurant_id
    JOIN mart.users_dim u ON o.user_id = u.user_id
""").df()

print(df.shape)
print(df["is_cancelled"].value_counts())

# 2. Encode text columns
df_encoded = pd.get_dummies(df, columns=["cuisine", "device"], drop_first=True)
feature_cols = [c for c in df_encoded.columns if c not in ["order_id", "is_cancelled"]]
X = df_encoded[feature_cols]
y = df_encoded["is_cancelled"]

# 3. Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 4. Train
model = LogisticRegression(max_iter=1000, class_weight="balanced")
model.fit(X_train, y_train)

# 5. Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
print(f"Precision: {precision_score(y_test, y_pred):.3f}")
print(f"Recall: {recall_score(y_test, y_pred):.3f}")

# 6. Save
Path("model").mkdir(exist_ok=True)
joblib.dump(model, "model/cancellation_model.pkl")
joblib.dump(feature_cols, "model/feature_cols.pkl")
print("Model saved.")