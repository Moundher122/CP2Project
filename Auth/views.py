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
from drf_yasg import openapi
from datetime import datetime
import pytz
from google.oauth2 import id_token
from google.auth.transport import requests as req
import requests
from django.http import JsonResponse
from ProjectCore.settings import WEB_CLIENT_ID, APP_CLIENT_ID,WEB_CLIENT_SECRET,REDIRECT_URI,LINKEDIN_CLIENT_ID,LINKEDIN_CLIENT_SECRET,LINKEDIN_REDIRECT_URI
import json
from post.pagination import CustomPagination
from post import serializer as post_serializers
from django.http import HttpResponse
from application import models as app_models


class LinkedInAuthenticate(APIView):
    @swagger_auto_schema(
        operation_description="Authenticate a user using LinkedIn OAuth. This endpoint accepts a LinkedIn access token and returns user information along with JWT tokens for authentication.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['access_token'],
            properties={
                'access_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='LinkedIn access token obtained from LinkedIn OAuth flow'
                )
            },
            example={
                "access_token": "AQVJ..."
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Success message'
                        ),
                        'access': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='JWT access token'
                        ),
                        'refresh': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='JWT refresh token'
                        ),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'picture': openapi.Schema(type=openapi.TYPE_STRING),
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message'
                        )
                    }
                )
            ),
            500: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message'
                        )
                    }
                )
            )
        },
        tags=['Authentication']
    )
    def post(self, request):
        code = request.POST.get("code")
        
        if not code:
            return JsonResponse({"error": "Authorization code required"}, status=400)
        
        try:
            token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': LINKEDIN_CLIENT_ID,
                'client_secret': LINKEDIN_CLIENT_SECRET,
                'redirect_uri': LINKEDIN_REDIRECT_URI
            }
            
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            token_response = requests.post(token_url, data=data, headers=headers)
            token_data = token_response.json()
            if 'access_token' not in token_data:
                return JsonResponse({"error": "Failed to get access token from LinkedIn"}, status=400)
            
            access_token = token_data['access_token']
            
            profile_url = "https://api.linkedin.com/v2/userinfo"
            profile_headers = {
                'Authorization': f'Bearer {access_token}',
                'Connection': 'Keep-Alive'
            }
            
            profile_response = requests.get(profile_url, headers=profile_headers)
            profile_data = profile_response.json()
            
            email = profile_data.get('email')
            name = "{profile_data.get('given_name', '')} {profile_data.get('family_name', '')}".strip()
            picture = profile_data.get('picture') 
            if not email:
                return JsonResponse({"error": "Email not provided by LinkedIn"}, status=400)
            
            user, _ = models.User.objects.get_or_create(
                email=email,
                defaults={
                    "email": email,
                    "name": name,  
                    'password': code,  
                    'profilepic': {'link': picture, 'size': None,'created_at': datetime.utcnow().replace(tzinfo=pytz.utc).isoformat(),'name':'profilepic'},
                }
            )
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                "message": "LinkedIn login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "email": email,
                    "name": name,
                    "profilepic": user.profilepic,
                    "id": user.id,
                    "type": user.type,
                }       
            })
            
        except requests.exceptions.RequestException as e:
            return JsonResponse({"error": f"LinkedIn API error: {str(e)}"}, status=503)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class GoogleAuthenticate(APIView):
    @swagger_auto_schema(
        operation_description="Authenticate a user using Google OAuth. This endpoint accepts a Google ID token and returns user information along with JWT tokens for authentication.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['code'],
            properties={
                'code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Google Authorization code obtained from Google OAuth flow'
                )
            },
            example={
                "code": "4/0AfJohXn..."
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Success message'
                        ),
                        'access': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='JWT access token'
                        ),
                        'refresh': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='JWT refresh token'
                        ),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'profilepic': openapi.Schema(type=openapi.TYPE_STRING),
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'type': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message'
                        )
                    }
                )
            ),
            500: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message'
                        )
                    }
                )
            )
        },
        tags=['Authentication']
    )
    def post(self, request):
        code = request.POST.get("code")  
        if not code:
           return JsonResponse({"error": "Authorization code required"}, status=400)
        try:
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                'code': code,
                'client_id': WEB_CLIENT_ID,
                'client_secret': WEB_CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI,
                'grant_type': 'authorization_code'
            }               
            response = requests.post(token_url, data=data)
            token_data = response.json() 
            
            if 'id_token' not in token_data:
                return JsonResponse({"error": "Failed to get ID token"}, status=400)
            
            decoded_token = None
            for client_id in [WEB_CLIENT_ID, APP_CLIENT_ID]:
                try:
                    decoded_token = id_token.verify_oauth2_token(
                        token_data['id_token'],
                        req.Request(),
                        client_id
                    )
                    break
                except ValueError:
                    continue
            
            if decoded_token is None:
                return JsonResponse({"error": "Invalid token"}, status=400)
                
            email = decoded_token.get('email')
            name = decoded_token.get('name')
            picture = decoded_token.get('picture')
            
            if not email:
                return JsonResponse({"error": "Email not found"}, status=400)
                
            user, _ = models.User.objects.get_or_create(email=email, defaults={"email": email, "name": name, 'password':code,'profilepic':{'link': picture, 'size': None,'created_at': datetime.utcnow().replace(tzinfo=pytz.utc).isoformat(),'name':'profilepic'},'type':None})
            refresh = RefreshToken.for_user(user)
            
            return JsonResponse({
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "email": email, 
                    "name": name, 
                    "profilepic": user.profilepic,
                    "id": user.id,
                    "type": user.type,
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
class googleauthforapp(APIView):
   def post(self, request):
    token_id = request.data.get("token_id")  # ⬅️ Client sends this directly

    if not token_id:
        return JsonResponse({"error": "ID token is required"}, status=400)

    try:
        decoded_token = None
        print(token_id)
        # Try both client IDs (Web and App)
        for client_id in [WEB_CLIENT_ID, APP_CLIENT_ID]:
            try:
                decoded_token = id_token.verify_oauth2_token(token_id, req.Request(), client_id)
                break
            except ValueError:
                continue
        if decoded_token is None:
            return JsonResponse({"error": "Invalid token"}, status=400)
        email = decoded_token.get('email')
        name = decoded_token.get('name')
        picture = decoded_token.get('picture')

        if not email:
            return JsonResponse({"error": "Email not found in token"}, status=400)

        # Create or get user
        user, _ = models.User.objects.get_or_create(
            email=email,
            defaults={
                "email": email,
                "name": name,
                "password": '123456789',  # Not safe in real apps; just for placeholder
                "profilepic": {'link': picture, 'size': None,'created_at': datetime.utcnow().replace(tzinfo=pytz.utc).isoformat(),'name':'profilepic'},
                "type": None
            }
        )
        print(user)
        print(user.student)
        if  user.student==None:
         ser=serlaizers.UserStudentSerializer(user,data={'type':'Student'},partial=True)
         if not ser.is_valid():
          return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)
         ser.save()
         print(ser.data)
        else:
           ser=serlaizers.UserStudentSerializer(user)
           print(ser.data)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": ser.data
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
     
                
class addtype(APIView):
  permission_classes=[IsAuthenticated]
  @swagger_auto_schema(
      operation_description="Set the user type (student or company) for an authenticated user. This endpoint is used after initial registration to specify the user's role in the system.",
      request_body=openapi.Schema(
          type=openapi.TYPE_OBJECT,
          properties={
              'type': openapi.Schema(type=openapi.TYPE_STRING, description='User type (student/company)'),
          },
          required=['type']
      ),
      responses={
          200: openapi.Response(description="Type added successfully"),
          400: 'Invalid type provided'
      }
  )
  
  def put(self,request):
    user=request.user
    type=request.data.get('type')
    if type is None:
      return Response('add type',status=status.HTTP_400_BAD_REQUEST)
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
class Try(APIView):
  def post(self,request):
    user, _ = models.User.objects.get_or_create(email='hiss@gmail.com', defaults={"email": 'hiss@gmail.com', "name": 'hssi', 'password':'0000','type':None})
    refresh = RefreshToken.for_user(user)
            
    return JsonResponse({
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "email": user.email, 
                    "name": user.name, 
                    "id": user.id,
                    "type": user.type,
                }
            }) 
