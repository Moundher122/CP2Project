from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . import models
from . import serlaizers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from . import permissions
from . import tasks
from numpy import random
from django.core.cache import cache
from post import models as md
from post import serializer as sr
from django.contrib.auth.models import Permission
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from datetime import datetime
import pytz
from google.oauth2 import id_token
from google.auth.transport import requests as req
import requests
from django.http import JsonResponse
from ProjectCore.settings import WEB_CLIENT_ID, APP_CLIENT_ID
def linkedin_authenticate(request):
    access_token = request.POST.get("access_token") or request.headers.get("Authorization")

    if not access_token:
        return JsonResponse({"error": "Access token required"}, status=400)

    linkedin_url = "https://api.linkedin.com/v2/me"
    linkedin_email_url = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"

    headers = {"Authorization": f"Bearer {access_token}"}

    profile_response = requests.get(linkedin_url, headers=headers)
    email_response = requests.get(linkedin_email_url, headers=headers)

    if profile_response.status_code != 200 or email_response.status_code != 200:
        return JsonResponse({"error": "Invalid LinkedIn token"}, status=400)

    profile_data = profile_response.json()
    email_data = email_response.json()
    
    first_name = profile_data.get("localizedFirstName", "")
    last_name = profile_data.get("localizedLastName", "")
    email = email_data.get("elements", [{}])[0].get("handle~", {}).get("emailAddress", "")

    if not email:
        return JsonResponse({"error": "Email not found"}, status=400)

    user, _ = models.User.objects.get_or_create(email=email, defaults={"username": email, "name": first_name+last_name, 'password':access_token,'profile_picture':profile_data.get("profilePicture", {}).get("displayImage", ""), 'type':None})
    refresh = RefreshToken.for_user(user)
    return JsonResponse({
        "message": "Login successful",
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "user": {"email": email, "name": f"{first_name} {last_name}"}
    })
class addtype(APIView):
  permission_classes=[IsAuthenticated]
  def put(self,request):
    user=request.user
    type=request.data['type']
    if type.lower()=='student':
        ser=serlaizers.UserStudentSerializer(user,data={'type':'Student'},partial=True)
        if ser.is_valid():
          ser.save()
          return Response(ser.data)
        return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)
    elif type.lower()=='company':
        ser=serlaizers.UserCompanySerializer(user,data={'type':'Company'},partial=True)
        if ser.is_valid():
          ser.save()
          return Response(ser.data)
        return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)
    else:
      return Response('Entre a valid type',status=status.HTTP_400_BAD_REQUEST)
def google_authenticate(request):
    token = request.POST.get("id_token")  
    try:
        for client_id in [WEB_CLIENT_ID, APP_CLIENT_ID]:
            try:
                decoded_token = id_token.verify_oauth2_token(token, req.Request(), client_id)
                break 
            except Exception:
                continue
        if decoded_token is None:
            return JsonResponse({"error": "Invalid token"}, status=400)
        email = decoded_token.get("email")
        name = decoded_token.get("name")
        picture = decoded_token.get("picture")
        if not email:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user, created = models.User.objects.get_or_create(email=email, defaults={"username": email, "name": name,'password':token})
        refresh = RefreshToken.for_user(user)
        return JsonResponse({
            "message": "Login successful",
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {"email": email, "name": name, "picture": picture,"type":None}
        })
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
class Signup(APIView):
  def post(self,request):
    data=request.data
    type=data.get('type')
    if type:
      if type.lower()=='student':
       ser=serlaizers.UserStudentSerializer(data=data)
       if ser.is_valid():
         ser.save(type='Student')
         user=models.User.objects.get(id=ser.data['id'])
         refresh=RefreshToken.for_user(user)
         access_token = refresh.access_token
         return Response({'user':ser.data,'refresh':str(refresh),'access':str(access_token)})
       return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)
      if type.lower()=='company':
       ser=serlaizers.UserCompanySerializer(data=data)
       if ser.is_valid():
        ser.save(type='Company')
        user=models.User.objects.get(id=ser.data['id'])
        refresh=RefreshToken.for_user(user)
        access_token = refresh.access_token
        return Response({'user':ser.data,'refresh':str(refresh),'access':str(access_token)})
      return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)
    return Response({'add type'},status=status.HTTP_405_METHOD_NOT_ALLOWED)


class Login(APIView):
  def post(self,request):
    name=request.data.get('name')
    email=request.data.get('email')
    password=request.data.get('password')
    try:
      if name:
       user=models.User.objects.get(name=name)
      elif email:
       user=models.User.objects.get(email=email)
      if name or email:
       if user.check_password(password):
        if user.has_perm('Auth.company'):
          ser=serlaizers.UserCompanySerializer(user)
        else:
         ser=serlaizers.UserStudentSerializer(user)
        refresh=RefreshToken.for_user(user)
        access_token = refresh.access_token
        return Response({'user':ser.data,'refresh':str(refresh),'access':str(access_token)})
       return Response({'Password inccorect'},status=status.HTTP_401_UNAUTHORIZED)
      return  Response({'Email or password are requeird'},status=status.HTTP_400_BAD_REQUEST)
    except models.User.DoesNotExist:
      return Response({'User Dosent exist'},status=status.HTTP_404_NOT_FOUND)


