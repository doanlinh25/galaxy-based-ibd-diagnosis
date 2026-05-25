import functools
import threading

from bioblend.galaxy import GalaxyInstance
import pandas as pd
import requests
import random
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import io
import os
import time
from pipeline_galaxy.shared_job import save_state_running, load_state_running, save_failed_srr, save_state_delete, load_state_delete

lock = threading.Lock()
# Tắt warning SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
session = requests.Session()

def connect_galaxy(API_KEY, GALAXY_URL, max_retries=5):
    try:
        retries = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"]
        )

        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Connection": "keep-alive"
        })

        gi = GalaxyInstance(
            url=GALAXY_URL,
            key=API_KEY
        )

        gi.session = session
        gi.session.verify = False
        orig_request = gi.session.request

        @functools.wraps(orig_request)
        def wrapper(*args, **kwargs):
            if "timeout" not in kwargs:
                kwargs["timeout"] = (5, 15)  # connect/read timeout
            return orig_request(*args, **kwargs)

        gi.session.request = wrapper
        return gi
    except Exception as e:
        print(f"Lỗi kết nối Galaxy: {e}")
        return None
def read_srr_list(s3_client, bucket, key):
    """
    Đọc file CSV chứa danh sách SRR từ Cloudflare R2.

    Params:
        s3_client : boto3 client đã tạo
        bucket : tên bucket
        key : đường dẫn file trên cloud (R2 key)

    Returns:
        lst : danh sách SRR (list of str)
    """
    # Tải file từ R2 về bộ nhớ
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    data = obj['Body'].read()

    # Chuyển bytes sang pandas DataFrame
    df = pd.read_csv(io.BytesIO(data))

    # Chuyển cột 'Run' thành list string
    lst = df['Run'].astype(str).str.strip().tolist()
    return lst

def check_library_layout(srr_id, retries=5):
    url = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={srr_id}&result=read_run&fields=library_layout&format=json"

    for attempt in range(retries):
        try:
            response = session.get(
                url,
                timeout=(5, 20),
                verify=False
            )

            response.raise_for_status()
            data = response.json()

            if not data:
                return "NO_DATA_RETURNED"

            layout = data[0].get("library_layout")
            return layout.upper() if layout else "UNKNOWN"

        except requests.exceptions.SSLError as e:
            print(f"[{srr_id}] SSL lỗi: {e}")
        except requests.exceptions.RequestException as e:
            print(f"[{srr_id}] Network lỗi: {e}")

        time.sleep(60 + attempt)

    return "ERROR_NETWORK"

def filter_paired_end(srr_list):
    ds_paired_end = []

    for srr in srr_list:
        layout = check_library_layout(srr)

        if layout == "PAIRED":
            ds_paired_end.append(srr)
        elif layout != "SINGLE":
            print(f"{srr}: Lỗi hệ thống → {layout}")

        time.sleep(random.uniform(1.5, 3))

    return ds_paired_end

def send_workflow(gi, workflow_id, srr_list,retries=10, n = 0):
    if n == 0:
        path_output_workflow = r"C:\Users\User\ppnckh\output_workflow\wf0"
    else :
        path_output_workflow = r"C:\Users\User\ppnckh\output_workflow\wf1"
    lstHistory = []
    with lock:
        current = load_state_running(n)
        current = [lst["srr"] for lst in current]

    for index, srr in enumerate(srr_list):
        if srr in current or os.path.exists(os.path.join(path_output_workflow, f"{srr}.csv")) or srr == "SRR6468544":
            continue
        sent_arr = False
        attempt = retries
        while attempt > 0:
            try:
                parameters = {"0": {"input|accession": srr}}

                invocation = gi.workflows.invoke_workflow(
                    workflow_id=workflow_id,
                    inputs={},
                    params=parameters,
                    history_name=f"{srr}"
                )

                hist_id = invocation.get('history_id')
                invocation_id = invocation.get('id')
                if not hist_id:
                    raise ValueError("Không nhận được history_id")
                if not invocation_id:
                    raise ValueError("Không nhận được invocation_id")

                lstHistory.append({"srr": srr, "history_id": hist_id, "invocation_id": invocation_id})

                now = datetime.now().strftime("%H:%M:%S")
                print(f"[{now}] OK: {srr} ({hist_id})")

                time.sleep(30)
                sent_arr = True
                break

            except Exception as e:
                attempt -= 1
                print(f"[s]{srr} lỗi: {e} | còn {attempt} lần")
                time.sleep(20)
        if not sent_arr:
            save_failed_srr(srr, n)
    return lstHistory


