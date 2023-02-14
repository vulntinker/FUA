import requests
from bs4 import BeautifulSoup
import re
import sys 
import urllib3
import random
from urllib.parse import urlsplit
from termcolor import colored
import argparse
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

reg_match = [
    r'"(/[a-zA-Z0-9_+-]+/[a-zA-Z0-9_+-]+(?:/[a-zA-Z0-9_+-]+)*)"',
    r'"([a-zA-Z0-9_+-]+/[a-zA-Z0-9_+-]+(?:/[a-zA-Z0-9_+-]+)*)"',
    r"'(/[a-zA-Z0-9_+-]+/[a-zA-Z0-9_+-]+(?:/[a-zA-Z0-9_+-]+)*)'",
    r"'([a-zA-Z0-9_+-]+/[a-zA-Z0-9_+-]+(?:/[a-zA-Z0-9_+-]+)*)'",
]
# Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36

baseAPI = ""
baseAPI_list = []
path_req = []
req_url = []
total_js = []
js_black_list = [
    "text/plain","+n/100+","text/plain","a/i","DD/MM/YYYY","YYYY/MM/DD","MM/D/YYYY","application/x-www-form-urlencoded","DD/M/YYYY","text/javascript","text/xml","M/D/yy","a/b","image/svg+xml","YYYY/M/D","text/css","D/M/YYYY","MM/DD/YYYY","D/JM"
]

def make_request(url, data={},auth_type="",token="",num=0,total=0,match_count=0,single_request=False):
    try:
        headers = {'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 9_3_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Mobile/13F69 MicroMessenger/6.6.1 NetType/4G Language/zh_CN'}
        if token != None and auth_type != None:
            headers.update({auth_type:token})
        
        if single_request:
            res = requests.get(url=url,headers=headers,verify=False,timeout=60)
            return res

        response_get = requests.get(url, headers=headers,verify=False,timeout=60)
        echo_res(url=url,method="GET",res_code=response_get.status_code,res_text=response_get.text,current_num=num,total_num=total,current_regex_num=match_count)
        
        response_post = requests.post(url, json=data, headers=headers,verify=False,timeout=60)
        echo_res(url=url,method="POST",res_code=response_post.status_code,res_text=response_post.text,current_num=num,total_num=total,current_regex_num=match_count)
        return response_get,response_post
    except Exception as e:
        print(colored("[!] Request ERR: "+str(e),"green"))
        pass



def echo_res(url,method,res_code,res_text,current_num,total_num,current_regex_num):
    sys.stdout.write("\033[2K\033[G"+"[+] Regex: {2}, ({0}/{1}) [{3}] URL: {4}".format(current_num,total_num,current_regex_num,method,url))
    sys.stdout.flush()
    file = open(urlsplit(url).netloc+".txt", "a")
    if (res_code == 200 or res_code == 500) and "<html>" not in res_text and "<!doctype html>" not in res_text and "<!DOCTYPE html>" not in res_text and "</script>" not in res_text and 'status":401,' not in res_text and 'status":401}' not in res_text and 'code":401}' not in res_text and 'code":401,' not in res_text and "<title>" not in res_text and 'Code": 404' not in res_text and '"Code": 401' not in res_text and 'status":-1' not in res_text:
        file.write("\n\n"+url+'\t\t'+str(res_code)+'\t\t'+ method+'\n\n'+res_text+"\n\n\n")
        print("\n\n")
        print("URL: ",url)
        print("Method: ",colored(method, 'red',attrs=["bold"]))
        print("HTTP CODE: ",res_code)
        print("SIZE: ",len(res_text))
        print("RAW: ",colored(res_text, 'red',attrs=["bold"]))
        print("\n\n")
    else:
        file.write(url+'\t\t'+str(res_code)+'\t\t'+ method+'\n\n')
    file.close()



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
            if len(baseAPI) == 1 and baseAPI[0] != " " and baseAPI[0] != "":
                if "http:" in baseAPI[0] or "https:" in baseAPI[0]:
                    if urlsplit(baseAPI[0]).netloc != urlsplit(url).netloc: # 如何域名不同则设置为输入的域名
                        baseAPI=remove_url_params(baseAPI[0])
                        return 
                    baseAPI=baseAPI[0]
                    return 
                if baseAPI[0][0] != '/' :
                    baseAPI[0] = '/' + baseAPI[0]
                baseAPI=remove_url_params(url)+baseAPI[0]
                return 
            elif len(baseAPI) == 2 and (baseAPI[1] == "" or baseAPI[1] == " "):
                if "http://" in baseAPI[0] or "https://" in baseAPI[0]:
                    baseAPI=urlsplit(baseAPI[0]).path
                    return 
                else:
                    baseAPI=remove_url_params(url)+baseAPI[0]
                    return 
            else: 
                continue
        baseAPI = remove_url_params(url)




