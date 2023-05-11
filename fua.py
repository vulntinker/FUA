import requests
from bs4 import BeautifulSoup
import re
import sys 
import urllib3
import random
from urllib.parse import urlsplit
from termcolor import colored
import argparse
import threading
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# reg_match = [r'([a-zA-Z0-9_-]+\s*/\s*[a-zA-Z0-9_+-=?]+(?:\s*/\s*[a-zA-Z0-9_+-=?]+)*)']
reg_match = [
    r'"(/[a-zA-Z0-9_+-]+/[a-zA-Z0-9_+-?=]+(?:/[a-zA-Z0-9_+-?=]+)*)"',
    r'"([a-zA-Z0-9_+-]+/[a-zA-Z0-9_+-?=]+(?:/[a-zA-Z0-9_+-?=]+)*)"',
    r'"(post /[a-zA-Z0-9_+-]+/[a-zA-Z0-9_+-?=]+(?:/[a-zA-Z0-9_+-?=]+)*)"',
    r'"(get /[a-zA-Z0-9_+-]+/[a-zA-Z0-9_+-?=]+(?:/[a-zA-Z0-9_+-?=]+)*)"',
    r"'(/[a-zA-Z0-9_+-]+/[a-zA-Z0-9_+-?=]+(?:/[a-zA-Z0-9_+-?=]+)*)'",
    r"'([a-zA-Z0-9_+-]+/[a-zA-Z0-9_+-?=]+(?:/[a-zA-Z0-9_+-?=]+)*)'"
]

# reg_match = [
#     r"['\"]?((?:post|get)?\s/[\w+-]+(?:/[\w+-?]+)*)['\"]?"
# ]
# Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36

baseAPI = ""
baseAPI_list = []
req_url = []
total_js = []
rel_fliter = []
js_black_list = [
    "text/plain","+n/100+","text/plain","a/i","DD/MM/YYYY","YYYY/MM/DD","MM/D/YYYY","application/x-www-form-urlencoded","DD/M/YYYY","text/javascript","text/xml","M/D/yy","a/b","image/svg+xml","YYYY/M/D","text/css","D/M/YYYY","MM/DD/YYYY","D/JM","application/json","assets/profile","text/ng-template","multipart/form-data","pan/move","lineX/Y","application/x-www-form-urlencoded;charset="
]

print_lock = threading.Lock()

def make_request(url, data={},auth_type="",token="",num=0,total=0,single_request=False):
    try:
        headers = {'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.32(0x18002035) NetType/WIFI Language/zh_CN'}
        
        if token != None and auth_type != None:
            headers.update({auth_type:token})
        
        if single_request:
            res = requests.get(url=url,headers=headers,verify=False,timeout=60)
            return res
        response_get = requests.get(url, headers=headers,verify=False,timeout=60)
        echo_res(url=url,method="GET",res_code=response_get.status_code,res_text=response_get.text,current_num=num,total_num=total)
        
        response_post = requests.post(url, json=data, headers=headers,verify=False,timeout=60)
        echo_res(url=url,method="POST",res_code=response_post.status_code,res_text=response_post.text,current_num=num,total_num=total)
        return response_get,response_post
    except Exception as e:
        print(colored("\n\n[!] Request ERR: "+str(e),"green"))
        pass


def echo_res(url, method, res_code, res_text, current_num, total_num):
    print_lock.acquire() # 获取锁
    try:
        # global rel_fliter
        sys.stdout.write("\033[2K\033[G" + "[+] ({0}/{1}) [{2}] URL: {3}".format(current_num, total_num, method, url))
        sys.stdout.flush()
        file = open(urlsplit(url).netloc + ".txt", "a")
        if res_code in (200,301,302,500) and all(x not in res_text for x in ("<html>", "<!doctype html>", "<!DOCTYPE html>","<!DOCTYPE HTML>","</script>", ":401", "<title>", 'status":-1', ":404",'"-4"',"<div","没有权限")):
            file.write("\n\n" + url + '\t\t' + str(res_code) + '\t\t' + method + '\n\n' + res_text + "\n\n\n")
            print("\n\n")
            print("URL: ", url)
            print("Method: ", colored(method, 'red', attrs=["bold"]))
            print("HTTP CODE: ", res_code)
            print("SIZE: ", len(res_text))
            print("RAW: ", colored(res_text, 'red', attrs=["bold"]))
            print("\n\n")
        else:
            # rel_fliter.append(urlsplit(url).path)
            file.write(url + '\t\t' + str(res_code) + '\t\t' + method + '\n\n')
        file.close()
    finally:
        print_lock.release() # 释放锁



def remove_url_params(url):
    split_url = urlsplit(url)
    return split_url.scheme + "://" + split_url.netloc.rstrip("/") # 返回http(s)://ip:(ports)的形式



