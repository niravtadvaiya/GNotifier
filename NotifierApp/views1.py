from django.shortcuts import render,render_to_response,redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files import File
from django.template import RequestContext, loader
from django.template.context_processors import csrf
from django.core.files import File
from django.template import RequestContext
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from urllib import urlencode
import os 
import urllib2
import nexmo
import json
import ConfigParser 
from django import forms

FILE_NAME = settings.BASE_DIR + '/.monitor.conf'


class NexmoForm(forms.Form):
    your_name = forms.CharField(max_length=100,widget=forms.TextInput(attrs={'class':'customTxtBox'}),required=True,error_messages={'required': 'Please enter the name.'})
	
@csrf_exempt
def index(request):
	if request.method != 'POST':
		return redirect('/login')
	data_dict = json.loads(request.body)
	nexmo_conf =  nexmo_config()
	FROM = dequote(nexmo_conf['NexmoFrom'])
	TO = dequote(nexmo_conf['NRecv'])
	EnableSMS = nexmo_conf['EnableSMS'].lower()

	incident = data_dict['incident']
	summary = data_dict['incident']['summary']
	condition_name = data_dict['incident']['condition_name']
	
	msg = 'ALRM: ' + str(condition_name)+ ': ' +str(summary) 
	print len(msg)
	if EnableSMS=='on':
		conn = nexmo.Client(key=str(nexmo_conf['NKey']),secret=str(nexmo_conf['NSecret']))
		conn.send_message({'from':FROM,'to':TO,'text':msg})

	return HttpResponse("200")



def settings(request):
	c = {}
	c.update(csrf(request))
	try:
		if 'logged_in' not in request.session:
			return redirect('/login')
	except:
		return redirect('/login')
		
	if request.method == 'GET':
		nexmo_conf = nexmo_config()
		return render_to_response('settings.htm',{'nxmo_conf':nexmo_conf},context_instance=RequestContext(request))
	
	if request.method == 'POST':
	  try:
		nxmo_conf = nexmo_config()
		for k,v in nxmo_conf.iteritems():
			if v is '':
				nxmo_conf[k]=request.POST[k]

		Error = False
		recv = ''.join(request.POST['NRecv'].split())
		recv = recv.replace('+','')
		
		if (trim(request.POST['NKey']) is None or trim(request.POST['NKey']) == '') and trim(request.POST['NSecret']) is None or trim(request.POST['NSecret']) == '':
			Error = True
			messages.error(request,"Please enter the Nexmo Key and Secret.")
			return render_to_response('settings.htm',{'nxmo_conf':nxmo_conf},context_instance=RequestContext(request))
			
		if trim(request.POST['NKey']) is None or trim(request.POST['NKey']) == '':
			Error = True
			messages.error(request,"Please enter the Nexmo Key.")
			return render_to_response('settings.htm',{'nxmo_conf':nxmo_conf},context_instance=RequestContext(request))
			
		if trim(request.POST['NSecret']) is None or trim(request.POST['NSecret']) == '':
			Error = True
			messages.error(request,"Please enter the Nexmo Secret.")
			return render_to_response('settings.htm',{'nxmo_conf':nxmo_conf},context_instance=RequestContext(request))
			
		if trim(request.POST['NSecret']) and trim(request.POST['NKey']):
			try:
				conn = nexmo.Client(key=str(request.POST['NKey']),secret=str(request.POST['NSecret']))
				json_number =  conn.get_account_numbers()
				from_number = json_number['numbers'][0]['msisdn']
			except:
				messages.error(request,"Please enter valid Nexmo Key and Secret.")
				return render_to_response('settings.htm',{'nxmo_conf':nxmo_conf},context_instance=RequestContext(request))
	
		if trim(request.POST['NexmoFrom']) is None or trim(request.POST['NexmoFrom']) == '':
			Error = True
			messages.error(request,"Please select the From Number.")
			
		if trim(recv) is None or trim(recv) == '':
			Error = True
			messages.error(request,"Please enter the Recipients Number.")
		
		if trim(recv):

			if not recv.isnumeric():
				Error = True
				messages.error(request,"Please enter a valid Recipients Number.")
				
			if len(trim(recv))<=10:
				Error = True
				messages.error(request,"Please enter a valid Recipients Number with country code.")
				
		if trim(request.POST['UserName']) is None or trim(request.POST['UserName']) == '':
			Error = True
			messages.error(request,"Please enter the Username.")

		if trim(request.POST['password']) is None or trim(request.POST['password']) == '':
			Error = True
			messages.error(request,"Please enter the Password.")
		
		if trim(request.POST['UserName']).lower()=='admin':
			Error = True
			messages.error(request,"Please change the default Username.")
			
		if trim(request.POST['password']).lower()=='admin':
			Error = True
			messages.error(request,"Please change the default Password.")
			
		if Error == True:
			return render_to_response('settings.htm',{'nxmo_conf':nxmo_conf},context_instance=RequestContext(request))

			
		from_number = request.POST['NexmoFrom']
		myvar = ''
		myvar +='api_key='+request.POST['NKey']+"\n"
		myvar +='secret_key='+request.POST['NSecret']+"\n"
		myvar +='fromuser='+str(from_number)+"\n"
		myvar +='touser='+recv+"\n"
		if 'EnableSMS' in request.POST:
			myvar +='EnableSMS='+request.POST['EnableSMS']+"\n"
		else:
			myvar +='EnableSMS=0\n'
		myvar +='username='+request.POST['UserName']+"\n"
		myvar +='password='+request.POST['password']+"\n"
		
		
		with open(FILE_NAME, 'w') as f:
			my = File(f)
			my.write('[nexmo_monitor]\n')
			my.write(myvar)
			
		f.close()
		my.close()
		nxmo_conf = nexmo_config() 
		messages.success(request,"Configuration Settings saved successfully.")
		return render_to_response('settings.htm',{'nxmo_conf':nxmo_conf,'form':form},context_instance=RequestContext(request))
	  except Exception as err:
		messages.error(request,"We are find some errors.")
		return render_to_response('settings.htm',{'nxmo_conf':nxmo_conf},context_instance=RequestContext(request))

