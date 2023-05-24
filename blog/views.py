from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from .models import Post
from .forms import PostForm
from distutils.log import debug
from fileinput import filename
import requests
import json
import discogs_client
import re

def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})

def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})

def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})
    
@csrf_protect
def Acknowledgement(request, methods = ['POST']):  
    if request.method == 'POST':  
        f = request.FILES['file']
        with open(f.name, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        name = f.name
        data = {
        'api_token': '01073b4b085ae8abea9e6ed7dfe4b503',
        'accurate_offsets': 'true',
        'skip': '2',
        'every': '1',
        }
        files = {
            'file': open(str(name), 'rb'),
        }

        result = requests.post('https://api.audd.io/', data=data, files=files)

        dict=json.loads(result.text)

        shazam_audd = {
            'Название': str(dict['result']['title']),
            'Исполнитель': str(dict['result']['artist']),
            'Дата релиза': str(dict['result']['release_date']),
            'Жанр': '',
            'Стиль': '',
            'Текст песни':''
        }
        music_name = str(shazam_audd['Исполнитель'])+' '+str(shazam_audd['Название'])
        url = "https://genius-song-lyrics1.p.rapidapi.com/search/"

        querystring = {"q":str(music_name),"per_page":"1","page":"1"}

        headers = {
            "X-RapidAPI-Key": "8d5b7b83admsh2b09484bcea92f9p155153jsna63f71772814",
            "X-RapidAPI-Host": "genius-song-lyrics1.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        dict1=json.loads(response.text)

        if (dict1 == {'hits': []}):

            shazam_Genius = {
                'title': '',
                'artist_name': '',
                'release_date': '',
                'genre': '',
                'style': '',
                'song_text':''
            }
        else:
            artist_id = (dict1['hits'][0]['result']['id'])


            url = "https://genius-song-lyrics1.p.rapidapi.com/song/lyrics/"

            querystring_song = {"id":str(artist_id)}

            headers = {
                "X-RapidAPI-Key": "8d5b7b83admsh2b09484bcea92f9p155153jsna63f71772814",
                "X-RapidAPI-Host": "genius-song-lyrics1.p.rapidapi.com"
            }

            response_song = requests.request("GET", url, headers=headers, params=querystring_song)

            dict_song=json.loads(response_song.text)

            CLEANR = re.compile('<.*?>') 

            cleantext = re.sub(CLEANR, '', (dict_song['lyrics']['lyrics']['body']['html']))
        
            shazam_Genius = {
                'title': str(dict1['hits'][0]['result']['full_title']),
                'artist_name': str(dict1['hits'][0]['result']['artist_names']),
                'release_date': str(dict1['hits'][0]['result']['release_date_for_display']),
                'genre': str(dict_song['lyrics']['tracking_data']['primary_tag']),
                'style': '',
                'song_text':str(cleantext)
            }

        d = discogs_client.Client('ExampleApplication/0.1', user_token="xldYxYHkUwshNGqQaIUZNwzghtVwIyjsLPuVfuFC")

        results = d.search(str(shazam_audd['Название']), artist=str(shazam_audd['Исполнитель']), type='release')
        x = (results.page(1))
        if (x == []):
            shazam_discogs = {
                'title':'',
                'artist_name': '',
                'release_date': '',
                'genre': '',
                'style': '',
                'song_text':''
            }
        else:
            x_id = (' '.join(map(str, x))).split()[1]
            art = (' '.join(map(str,(d.release(x_id).artists)))).split()
            del art[:2]

            art1 = ' '.join(map(str,art))

            art1 = art1.replace("'>","")
            art1 = art1.replace("'","")

            if ((d.release(x_id).genres) is None):
                genr = ''
            else:
                genr = str(' '.join(map(str,(d.release(x_id).genres))))

            if ((d.release(x_id).genres) != ('None')):
                stl = ''
            else:
                stl = str(' '.join(map(str,(d.release(x_id).styles))))
            
        
            shazam_discogs = {
                'title': '',
                'artist_name': str(art1),
                'release_date': str(d.release(x_id).year),
                'genre': genr,
                'style': stl,
                'song_text':''
            }


        return render(request, "blog/Acknowledgement.html", {'shazam_audd': shazam_audd, 'shazam_Genius': shazam_Genius, 'shazam_discogs': shazam_discogs})
