import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from custom_tokeniser import custom_tokenizer
import pickle
def pass_fun(doc):
    return doc
try:
    print("loading pretrained models")
    tfidf = pickle.load(open("./pickles/tfidf-2048.pkl", "rb"))
    svd = pickle.load(open("./pickles/svd-256.pkl", "rb"))
    lr = pickle.load(open("./pickles/logreg.pkl", "rb"))
except:
    print("models not found, fitting new model")
    df = pd.read_parquet("small_train.parquet", columns=["tokens", "class"])
    X_train = df["tokens"]
    y_train = df["class"]

    print(y_train.value_counts())


    tfidf = TfidfVectorizer(max_features=2048, sublinear_tf=True, preprocessor=pass_fun, tokenizer=pass_fun)

    X_train = tfidf.fit_transform(X_train)
    print("saving tfidf model")
    pickle.dump(tfidf, open("pickles/tfidf-2048.pkl", "wb"))

    svd = TruncatedSVD(n_components=256, random_state = 42)
    X_train = svd.fit_transform(X_train)
    print("saving svd model")
    pickle.dump(svd, open("pickles/svd-256.pkl", "wb"))

    lr = LogisticRegression(random_state=42)
    lr.fit(X_train, y_train)

    print("saving logistic regressor model")
    pickle.dump(lr, open("pickles/logreg.pkl", "wb"))
    print("finished fitting models")

df_test = pd.read_parquet("test.parquet")

X_test = df_test["tokens"]
y_test = df_test["class"]

X_test = svd.transform(tfidf.transform(X_test))
score = lr.score(X_test, y_test)
print(score)