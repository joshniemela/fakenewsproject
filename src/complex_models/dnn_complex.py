import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from custom_tokeniser import custom_tokenizer
import pickle
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from multiprocessing import Pool
import numpy as np


def pass_fun(doc):
    return doc


def parallel_apply(func, df, n_jobs=8):
    df_split = np.array_split(df, n_jobs)
    pool = Pool(n_jobs)
    df = np.concatenate(pool.map(func, df_split))
    pool.close()
    pool.join()
    return df


try:
    print("loading pretrained svd and tfidf")
    tfidf = pickle.load(open("data/tfidf-dnn.pkl", "rb"))
    svd = pickle.load(open("data/svd-dnn.pkl", "rb"))
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

    print("fitting tfidf")
    X_train = tfidf.fit_transform(X_train)
    print("saving tfidf model")
    pickle.dump(tfidf, open("data/tfidf-dnn.pkl", "wb"))

    print("fitting svd")
    svd = TruncatedSVD(n_components=384, random_state=42)
    X_train = svd.fit_transform(X_train)
    print("saving svd model")
    pickle.dump(svd, open("data/svd-dnn.pkl", "wb"))


def transform(chunk):
    return svd.transform(tfidf.transform(chunk))


try:
    dnn = load_model("data/smollboi1")
    print("Loaded tf model")
except:
    print("loading df")
    df = pd.read_parquet(
        "data/small_train.parquet", columns=["tokens", "class"], engine="fastparquet"
    )

    X_train = df["tokens"].to_numpy()
    y_train = df["class"].to_numpy()
    X_train = transform(X_train)
    input_dim = X_train.shape[1]
    del df
    print("loaded df")

    callback = tf.keras.callbacks.EarlyStopping(
        monitor="loss", patience=3, restore_best_weights=True
    )

    dnn = Sequential()
    dnn.add(Dense(384, input_dim=input_dim, activation="relu"))
    dnn.add(Dropout(0.2))
    dnn.add(Dense(512, activation="relu"))
    dnn.add(Dropout(0.2))
    dnn.add(Dense(512, activation="relu"))
    dnn.add(Dropout(0.2))
    dnn.add(Dense(128, activation="relu"))
    dnn.add(Dropout(0.1))
    dnn.add(Dense(16, activation="relu"))
    dnn.add(Dense(1, activation="sigmoid"))

    val_df = pd.read_parquet("data/val.parquet", columns=["tokens", "class"])

    print("loading val")
    X_val = val_df["tokens"].to_numpy()
    y_val = val_df["class"].to_numpy()
    del val_df
    X_val = transform(X_val)
    print("loaded val")

    history = dnn.compile(
        loss="binary_crossentropy",
        optimizer=Adam(learning_rate=0.00075),
        metrics=["accuracy"],
    )

    print("Fitting dnn")
    dnn.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=10,
        batch_size=256,
        callbacks=[callback],
    )


test_df = pd.read_parquet("data/test.parquet")

X_test = test_df["tokens"]
y_test = test_df["class"]
del test_df

X_test = transform(X_test)

y_pred = dnn.predict(X_test)
acc = accuracy_score(y_pred, y_test)
print(f"Accuracy {acc}")

# >0.5 is used to make the valies of y_pred discrete since tensorflow spits them out in floats. This could be calibrated instead.
print(classification_report(y_test, y_pred > 0.5))
