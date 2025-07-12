from math import ceil
from django.shortcuts import render,redirect
from django.core.paginator import Paginator
from . models import Song,Playlist,Category,UserSong,Queue,UserProfile
from django.http import HttpResponse
from django.contrib.auth.models import User,auth
from django.contrib import messages
from django.http import JsonResponse
from .models import Song
from django.shortcuts import get_object_or_404,render
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt

import requests
import random

User = get_user_model()

def get_adjacent_song(request, song_id, direction):
    try:
        if direction == 'next':
            song = Song.objects.filter(id__gt=song_id).order_by('id').first()
        elif direction == 'prev':
            song = Song.objects.filter(id__lt=song_id).order_by('-id').first()
        else:
            return JsonResponse({'error': 'Invalid direction'}, status=400)

        if song:
            return JsonResponse({
                'id': song.id,
                'title': song.title,
                'artist': song.artist,
                'url': song.audio_file.url
            })
        else:
            return JsonResponse({'error': 'No song found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def home(request):
    user = request.user
    # if not user.is_authenticated:
    #     return redirect('/login')
    categories = Category.objects.all().order_by('priority')
    data = []
    for cat in categories:
        if cat.public==False and cat.name!=user.username:
            continue
        playlists=Playlist.objects.filter(category=cat)
        n = len(playlists)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        data.append([playlists, range(1, nSlides), nSlides, cat.name])

    print(user)
    if user.is_authenticated:
        queue = Queue.objects.filter(user=request.user).first()
    else:
        queue = Queue.objects.first()

    # params = {'data':data,'signin':0,'queue':queue,'total_songs':len(queue.songs.all())}
    total_songs = len(queue.songs.all()) if queue else 0

    params = {
        'data': data,
        'signin': 0,
        'queue': queue,
        'total_songs': total_songs
    }

    if request.user.is_authenticated:
        params['signin']=1
    return render(request,"home.html",params)

def playlist(request,id):
    playlist = get_object_or_404(Playlist, id=id)
    # p = Playlist.objects.filter(id=int(id))
    params={'playlist':playlist}
    # params={'playlist':p[0]}
    return render(request,'playlist.html',params)

def likedsongs(request):
    return HttpResponse("likedsongs")

def register(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        phone_number = request.POST['phone_number']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return render(request, "register.html")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return render(request, "register.html")

        # Generate OTP and store form data in session
        otp = str(random.randint(100000, 999999))
        request.session['registration_data'] = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': password1,
            'phone_number': phone_number,
            'otp': otp,
        }

        # Send OTP
        payload = {
            'sender_id': 'FSTSMS',
            'message': f'Your OTP is {otp}',
            'language': 'english',
            'route': 'p',
            'numbers': phone_number,
        }
        headers = {
            'authorization': '<YOUR_FAST2SMS_API_KEY>',
            'Content-Type': "application/x-www-form-urlencoded"
        }
        try:
            requests.post('https://www.fast2sms.com/dev/bulkV2', data=payload, headers=headers)
        except:
            messages.error(request, "Failed to send OTP.")
            return render(request, "register.html")

        return redirect('App:verify_otp')  # route name

    return render(request, "register.html")
# @csrf_exempt
# def register(request):
#     if request.user.is_authenticated:
#         messages.info(request,'you are already registered')
#         return redirect('/')
#     params={'username':'','first_name':'','last_name':'','email':'','pss1':'','pss2':'','phone_number':'',}
#     if(request.method=="GET"):
#         return render(request,"register.html",params)
#     params['username'] = request.POST['username']
#     params['first_name'] = request.POST['first_name']
#     params['last_name'] = request.POST['last_name']
#     params['email'] = request.POST['email']
#     params['pss1'] = request.POST['password1']
#     params['pss2'] = request.POST['password2']
#     params['phone_number']=request.POST['phone_number']
#     if(User.objects.filter(username=params['username']).exists()):
#         messages.info(request,'username already exists')
#         return render(request,"register.html",params)
#     if(User.objects.filter(email=params['email']).exists()):
#         messages.info(request,'email already exists')
#         return render(request,"register.html",params)
#     if(params['pss1']!=params['pss2']):
#         messages.info(request,'password is not same in both column')
#         return render(request,"register.html",params)
#     if(len(params['pss1'])<5):
#         messages.info(request,'password should be of atleast 5 characters')
#         return render(request,"register.html",params)
#     user = User.objects.create_user(username=params['username'],password=params['pss1'],first_name=params['first_name'],last_name=params
#     ['last_name'],email=params['email'])
#     user.save()
#     profile = UserProfile(user=user, phone_number=params['phone_number'])
#     profile.save()
#     auth.login(request,user)
#     messages.info(request,"you are successfully registered")
#     return redirect('/')



def login(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in')
        return redirect('/')

    params = {'username': '', 'pss': ''}
    
    if request.method == "GET":
        return render(request, "login.html", params)

    # Step 1: Authenticate username & password
    params['username'] = request.POST['username']
    params['pss'] = request.POST.get('password', False)
    user = auth.authenticate(username=params['username'], password=params['pss'])

    if user is None:
        messages.info(request, "Credentials do not match")
        return render(request, "login.html", params)

    # Step 2: If correct, send OTP to user's phone number
    phone_number = user.userprofile.phone_number
    otp = str(random.randint(100000, 999999))

    request.session['otp'] = otp
    request.session['user_id'] = user.id

    # Send OTP using Fast2SMS
    payload = {
        'sender_id': 'FSTSMS',
        'message': f'Your OTP is {otp}',
        'language': 'english',
        'route': 'q',
        'numbers': phone_number,
    }
    headers = {
        'authorization': '5V4t0ArnBCLEblvRZjHT1Y9e6MF72mkQSGqhW8zdgDNayPXiIwxsPM7ekjypQfgOr90Amu15hVGbdFtR',
        'Content-Type': "application/x-www-form-urlencoded"
    }
    try:
        response = requests.post('https://www.fast2sms.com/dev/bulkV2', data=payload, headers=headers)
        print("Fast2SMS Response:", response.status_code, response.text)
        # print("OTP Sent:", response.text)
        return redirect('App:verify_otp')
    except Exception as e:
        print("Error sending OTP:", e)
        messages.error(request, "Failed to send OTP. Try again.")
        return render(request, "login.html", params)

def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        data = request.session.get('registration_data', {})

        if not data:
            messages.error(request, "Session expired. Please register again.")
            return redirect('App:register')

        if entered_otp == data.get('otp'):
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            profile = UserProfile.objects.create(
                user=user,
                phone_number=data['phone_number'],
                is_phone_verified=True
            )
            auth.login(request, user)
            messages.success(request, "Registration successful!")
            del request.session['registration_data']
            return redirect('/')
        else:
            messages.error(request, "Incorrect OTP. Try again.")
            return render(request, "verify_otp.html")

    return render(request, "verify_otp.html")

# def verify_otp(request):
#     if request.method == 'POST':
#         entered_otp = request.POST.get('otp')
#         session_otp = request.session.get('otp')
#         user_id = request.session.get('user_id')

#         if entered_otp == session_otp:
#             user = User.objects.get(id=user_id)
#             auth.login(request, user)
#             user.is_phone_verified = True
#             user.save()
#             messages.success(request, "Login successful via OTP.")
#             return redirect('/')
#         else:
#             messages.error(request, "Invalid OTP.")
#             return render(request, 'verify_otp.html')

#     return render(request, 'verify_otp.html')


def logout(request):
    auth.logout(request)
    return redirect('/')

def song(request, id, playlist_id=None):
    print("Song view triggered with id:", id, "playlist:", playlist_id)
    song = get_object_or_404(Song, id=id)
    mode = request.GET.get('mode', 'all')
    autoplay = request.GET.get('autoplay') == '1'

    if mode == 'playlist' and playlist_id:
        playlist = get_object_or_404(Playlist, id=playlist_id)
        song_list = list(playlist.songs.all().order_by('id'))
    else:
        song_list = list(Song.objects.all().order_by('id'))
        playlist = None

    try:
        index = song_list.index(song)
    except ValueError:
        return render(request, '404.html')

    previous_id = song_list[index - 1].id if index > 0 else None
    next_id = song_list[index + 1].id if index < len(song_list) - 1 else None

    context = {
        'song': song,
        'playlist': playlist,
        'previous_id': previous_id,
        'next_id': next_id,
        'mode': mode,
        'autoplay': autoplay,
        'signin': request.user.is_authenticated
    }
    return render(request, 'song.html', context)

    # paginator= Paginator(Song.objects.all(),1)
    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)
    # context={"page_obj":page_obj,
    #          "id":id}
    # return render(request,"index.html",context)

def playsong(request):
    if not request.user.is_authenticated:
        messages.info(request,"please login first before playing a song")
        return redirect("/")
    # queue = Queue.objects.filter(user=request.user)[0]
    # queue.pointer+=1
    # queue.save()
    # print(queue.pointer)
    # print(Queue.objects.filter(user=request.user)[0].pointer)
    paginator= Paginator(Queue.objects.filter(user=request.user)[0].songs.all(),1)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # for item in page_obj:
    #     print(item.image)
    context={"page_obj":page_obj}
    return render(request,"playsong.html",context)

def queue(request):
    if not request.user.is_authenticated:
        messages.info(request,"please login first to access queue")
        return redirect("/")
    queue = Queue.objects.filter(user=request.user)
    params = {"queue":queue[0]}
    return render(request,"queue.html",params)