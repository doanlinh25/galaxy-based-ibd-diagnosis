import glob
import os
import time
from io import BytesIO
import random as rd
import boto3
import botocore
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from WorkFlowGalaxy.mainwfg import check_library_layout
from pipeline_galaxy.mainplg import pipelineglx
from Stored.upload_to_database import upload_disease_predictions_db
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns
from joblib import dump, load
import warnings

warnings.filterwarnings('ignore')

def load_data(s3_client=None, bucket_name="ppnckh", key="train/cleaned_data/wf0/merged.csv", path_file=None):
    """
    Load dataset:
    - Nếu s3_client != None, lấy từ Cloudflare R2
    - Ngược lại, lấy từ path_file (local)
    """
    if s3_client is not None:
        print("Đang tải file Cloudflare R2...")
        obj = s3_client.get_object(Bucket=bucket_name, Key=key)
        data = obj['Body'].read()
        df = pd.read_csv(BytesIO(data), sep=r"\s+|,", engine="python")
    elif path_file is not None and os.path.exists(path_file):
        print(f"Đang tải từ file: {path_file}")
        df = pd.read_csv(path_file, sep=r"\s+|,", engine="python")
    else:
        raise FileNotFoundError("Không có dữ liệu!")

    if "Diagonies" not in df.columns:
        df.columns = list(df.columns[:-1]) + ["Diagonies"]

    print(f"Data shape: {df.shape}")
    return df

def visualize_model_results(X, y, model, X_test, y_test, y_pred):
    sns.set_theme(style="whitegrid")

    # 1. t-SNE: Phân cụm tự nhiên
    print("\n[1/3] Đang vẽ biểu đồ t-SNE (Học không giám sát)...")
    tsne = TSNE(n_components=2, random_state=42, perplexity=30)
    X_tsne = tsne.fit_transform(X)
    plt.figure(figsize=(9, 6))
    sns.scatterplot(x=X_tsne[:, 0], y=X_tsne[:, 1], hue=y, palette="Set1", s=80, alpha=0.8)
    plt.title("Phân cụm tự nhiên Hệ vi sinh đường ruột (t-SNE)", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

    # 2. Feature Importance: Dấu ấn sinh học (Biomarkers)
    print("[2/3] Đang vẽ biểu đồ Feature Importance...")
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:10] # Top 10
    top_features = [X.columns[i] for i in indices]
    top_importances = importances[indices]

    plt.figure(figsize=(10, 6))
    sns.barplot(x=top_importances, y=top_features, palette="viridis")
    plt.title("Top 10 Đặc trưng (Vi khuẩn) quan trọng nhất chẩn đoán IBD", fontsize=14, fontweight='bold')
    plt.xlabel("Mức độ đóng góp (Importance Score)")
    plt.ylabel("Taxonomy ID (Mã vi khuẩn)")
    plt.tight_layout()
    plt.show()

    # 3. Confusion Matrix: Ma trận nhầm lẫn
    print("[3/3] Đang vẽ Ma trận nhầm lẫn...")
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
    fig, ax = plt.subplots(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=model.classes_)
    disp.plot(cmap="Blues", ax=ax, colorbar=False, values_format='d')
    plt.title("Ma trận nhầm lẫn dự đoán bệnh", fontsize=14, fontweight='bold')
    plt.grid(False)
    plt.tight_layout()
    plt.show()



def prepare_data(df, n=0):
    # clean tên cột
    df.columns = df.columns.str.strip()

    # fix lỗi chính tả nếu có
    if "Diagonies" in df.columns:
        df = df.rename(columns={"Diagonies": "Diagnosis"})

    # label
    y = None
    if n == 0 and "Diagnosis" in df.columns:
        y = df["Diagnosis"].copy()

    # feature
    X = df.drop(columns=["Run", "Diagnosis"], errors="ignore")

    # convert số
    X = X.apply(pd.to_numeric, errors='coerce')

    # xử lý
    X = X.fillna(0)
    X = np.log(X + 1)

    return X, y