class Signup(APIView):
    @swagger_auto_schema(
        operation_description="Register a new user in the system. This endpoint creates a new user account with the specified type (student or company), name, email, and password.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['type', 'name', 'email', 'password'],
            properties={
                'type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User type (student/company)',
                    enum=['student', 'company']
                ),
                'name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User full name'
                ),
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User email address',
                    format='email'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User password',
                    format='password'
                ),
                'number': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='User phone number (optional)'
                )
            },
            example={
                "type": "student",
                "name": "John Doe",
                "email": "john@example.com",
                "password": "securepassword123",
                "number": 1234567890
            }
        ),
        responses={
            200: openapi.Response(
                description="Signup successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'type': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        ),
                        'refresh': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='JWT refresh token'
                        ),
                        'access': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='JWT access token'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message'
                        )
                    }
                )
            ),
            405: openapi.Response(
                description="Method Not Allowed",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Type not provided'
                        )
                    }
                )
            )
        },
        tags=['Authentication']
    )
    def post(self,request):
        data=request.data
        type=data.get('type')
        if type:
          if type.lower()=='student':
           ser=serlaizers.UserStudentSerializer(data=data)
           if ser.is_valid():
             ser.save(type='Student')
             refresh=RefreshToken.for_user(ser.instance)
             access_token = refresh.access_token
             return Response({'user':ser.data,'refresh':str(refresh),'access':str(access_token)})
           return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)
          if type.lower()=='company':
           ser=serlaizers.UserCompanySerializer(data=data)
           if ser.is_valid():
            ser.save(type='Company')
            refresh=RefreshToken.for_user(ser.instance)
            access_token = refresh.access_token
            return Response({'user':ser.data,'refresh':str(refresh),'access':str(access_token)})
          return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({'add type'},status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Login(APIView):
    @swagger_auto_schema(
        operation_description="Authenticate a user with email/name and password. This endpoint returns user information and JWT tokens for authentication.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['password'],
            properties={
                'name/email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User email or username for login'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User password',
                    format='password'
                ),
            },
            example={
                "name/email": "user@example.com",
                "password": "yourpassword123"
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'type': openapi.Schema(type=openapi.TYPE_STRING),
                                'profilepic': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        ),
                        'refresh': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='JWT refresh token'
                        ),
                        'access': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='JWT access token'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message'
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message'
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message'
                        )
                    }
                )
            )
        },
        tags=['Authentication']
    )
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
  @swagger_auto_schema(
      operation_description="Get the current user's profile information. This endpoint returns the authenticated user's profile details.",
      manual_parameters=[
          openapi.Parameter(
              'Authorization',
              openapi.IN_HEADER,
              description="JWT token",
              type=openapi.TYPE_STRING,
              required=True
          )
      ],
      responses={
          200: openapi.Response(
              description="Profile retrieved successfully",
              schema=openapi.Schema(
                  type=openapi.TYPE_OBJECT,
                  properties={
                      'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                      'email': openapi.Schema(type=openapi.TYPE_STRING),
                      'name': openapi.Schema(type=openapi.TYPE_STRING),
                      'type': openapi.Schema(type=openapi.TYPE_STRING),
                      'profilepic': openapi.Schema(type=openapi.TYPE_STRING)
                  }
              )
          ),
          401: openapi.Response(
              description="Unauthorized",
              schema=openapi.Schema(
                  type=openapi.TYPE_OBJECT,
                  properties={
                      'error': openapi.Schema(
                          type=openapi.TYPE_STRING,
                          description='Error message'
                      )
                  }
              )
          )
      },
      tags=['User Profile']
  )
  def get(self,request):
     user=request.user
     if user.company:
       ser=serlaizers.UserCompanySerializer(user)
     elif user.student:
       ser=serlaizers.UserStudentSerializer(user)
     return Response(ser.data)

  @swagger_auto_schema(
      operation_description="Update a user's profile information. This endpoint allows users to modify their profile details.",
      manual_parameters=[
          openapi.Parameter(
              'Authorization',
              openapi.IN_HEADER,
              description="JWT token",
              type=openapi.TYPE_STRING,
              required=True
          )
      ],
      request_body=openapi.Schema(
          type=openapi.TYPE_OBJECT,
          properties={
              'name': openapi.Schema(
                  type=openapi.TYPE_STRING,
                  description='User full name'
              ),
              'email': openapi.Schema(
                  type=openapi.TYPE_STRING,
                  description='User email address',
                  format='email'
              ),
              'profilepic': openapi.Schema(
                  type=openapi.TYPE_STRING,
                  description='URL to user profile picture'
              )
          },
          example={
              "name": "John Doe",
              "email": "john@example.com",
              "profilepic": "https://example.com/profile.jpg"
          }
      ),
      responses={
          200: openapi.Response(
              description="Profile updated successfully",
              schema=openapi.Schema(
                  type=openapi.TYPE_OBJECT,
                  properties={
                      'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                      'email': openapi.Schema(type=openapi.TYPE_STRING),
                      'name': openapi.Schema(type=openapi.TYPE_STRING),
                      'type': openapi.Schema(type=openapi.TYPE_STRING),
                      'profilepic': openapi.Schema(type=openapi.TYPE_STRING)
                  }
              )
          ),
          401: openapi.Response(
              description="Unauthorized",
              schema=openapi.Schema(
                  type=openapi.TYPE_OBJECT,
                  properties={
                      'error': openapi.Schema(
                          type=openapi.TYPE_STRING,
                          description='Error message'
                      )
                  }
              )
          ),
          400: openapi.Response(
              description="Bad Request",
              schema=openapi.Schema(
                  type=openapi.TYPE_OBJECT,
                  properties={
                      'error': openapi.Schema(
                          type=openapi.TYPE_STRING,
                          description='Error message'
                      )
                  }
              )
          )
      },
      tags=['User Profile']
  )
  def put(self,request):
    user=request.user
    data=request.data
    if user.company :
      ser=serlaizers.UserCompanySerializer(user,data=data,partial=True)
      if ser.is_valid():
       ser.save()
       return Response(ser.data)
      return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)
    elif user.student:
      education=data.get('education')
      skills=data.get('skills')
      jsondata=data.get('json')
      dataentry=data.copy()
      if education :
        if not jsondata:
         education=json.loads(education)
         dataentry['education']=education
        else:
            dataentry['education']=[education]
            if not isinstance(education,list) :
             return Response(status=status.HTTP_304_NOT_MODIFIED)
      if skills:  
        if not jsondata:
         skills=json.loads(skills)
        dataentry['skills']=skills
      ser=serlaizers.UserStudentSerializer(user,data=dataentry,partial=True)
      if ser.is_valid():
       ser.save()
       return Response(ser.data)
      return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)

  @swagger_auto_schema(
      operation_description="Delete a user account. This endpoint requires the user's password for confirmation.",
      manual_parameters=[
          openapi.Parameter(
              'Authorization',
              openapi.IN_HEADER,
              description="JWT token",
              type=openapi.TYPE_STRING,
              required=True
          )
      ],
      request_body=openapi.Schema(
          type=openapi.TYPE_OBJECT,
          required=['password'],
          properties={
              'password': openapi.Schema(
                  type=openapi.TYPE_STRING,
                  description='User password for confirmation',
                  format='password'
              )
          },
          example={
              "password": "yourpassword123"
          }
      ),
      responses={
          200: openapi.Response(
              description="Account deleted successfully"
          ),
          401: openapi.Response(
              description="Unauthorized",
              schema=openapi.Schema(
                  type=openapi.TYPE_OBJECT,
                  properties={
                      'error': openapi.Schema(
                          type=openapi.TYPE_STRING,
                          description='Error message'
                      )
                  }
              )
          ),
          400: openapi.Response(
              description="Bad Request",
              schema=openapi.Schema(
                  type=openapi.TYPE_OBJECT,
                  properties={
                      'error': openapi.Schema(
                          type=openapi.TYPE_STRING,
                          description='Error message'
                      )
                  }
              )
          )
      },
      tags=['User Profile']
  )
  def delete(self,request):
    user=models.User.objects.get(id=request.user.id)
    password=request.data.get('password')
    if password:
      if user.check_password(password):
        user.delete()
        return Response({'user deleted succefuly'})
      return Response({'incorect password'},status=status.HTTP_401_UNAUTHORIZED)
    return Response({'add password'},status=status.HTTP_400_BAD_REQUEST)