def find_base_api(url,res_text):
    global baseAPI
    global baseAPI_list
    base_url_match = ['baseurl:"(.*?)"','baseurl: "(.*?)"','baseapi:"(.*?)"','baseapi: "(.*?)"']
    c = 1
    if baseAPI == "":
        for m in base_url_match:
            baseAPI = re.findall(m, res_text,re.IGNORECASE)
            for i in baseAPI:
                tmp = i
                i = i.replace("./","")
                baseAPI[baseAPI.index(tmp)] = i
            if len(baseAPI) == 1 and baseAPI[0] != " " and baseAPI[0] != "":
                if "http:" in baseAPI[0] or "https:" in baseAPI[0]:
                    if urlsplit(baseAPI[0]).netloc != urlsplit(url).netloc: # 如何域名不同则设置为输入的域名
                        baseAPI=remove_url_params(baseAPI[0])
                        return 
                    baseAPI=baseAPI[0]
                    return 
                if "//" in baseAPI[0]:
                    baseAPI = remove_url_params(url) + urlsplit(baseAPI[0]).path
                    return
                if baseAPI[0][0] != '/' :
                    baseAPI[0] = '/' + baseAPI[0]
                baseAPI=remove_url_params(url)+baseAPI[0]
                return 
            elif len(baseAPI) == 2 and (baseAPI[1] == "" or baseAPI[1] == " "):
                if urlsplit(baseAPI[0]).path != "":
                    if "http://" in baseAPI[0] or "https://" in baseAPI[0]:
                        baseAPI=urlsplit(baseAPI[0]).path
                        return 
                    else:
                        baseAPI=remove_url_params(url)+baseAPI[0]
                        return 
                else:
                    baseAPI = baseAPI[0]
                    return baseAPI
            else: 
                continue
        baseAPI = remove_url_params(url)



def find_hidden_js(url,res_text):
    global total_js
    js_match = r'"([a-zA-Z0-9_+-.]+/[a-zA-Z0-9_+-.]+(?:/[a-zA-Z0-9_+-.]+)*)"'

    domain = remove_url_params(url)
    pattern = r'"chunk-\w{8}":"\w{8}"'
    matches = re.findall(pattern, res_text)
    pattern_1 = r"/^[0-9a-f]{8}\.[0-9]{13}\.js$/"
    m2 = re.findall(pattern_1,res_text)
    prefix = ["/static/js/"]
    # prefix = ["/wechat_wujin/js/]"
    if matches or m2:
        if matches:
            matches = matches
        if m2:
            matches = m2
        for i in prefix:
            for j in matches:
                j = j.replace('"',"")
                j = j.replace(':',".")
                j = j + '.js'
                j = i + j
                if j[0] != '/':
                    j = "/" + j
                # js_path = urlsplit(url).path
                # js_path = "/".join(js_path.split("/")[:-1])
                # chunk_js = domain + js_path + i
                chunk_js = domain + j
                if chunk_js not in total_js:
                    total_js.append(chunk_js)

    hidden_js = []
    find_hidden_js = re.findall(js_match, res_text,re.IGNORECASE)
    if find_hidden_js:
        for j in find_hidden_js:
            if j not in hidden_js and ".js" in j:
                domain = remove_url_params(url)
                while "./" in j:
                    j = j.replace("./","/")
                    if "//" in j:
                        j = j.replace("//","/")
                if j[0] != '/':
                    j = '/' + j
                if j.count('/') <= 1:
                    js_path = urlsplit(url).path
                    js_path = "/".join(js_path.split("/")[:-1])
                    domain = domain + js_path + j
                else:
                    domain = domain+j
                if domain not in total_js:
                    total_js.append(domain)
                    domain = remove_url_params(url)