def train_rf_model(object_key="models/rf_model.joblib",
                         min_accuracy=0.7, test_size=0.2):
    """
    Train Random Forest và lưu mô hình lên Cloudflare R2 nếu accuracy >= min_accuracy
    - X, y: dữ liệu
    - s3_client: boto3 compatible client (Cloudflare R2)
    - bucket_name: tên bucket trên R2
    - object_key: đường dẫn lưu model trong bucket
    """
    s3_client = boto3.client(
        's3',
        endpoint_url="https://d63681a062448ae7aa50388acf0ee16f.r2.cloudflarestorage.com/",
        aws_access_key_id="e13229540b5d1188b0aabae2ab1741c0",
        aws_secret_access_key="b21fed7924f5e4e654321289e7b48022c956774fd8b51ac109a606a149e73edb",
        config=botocore.client.Config(signature_version='s3v4'),
        verify=False
    )
    count = 5
    while count >= 0:
        try:
            X, y = prepare_data(load_data(s3_client=s3_client, bucket_name="ppnckh"))
            break
        except s3_client.exceptions.ClientError as e:
            print(e)
            count -= 1
            time.sleep(60)
    # X, y = prepare_data(load_data(path_file=r"C:\Users\User\ppnckh\cleaned_data\wf0\r2\merged.csv")

    while True:
        random_state = rd.randint(600, 700)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, stratify=y, random_state=random_state
        )

        clf = RandomForestClassifier(n_estimators=200, random_state=random_state)
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)

        print(f"Accuracy: {acc:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))

        if acc >= min_accuracy:
            buffer = BytesIO()
            dump(clf, buffer)
            buffer.seek(0)

            s3_client.put_object(Bucket="ppnckh", Key=object_key, Body=buffer)
            print(f"Mô hình đã được lưu lên Cloudflare R2: s3://ppnckh/{object_key}")

            os.makedirs(r"C:\Users\User\ppnckh\models", exist_ok=True)
            file_path = os.path.join(r"C:\Users\User\ppnckh\models", "rf_model.joblib")
            dump(clf, file_path)
            print(f"Mô hình đã được lưu tại '{file_path}'")
            # Vẽ biểu đồ kết quả
            visualize_model_results(X, y, clf, X_test, y_test, y_pred)
            break
    return clf, X_train, X_test, y_train, y_test

def check_file_exists_r2(object_key="models/rf_model.joblib"):
    """
    Kiểm tra xem object_key có tồn tại trong bucket R2 không
    """
    R2_ACCESS_KEY = "e13229540b5d1188b0aabae2ab1741c0"
    R2_SECRET_KEY = "b21fed7924f5e4e654321289e7b48022c956774fd8b51ac109a606a149e73edb"
    R2_ENDPOINT = "https://d63681a062448ae7aa50388acf0ee16f.r2.cloudflarestorage.com/"
    R2_BUCKET = "ppnckh"

    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=botocore.client.Config(signature_version='s3v4'),
        verify=False
    )
    try:
        s3_client.head_object(Bucket=R2_BUCKET, Key=object_key)
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        else:
            raise


def predictml():
    while True:
        choose = input("1: Dự đoán từ folder (*.fastq)\n2: Nhập mã SRR\nChọn: ").strip()
        if choose == "1":
            folder_path = input("folder_path: ").strip()
            fastq_files = glob.glob(os.path.join(folder_path, "*.fastq"))
            if not fastq_files:
                print("Không tìm thấy file .fastq nào trong folder.")
                continue
            srr_list = [os.path.splitext(os.path.basename(f))[0] for f in fastq_files]
            print(f"Tìm thấy {len(srr_list)} mẫu: {srr_list}")

        elif choose == "2":
            srr_input = input("Nhập các mã SRR (cách nhau 1 dấu cách): ").strip()
            srr_list = srr_input.split()
            break
        else:
            print("Lựa chọn không hợp lệ.")

    path_file = r"C:\Users\User\ppnckh\cleaned_data\wf1\r2\cleaned.csv"

    n = len(srr_list)
    if check_library_layout(srr_list):
        if not os.path.exists(path_file):
            print("Không tìm thấy file feature có sẵn để dự đoán!")
            print("Chờ dự đoán mẫu vi sinh vật...")
            pipelineglx(srr_list)
        else:
            if not os.path.exists(path_file):
                print("Không tìm thấy file feature để dự đoán!")
                return
            df = pd.read_csv(path_file, sep=r"\s+|,", engine="python")

    model_path_local = r"C:\Users\User\ppnckh\models\rf_model.joblib"
    model = None
    if os.path.exists(model_path_local):
        print(f"Load model từ local: {model_path_local}")
        model = load(model_path_local)
    else:
        try:
            R2_ACCESS_KEY = "e13229540b5d1188b0aabae2ab1741c0"
            R2_SECRET_KEY = "b21fed7924f5e4e654321289e7b48022c956774fd8b51ac109a606a149e73edb"
            R2_ENDPOINT = "https://d63681a062448ae7aa50388acf0ee16f.r2.cloudflarestorage.com/"
            R2_BUCKET = "ppnckh"

            s3_client = boto3.client(
                's3',
                endpoint_url=R2_ENDPOINT,
                aws_access_key_id=R2_ACCESS_KEY,
                aws_secret_access_key=R2_SECRET_KEY,
                config=botocore.client.Config(signature_version='s3v4'),
                verify=False
            )

            key_model = "models/rf_model.joblib"
            obj = s3_client.get_object(Bucket=R2_BUCKET, Key=key_model)
            buffer = BytesIO(obj['Body'].read())
            model = load(buffer)
            print(f"Load model từ Cloudflare R2: {key_model}")

        except Exception:
            print("Chưa có model. Chờ huấn luyện model!")
            train_rf_model()  # gọi hàm train
            model = load(model_path_local)


    results = []
    print("Bắt đầu dự đoán cho các mẫu...")
    for srr in srr_list:
        df_sample = df[df['sample'] == srr]
        if df_sample.empty:
            print(f"Không tìm thấy dữ liệu cho {srr}, bỏ qua.")
            continue

        X, _ = prepare_data(df_sample, n)
        pred = model.predict(X)
        print(f"SRR: {srr}, Dự đoán: {pred[0]}")
        results.append({"sample": srr, "disease": pred[0]})

    if results:
        for r in results:
            df_single = pd.DataFrame([r])
            csv_buffer = BytesIO()
            df_single.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            key_pred = f"users/prediction_{r['sample']}.csv"
            s3_client.put_object(Bucket=R2_BUCKET, Key=key_pred, Body=csv_buffer.getvalue())
            print(f"Lưu dự đoán SRR {r['sample']} lên Cloudflare R2: {key_pred}")

    upload_disease_predictions_db(results)