class acc(APIView):
  permission_classes=[IsAuthenticated]
  def delete(self,request):
    user=models.User.objects.get(id=request.user.id)
    password=request.data.get('password')
    if password:
      if user.check_password(password):
        user.delete()
        return Response({'user deleted succefuly'})
      return Response({'incorect password'},status=status.HTTP_401_UNAUTHORIZED)
    return Response({'add password'},status=status.HTTP_400_BAD_REQUEST)
  def put(self,request):
    user=request.user
    data=request.data
    if user.company :
      ser=serlaizers.UserCompanySerializer(user,data=data,partial=True)
      if ser.is_valid():
       ser.save()
       return Response(ser.data)
      return Response(ser.errors)
    elif user.student:
      ser=serlaizers.UserStudentSerializer(user,data=data,partial=True)
      if ser.is_valid():
       ser.save()
       return Response(ser.data)
      return Response(ser.errors)

  def get(self,request):
     user=request.user
     if user.company:
       ser=serlaizers.UserCompanySerializer(user)
     elif user.student:
       ser=serlaizers.UserStudentSerializer(user)
     return Response(ser.data)
class ForgotPass(APIView):
  def post(self,request):
    email=request.data.get('email')
    name=request.data.get('name')
    try:
      if email:
       user=models.User.objects.get(email=email)
      elif name:
       user=models.User.objects.get(name=name)
      useremail=user.email
      otp = f"{random.randint(0, 999999):06d}"
      tasks.sendemail.delay(
      message=(
        "You requested to reset your password. Please use the OTP below:<br><br>"
        "<h2 style='color: #007bff; text-align: center;'>{}</h2><br>"
        "This OTP is valid for only 5 minutes.<br><br>"
        "If you didn't request this, please ignore this email.<br><br>"
    ).format(otp),
    subject="Reset Your Password",
    receipnt=[useremail],
    title="Reset Password",
    user=user.name)
      return Response({'otp':otp,'iat':datetime.utcnow().replace(tzinfo=pytz.utc).isoformat()})
    except models.User.DoesNotExist:
      return Response({'user dosnet exist'},status=status.HTTP_404_NOT_FOUND)

class Fcm(APIView):
  permission_classes=[IsAuthenticated]
  def post(self,request):
    user=request.user
    ser=serlaizers.Fcmserlaizer(data=request.data)
    if ser.is_valid():
      ser.save()
      return Response({'suceffuly'})
    return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)
class reset_password(APIView):
  def put(self,request):
    email=request.data.get('email')
    name=request.data.get('name')
    newpassword=request.data.get('password')
    try:
      if newpassword:
         if email:
           user=models.User.objects.get(email=email)
         elif name:
          user=models.User.objects.get(name=name)
         if name or email:
          if user.check_password(newpassword):
            return Response({'pervieuos password'})
          user.set_password(newpassword)
          user.save()
          tasks.sendemail.delay(
           message=(
           "Your password has been successfully reset.<br><br>"
           "If you made this change, you can ignore this email.<br><br>"
            "If you did not request this change, please contact our support immediately.<br><br>"
            ).format(user.name),
            subject="Your Password Has Been Reset",
            receipnt=[user.email],
            title="Password Reset Successful",
            user=user.name)
          return Response({'password changed succefuly'})
         return Response({'Email or name is requeird'},status=status.HTTP_406_NOT_ACCEPTABLE)
      return Response({'password and otp are requeird'},status=status.HTTP_406_NOT_ACCEPTABLE)
    except models.User.DoesNotExist:
      return Response({'user dosent exist'},status=status.HTTP_404_NOT_FOUND)
    
class getuser(APIView):
  permission_classes=[IsAuthenticated]
  def get(self,request,id):
    try:
      user=models.User.objects.get(id=id)
      if user.company:
       ser=serlaizers.UserCompanySerializer(user)
      elif user.student:
        ser=serlaizers.UserStudentSerializer(user)
      return Response(ser.data)
    except Exception :
      return Response({'user dosent exist'},status=status.HTTP_404_NOT_FOUND)

class savedpost(APIView):
  permission_classes=[IsAuthenticated,permissions.IsStudent]
  def post(self,request,id):
    user =request.user 
    try:
       post=md.Opportunity.objects.get(id=id)
       student=user.student
       student.savedposts.add(post)
       student.save()
       return Response({'saved succefluy'})
    except Exception :
      return Response({"post does'nt exist"},status=status.HTTP_404_NOT_FOUND)
  def delete(self,request,id):
    user=request.user
    try:
        post=md.Opportunity.objects.get(id=id)
        if not user.student.savedposts.filter(id=post.id).exists():
          return Response({"item is'nt saved"})
        user.student.savedposts.remove(post)
        user.student.save()
        return Response({'post removed succefuly'})
    except Exception as e:
      return Response({'eror':str(e)},status=status.HTTP_404_NOT_FOUND)

class post(APIView):
  permission_classes=[IsAuthenticated,permissions.IsStudent]
  def get(self,request):
    user=request.user
    ser=sr.opportunity_serializer(user.student.savedposts,many=True)
    return Response(ser.data)
class notfication(APIView):
  permission_classes=[IsAuthenticated]
  def put(self,request,id):
    user=request.user
    notf=models.Notfications.objects.filter(id=id).update(isseen=True)
    return Response({'updated'})
  






