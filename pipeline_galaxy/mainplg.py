import boto3
import botocore

from DataPreprocessing.cleaned_data import process_folder_r2, merge_label_r2, process_folder_db
from WorkFlowGalaxy.mainwfg import (
    connect_galaxy,
    read_srr_list,
)
from pipeline_galaxy.processed_file import count_downloaded
from pipeline_galaxy.send_downd_data import send_download
from Stored.upload_to_R2 import upload_folder_to_r2
from Stored.upload_to_database import upload_datafolder_to_db, upload_disease_r2_to_db


def pipelineglx(nsrr_list = None):
    # Thông tin Galaxy
    WORKFLOW_ID = "93241e9240c4f2cf"
    API_KEY = "eba707cffe5c6652689df32b30c4b863"
    GALAXY_URL = "https://galaxy-main.usegalaxy.org"
    gi = connect_galaxy(API_KEY, GALAXY_URL)

    # Thông tin Cloundflare
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

    if not nsrr_list:
        srr_list = read_srr_list(s3_client, R2_BUCKET, "train/SraRunTable.csv")
        send_download(gi=gi, WORKFLOW_ID= WORKFLOW_ID, srr_list= srr_list)
        print(f"Đã tải: {count_downloaded()}/220")

        process_folder_r2()
        process_folder_db()
        merge_label_r2(s3_client, R2_BUCKET)

        upload_folder_to_r2(r"C:\Users\User\ppnckh\output_workflow\wf0", r"train/output_workflow/wf0")
        upload_folder_to_r2(r"C:\Users\User\ppnckh\cleaned_data\wf0\r2", r"train/cleaned_data/wf0")
        upload_datafolder_to_db(r"C:\Users\User\ppnckh\cleaned_data\wf0\db\data", "traindata.data")
        upload_disease_r2_to_db(s3_client, R2_BUCKET)
    elif nsrr_list:
        n = len(nsrr_list)
        send_download(gi, WORKFLOW_ID, nsrr_list, n)

        print(f"Đã tải: {count_downloaded(n)}/{n}")

        process_folder_r2(n)
        process_folder_db(n)
        upload_folder_to_r2(r"C:\Users\User\ppnckh\output_workflow\wf1", r"users/output_workflow/wf1")
        upload_folder_to_r2(r"C:\Users\User\ppnckh\cleaned_data\wf1\r2", r"users/cleaned_data/wf1")
        upload_datafolder_to_db(r"C:\Users\User\ppnckh\cleaned_data\wf1\db\data", "users.data", n)
        print("Đã lưu mẫu vi sinh vật vào cơ sở dữ liệu")