def get_apis_from_js_link(js_link,res_text="",user_set_base="",token="",auth_type="",change_domain="",custom_threads_num=10):
    try:     
        global reg_match
        global baseAPI
        global js_black_list
        global rel_fliter
        
        parameters = ["?id=1","?type=01&page=1&size=30","?type=1","?page=1","?size=10","?list=10","?info=1","?user=1","?user=admin","?logintype=1","?aid=123","?uid=123"]
        guess = []
        threads = []
        path_req = []
        if baseAPI == "":
            find_base_api(js_link,res_text)
        if change_domain:
                baseAPI = change_domain
        if res_text == "":
            res_text = make_request(url=js_link,token=token,single_request=True,auth_type=auth_type).text
        if user_set_base != None:
            baseAPI = user_set_base.replace(" ","")
            if change_domain:
                baseAPI = (change_domain+baseAPI)
            else:
                baseAPI = remove_url_params(js_link)+baseAPI
        
        print(colored("\n[+] baseAPI|URL: ","red",attrs=["bold"]),baseAPI)

        print("\n[+] Fuzzing apis, good luck ;-)\n")
        guess_url = ""

        count = 1
        for match in reg_match:
            file_path_match = re.findall(match, res_text,re.IGNORECASE)
            if file_path_match:
                file_path_match = list(set(file_path_match))
                for rel_path in file_path_match:
                    if rel_path not in js_black_list and rel_path not in rel_fliter:
                        # if ".jpg" in rel_path or ".png" in rel_path or ".svg" in rel_path:
                        if any(x in rel_path for x in [".png", ".svg", ".ttf",".eot", ".woff",".jpg",".vue",".gif",".jpeg",".css",".js",".mp3",".mp4",".bmp",".cur",".otf"]):
                            continue
                        rel_fliter.append(rel_path)
                        sent = baseAPI
                        if sent[-1] == '/':
                            sent = sent.rstrip('/')
                        if not (rel_path[0] == '/' or rel_path.startswith("post ") or rel_path.startswith("get ")):
                            rel_path = '/'+rel_path

                        if any(x in rel_path for x in ["logout", "loginOut", "loginout","logOut", "resetToken", "refreshToken", "delete", "Delete","del","Del"]):
                            continue 

                        rel_path = rel_path.replace("post ","")
                        rel_path = rel_path.replace("get ","")
                        rel_path = rel_path.replace("POST ","")
                        rel_path = rel_path.replace("GET ","")

                               
                        final_req_url = sent + rel_path                       
                        if len(final_req_url) < 120:
                            path_req.append(final_req_url) 

                            if "/api" not in rel_path or "api/" not in rel_path:
                                guess_0 = sent+"/api"+rel_path 
                                guess_1 = sent+"/api/v1"+rel_path.rstrip('/')
                                guess_2 = sent+"/api/v2"+rel_path.rstrip('/') 
                                guess_3 = sent+"/api/v3"+rel_path.rstrip('/') 
                                guess = [guess_0,guess_1,guess_2,guess_3]
                                for i in guess:
                                    if "?" not in guess:
                                        for j in parameters:
                                            another_shot = i + j
                                            path_req.append(another_shot)


                            if "?" not in final_req_url:
                                for t_p in parameters:
                                    normal_url_with_parameters = final_req_url + t_p
                                    path_req.append(normal_url_with_parameters) 
                            
                            if "=" in final_req_url:
                                url_with_random_p = final_req_url+"4321"
                                url_with_random_p_w = final_req_url + "C:\Windows\win.ini"
                                url_with_random_p_l = final_req_url + "/etc/passwd"
                                path_req.append(url_with_random_p_w)
                                path_req.append(url_with_random_p_l)
                            else:
                                url_with_random_p = final_req_url+"/4321"

                            path_req.append(url_with_random_p)

                            if len(guess) != 0:
                                for guess_url in guess:
                                    if len(guess_url) < 120 :
                                        if guess_url and guess_url not in path_req:
                                            if "=" in guess_url:
                                                guess_url_with_random_p_w = guess_url + "C:\Windows\win.ini"
                                                guess_url_with_random_p_l = guess_url + "/etc/passwd"
                                                guess_url_with_random_p = guess_url + "1234"
                                                path_req.append(guess_url_with_random_p)
                                                path_req.append(guess_url_with_random_p_w)
                                                path_req.append(guess_url_with_random_p_l)
                                            path_req.append(guess_url)
                                            
                    path_req = list(set(path_req))
        batch_size = custom_threads_num
        for i in path_req:
            t = threading.Thread(target=make_request, kwargs={'url': i,'token': token, 'auth_type': auth_type, 'num':count,'total':len(path_req)})
            count += 1
            threads.append(t)
        for i in range(0, len(threads), batch_size):
            batch_threads = threads[i:i+batch_size]
            for thread in batch_threads:
                thread.start()
            for thread in batch_threads:
                thread.join()
    except Exception as e:
        print(colored("\n\n[!] *F: get_apis_from_js_link, ERR: "+str(e),"green"))
        pass




