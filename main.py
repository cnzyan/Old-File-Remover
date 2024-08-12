import os
import shutil
import threading
import time
import sys
import tkinter as tk
from functools import wraps

# python -m venv .venv
# .venv\Scripts\activate.ps1
# pyinstaller -F -w main.py -i logo.png -n 旧文件自动送走 --add-data="logo.png;."



def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def check_disk_space(folder_path_1, threshold_percentage_1):
    global folder_path, threshold_percentage,settings_changed
    
    if settings_changed==True:
        folder_path_1=folder_path
        threshold_percentage_1=threshold_percentage
        settings_changed=False
        
    folder_path = folder_path_1
    threshold_percentage = threshold_percentage_1
    
    total, used, free = shutil.disk_usage(folder_path)
    #print("Total: %d GiB" % (total // (2**30)))
    #print("Used: %d GiB" % (used // (2**30)))
    #print("Free: %d GiB" % (free // (2**30)))
    used_percentage = (used/total)*100
    # print(used_percentage)
    if used_percentage >= threshold_percentage:
        # 执行删除操作
        delete_oldest_folder(folder_path)

    else:
        print("磁盘未满，无需删除文件夹。")


def delete_oldest_folder(folder_path):
    folders = [f for f in os.listdir(folder_path) if os.path.isdir(
        os.path.join(folder_path, f))]
    if not folders:
        print("无子文件夹，检测文件。")
        files = [f for f in os.listdir(folder_path) if not os.path.isdir(
            os.path.join(folder_path, f))]
        if not files:
            return
    if folders:
        target = folders
    if files:
        target = files
    folder_times = [(f, get_folder_datetime(f, folder_path)) for f in target]
    # print(folder_times)
    oldest_folder = min(folder_times, key=lambda x: x[1])
    folder_name, folder_datetime = oldest_folder
    folder_path = os.path.join(folder_path, folder_name)
    # 递归删除文件夹及其内容
    if folders:
        shutil.rmtree(folder_path)
        print(f"已删除最早创建的文件夹:{folder_name}(创建时间:{folder_datetime})")
    if files:
        os.remove(folder_path)
        print(f"已删除最早创建的文件:{folder_name}(创建时间:{folder_datetime})")


def get_folder_datetime(folder_name, folder_path):
    try:
        datetime_str = folder_name.split('年')[0], folder_name.split(
            '年')[1].split('月')[0], folder_name.split('月')[1]
        datetime_str = '-'.join(datetime_str)
        # 解析日期时间

        return time.mktime(time.strptime(datetime_str,"%Y-%m-%d"))
    except:
        return get_folder_creation_time(folder_name, folder_path)


def get_folder_creation_time(folder_name, folder_path):
    full_path = os.path.join(folder_path, folder_name)
    try:
        creation_time = os.path.getctime(full_path)
        # print(creation_time)
        return creation_time
    except Exception as e:
        print(f"无法获取文件夹创建时间:{e}")
        return None


def get_file_data():
    f = ""
    for i in range(1, 99999):
        f = f+("odsfbsdjhfjkdhskhfashjdhkahdkjashdjkahdjkhdkjahsdkhakdhakjdhkajhdka\n")
    return f


def new_thread(func):

    @wraps(func)
    def inner(*args, **kwargs):
        # print(f'函数的名字：{func.__name__}')
        # print(f'函数的位置参数：{args}')
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()

    return inner


@new_thread
def make_file(folder_path, filename,file_Data):
    file_uri = folder_path+"\\"+filename+".txt"
    if os.path.exists(file_uri):
        pass
    else:
        with open(file_uri, "w", encoding="utf-8") as f:
            f.write(file_Data)
            
def on_quit():
    icon.stop()
    os._exit(0)
    
@new_thread
def run_app():
    print("自动删除旧文件")
    print("监视文件夹路径:", folder_path)
    print("磁盘使用阈值:", threshold_percentage)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    while True:
        if settings_changed==True:
            print("监视文件夹路径:", folder_path)
            print("磁盘使用阈值:", threshold_percentage)
        check_disk_space(folder_path, threshold_percentage)
        time.sleep(1)


@new_thread
def full_disk():
    print("装满磁盘")
    file_Data = get_file_data()
    make_random_file = True
    if make_random_file == True:
        for i in range(1, 10000):
            total, used, free = shutil.disk_usage(folder_path)
            if free < 1024*1024*1024:
                break
            make_file(folder_path, str(i),file_Data)
    print("装满磁盘结束")
    pass

def input_folder_path():
    def get_input():
        global folder_path,settings_changed
        folder_path_new = entry.get()
        if not os.path.exists(folder_path_new):
            pass
        else:
            if folder_path_new[-1] != '\\':
                folder_path_new += '\\'
            folder_path = folder_path_new
            settings_changed = True
        root.destroy()
    root = tk.Tk()
    root.title("输入文件夹路径")
    entry = tk.Entry(root, width=50)
    entry.insert(0, str(folder_path))
    entry.pack()
    button = tk.Button(root, text="确定", command=get_input)
    button.pack()
    root.mainloop()

    return folder_path

def input_threshold_percentage():
    def get_input():
        global threshold_percentage,settings_changed
        try:
            threshold_percentage = int(entry.get())
            if threshold_percentage < 0 or threshold_percentage > 100:
                threshold_percentage = 90
            settings_changed = True
        except:
            pass
        root.destroy()
    root = tk.Tk()
    root.title("输入磁盘使用阈值")
    entry = tk.Entry(root, width=50)
    entry.insert(0, str(threshold_percentage))
    entry.pack()
    button = tk.Button(root, text="确定", command=get_input)
    button.pack()
    root.mainloop()

    return threshold_percentage
if __name__ == "__main__":

    threshold_percentage = 90  # 设置磁盘使用阈值，超过该阈值将触发删除操作
    folder_path = "d:\\ZhaoPian\\"  # 将路径替换为你的文件夹路径
    settings_changed=False  # 设置是否更改过监视文件夹路径或磁盘使用阈值
    import pystray
    from PIL import Image
    icon = pystray.Icon(
        name="旧文件自动送走",
        title="旧文件自动送走",
        icon=Image.open(get_resource_path("./logo.png")),
        menu=pystray.Menu(
            pystray.MenuItem("自动删除旧文件", run_app),
            # pystray.MenuItem("装满磁盘", full_disk),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("设置监视文件夹", input_folder_path),
            pystray.MenuItem("设置磁盘空间阈值", input_threshold_percentage),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", on_quit)
        )
    )

    icon.run()
