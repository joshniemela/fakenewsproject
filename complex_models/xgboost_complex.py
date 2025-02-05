import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from lib.custom_tokeniser import custom_tokenizer
import pickle
from xgboost import XGBClassifier
from lib.pass_fun import pass_fun

xgb = XGBClassifier()
try:
    print("loading pretrained models")
    tfidf = pickle.load(open("data/tfidf-4096.pkl", "rb"))
    svd = pickle.load(open("data/svd-384.pkl", "rb"))
    xgb.load_model("data/xgb.json")
except:
    print("models not found, fitting new model")
    df = pd.read_parquet(
        "data/small_train.parquet", columns=["tokens", "class"], engine="fastparquet"
    )
    X_train = df["tokens"]
    y_train = df["class"]

    print(y_train.value_counts())

    tfidf = TfidfVectorizer(
        max_features=4096, sublinear_tf=True, preprocessor=pass_fun, tokenizer=pass_fun
    )

    X_train = tfidf.fit_transform(X_train)
    print("saving tfidf model")
    pickle.dump(tfidf, open("data/tfidf-4096.pkl", "wb"))

    svd = TruncatedSVD(n_components=384, random_state=42)
    X_train = svd.fit_transform(X_train)
    print("saving svd model")
    pickle.dump(svd, open("data/svd-384.pkl", "wb"))

    xgb.fit(X_train, y_train)

    print("saving xgb model")
    xgb.save_model("data/xgb.json")
    print("finished fitting models")

df_test = pd.read_parquet("data/test.parquet", engine="fastparquet")

X_test = df_test["tokens"]
y_test = df_test["class"]

from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report

X_test = svd.transform(tfidf.transform(X_test))
y_pred = xgb.predict(X_test)
y_probs = xgb.predict_proba(X_test)
acc = accuracy_score(y_pred, y_test)
print(f"Accuracy {acc}")

print(classification_report(y_test, y_pred))

# Save results for later use
y_pred = np.array(y_pred)  # Your predictions
y_true = np.array(y_test)  # True labels
y_probs = np.array(y_probs)  # True labels
np.save("data/predictions/xgboost_y_preds.npy", y_pred)
np.save("data/predictions/xgboost_y_true.npy", y_true)
np.save("data/predictions/xgboost_y_probs.npy", y_probs)