def get_apis_from_js_link(js_link,res_text="",user_set_base="",token="",auth_type="",change_domain=""):
    try:     
        global reg_match
        global baseAPI
        global baseAPI_list
        global path_req
        global js_black_list

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

        print("\n[+] Requesting Apis,this will take a moment...\n")
        match_count = 0
        guess_url = ""
        for match in reg_match:
            count = 0
            match_count += 1
            file_path_match = re.findall(match, res_text,re.IGNORECASE)
            if file_path_match:
                for rel_path in file_path_match:
                    if rel_path not in js_black_list:
                        count += 1
                        sent = baseAPI
                        if sent[-1] == '/':
                            sent = sent.rstrip('/')
                        if rel_path[0] != '/':
                            rel_path = '/'+rel_path
                        if "/api" not in rel_path or "api/" not in rel_path:
                            guess = "/api"+rel_path
                            guess_url = sent+guess+'/'
                        if "/logout" in rel_path or "loginOut" in rel_path or "loginout" in rel_path or "resetToken" in rel_path or "refreshToken" in rel_path or "delete" in rel_path or "Delete" in rel_path:
                            continue                                 
                        final_req_url = sent+rel_path
                        
                        if final_req_url not in path_req and (all( c.isupper() for c in final_req_url[-5:]) or len(final_req_url) < 120):
                            path_req.append(final_req_url) 

                            url_with_random_p = final_req_url+'/'+"4321"

                            make_request(url=final_req_url,token=token,auth_type=auth_type,num=count,total=len(file_path_match),match_count=match_count)

                            make_request(url=url_with_random_p,token=token,auth_type=auth_type,num=count,total=len(file_path_match),match_count=match_count)

                            if guess_url not in path_req and (all( c.isupper() for c in guess_url[-5:]) or len(guess_url) < 120 ):
                                if guess_url:
                                    guess_url_with_random_p = guess_url + "1234" # 固定数字防止后面重复访问
                                    make_request(url=guess_url,token=token,auth_type=auth_type,num=count,total=len(file_path_match),match_count=match_count)
                                    make_request(url=guess_url_with_random_p,token=token,auth_type=auth_type,num=count,total=len(file_path_match),match_count=match_count)
    except Exception as e:
        print("\n")
        print(colored("[!] *F: get_apis_from_js_link, ERR: "+str(e),"green"))
        pass




def auto_find_directory(url,token="",auth_type="",user_set_base="",keep_path="",change_domain=""):
    try:
        url = url.replace(" ","")
        global total_js 
        global reg_match
        print(colored("[~] May the force be with you ; )\n\n","red",attrs=["bold"]))
        print("[+] Total regex num:\t",len(reg_match))
        response = make_request(url=url,token=token,auth_type=auth_type,single_request=True)
        url = remove_url_params(url) # 访问用户提供的URL之后取netloc
        if keep_path:
            url = url + keep_path
        if response.ok:
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
                if "config" in i:
                    print(colored("\n\n"+"[+] "+i,"yellow"))
                    js_response = make_request(url=i,auth_type=auth_type,token=token,single_request=True)
                    find_hidden_js(i,js_response.text)
                    get_apis_from_js_link(i,js_response.text,auth_type=auth_type,token=token,user_set_base=user_set_base,change_domain=change_domain)
                    total_js.remove(i)
                    break
                elif "app" in i:
                    print(colored("\n"+"[+] "+i,"yellow"))
                    js_response = make_request(url=i,auth_type=auth_type,token=token,single_request=True)
                    find_hidden_js(i,js_response.text)
                    get_apis_from_js_link(i,js_response.text,auth_type=auth_type,token=token,user_set_base=user_set_base,change_domain=change_domain)
                    total_js.remove(i)
                    break
            for j in total_js:
                print(colored("\n\n"+"[+] "+j,"yellow"))
                js_response = make_request(url=j,token=token,auth_type=auth_type,single_request=True)
                find_hidden_js(j,js_response.text)
                get_apis_from_js_link(j,js_response.text,token=token,auth_type=auth_type,user_set_base=user_set_base,change_domain=change_domain)
        else:
            print(colored("[!] ERR:\t"+url+'\t'+str(response.status_code)+"\t"+response.reason,"green")) 
    except Exception as e:
        print(colored("[!] *F: auto_find_directory, ERR: "+str(e),"green"))
        pass


