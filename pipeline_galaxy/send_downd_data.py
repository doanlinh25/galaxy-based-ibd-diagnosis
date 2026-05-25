import threading
import time
from WorkFlowGalaxy.mainwfg import send_workflow, download_kraken_biom_outputs, delete_history_safe
from pipeline_galaxy.shared_job import save_state_running, load_state_running,load_failed_srr,clear_failed_srr, load_state_delete, save_state_delete
from pipeline_galaxy.processed_file import count_downloaded
lock = threading.Lock()
max_running = 10
srr_cant_rerun = 0
download_done = False

def send_thread(gi, WORKFLOW_ID, srr_list, n):
    global srr_cant_rerun
    for srr in srr_list:
        while True:
            with lock:
                running_jobs = load_state_running(n)
                if len(running_jobs) <= max_running:
                    break
            time.sleep(30)
        with lock:
            fail_srrs = load_failed_srr(n)
        if srr not in fail_srrs:
            lst = send_workflow(gi = gi, workflow_id=WORKFLOW_ID, srr_list = [srr], n = n)
        if lst:
            with lock:
                current = load_state_running(n)
                current.append(lst[0])
                save_state_running(current, n)

                del_jobs = load_state_delete(n)
                del_jobs.append(lst[0])
                save_state_delete(del_jobs, n)
    with lock:
        failed_srrs = load_failed_srr(n)

    if failed_srrs:
        print(f"Còn {len(failed_srrs)} srr lỗi → gửi lại")

    for srr in failed_srrs:
        while True:
            with lock:
                running_jobs = load_state_running(n)
                if len(running_jobs) < max_running:
                    break
            time.sleep(30)

        lst = send_workflow(gi, WORKFLOW_ID, [srr])
        if lst:
            with lock:
                current = load_state_running(n)
                current.append(lst[0])
                save_state_running(current, n)

                del_jobs = load_state_delete(n)
                del_jobs.append(lst[0])
                save_state_delete(del_jobs, n)

        print(f"Tải lại {srr}")
    while True:
        if download_done:
            with lock:
                srr_cant_rerun = len(load_failed_srr(n))
                print(f"{srr_cant_rerun} không thể chạy lại.")
                clear_failed_srr(n)
                break
        else:
            time.sleep(180)
    print("Dừng send_thread !")

def download_thread(gi, n):
    global download_done
    while True:
        try:

            with lock:
                running_jobs = load_state_running(n)
                if not running_jobs:
                    if n == 0:
                        if count_downloaded(n) >= 220 - srr_cant_rerun:
                            break
                        else:
                            continue
                    else:
                        if count_downloaded(n) >= n - srr_cant_rerun:
                            break
                        else:
                            continue
            print("Doawnload thread!")
            download_kraken_biom_outputs(gi=gi, n=n)

        except:
            time.sleep(5)
            continue
    with lock:
        del_jobs = load_state_delete(n)
        for e in del_jobs:
            delete_history_safe(gi, e["history_id"], e["srr"], n)
    download_done = True
    print("Dừng download_thread!")


def send_download(gi, WORKFLOW_ID, srr_list, n = 0):
    t1 = threading.Thread(target=send_thread, args=(gi, WORKFLOW_ID, srr_list, n))
    t2 = threading.Thread(target=download_thread, args=(gi, n))

    t1.start()
    t2.start()
    t1.join()
    t2.join()