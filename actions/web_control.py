import subprocess
import urllib.parse
import platform

def open_website(url):
    if not url.startswith("http"):
        if "百度" in url:
            url = "https://www.baidu.com"
        elif "B站" in url:
            url = "https://www.bilibili.com"
        else:
            url = f"https://{url}"
    open_url(url)

def navigate_to(destination, provider="baidu"):
    dest_encoded = urllib.parse.quote(destination)
    if provider == "baidu":
        url = f"https://map.baidu.com/search/{dest_encoded}"
    elif provider == "amap":
        url = f"https://www.amap.com/search?query={dest_encoded}"
    else:
        url = f"https://www.google.com/maps/search/{dest_encoded}"
    open_url(url)

def open_url(url):
    sys_name = platform.system().lower()
    if "windows" in sys_name:
        subprocess.Popen(["start", url], shell=True)
    elif "darwin" in sys_name:
        subprocess.Popen(["open", url])
    else:
        subprocess.Popen(["xdg-open", url])