def find_hidden_js(url,res_text):
    global total_js
    reg_match = [
    r'"(/[a-zA-Z0-9_+-.]+/[a-zA-Z0-9_+-.]+(?:/[a-zA-Z0-9_+-.]+)*)"',
    r'"([a-zA-Z0-9_+-.]+/[a-zA-Z0-9_+-.]+(?:/[a-zA-Z0-9_+-.]+)*)"',
    r"'(/[a-zA-Z0-9_+-.]+/[a-zA-Z0-9_+-.]+(?:/[a-zA-Z0-9_+-.]+)*)'",
    r"'([a-zA-Z0-9_+-.]+/[a-zA-Z0-9_+-.]+(?:/[a-zA-Z0-9_+-.]+)*)'",]

    hidden_js = []
    for i in reg_match:
        find_hidden_js = re.findall(i, res_text,re.IGNORECASE)
        if find_hidden_js:
            for j in find_hidden_js:
                if j not in hidden_js and ".js" in j:
                    while "./" in j:
                        j = j.replace("./","/")
                        if "//" in j:
                            j = j.replace("//","/")
                    if j[0] != '/':
                        j = '/' + j
                    domain = remove_url_params(url)
                    domain = domain+j
                    if domain not in total_js:
                        total_js.append(domain)

    

def fuzzing_complete():
    print("\n")
    print(colored("[*] Api Fuzzing Completed :)","yellow"))



if __name__ == '__main__':
    header = '''
\t\t\t _______   __    __       ___          
\t\t\t|   ____| |  |  |  |     /   \         
\t\t\t|  |__    |  |  |  |    /  ^  \      
\t\t\t|   __|   |  |  |  |   /  /_\  \       
\t\t\t|  |      |  `--'  |  /  _____  \  
\t\t\t|__|       \______/  /__/     \__\ 
                                    \t\t\t    Fuzzing Unauthorized Api (Beta v1.0)
                                    \t\t\t    by vulntinker (vulntinker@gmail.com)
    '''
    print(colored(header, 'red',attrs=["bold"]))
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-a", "--auto", dest="autourl", help="The site URL that contians JS links.")
        parser.add_argument("-A", "--auth", dest="auth_type", help="Auth type:AccessToken, Cookie,Authorization")
        parser.add_argument("-j", "--js", dest="single_js", help="Single JS link to proceed.")
        parser.add_argument("-b", "--base", dest="url_base", help="baseURL of the site incase the programme missed it.")
        parser.add_argument("-t", "--token", dest="token", help="token value")
        parser.add_argument("-k", "--keep", dest="keep_path", help="keep the path of user input URL.")
        parser.add_argument("-c", "--change", dest="change_domain", help="Change domain incase the interface is different.")

        args = parser.parse_args()
        if args.autourl:
            auto_find_directory(url=args.autourl,auth_type=args.auth_type,token=args.token,user_set_base=args.url_base,keep_path=args.keep_path,change_domain=args.change_domain)
        elif args.single_js:
            get_apis_from_js_link(js_link=args.single_js,user_set_base=args.url_base,token=args.token,auth_type=args.auth_type,change_domain=args.change_domain,) 
        fuzzing_complete()
    except KeyboardInterrupt:
        print("\n")
        print(colored("[!] USER EXITED\n","green"))
        

