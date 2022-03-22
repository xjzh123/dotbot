import requests
def fanyi(strr):
	data = {"doctype":"json",
			"type":"AUTO",
			"i":str(strr)}
	headers = {"User-Agent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"}
	url = "http://fanyi.youdao.com/translate"
	try:
		r = requests.get(url,params=data,headers=headers,timeout=10)
		if r.status_code == 200:
			result = r.json()
			translate_result = result["translateResult"][0][0]["tgt"]
			return translate_result
	except:
		pass
if __name__ == '__main__':
	while 1:
		print(fanyi(input('')))