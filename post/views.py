from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from post.models import Opportunity,Team
from post import serializer
from . import models
from Auth.models import User,company,Student
from Auth.serlaizers import UserStudentSerializer
from itertools import chain
from Auth import permissions
from django.db.models import Q
from elasticsearch_dsl import Q as elastic_Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .pagination import CustomPagination
from .models import TeamInvite
from Auth import documents as auth_doc
from . import documents as post_doc
from application.models import Application
from application.serlaizers import application_serializer
from datetime import datetime, timedelta
from django.utils import timezone




class opportunity_crud(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = [CustomPagination]

    @swagger_auto_schema(
    operation_description="Get all opportunities. For companies, this returns only their own opportunities. For other users, this returns all opportunities.",
    manual_parameters=[
        openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
    ],
    
    responses={
        200: openapi.Response(description="Operation successful"),
        201: openapi.Response(description="Created successfully"),
        204: openapi.Response(description="Deleted successfully"),
        400: 'Invalid data provided',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not found'
    })
    def get(self,request):
        user = request.user
        if user.has_perm('Auth.company'):
            post = models.Opportunity.objects.filter(company=user)
        else:
            post = models.Opportunity.objects.order_by('-created_at')
        paginator = CustomPagination()
        paginated_qs = paginator.paginate_queryset(post, request)
        ser = serializer.opportunity_serializer(paginated_qs, many=True)
        return Response(ser.data)
    
    @swagger_auto_schema(
        operation_description="Create a new opportunity. This endpoint allows companies to post new opportunities for students to apply.",
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'Type': openapi.Schema(type=openapi.TYPE_STRING),
                'category': openapi.Schema(type=openapi.TYPE_STRING),
                'skill_input': openapi.Schema(type=openapi.TYPE_STRING),
                'worktype': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: openapi.Response(description="Operation successful"),
            201: openapi.Response(description="Created successfully"),
            204: openapi.Response(description="Deleted successfully"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )
    def post(self, request):
        user = request.user
        if user.has_perm('Auth.company'):
            ser = serializer.opportunity_serializer(data=request.data)
            if ser.is_valid():
                ser.save(company=user)
                return Response(ser.data, status=status.HTTP_201_CREATED)
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'you are not a company'}, status=status.HTTP_403_FORBIDDEN)
    
    @swagger_auto_schema(
        operation_description="Update an existing opportunity. This endpoint allows companies to modify details of their posted opportunities.",
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'Type': openapi.Schema(type=openapi.TYPE_STRING),
                'category': openapi.Schema(type=openapi.TYPE_STRING),
                'skill_input': openapi.Schema(type=openapi.TYPE_STRING),
                'worktype': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: openapi.Response(description="Operation successful"),
            201: openapi.Response(description="Created successfully"),
            204: openapi.Response(description="Deleted successfully"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )
    def put(self, request):
        user = request.user
        if user.has_perm('Auth.company'):
            try:
                id = request.data.get('id')
                opp = Opportunity.objects.filter(id=id,company=user).first()
                if opp is None:
                    return Response({'post not found'}, status=status.HTTP_404_NOT_FOUND)
                ser = serializer.opportunity_serializer(opp, data=request.data, partial=True)
                if ser.is_valid():
                    ser.save()
                    return Response(ser.data)
                return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
            except models.Opportunity.DoesNotExist:
                return Response({'post does not exist'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'you are not a company'}, status=status.HTTP_403_FORBIDDEN)

@swagger_auto_schema(
    operation_description="Get all teams for the authenticated student. This endpoint returns a list of teams that the student is a member of.",
    manual_parameters=[
        openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'emails': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
        }
    ),
    responses={
        200: openapi.Response(description="Operation successful"),
        201: openapi.Response(description="Created successfully"),
        204: openapi.Response(description="Deleted successfully"),
        400: 'Invalid data provided',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not found'
    }
)
class team_crud(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = [CustomPagination]

    def get(self,request):
        user = request.user
        if user.has_perm('Auth.student'):
            team = models.Team.objects.prefetch_related("students").filter(students=user)
            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(team, request)
            ser = serializer.team_serializer(paginated_qs, many=True)
            return paginator.get_paginated_response(ser.data)
        return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
    
    @swagger_auto_schema(
        operation_description="Create a new team. This endpoint allows students to create teams for collaborative applications.",
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'emails': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            }
        ),
        responses={
            200: openapi.Response(description="Operation successful"),
            201: openapi.Response(description="Created successfully"),
            204: openapi.Response(description="Deleted successfully"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )
    def post(self, request):
        user = request.user
        data = request.data.copy()
        data['student_ids'] = [user.id]
        data['leader_id'] = user.id
        if user.has_perm('Auth.student'):
            ser = serializer.team_serializer(data=data)
            if ser.is_valid():
                ser.save()
                team = models.Team.objects.get(id=ser.data['id'])
                emails = data.get('emails')
                if emails is None:
                    return Response({"details" : "team created , invites sent" , "data" : ser.data}, status=status.HTTP_201_CREATED)
                students = User.objects.filter(email__in= emails , type = 'Student').all()

                for student in students :
                    if student is not None and student != user and not TeamInvite.objects.filter(inviter=user.id,receiver=student.id,team=team.id).exists() :
                        invite_data = {
                            "team_id" : team.id,
                            "inviter_id" : user.id ,
                            "receiver_id" : student.id,
                            "status" : "pending" 
                        }
                        invite_ser = serializer.TeamInviteSerializer(data = invite_data)
                        invite_ser.is_valid()
                        invite_ser.save()
                    

                return Response({"details" : "team created , invites sent" , "data" : ser.data}, status=status.HTTP_201_CREATED)
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
    
    @swagger_auto_schema(
        operation_description="Update an existing team. This endpoint allows students to modify details of their teams. only name, description and category is allowed to be edited",
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'team_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'team': openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        ),
        responses={
            200: openapi.Response(description="Operation successful"),
            201: openapi.Response(description="Created successfully"),
            204: openapi.Response(description="Deleted successfully"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )
    def put(self, request):
        user = request.user
        data = request.data
        if user.has_perm('Auth.student'):
            try:
                
                team_id = data.get('team_id')
                if team_id is None :
                    return Response({'team id not provided'}, status=status.HTTP_400_BAD_REQUEST)
                team = user.teams.filter(id=team_id).first()
                if team is None:
                    return Response({'team does not exist'}, status=status.HTTP_404_NOT_FOUND)
                team_data = data.get('team')
                if team_data is None:
                    return Response({'empty data , team remains the same'}, status=status.HTTP_200_OK)
                name = team_data.get('name')
                description = team_data.get('description')
                category = team_data.get('category')
                updated_team= {}
                if name is not None and name != "" :
                    updated_team['name'] = name
                if description is not None and description != "" :
                    updated_team['description'] = description    
                if category is not None and category != "" :
                    updated_team['category'] = category
                ser = serializer.team_serializer(team, data=updated_team, partial=True)
                if ser.is_valid():
                    ser.save()
                    return Response(ser.data)
                return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
            except models.Team.DoesNotExist:
                return Response({'team does not exist'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
    
    @swagger_auto_schema(
        operation_description="delete a team , only owners can delete the team",
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'team_id': openapi.Schema(type=openapi.TYPE_INTEGER,description="id of the team to delete"),
                'id': openapi.Schema(type=openapi.TYPE_INTEGER,description="alternative for team_id , only one is required")
            }
        ),
        responses={
            200: openapi.Response(description="Operation successful"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )

    def delete(self, request):
        user = request.user
        data = request.data
        if user.has_perm('Auth.student'):
            team_id = data.get('team_id')
            if team_id is None :
                team_id = data.get('id')
                if team_id is None:
                    return Response({'team_id not provided'}, status=status.HTTP_400_BAD_REQUEST)
            team = user.owned_teams.filter(id=team_id).first()
            if team is None:
                return Response({'team not found , or must be a leader'}, status=status.HTTP_404_NOT_FOUND)
            team.students.clear()
            user.owned_teams.remove(team)
            team.delete()
            return Response({'team removed successfully'}, status=status.HTTP_200_OK)
            
        return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
    
class team_managing(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="kick a user from a team , must be the leader of that team",
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'team_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            200: openapi.Response(description="Operation successful"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )
    def put(self, request):
        user = request.user
        data = request.data
        if user.has_perm('Auth.student'):
            
            team_id = data.get('team_id')
            if team_id is None :
                return Response({'team_id not provided'}, status=status.HTTP_400_BAD_REQUEST)
            team = user.owned_teams.filter(id=team_id).first()
            if team is None:
                return Response({'team not found , or must be a leader'}, status=status.HTTP_404_NOT_FOUND)
            user_id = data.get('user_id')
            if user_id is None :
                return Response({'user_id not provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            if user.id == user_id:
                return Response({'cant kick your self , use leave instead'}, status=status.HTTP_409_CONFLICT)

            kicked_user = team.students.all().filter(id = user_id).first()
            if kicked_user is None:
                return Response({'the user to kick is not a member in this team'}, status=status.HTTP_409_CONFLICT)
            team.students.remove(kicked_user)

            ser = serializer.team_serializer(team,many=False)
            return Response({"team":ser.data}, status=status.HTTP_200_OK)

        return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
    
    @swagger_auto_schema(
        operation_description="allows users to leave a team",
        manual_parameters=[

            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'team_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            200: openapi.Response(description="Operation successful"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )
    def delete(self, request):
        user = request.user
        data = request.data
        if user.has_perm('Auth.student'):
            
            team_id = data.get('team_id')
            if team_id is None :
                return Response({'team_id not provided'}, status=status.HTTP_400_BAD_REQUEST)
            team = user.teams.filter(id=team_id).first()
            if team is None:
                return Response({'team not found , or user is not in team'}, status=status.HTTP_404_NOT_FOUND)
            
            if not team.students.filter(id=user.id).exists():
                return Response({'must be in team to leave'}, status=status.HTTP_409_CONFLICT)

            if team.leader.id == user.id:
                if team.students.all().count()==1:
                    team.students.clear()
                    user.owned_teams.remove(team)
                    team.delete()
                else:
                    team.students.remove(user)
                    team.leader = team.students.all().order_by('date_joined').first()  
            else:
                team.students.remove(user)
            
            return Response({'user left team successfully'}, status=status.HTTP_200_OK)

        return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
    
    

    

class InviterTeamInvites(APIView):
    permission_classes = [IsAuthenticated]
    

    #get the invites sent by user
    def get(self,request):
        user = request.user 
        if user.has_perm('Auth.student'):
            try:
                invites = TeamInvite.objects.filter(inviter=user.id)
                paginator = CustomPagination()
                paginated_qs = paginator.paginate_queryset(invites, request)
                ser = serializer.TeamInviteSerializer(paginated_qs, many=True)
                return paginator.get_paginated_response(ser.data)
            except AttributeError:
                return Response({'user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
    #send an invite to a student by email
    def post(self,request):
        user = request.user
        data = request.data
        if not user.has_perm('Auth.student'):
            return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
        try:
            team_id = data.get('team_id')
            if team_id is None :
                return Response({'team_id not provided'},status=status.HTTP_400_BAD_REQUEST)
            
            
            
            team =   Team.objects.filter(id=team_id).first()
            if team is None :
                return Response({'team not found'},status=status.HTTP_404_NOT_FOUND)

            invited_emails = data.get('invited_emails') 
            if invited_emails is None :
                return Response({'invited_emails not provided'},status=status.HTTP_400_BAD_REQUEST)

            inviteds = User.objects.filter(email__in = invited_emails).filter(type='Student')
            if not inviteds.exists() :
                return Response({'no student found '},status=status.HTTP_404_NOT_FOUND)
            if user.id != team.leader.id : 
                return Response({'must be the leader'},status=status.HTTP_403_FORBIDDEN)
            results = []
            for invited in inviteds :
                if not team.students.filter(id = invited.id).exists() :
                    if not TeamInvite.objects.filter(inviter=user.id,receiver=invited.id,team=team_id).exists() :
                        ser = serializer.TeamInviteSerializer(data={
                        'team_id': team.id,  
                        'inviter_id': user.id,  
                        'receiver_id': invited.id,  
                        'status': 'pending'
                        })
                        if  ser.is_valid():
                            ser.save()
                            results.append(ser.data)
            
            
            return Response({"details" : " invites sent" , "data" : results},status=status.HTTP_201_CREATED)

        except AttributeError as e:
            
            return Response({"details" : " user not found" }, status=status.HTTP_404_NOT_FOUND)

    #delete an invite sent by a user
    def delete(self,request):
        user = request.user
        data = request.data
        if not user.has_perm('Auth.student'):
            return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
        
        invite_id = data.get('invite_id')
        if invite_id is None:
            return Response({"details" : "invite id not provided" },status=status.HTTP_400_BAD_REQUEST)
        invite = TeamInvite.objects.filter(id=invite_id).first()
        if invite is None or invite.inviter.id != user.id:
            return Response({"details" : "invite not found" },status=status.HTTP_404_NOT_FOUND)

        invite.delete()
        return Response({"details" : "deleted" },status=status.HTTP_200_OK)
         
class ReceiverTeamInvites(APIView):
    permission_classes = [IsAuthenticated]
    

    #get the invites sent to user
    def get(self,request):
        user = request.user 
        if user.has_perm('Auth.student'):
            try:
                
                invites = TeamInvite.objects.filter(receiver=user.id,status="pending")
                paginator = CustomPagination()
                paginated_qs = paginator.paginate_queryset(invites, request)
                ser = serializer.TeamInviteSerializer(paginated_qs, many=True)
                return paginator.get_paginated_response(ser.data)
            except AttributeError:
                return Response({'user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)

    #accept a pending invite by id
    def post(self,request):
        user = request.user
        data = request.data
        if not user.has_perm('Auth.student'):
            return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
        try:
            invite_id = data.get('invite_id')
            if invite_id is None:
                return Response({"details" : "invite id not provided" },status=status.HTTP_400_BAD_REQUEST)
            
            invite = TeamInvite.objects.filter(id=invite_id).first()
            if invite is None or invite.receiver.id != user.id or invite.status!="pending":
                return Response({"details" : "invite not found" },status=status.HTTP_404_NOT_FOUND)        

            team = invite.team
            if team is None :
                return Response({"details" : "team no longer exists" },status=status.HTTP_404_NOT_FOUND)

            if team.students.filter(id= user.id).exists() : 
                return Response({"details" : "user already in team" },status=status.HTTP_200_OK)

            team.students.add(user)
            invite.status = "accepted"
            invite.save()
            return Response({"details" : "accepted ,  user added" },status=status.HTTP_200_OK)

        except AttributeError:
            return Response({'user does not exist'}, status=status.HTTP_404_NOT_FOUND)

    #reject an invite by id (the invite is not deleted)
    def delete(self,request):
        user = request.user
        data = request.data
        if not user.has_perm('Auth.student'):
            return Response({'you are not a student'}, status=status.HTTP_403_FORBIDDEN)
        try:
            invite_id = data.get('invite_id')
            if invite_id is None:
                return Response({"details" : "invite id not provided" },status=status.HTTP_400_BAD_REQUEST)
            
            invite = TeamInvite.objects.filter(id=invite_id).first()
            if invite is None or invite.receiver.id != user.id or invite.status!="pending":
                return Response({"details" : "invite not found" },status=status.HTTP_404_NOT_FOUND)        

            
            invite.status = "rejected"
            invite.save()
            return Response({"details" : "invite rejected" },status=status.HTTP_200_OK)

        except AttributeError:
            return Response({"details" : " user not found" , "erros" :AttributeError.args }, status=status.HTTP_404_NOT_FOUND)




    
class SearchUser(APIView):
    permission_classes =[IsAuthenticated]

    @swagger_auto_schema(
      operation_description="search for a user by name + filter by type ",
      manual_parameters=[
          openapi.Parameter('username', openapi.IN_QUERY, description="the user's name", type=openapi.TYPE_STRING),
          openapi.Parameter('type', openapi.IN_QUERY, description="the user's type", type=openapi.TYPE_STRING),
          openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
      ],
      responses={
          200: 'Operation successful',
          400: 'username not provided'
      }
  )

    def get(self,request):
        username = request.query_params.get('username')
        if username is None : 
            return Response({"details":"username not provided"},status=status.HTTP_400_BAD_REQUEST)
        
        if username=="":
            return Response({},status=status.HTTP_200_OK)
        
        q = elastic_Q(
                "wildcard",
                name={"value": f"*{username.lower()}*"}
                )

        query = auth_doc.UserDocument.search().query(q)

        search_results = query.execute()

        type = request.query_params.get('type')
            
        ids = [hit.meta.id for hit in search_results.hits]
        qs = User.objects.filter(id__in = ids).exclude(id=request.user.id)

        if type is not None : 
            qs = qs.filter(type=type)

        paginator = CustomPagination()
        paginated_qs = paginator.paginate_queryset(qs,request)
        ser = serializer.UserStudentSerializer(paginated_qs,many=True)
        return paginator.get_paginated_response(ser.data)
    

class Search_saved(APIView):
  permission_classes = [ IsAuthenticated,permissions.IsStudent]

  @swagger_auto_schema(
      operation_description="search in saved opportunities for a user  by title ",
      manual_parameters=[
          openapi.Parameter('title', openapi.IN_PATH, description="opportunity's title", type=openapi.TYPE_STRING),
          openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
      ],
      responses={
          200: 'Operation successful',
          400: 'title not provided'
      }
  )
  def get(self, request):
    title = request.query_params.get('title')
    
    if title is None:
        return Response({"details": "title not provided"}, status=status.HTTP_400_BAD_REQUEST)

    student = request.user.student

    if student is None:
        return Response({"details": "must be a student"}, status=status.HTTP_401_UNAUTHORIZED)


    q = elastic_Q("multi_match", query=title, fields=["title"], fuzziness="auto")

    query = post_doc.OpportunityDocument.search().query(q)

    search_results = query.execute()
    
    ids = [hit.meta.id for hit in search_results.hits]
    saveds = student.savedposts.all()
    saved_ids = [saved.id for saved in saveds]
    
    qs = Opportunity.objects.filter(id__in=ids)
    qs = qs.filter(id__in= saved_ids )
    
    
   
    paginator = CustomPagination()
    paginated_qs = paginator.paginate_queryset(qs, request)
    

    ser = serializer.opportunity_serializer(paginated_qs, many=True)
    return paginator.get_paginated_response(ser.data)



class get_opportunities(APIView):
    @swagger_auto_schema(
      operation_description="get opportunities for the user to see ,(homepage)",
      manual_parameters=[
          openapi.Parameter('type', openapi.IN_QUERY, description="opportunity's type", type=openapi.TYPE_STRING)
      ],
      responses={
          200: 'Operation successful'
      })
    def get(self,request):
        type = request.query_params.get('type')
        
        qs = Opportunity.objects.filter(Type=type).order_by('-created_at')

        paginator = CustomPagination()
        paginated_qs = paginator.paginate_queryset(qs,request)

        ser = serializer.opportunity_serializer(paginated_qs,many=True)

        return paginator.get_paginated_response(ser.data)

class dashboard(APIView):
    permission_classes = [IsAuthenticated,permissions.IsStudent]

    @swagger_auto_schema(
      operation_description="get dashboard data for a student ",
      manual_parameters=[ 
          openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
      ],
      responses={
          200: '{ "total_application": int, "total_application_last_month": int, "accepted_count": int, "refused_count": int, "accepted_ratio": float, "refused_ratio": float, "daily_count": array_of_int[0-6], "teams": json, "applications": json }'


      }
  )

    def get(self,request):
        user =request.user
        applications = Application.objects.filter(student=user.id)
        total = applications.count()


        
        from dateutil.relativedelta import relativedelta
        last_month = timezone.now() - relativedelta(months=1)
  

        last_month_application = applications.filter(
            createdate__gte = last_month
        )

        last_month_count = last_month_application.count()


        accepted = last_month_application.filter(approve=True)
        accepted_count = accepted.count()
        refused_count = last_month_count - accepted_count
        if last_month_count !=0 :
            accepted_ratio = float(accepted_count) / last_month_count
            refused_ratio = 1 - accepted_ratio
        else:
            accepted_ratio =0
            refused_ratio = 0
        
        latest_app = applications.order_by('-createdate')
        paginator = CustomPagination()
        latest_app_paginated = paginator.paginate_queryset(latest_app,request)
        ser_app = application_serializer(latest_app_paginated,many=True)

        teams = user.teams.order_by('-createdate')
        teams = paginator.paginate_queryset(teams,request)
        ser_teams = serializer.team_serializer(teams,many=True)

        array = [0] * 7
        today = timezone.now()
        this_month = today.month
        this_day = today.day
        for i in range(0,6):
            loop_day = this_day-i
            if loop_day<1 :
                this_month -= 1
                this_day = 30
            array[i] = applications.filter(createdate__month=this_month,createdate__day = loop_day).count()

        return Response(
            {
                "total_application" : total ,
                "total_application_last_month" : last_month_count ,
                "accepted_count" : accepted_count ,
                "refused_count" : refused_count ,
                "accepted_ratio" : accepted_ratio ,
                "refused_ratio" : refused_ratio ,
                "daily_count" : array ,
                "teams" : ser_teams.data ,
                "applications" : ser_app.data ,
            }
            ,status=status.HTTP_200_OK)    

class team_by_id(APIView):
    permission_classes = [IsAuthenticated,permissions.IsStudent]
    @swagger_auto_schema(
      operation_description="get a team by id ",
      manual_parameters=[
          openapi.Parameter('id', openapi.IN_PATH, description="team's id", type=openapi.TYPE_STRING),
          openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
      ],
      responses={
          200: 'Operation successful',
          400: 'id not provided',
          404: 'team not found'
      }
  )
    def get(self,request,id):
        if id is None :
            return Response({"details" : "id not provided"},status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        teams = user.teams
        team = teams.filter(id=id).first()
        if team is None :
            return Response({"details" : "team not found"},status=status.HTTP_404_NOT_FOUND)
        ser = serializer.team_serializer(team,many=False)
        return Response({"details" : "successful","data" : ser.data},status=status.HTTP_200_OK)
        

class opp_by_id(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
      operation_description="get an opportunity by id ",
      manual_parameters=[
          openapi.Parameter('id', openapi.IN_PATH, description="opportunity's id", type=openapi.TYPE_STRING),
          openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
      ],
      responses={
          200: 'Operation successful',
          400: 'id not provided',
          404: 'opportunity not found'
      }
  )
    def get(self,request,id):
        if id is None :
            return Response({"details" : "id not provided"},status=status.HTTP_400_BAD_REQUEST)
        opps = Opportunity.objects.all()
        opp = opps.filter(id=id).first()
        if opp is None :
            return Response({"details" : "opportunity not found"},status=status.HTTP_404_NOT_FOUND)
        ser = serializer.opportunity_serializer(opp,many=False)
        return Response({"details" : "successful","data" : ser.data},status=status.HTTP_200_OK)
    def delete(self, request,id):
        user = request.user
        if user.has_perm('Auth.company'):
            try:
                post = models.Opportunity.objects.filter(id=id, company=user).first()
                post.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except models.Opportunity.DoesNotExist:
                return Response({'post does not exist'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'you are not a company'}, status=status.HTTP_403_FORBIDDEN)
    
    
class opp_by_company(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
      operation_description="get an opportunities by company ",
      manual_parameters=[
          openapi.Parameter('id', openapi.IN_PATH, description="company's id", type=openapi.TYPE_STRING),
          openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
      ],
      responses={
          200: 'Operation successful',
          400: 'id not provided',
          404: 'comany not found'
      }
  )
    def get(self,request,id):
        if id is None :
            return Response({"details" : "id not provided"},status=status.HTTP_400_BAD_REQUEST)
        company = User.objects.filter(id=id).first()
        if company is None or company.type != 'Company':
            return Response({"details" : "company not found"},status=status.HTTP_404_NOT_FOUND)
        opps = company.opportunity.all()
        paginator = CustomPagination()
        paginated_qs = paginator.paginate_queryset(opps,request)
        ser = serializer.opportunity_serializer(paginated_qs,many=True)
        return paginator.get_paginated_response(ser.data)