class ForgotPass(APIView):
    @swagger_auto_schema(
        operation_description="Request a password reset. This endpoint sends an OTP to the user's email for password reset verification.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email/name'],
            properties={
                'email/name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User email or username'
                )
            },
            example={
                "email/name": "user@example.com"
            }
        ),
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'otp': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='One-time password for verification'
                        ),
                        'iat': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Issued at timestamp'
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='User does not exist'
                        )
                    }
                )
            )
        },
        tags=['Password Management']
    )
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
    @swagger_auto_schema(
        operation_description="Register a Firebase Cloud Messaging (FCM) token for push notifications. This endpoint associates an FCM token with the authenticated user.",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT token",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['token'],
            properties={
                'token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Firebase Cloud Messaging token'
                )
            },
            example={
                "token": "fcm_token_here"
            }
        ),
        responses={
            200: openapi.Response(
                description="FCM token registered successfully"
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Invalid data provided'
                        )
                    }
                )
            )
        },
        tags=['Notifications']
    )
    def post(self,request):
        user=request.user
        ser=serlaizers.Fcmserlaizer(data=request.data)
        if ser.is_valid():
            ser.save()
            ser.instance.user.add(user)
            return Response({'suceffuly'})
        return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)
class logout(APIView):
      permission_classes=[IsAuthenticated]
      def delete(self,request):
        user=request.user
        token = request.headers.get('token')
        try:
            fcm=models.MCF.objects.get(user=user,token=token)
            fcm.delete()
            return Response({'logout succefuly'})
        except models.MCF.DoesNotExist:
            return Response({'fcm token does not exist'},status=status.HTTP_404_NOT_FOUND)

