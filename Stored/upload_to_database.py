import os
import glob
from io import BytesIO

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values


def parse_table_name(table_name):
    if "." in table_name:
        return table_name.split(".", 1)
    return "public", table_name


def get_connection():
    return psycopg2.connect(
        dbname="ppnckh",
        user="postgres",
        password="2005",
        host="localhost",
        port="5432"
    )


def upload_datafolder_to_db(input_folder, table_name, batch_size=1000):
    schema_name, table_only = parse_table_name(table_name)
    print(f"Insert vào: {schema_name}.{table_only}")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        sql.SQL("CREATE SCHEMA IF NOT EXISTS {};")
        .format(sql.Identifier(schema_name))
    )

    cur.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS {}.{} (
            sample VARCHAR(50),
            taxa_id INTEGER,
            abundance NUMERIC(20,5),
            PRIMARY KEY (sample, taxa_id)
        )
    """).format(
        sql.Identifier(schema_name),
        sql.Identifier(table_only)
    ))
    conn.commit()

    files = glob.glob(os.path.join(input_folder, "*.csv"))
    print(f"Tìm thấy {len(files)} file")

    for i, file_path in enumerate(files):
        try:
            print(f"[{i + 1}/{len(files)}] {file_path}")

            df = pd.read_csv(file_path, sep=r"\s+|,", engine="python")

            if not {"sample", "taxa_id", "abundance"}.issubset(df.columns):
                df.columns = ["sample", "taxa_id", "abundance"]

            df["taxa_id"] = pd.to_numeric(df["taxa_id"], errors="coerce")
            df["abundance"] = pd.to_numeric(df["abundance"], errors="coerce")

            df = df.dropna(subset=["sample", "taxa_id", "abundance"])
            df = df.drop_duplicates(subset=["sample", "taxa_id"])

            rows = df[["sample", "taxa_id", "abundance"]].values.tolist()
            if not rows:
                continue

            insert_query = sql.SQL("""
                INSERT INTO {}.{} (sample, taxa_id, abundance)
                VALUES %s
                ON CONFLICT (sample, taxa_id)
                DO UPDATE SET abundance = EXCLUDED.abundance
            """).format(
                sql.Identifier(schema_name),
                sql.Identifier(table_only)
            )

            for start in range(0, len(rows), batch_size):
                execute_values(cur, insert_query, rows[start:start + batch_size])

            conn.commit()

        except Exception as e:
            print(f"Lỗi {file_path}: {e}")
            conn.rollback()

    cur.close()
    conn.close()
    print("Hoàn tất data")


def upload_disease_r2_to_db(s3_client, bucket_name, table_name="traindata.diseases"):
    schema_name, table_only = parse_table_name(table_name)
    print(f"Insert vào: {schema_name}.{table_only}")

    obj = s3_client.get_object(Bucket=bucket_name, Key="train/label_ppnckh.csv")
    df = pd.read_csv(BytesIO(obj['Body'].read()))

    df = df.rename(columns={"Run": "sample", "Diagnosis": "disease"})
    df = df.dropna(subset=["sample", "disease"])
    rows = df[["sample", "disease"]].values.tolist()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {};")
                .format(sql.Identifier(schema_name)))

    cur.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS {}.{} (
            sample VARCHAR(50) PRIMARY KEY,
            disease VARCHAR(100)
        )
    """).format(
        sql.Identifier(schema_name),
        sql.Identifier(table_only)
    ))
    conn.commit()

    insert_query = sql.SQL("""
        INSERT INTO {}.{} (sample, disease)
        VALUES %s
        ON CONFLICT (sample) DO NOTHING
    """).format(
        sql.Identifier(schema_name),
        sql.Identifier(table_only)
    )

    execute_values(cur, insert_query, rows)
    conn.commit()

    cur.close()
    conn.close()
    print("Hoàn tất disease R2")


def upload_disease_predictions_db(predictions, table_name="users.diseases"):
    if not predictions:
        print("Không có dữ liệu")
        return

    schema_name, table_only = parse_table_name(table_name)
    print(f"Insert vào: {schema_name}.{table_only}")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {};")
                .format(sql.Identifier(schema_name)))

    cur.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS {}.{} (
            sample VARCHAR(50) PRIMARY KEY,
            disease VARCHAR(100)
        )
    """).format(
        sql.Identifier(schema_name),
        sql.Identifier(table_only)
    ))
    conn.commit()

    rows = [(r['sample'], r['disease']) for r in predictions]

    insert_query = sql.SQL("""
        INSERT INTO {}.{} (sample, disease)
        VALUES %s
        ON CONFLICT (sample)
        DO UPDATE SET disease = EXCLUDED.disease
    """).format(
        sql.Identifier(schema_name),
        sql.Identifier(table_only)
    )

    execute_values(cur, insert_query, rows)
    conn.commit()

    cur.close()
    conn.close()
    print(f"Đã lưu {len(rows)}prediction")