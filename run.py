<<<<<<< HEAD
=======

>>>>>>> d1302726762564361f358a3830603d2f07f74a7f
# to make virtual env to all project 
# .\venv\Scripts\Activate.ps1
# .\venv\Scripts\activate.bat
#  uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
# http://localhost:8001/docs#/

############## CloudFlare ##############

# python -m venv venv
# .\venv\Scripts\Activate.ps1
# .\venv\Scripts\activate.bat
# pip install -r requirements.txt
# uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload


###### on Terminal 1 #####
# 1- cd path\to\your\project
# 2- .\venv\Scripts\activate
# 3- uvicorn app.main:app --host 0.0.0.0 --port 8001

###### on Terminal 2 #####
# 1- cd C:\cloudflared  ... المكان اللى حاطين فيه كلاود فلير لما تنزلوه 
# 2- .\cloudflared-windows-386.exe tunnel --url http://localhost:8001
# 3- https://yeast-east-diversity-organ.trycloudflare.com ... ده هيكون لينك متغير هيظهر عندكم معرفتش اخليه ثابت للتسهيل 


# دى كانت تجربه تثبيت اللينك لو حد حاول يثبته يبص عليها الاول 

############ how to use same link every time ###########
# cd C:\cloudflared
# .\cloudflared-windows-386.exe tunnel login
# Connect your website or app
# make random domin as graduation.com
# Authorize 
# in the same terminal 
# cd C:\cloudflared
# .\cloudflared-windows-386.exe tunnel create 'name of your Tunnel '

# Tunnel credentials written to C:\Users\Techno Shield\.cloudflared\xxxxx-xxxx-xxxx.json
# Created tunnel graduation-api with id xxxxx-xxxx-xxxx-xxxx

# example 
# PS C:\cloudflared> .\cloudflared-windows-386.exe tunnel create Graduation_Project
# Tunnel credentials written to C:\Users\Techno Shield\.cloudflared\038d301c-12ff-48fa-b90c-a18205a590b4.json. cloudflared chose this file based on where your origin certificate was found. Keep this file secret. To revoke these credentials, delete the tunnel.

# Created tunnel Graduation_Project with id 038d301c-12ff-48fa-b90c-a18205a590b4


#  معلومات الـ Tunnel بتاعك:

# اسم الـ Tunnel: Graduation_Project
# Tunnel ID: 038d301c-12ff-48fa-b90c-a18205a590b4
# ملف الـ Credentials: C:\Users\Techno Shield\.cloudflared\038d301c-12ff-48fa-b90c-a18205a590b4.json


# هنفتح توت باد وهنحط فيها ده 
# tunnel: 038d301c-12ff-48fa-b90c-a18205a590b4
# credentials-file: C:\Users\Techno Shield\.cloudflared\038d301c-12ff-48fa-b90c-a18205a590b4.json

# ingress:
#   - hostname: api.graduationproject.com
#     service: http://localhost:8001
#   - service: http_status:404
# وهنسميه config.yml وهنحطه ف الفايل اللى ف السى اللى اسمه كلاود فلير


# دلوقت بقا هنربط الدومين بالتانيل اللى عملناه 

# on terminal 
# cd C:\cloudflared
# .\cloudflared-windows-386.exe tunnel route dns Graduation_Project api.graduationproject.com
# ده هيعملك subdomain: api.graduationproject.com ← ده الرابط الثابت بتاعك!