class reset_password(APIView):
    @swagger_auto_schema(
        operation_description="Reset a user's password. This endpoint allows users to set a new password after receiving an OTP.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name/email', 'password'],
            properties={
                'name/email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User email or username'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='New password',
                    format='password'
                )
            },
            example={
                "name/email": "user@example.com",
                "password": "newpassword123"
            }
        ),
        responses={
            200: openapi.Response(
                description="Password changed successfully"
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Invalid data provided'
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='User does not exist'
                        )
                    }
                )
            ),
            406: openapi.Response(
                description="Not Acceptable",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Password and OTP required'
                        )
                    }
                )
            )
        },
        tags=['Password Management']
    )
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
  @swagger_auto_schema(
      operation_description="Get a user's profile information by ID. This endpoint returns the profile details of a specific user.",
      manual_parameters=[
          openapi.Parameter('id', openapi.IN_PATH, description="User ID", type=openapi.TYPE_INTEGER),
          openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
      ],
      responses={
          200: openapi.Response(description="User details retrieved successfully"),
          404: 'User does not exist'
      }
  )
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

class getuserwithname(APIView):
  def get(self,request,name):
    try:
     user=models.User.objects.get(name=name)
     if user.student:
       ser=serlaizers.UserStudentSerializer(user)
     elif user.company:
       ser=serlaizers.UserCompanySerializer(user)
     return Response(ser.data)
    except models.User.DoesNotExist:
      return Response({'user dosent exist'},status=status.HTTP_404_NOT_FOUND)   

    