def config_reader(key):
	try:
		if os.path.exists(FILE_NAME):
			config = ConfigParser.RawConfigParser()
			config.read(FILE_NAME)
			return config.get('nexmo_monitor', key).strip()
		else:
			print "Configuration file does not exist."
	except Exception as err:
		print str(err)

def nexmo_config():
	nxmo_conf={}
	nxmo_conf['NKey']=config_reader('api_key')
	nxmo_conf['NSecret']=config_reader('secret_key')
	nxmo_conf['NexmoFrom']=config_reader('fromuser')
	nxmo_conf['NRecv']=config_reader('touser')
	nxmo_conf['EnableSMS']=config_reader('EnableSMS')
	nxmo_conf['username']=config_reader('username')
	nxmo_conf['password']=config_reader('password')
	
	
	return nxmo_conf
	
def dequote(str):
	if str.startswith(("'", '"')):
		return str[1:-1]
	return str
	
def trim(strn):
		if strn:
			return strn.strip()
		return strn
		
def login(request):
	if request.method == 'GET':
		return render_to_response('login.htm',{},context_instance=RequestContext(request))
	if request.method == 'POST':
		if request.POST['NKey']==config_reader('username') and request.POST['NSecret']==config_reader('password'):
			request.session['logged_in']=True
			return redirect("/settings/")
		else:
			messages.error(request,"Invalid login credentials.")
			return render_to_response('login.htm',{},context_instance=RequestContext(request))
		
def logout(request):
	try:
		if request.session['logged_in']:
			del(request.session['logged_in'])
		return redirect('/login/')
	except:
		return redirect('/login/')

@csrf_exempt	
def ajax_validator(request):
	if 'logged_in' not in request.session:
		return HttpResponse("you are not logged in")
	
	api_key = request.POST['NKey']
	api_secret = request.POST['NSecret'] 
	django_html = []
	get_num  = None
	if not api_key and  not api_secret:
		django_html = {'error':'true','html':str('Please enter the Nexmo Key and Secret.')}
		return HttpResponse(json.dumps(django_html))
	if not api_key:
		django_html = {'error':'true','html':str('Please enter the Nexmo Key.')}
		return HttpResponse(json.dumps(django_html))
	if not api_secret:
		django_html = {'error':'true','html':str('Please enter the Nexmo Secret.')}
		return HttpResponse(json.dumps(django_html))
	try:
		conn = nexmo.Client(key=str(api_key),secret=str(api_secret))
		json_number =  conn.get_account_numbers()
		from_number = json_number['numbers']
		get_num = []
		for from_number in json_number['numbers']:
			if from_number['msisdn'].strip() is not None:
				get_num.append(from_number['msisdn'])
		
		msisdn = ','.join(get_num)
		django_html = {'error':'false','html':msisdn}
		return HttpResponse(json.dumps(django_html))
	except nexmo.AuthenticationError as err:
		django_html = {'error':'true','html':"Please enter valid Nexmo Key and Secret."}
		return HttpResponse(json.dumps(django_html))
	except Exception as err:
		django_html = {'error':'true','html':str(err)}
		return HttpResponse(json.dumps(django_html))