def auto_find_directory(url,token="",auth_type="",user_set_base="",keep_path="",change_domain="",custom_threads_num=10):
    try:
        url = url.replace(" ","")
        global total_js 
        global reg_match
        print(colored("[~] May the force be with you ; )\n\n","red",attrs=["bold"]))
        response = make_request(url=url,token=token,auth_type=auth_type,single_request=True)
        url = remove_url_params(url) # 访问用户提供的URL之后取netloc
        if keep_path:
            url = url + keep_path
        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            tags_and_attrs = [("script", "src"), ("link", "href")]
            for tag, attr in tags_and_attrs:
                for js in soup.find_all(tag, {attr: True}):
                    if js[attr] and (".js" in js[attr]):
                        js_url = js[attr]
                        while './' in js_url:
                            js_url = js_url.replace("./","/")
                            if '//' in js_url:
                                js_url = js_url.replace("//","/")
                        if "://" not in js_url:
                            if url[-1] != '/':
                                url += '/'
                            if js_url[0] == '/':
                                js_url = js_url.lstrip('/')
                            if js_url.startswith("./"):
                                js_url = js_url[2:]
                            js_url = url + js_url
                        if urlsplit(js_url).netloc != urlsplit(url).netloc:  # 用来跳过那些第三方的JS，比如JS中调用了高德地图等。
                                continue
                        if js_url not in total_js:
                            total_js.append(js_url)
            for i in total_js:
                if "app" in i or "config" in i or "index" in i:
                    print(colored("\n\n"+"[+] "+i,"yellow"))
                    js_response = make_request(url=i,auth_type=auth_type,token=token,single_request=True)
                    find_base_api(i,js_response.text)
                    find_hidden_js(i,js_response.text)
                    get_apis_from_js_link(i,js_response.text,token=token,auth_type=auth_type,user_set_base=user_set_base,change_domain=change_domain,custom_threads_num=custom_threads_num)
                    total_js.remove(i)
                    # break
            for i in total_js:
                print(colored("\n\n"+"[+] "+i,"yellow"))
                js_response = make_request(url=i,token=token,auth_type=auth_type,single_request=True)
                find_hidden_js(i,js_response.text)
                get_apis_from_js_link(i,js_response.text,token=token,auth_type=auth_type,user_set_base=user_set_base,change_domain=change_domain,custom_threads_num=custom_threads_num)
        else:
            print(colored("[!] ERR:\t"+url+'\t'+str(response.status_code)+"\t"+response.reason,"green")) 
    except Exception as e:
        print(colored("\n\n[!] *F: auto_find_directory, ERR: "+str(e),"green"))
        pass


    

def fuzzing_complete():
    print("\n")
    print(colored("[*] Api Fuzzing Completed :)\n","yellow"))



if __name__ == '__main__':
    header = '''
     _______   __    __       ___          
    |   ____| |  |  |  |     /   \         
    |  |__    |  |  |  |    /  ^  \      
    |   __|   |  |  |  |   /  /_\  \       
    |  |      |  `--'  |  /  _____  \  
    |__|       \______/  /__/     \__\ 
                                    \t\tFuzzing Unauthorized Api (Beta)
                                    \t\tvulntinker (vulntinker@gmail.com)
    '''
    print(colored(header, 'red',attrs=["bold"]))
    headers = {'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 9_3_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Mobile/13F69 MicroMessenger/6.6.1 NetType/4G Language/zh_CN'}
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-u", "--url", dest="autourl", help="The site URL that contians JS links.")
        parser.add_argument("-A", "--auth", dest="auth_type", help="Auth type:AccessToken, Cookie,Authorization")
        parser.add_argument("-j", "--js", dest="single_js", help="Single JS link to proceed.")
        parser.add_argument("-b", "--base", dest="url_base", help="baseURL of the site incase the programme missed it.")
        parser.add_argument("-t", "--token", dest="token", help="token value")
        parser.add_argument("-k", "--keep", dest="keep_path", help="keep the path of user input URL.")
        parser.add_argument("-c", "--change", dest="change_domain", help="Change domain incase the interface is different.")
        parser.add_argument("-T", "--Thread", dest="threads_num",type=int,default=10,help="Custom threads number.")

        args = parser.parse_args()
        if args.autourl:
            if args.threads_num != 10:
                auto_find_directory(url=args.autourl,auth_type=args.auth_type,token=args.token,user_set_base=args.url_base,keep_path=args.keep_path,change_domain=args.change_domain,custom_threads_num=args.threads_num)
            else:
                auto_find_directory(url=args.autourl,auth_type=args.auth_type,token=args.token,user_set_base=args.url_base,keep_path=args.keep_path,change_domain=args.change_domain)
        elif args.single_js:
            if args.threads_num != 10:
                get_apis_from_js_link(js_link=args.single_js,user_set_base=args.url_base,token=args.token,auth_type=args.auth_type,change_domain=args.change_domain,custom_threads_num=args.threads_num)
            else:
                get_apis_from_js_link(js_link=args.single_js,user_set_base=args.url_base,token=args.token,auth_type=args.auth_type,change_domain=args.change_domain)         
        fuzzing_complete()
    except KeyboardInterrupt:
        print("\n")
        print(colored("[!] USER EXITED\n","green"))
        