class savedpost(APIView):
  permission_classes=[IsAuthenticated,permissions.IsStudent]
  @swagger_auto_schema(
      operation_description="Save an opportunity post to the user's saved posts. This endpoint allows students to bookmark opportunities they're interested in.",
      manual_parameters=[
          openapi.Parameter(
              'id',
              openapi.IN_PATH,
              description="Post ID",
              type=openapi.TYPE_INTEGER,
              required=True
          ),
          openapi.Parameter(
              'Authorization',
              openapi.IN_HEADER,
              description="JWT token",
              type=openapi.TYPE_STRING,
              required=True
          )
      ],
      responses={
          200: openapi.Response(
              description="Post saved successfully"
          ),
          404: openapi.Response(
              description="Not Found",
              schema=openapi.Schema(
                  type=openapi.TYPE_OBJECT,
                  properties={
                      'error': openapi.Schema(
                          type=openapi.TYPE_STRING,
                          description='Post does not exist'
                      )
                  }
              )
          )
      },
      tags=['Saved Posts']
  )
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
  
  @swagger_auto_schema(
      operation_description="Remove an opportunity post from the user's saved posts. This endpoint allows students to unbookmark opportunities.",
      manual_parameters=[
          openapi.Parameter(
              'id',
              openapi.IN_PATH,
              description="Post ID",
              type=openapi.TYPE_INTEGER,
              required=True
          ),
          openapi.Parameter(
              'Authorization',
              openapi.IN_HEADER,
              description="JWT token",
              type=openapi.TYPE_STRING,
              required=True
          )
      ],
      responses={
          200: openapi.Response(
              description="Post removed from saved posts successfully"
          ),
          404: openapi.Response(
              description="Not Found",
              schema=openapi.Schema(
                  type=openapi.TYPE_OBJECT,
                  properties={
                      'error': openapi.Schema(
                          type=openapi.TYPE_STRING,
                          description='Post does not exist'
                      )
                  }
              )
          )
      },
      tags=['Saved Posts']
  )
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
  @swagger_auto_schema(
      operation_description="Get all saved opportunity posts for the authenticated student. This endpoint returns a list of opportunities that the student has bookmarked.",
      manual_parameters=[
          openapi.Parameter(
              'Authorization',
              openapi.IN_HEADER,
              description="JWT token",
              type=openapi.TYPE_STRING,
              required=True
          )
      ],
      responses={
          200: openapi.Response(
              description="Saved posts retrieved successfully",
              schema=openapi.Schema(
                  type=openapi.TYPE_OBJECT,
                  properties={
                      'posts': openapi.Schema(
                          type=openapi.TYPE_ARRAY,
                          items=openapi.Schema(
                              type=openapi.TYPE_OBJECT,
                              properties={
                                  'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                  'title': openapi.Schema(type=openapi.TYPE_STRING),
                                  'description': openapi.Schema(type=openapi.TYPE_STRING),
                                  'Type': openapi.Schema(type=openapi.TYPE_STRING),
                                  'category': openapi.Schema(type=openapi.TYPE_STRING),
                                  'skill_input': openapi.Schema(type=openapi.TYPE_STRING),
                                  'worktype': openapi.Schema(type=openapi.TYPE_STRING)
                              }
                          )
                      )
                  }
              )
          )
      },
      tags=['Saved Posts']
  )
  def get(self,request):
    user=request.user
    ser=sr.opportunity_serializer(user.student.savedposts,many=True)
    return Response(ser.data)
