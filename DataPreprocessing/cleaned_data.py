import pandas as pd
import os
import glob
import io

def process_kraken_file(file_path):
    """
    Xử lý 1 file Kraken -> trả về 1 dòng dataframe (1 sample)
    """
    filename = os.path.basename(file_path)
    srr = filename.split(".")[0].split(" ")[0]

    df = pd.read_csv(file_path, sep=r"\s+", engine="python", header=None)

    df = df.iloc[:, :2]
    df.columns = ["Feature", "Value"]

    df["Feature"] = pd.to_numeric(df["Feature"], errors="coerce")
    df = df.dropna()

    df_t = df.set_index("Feature").T

    df_t.insert(0, "Run", srr)

    return df_t


def process_folder_r2(n = 0):
    if n == 0:
        input_folder = r"C:\Users\User\ppnckh\output_workflow\wf0"
        output_folder = r"C:\Users\User\ppnckh\cleaned_data\wf0\r2"
    else:
        input_folder = r"C:\Users\User\ppnckh\output_workflow\wf1"
        output_folder = r"C:\Users\User\ppnckh\cleaned_data\wf1\r2"

    output_file = os.path.join(output_folder, "cleaned.csv")

    os.makedirs(output_folder, exist_ok=True)

    all_data = []

    files = glob.glob(os.path.join(input_folder, "*.csv"))

    print(f"Tìm thấy {len(files)} file")

    for i, file_path in enumerate(files):
        try:
            df = process_kraken_file(file_path)
            all_data.append(df)
        except Exception as e:
            print(f"Lỗi file {file_path}: {e}")

    final_df = pd.concat(all_data, ignore_index=True).fillna(0)

    final_df.to_csv(output_file, index=False)

    print(f"\nDone! File lưu tại: {output_file}")

def merge_label_r2(s3_client, bucket, n = 0):
    if n == 0:
        local_file = r"C:\Users\User\ppnckh\cleaned_data\wf0\r2\cleaned.csv"
        output_file = r"C:\Users\User\ppnckh\cleaned_data\wf0\r2\merged.csv"
    else:
        local_file = r"C:\Users\User\ppnckh\cleaned_data\wf1\r2\cleaned.csv"
        output_file = r"C:\Users\User\ppnckh\cleaned_data\wf1\r2\merged.csv"
    r2_path_label = "train/label_ppnckh.csv"
    obj = s3_client.get_object(Bucket=bucket, Key=r2_path_label)
    data = obj['Body'].read()
    label_df = pd.read_csv(io.BytesIO(data))

    data_df = pd.read_csv(local_file)

    merged_df = pd.merge(data_df, label_df, on='Run', how='left')  # left join giữ nguyên dữ liệu local

    merged_df.to_csv(output_file, index=False)

    print(f"Merged xong! Lưu tại: {output_file}")

def process_folder_db(n = 0):
    if n == 0:
        input_folder = r"C:\Users\User\ppnckh\output_workflow\wf0"
        output_folder = r"C:\Users\User\ppnckh\cleaned_data\wf0\db\data"
    else:
        input_folder = r"C:\Users\User\ppnckh\output_workflow\wf1"
        output_folder = r"C:\Users\User\ppnckh\cleaned_data\wf1\db\data"

    os.makedirs(output_folder, exist_ok=True)

    files = glob.glob(os.path.join(input_folder, "*.csv"))

    print(f"Tìm thấy {len(files)} file")

    for i, file_path in enumerate(files):
        try:
            print(f"[{i + 1}/{len(files)}] Đang xử lý: {file_path}")
            df = process_kraken_file_db(file_path)

            base_name = os.path.basename(file_path)
            output_file = os.path.join(output_folder, f"{base_name}")

            df.fillna(0).to_csv(output_file, index=False)
            print(f"Đã lưu file: {output_file}")
        except Exception as e:
            print(f"Lỗi file {file_path}: {e}")

    print("\nDone! Tất cả file đã được xử lý.")

def process_kraken_file_db(file_path):
    """
    Xử lý 1 file Kraken -> trả về dataframe giữ nguyên chiều
    """
    filename = os.path.basename(file_path)
    srr = filename.split(".")[0].split(" ")[0]

    df = pd.read_csv(file_path, sep=r"\s+", engine="python", header=None)

    df = df.iloc[:, :2]
    df.columns = ["taxa_id", "abundance"]

    df["taxa_id"] = pd.to_numeric(df["taxa_id"], errors="coerce")
    df = df.dropna()

    df.insert(0, "sample", srr)

    return df