def download_kraken_biom_outputs(
    gi,
    n = 0,
    max_retries=10,
    retry_interval=180
):
    if n == 0:
        output_dir = r"C:\Users\User\ppnckh\output_workflow\wf0"
    else:
        output_dir = r"C:\Users\User\ppnckh\output_workflow\wf1"
    os.makedirs(output_dir, exist_ok=True)

    downloaded_ids = set()

    while True:
        with lock:
            running_jobs = load_state_running(n)

        if not running_jobs:
            print("Không còn job")
            break

        new_jobs = load_new_jobs(n)

        for item in running_jobs:
            srr = item["srr"]
            hist_id = item["history_id"]
            invocation_id = item["invocation_id"]
            file_path = os.path.join(output_dir, f"{srr}.csv")
            err_wf = False
            waiting = True
            downloaded = False

            if os.path.exists(file_path):
                print(f"{srr} đã tồn tại")
                with lock:
                    new_jobs = load_state_running(n)
                    new_jobs.remove(item)
                    save_state_running(new_jobs, n)
                delete_history_safe(gi, hist_id, srr)
                continue
            for i in range(max_retries):
                try:
                    inv, state_conn = connect_invocation_safe(gi, invocation_id, srr)
                    if not state_conn:
                        waiting = True
                        break
                    else:
                        if inv["state"] == "completed":
                            datasets = gi.histories.show_history(hist_id, contents=True)
                            for ds in datasets:
                                if ds.get("state") in ["error", "failed"]:
                                    err_wf = True
                                    print(f"{srr} lỗi workflow!")
                                    delete_history_safe(gi, hist_id, srr)
                                    print(f"{srr} -> save_failed_srr.csv")
                                    save_failed_srr(srr, n)
                                    waiting = False
                                    break
                                if ds.get("type") != "file":
                                    continue
                                if ds.get("state") != "ok":
                                    continue
                                name = ds.get("name", "").lower()
                                if "kraken" not in name or "biom" not in name:
                                    continue

                                dataset_id = ds["id"]

                                if dataset_id in downloaded_ids:
                                    continue

                                downloaded = download_output_safe(gi, dataset_id, srr, file_path)
                                downloaded_ids.add(dataset_id)
                                if downloaded:
                                    waiting = False
                                    delete_history_safe(gi, hist_id, srr, n)
                                    with lock:
                                        new_jobs = load_state_running(n)
                                        new_jobs.remove(item)
                                        save_state_running(new_jobs, n)
                                    break
                            break
                        else:
                            waiting = True
                            break
                except requests.exceptions.RequestException as e:
                    waiting = True
                    print(f"Lỗi kết nối || tải {srr}")
                    time.sleep(30)
                if err_wf:
                    break
            if not waiting:
                with lock:
                    new_jobs = load_state_running(n)
                    new_jobs.remove(item)
                    del_jobs = load_state_delete(n)
                    save_state_delete(del_jobs, n)
                    save_state_running(new_jobs, n)
        if new_jobs:
            print(f"Chờ {retry_interval}s | còn {len(new_jobs)} job")
            time.sleep(retry_interval)

    print(f"HOÀN TẤT")

def delete_history_safe(gi, hist_id, srr, n = 0,retries=5):
    for i in range(retries):
        try:
            gi.histories.delete_history(hist_id, purge=True)
            print(f"Đã xóa {srr}")
            with lock:
                jobs = load_state_delete(n)
                jobs = [job for job in jobs if job["srr"] != srr]
                save_state_delete(jobs, n)
            print(f"Đã xóa khỏi danh sách xóa.")
            return True
        except Exception as e:
            print(f"Lỗi xóa {srr}: {e}")
            time.sleep(20)
    with lock:
        jobs = load_state_delete(n)
        jobs = [job for job in jobs if job["srr"] != srr]
        save_state_delete(jobs, n)
    print(f"Đã xóa khỏi danh sách xóa.")
    return False

def connect_invocation_safe(gi,invocation_id , srr, retries=5):
    for i in range(retries):
        try:
            inv = gi.invocations.show_invocation(invocation_id)
            print(f"[{srr}] đã kết nối.")
            return (inv, True)
        except Exception as e:
            print(f"Lỗi kết nối {srr}: {e}")
            time.sleep(60)

    return (None, False)

def download_output_safe(gi,dataset_id , srr, file_path,retries=10):
    for i in range(retries):
        try:
            gi.datasets.download_dataset(
                dataset_id,
                file_path=file_path,
                use_default_filename=False
            )
            print(f"Đã tải {srr}")
            return True
        except Exception as e:
            print(f"Lỗi tải {srr}")
            time.sleep(60)
    return False

def load_new_jobs(n):
    with lock:
        return load_state_running(n)