class notfication(APIView):
    permission_classes=[IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Get all notifications for the authenticated user. This endpoint returns a list of notifications.",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT token",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Notifications retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'notifications': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING),
                                    'read': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                                }
                            )
                        )
                    }
                )
            )
        },
        tags=['Notifications']
    )
    def get(self,request):
        user=request.user
        notf=models.Notfications.objects.filter(user=user)
        ser=serlaizers.notficationserlaizer(notf,many=True)
        return Response(ser.data)

    @swagger_auto_schema(
        operation_description="Mark a notification as read. This endpoint updates the read status of a notification.",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="Notification ID",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT token",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Notification marked as read successfully"
            ),
            404: openapi.Response(
                description="Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Notification does not exist'
                        )
                    }
                )
            )
        },
        tags=['Notifications']
    )
    def put(self,request,id):
        user=request.user
        models.Notfications.objects.filter(id=id ,user=user).update(isseen=True)
        return Response({'updated'})

class notfi(APIView):
    permission_classes=[IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Delete a notification. This endpoint removes a notification from the user's notification list.",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="Notification ID",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT token",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Notification deleted successfully"
            ),
            404: openapi.Response(
                description="Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Notification does not exist'
                        )
                    }
                )
            )
        },
        tags=['Notifications']
    )
    def delete(self,request,id):
        notf=models.Notfications.objects.filter(id=id,user=request.user).first()
        notf.delete()
        return Response('deleted succefuly')