import os
import time
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.config import Config
from boto3.s3.transfer import TransferConfig

R2_ACCESS_KEY = "e13229540b5d1188b0aabae2ab1741c0"
R2_SECRET_KEY = "b21fed7924f5e4e654321289e7b48022c956774fd8b51ac109a606a149e73edb"
R2_ENDPOINT = "https://d63681a062448ae7aa50388acf0ee16f.r2.cloudflarestorage.com"
R2_BUCKET = "ppnckh"

session = boto3.session.Session()

s3 = session.client(
    service_name="s3",
    endpoint_url=R2_ENDPOINT.rstrip("/"),
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    verify=False,
    config=Config(
        signature_version="s3v4",
        retries={
            "max_attempts": 10,
            "mode": "standard"
        },
        max_pool_connections=20
    )
)

transfer_config = TransferConfig(
    multipart_threshold=10 * 1024 * 1024,
    multipart_chunksize=5 * 1024 * 1024,
    max_concurrency=5,
    use_threads=True
)

def upload_folder_to_r2(path_folder, cloudflare_path, max_workers=4):
    all_files = []

    for root, _, files in os.walk(path_folder):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, path_folder)
            r2_key = f"{cloudflare_path}/{rel_path}".replace("\\", "/")
            all_files.append((full_path, r2_key))

    print(f"Total files: {len(all_files)}")

    def upload_file(local_path, r2_key):
        for i in range(5):
            try:
                start = time.time()

                s3.upload_file(
                    local_path,
                    R2_BUCKET,
                    r2_key,
                    Config=transfer_config
                )

                print(f"OK: {local_path} ({time.time() - start:.2f}s)")
                return "ok"

            except Exception as e:
                print(f"Retry {i} - {local_path}: {e}")
                time.sleep(2 ** i)

        return "fail"

    results = {"ok": 0, "fail": 0}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(upload_file, f[0], f[1]) for f in all_files]

        for future in as_completed(futures):
            results[future.result()] += 1

    return results
