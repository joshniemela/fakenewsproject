import pandas as pd
import matplotlib.pyplot as plt
import pickle
import numpy as np
import matplotlib.pyplot as plt
from lib.pass_fun import pass_fun
from lib.custom_tokeniser import custom_tokenizer
from xgboost import XGBClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    roc_curve,
    roc_auc_score,
    auc,
    confusion_matrix,
)
from tensorflow.keras.models import Sequential, load_model


def main():
    models = load_models()
    df = pd.read_parquet("liar/liar.parquet", engine="fastparquet")
    X_tokens = df["tokens"]
    y = np.array(df["class"])

    pipelines = [
        {
            "name": "Simple Model",
            "type": "sklearn",
            "transformations": ["tfidf_2048", "svd_256"],
            "model": "logreg",
            "color": "darkorange",
        },
        {
            "name": "Big DNN",
            "type": "tensorflow",
            "transformations": ["tfidf_4096", "sparse_to_dense"],
            "model": "bigchungus",
            "color": "forestgreen",
        },
        {
            "name": "Small DNN",
            "type": "tensorflow",
            "transformations": ["tfidf_4096", "svd_384"],
            "model": "dnn",
            "color": "darkmagenta",
        },
        {
            "name": "XGBoost",
            "type": "sklearn",
            "transformations": ["tfidf_4096", "svd_384"],
            "model": "xgb",
            "color": "indianred",
        },
    ]

    evaluate_pipelines(pipelines, models, X_tokens, y)
    plot_roc_curve(pipelines)


def plot_roc_curve(pipelines):
    plt.figure()
    plt.plot([0, 1], [0, 1], color="navy", lw=1, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC on LIAR dataset")
    for pipeline in pipelines:
        plt.plot(
            pipeline["fpr"],
            pipeline["tpr"],
            color=pipeline["color"],
            lw=1,
            label=f'{pipeline["name"]} (AUC = %0.3f)' % pipeline["roc_auc"],
        )
    plt.legend(loc="lower right")
    plt.savefig("report/src/figures/ROC_LIAR.png")


def load_models():
    models = {}

    models["tfidf_2048"] = pickle.load(open("data/tfidf-2048.pkl", "rb"))
    models["svd_256"] = pickle.load(open("data/svd-256.pkl", "rb"))
    models["logreg"] = pickle.load(open("data/logreg.pkl", "rb"))
    models["tfidf_4096"] = pickle.load(open("data/tfidf-4096.pkl", "rb"))
    models["svd_384"] = pickle.load(open("data/svd-384.pkl", "rb"))
    models["dnn"] = load_model("data/smollboi2")
    models["bigchungus"] = load_model("data/biggus_chungus")
    models["xgb"] = XGBClassifier()
    models["xgb"].load_model("data/xgb.json")
    models["sparse_to_dense"] = sparse_to_dense

    return models


def sparse_to_dense(X):
    return X.todense()


def evaluate_pipelines(pipelines, models, X, y):
    for pipeline in pipelines:
        evaluate_pipeline(pipeline, models, X, y)


def evaluate_pipeline(pipeline, models, X, y):
    # Apply transformations
    for step in pipeline["transformations"]:
        transform_function = models[step]
        if callable(transform_function):
            X = transform_function(X)
        else:
            X = transform_function.transform(X)

    # Predict and evaluate model
    model = models[pipeline["model"]]
    if pipeline["type"] == "tensorflow":
        y_pred = model.predict(X)
        y_pred_binary = (y_pred > 0.5).astype(int)
    else:
        y_pred = model.predict_proba(X)
        ## predict_proba gives each guess as a list of probabilities.
        ## the predicted value can therefore be interpreted as the p(1)
        y_pred = [b for a, b in y_pred]
        y_pred_binary = model.predict(X)

    print(f"Results for {pipeline['name']}")
    print(classification_report(y, y_pred_binary))
    save_matrix(pipeline["name"], y, y_pred_binary)

    # Calculate the ROC curve, AUC score and store the values in the pipeline dictionary
    fpr, tpr, _ = roc_curve(y, y_pred)
    roc_auc = auc(fpr, tpr)
    pipeline["fpr"] = fpr
    pipeline["tpr"] = tpr
    pipeline["roc_auc"] = roc_auc


def save_matrix(name, y_true, y_pred):
    path = "report/src/figures/"
    # Make confusion matrix
    conf_matrix = confusion_matrix(y_true, y_pred, normalize="true")

    # Create a new figure and axis
    fig, ax = plt.subplots(figsize=(5, 5))

    # Plot confusion matrix
    im = ax.imshow(conf_matrix, interpolation="nearest", cmap=plt.cm.gray_r)

    # Define labels
    labels = [["TN", "FP"], ["FN", "TP"]]

    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{labels[i][j]}: {format(conf_matrix[i, j], '.2f')}",
                horizontalalignment="center",
                color="white" if conf_matrix[i, j] > 0.5 else "black",
            )

    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.axis("off")
    ax.set_title(name)

    # Save confusion matrix as PNG file
    fig.savefig(path + name + "_conf_matrix.png", dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    main()
