import os
import shutil
import threading
import time
import sys
import tkinter as tk
from functools import wraps
import pystray
from PIL import Image
import configparser
import chardet
# python -m venv .venv
# .venv\Scripts\activate.ps1
# pyinstaller -F -w main.py -i logo.png -n 旧文件自动送走 --add-data="logo.png;."


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def check_disk_space(folder_path_1, threshold_percentage_1):
    global folder_path, threshold_percentage, settings_changed

    if settings_changed == True:
        folder_path_1 = folder_path
        threshold_percentage_1 = threshold_percentage
        settings_changed = False

    folder_path = folder_path_1
    threshold_percentage = threshold_percentage_1

    total, used, free = shutil.disk_usage(folder_path)
    # print("Total: %d GiB" % (total // (2**30)))
    # print("Used: %d GiB" % (used // (2**30)))
    # print("Free: %d GiB" % (free // (2**30)))
    used_percentage = (used/total)*100
    # print(used_percentage)
    if used_percentage >= threshold_percentage:
        # 执行删除操作
        delete_oldest_folder(folder_path)

    else:
        console_print("磁盘未满，无需删除文件夹。")


def delete_oldest_folder(folder_path):
    if not os.path.exists(folder_path):
        console_print("无文件夹，请修改设置。")
        return
    folders = [f for f in os.listdir(folder_path) if os.path.isdir(
        os.path.join(folder_path, f))]
    if not folders:
        console_print("无子文件夹，检测文件。")
        files = [f for f in os.listdir(folder_path) if not os.path.isdir(
            os.path.join(folder_path, f))]
        if not files:
            return
    if folders:
        target = folders
    else:
        if files:
            target = files
        else:
            return
    folder_times = [(f, get_folder_datetime(f, folder_path)) for f in target]
    # print(folder_times)
    oldest_folder = min(folder_times, key=lambda x: x[1])
    folder_name, folder_datetime = oldest_folder
    folder_path = os.path.join(folder_path, folder_name)
    # 递归删除文件夹及其内容
    if folders:
        shutil.rmtree(folder_path)
        console_print(f"已删除最早创建的文件夹:{folder_name}(创建时间:{folder_datetime})")
    else:
        if files:
            os.remove(folder_path)
            console_print(f"已删除最早创建的文件:{folder_name}(创建时间:{folder_datetime})")
        else:
            return


def get_folder_datetime(folder_name, folder_path):
    try:
        datetime_str = folder_name.split('年')[0], folder_name.split(
            '年')[1].split('月')[0], folder_name.split('月')[1]
        datetime_str = '-'.join(datetime_str)
        # 解析日期时间

        return time.mktime(time.strptime(datetime_str, "%Y-%m-%d"))
    except:
        return get_folder_creation_time(folder_name, folder_path)


def get_folder_creation_time(folder_name, folder_path):
    full_path = os.path.join(folder_path, folder_name)
    try:
        creation_time = os.path.getctime(full_path)
        # print(creation_time)
        return creation_time
    except Exception as e:
        console_print(f"无法获取文件夹创建时间:{e}")
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
def make_file(folder_path, filename, file_Data):
    file_uri = folder_path+"\\"+filename+".txt"
    if os.path.exists(file_uri):
        pass
    else:
        with open(file_uri, "w", encoding="utf-8") as f:
            f.write(file_Data)


def on_quit():
    global icon
    icon.stop()
    os._exit(0)


@new_thread
def run_app():
    global app_runned
    if app_runned == True:
        return
    app_runned = True
    console_print("自动删除旧文件")
    console_print("监视文件夹路径:"+folder_path)
    console_print("磁盘使用阈值:"+str(threshold_percentage))
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    while True:
        if settings_changed == True:
            console_print("监视文件夹路径:" + folder_path)
            console_print("磁盘使用阈值:"+str(threshold_percentage))
        check_disk_space(folder_path, threshold_percentage)
        time.sleep(1)


@new_thread
def full_disk():
    console_print("装满磁盘")
    file_Data = get_file_data()
    make_random_file = True
    if make_random_file == True:
        for i in range(1, 10000):
            total, used, free = shutil.disk_usage(folder_path)
            if free < 1024*1024*1024:
                break
            make_file(folder_path, str(i), file_Data)
    console_print("装满磁盘结束")
    pass


def input_folder_path():
    def get_input():
        global folder_path, settings_changed
        folder_path_new = entry.get()
        if not os.path.exists(folder_path_new):
            pass
        else:
            if folder_path_new[-1] != '\\':
                folder_path_new += '\\'
            folder_path = folder_path_new
            settings_changed = True
        if settings_changed == True:
            try:
                config.add_section('Config')  # 首先添加一个新的section
            except:
                pass
            config.set('Config', 'folder_path', folder_path)  # 写入数据
            config.write(open(configpath, 'r+', encoding='utf-8'))  # 保存数据
        root.destroy()
    root = tk.Toplevel(mainwin)
    root.title("输入文件夹路径")
    entry = tk.Entry(root, width=50)
    entry.insert(0, str(folder_path))
    entry.pack()
    button = tk.Button(root, text="确定", command=get_input)
    button.pack()
    # root.mainloop()

    return folder_path


def input_threshold_percentage():
    def get_input():
        global threshold_percentage, settings_changed
        try:
            threshold_percentage = int(entry.get())
            if threshold_percentage < 0 or threshold_percentage > 100:
                threshold_percentage = 90
            settings_changed = True
        except:
            pass
        if settings_changed == True:
            try:
                config.add_section('Config')  # 首先添加一个新的section
            except:
                pass
            config.set('Config', 'threshold_percentage',
                       str(threshold_percentage))  # 写入数据
            config.write(open(configpath, 'r+', encoding='utf-8'))  # 保存数据

        root.destroy()
    root = tk.Toplevel(mainwin)
    root.title("输入磁盘使用阈值")
    entry = tk.Entry(root, width=50)
    entry.insert(0, str(threshold_percentage))
    entry.pack()
    button = tk.Button(root, text="确定", command=get_input)
    button.pack()
    # root.mainloop()

    return threshold_percentage


def prepare_conf_file(configpath):  # 准备配置文件
    if os.path.isfile(configpath) == True:
        pass
    else:
        config.add_section("Config")
        config.set("Config", "folder_path", "d:\\ZhaoPian\\")
        config.set("Config", "threshold_percentage", r"90")
        # write to file
        config.write(open(configpath, "w", encoding='utf-8'))
        pass
    pass


def get_conf_from_file(config_path, config_section, conf_list):  # 读取配置文件
    conf_default = {
        "folder_path": "d:\\ZhaoPian\\",
        "threshold_percentage": "90",
    }
    with open(config_path, "rb") as f:
        result = chardet.detect(f.read())
        encoding = result["encoding"]
    config.read(config_path, encoding=encoding)
    conf_item_settings = []
    for conf_item in conf_list:
        try:
            conf_item_setting = config[config_section][conf_item]

            # 获取 列表类型的配置项
            if conf_item == "email_receivers":
                item_nodes = conf_item_setting.split(",")
                conf_item_setting = []
                for item_node in item_nodes:
                    conf_item_setting.append(item_node)
        except Exception as e:
            conf_item_setting = conf_default[conf_item]

        console_print(str(conf_item) + ":" + str(conf_item_setting))
        conf_item_settings.append(conf_item_setting)
        pass
    if len(conf_list) > 1:
        return tuple(conf_item_settings)
    else:
        return conf_item_settings[0]


def textpad_insert(text, f):
    if text.get("1.0", "end") == "\n":
        text.insert(tk.END, f)
    else:
        text.insert(tk.END, f+"\n")
    pass


def console_print(text):
    global textpad
    mainwin.after(500, textpad_insert, textpad, text)
    pass


def sw_console():
    global console_show
    if console_show == 0:
        mainwin.deiconify()
        console_show = 1
    else:
        mainwin.withdraw()
        console_show = 0
    pass


@new_thread
def sys_panel():
    global icon
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
            pystray.MenuItem("控制台", sw_console),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", on_quit)
        )
    )

    icon.run()


if __name__ == "__main__":
    icon = None
    app_runned = False
    sys_panel()
    mainwin = tk.Tk()
    mainwin.title("控制台")
    mainwin.geometry("600x600")
    textpad = tk.Text(mainwin, undo=False)
    textpad.pack(expand=True, fill='both')
    textpad.insert(tk.END, "开启控制台\n")
    console_show = 1
    mainwin.protocol("WM_DELETE_WINDOW", sw_console)
    mainwin.withdraw()
    console_show = 0

    config = configparser.ConfigParser()  # 类实例化

    # 定义文件路径
    configpath = r".\setup.ini"
    prepare_conf_file(configpath)
    (
        folder_path,
        threshold_percentage,
    ) = get_conf_from_file(
        configpath,
        "Config",
        [
            "folder_path",
            "threshold_percentage",
        ],
    )

    # 设置磁盘使用阈值，超过该阈值将触发删除操作
    try:
        threshold_percentage = int(threshold_percentage)
        if threshold_percentage < 0 or threshold_percentage > 100:
            threshold_percentage = 90
        settings_changed = True
    except:
        threshold_percentage = 90
    # 设置监视文件夹路径
    if folder_path[-1] != '\\':
        folder_path += '\\'

    settings_changed = False  # 设置是否更改过监视文件夹路径或磁盘使用阈值
    mainwin.mainloop()
