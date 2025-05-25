
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from Auth.models import User
from post.pagination import CustomPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from chat.serializer import ChatSerializer,MessageSerializer
from .models import Chat

class RoomName(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="return chats of a user,messages are NOT returned only last messages is provided , use [get /chat/messages?room_name=] to get all messages, pagination with 'page''limit'",
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response(description="Operation successful"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )
    #get chats for a user
    def get(self,request):
        user = request.user
        type = user.type.lower()
        chats = []
        if type == 'student' :
            chats = user.chats_as_student
        elif type == 'company' :
            chats = user.chats_as_company
        else:
            return Response({"details" : "must be a student or company"},status=status.HTTP_403_FORBIDDEN)
        paginator = CustomPagination()
        paginated_qs = paginator.paginate_queryset(chats.all(),request)
        ser = ChatSerializer(paginated_qs,context = {"user_id" : user.id},many=True)
        return paginator.get_paginated_response({"details" : "successful","chats":ser.data})


    @swagger_auto_schema(
        operation_description="create and start a chat with a user , only student-company chats are allowed , chat model is returned ",
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING),
            openapi.Parameter('user_id', openapi.IN_QUERY, description="provide the id of the user u want to create a chat with", type=openapi.TYPE_INTEGER)
        ],
        
        responses={
            201: openapi.Response(description="Operation successful,created"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )
    def post(self,request):
        user = request.user 
        user_id = request.query_params.get('user_id')
        if user_id is None:
            return Response({"details" : "user_id not provided"},status=status.HTTP_400_BAD_REQUEST)
        user2 = User.objects.filter(id=user_id).first()
        if user2 is None:
            return Response({"details" : "user not found"},status=status.HTTP_404_NOT_FOUND)
        if user.type.lower() != 'student' and user.type.lower() != 'company' or user2.type.lower() == user.type.lower() :
            return Response({"details" : "cant chat with this user , must be student-company only"},status=status.HTTP_403_FORBIDDEN)
        
        student_id = user.id if user.type.lower()=="student" else user2.id
        company_id = user.id if user.type.lower()=="company" else user2.id
        room_name=f"room_{student_id}_{company_id}"

        chat = Chat.objects.filter(room_name=room_name).first()
        if chat is not None:
            ser = ChatSerializer(chat,many=False,context = {"user_id" : user.id})
            return Response({f"details" : f"chat already exist at [{room_name}] ","chat": ser.data},status=status.HTTP_201_CREATED)
        else:
            ser = ChatSerializer(data={
                "student_id" :student_id ,
                "company_id" :company_id ,

            },many=False)
            if not ser.is_valid():
                return Response({f"details" : "invalide data ","errors": ser.errors},status=status.HTTP_400_BAD_REQUEST)
            ser.save()
            return Response({"details" : f"chat created at [{room_name}] ","chat": ser.data},status=status.HTTP_201_CREATED)
        
class Messages(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="get all messages of a chat , the chat must be yours and already created,pagination with 'page''limit'" ,
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING),
            openapi.Parameter('room_name', openapi.IN_QUERY, description="room_name of the chat u want its messages ", type=openapi.TYPE_STRING)
        ],
        
        responses={
            200: openapi.Response(description="Operation successful"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )
    def get(self,request):
        user = request.user
        room_name = request.query_params.get('room_name')      
        if room_name is None:
            return Response({"details" : "room_name not provided"},status=status.HTTP_400_BAD_REQUEST)
        chat = Chat.objects.filter(room_name=room_name).first()
        if chat is None:
            return Response({"details" : "chat not found"},status=status.HTTP_404_NOT_FOUND)
        if chat.student.id != user.id and chat.company.id != user.id:
            return Response({"details" : "you cant access this chat"},status=status.HTTP_403_FORBIDDEN)
        messages = chat.messages.order_by('-sent_time')
        paginator = CustomPagination()
        paginated_qs = paginator.paginate_queryset(messages.all(),request)
        ser = MessageSerializer(paginated_qs,many=True)
        return paginator.get_paginated_response({"details" : "successful","messages":ser.data })
    
    @swagger_auto_schema(
        operation_description="set all messages to seen for a chat" ,
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="JWT token", type=openapi.TYPE_STRING),
            openapi.Parameter('room_name', openapi.IN_QUERY, description="room_name of the chat u want to set it to seen ", type=openapi.TYPE_STRING)
        ],
        
        responses={
            200: openapi.Response(description="Operation successful"),
            400: 'Invalid data provided',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not found'
        }
    )
    def put(self,request):
        user = request.user
        room_name = request.query_params.get('room_name')      
        if room_name is None:
            return Response({"details" : "room_name not provided"},status=status.HTTP_400_BAD_REQUEST)
        chat = Chat.objects.filter(room_name=room_name).first()
        if chat is None:
            return Response({"details" : "chat not found"},status=status.HTTP_404_NOT_FOUND)
        if chat.student.id != user.id and chat.company.id != user.id:
            return Response({"details" : "you can't access this chat"},status=status.HTTP_403_FORBIDDEN)
        messages = chat.messages.all()
        received_messages = messages.filter(receiver=user.id,seen = False).all()
        count = 0
        if received_messages.exists():
            for message in received_messages:
                message.seen = True 
                message.save()
                count += 1
        return Response({"details" : "updated" , "count" : count},status=status.HTTP_200_OK)        
                
        
class WebSocketChatDocs(APIView):
    @swagger_auto_schema(
        operation_description="""
        ### WebSocket Chat API

        **URL Format:**  
        `ws://<your-domain>/ws/chat/<room_name>/?token=<JWT>`

        - `room_name` must be in format: `room_<student_id>_<company_id>`
        - JWT token must be valid and passed as a query parameter `token`.

        **Events:**

        1. **chat_message**
        - Sent by client:
        ```json
        {
          "type": "chat_message",
          "message": "Hello!"
        }
        ```
        - Received from server:
        ```json
        {
          "type": "chat_message",
          "data": {
            "id": 1,
            "message": "Hello!",
            "sender_name": "Alice",
            "sender": 2,
            "sent_time": "2025-05-22T14:34:00Z"
          }
        }
        ```

        2. **read_message**
        - Sent by client:
        ```json
        {
          "type": "read_message",
          "id": 1
        }
        ```
        - Received from server:
        ```json
        {
          "type": "read_message",
          "data": {
            "id": 1,
            "reader_name": "Bob",
            "reader_id": 3,
            "read_time": "2025-05-22T14:35:00Z"
          }
        }
        ```

        **Disconnect Reasons:**
        - Invalid or expired token
        - Invalid room format
        - Unauthorized user

        """,
        responses={200: openapi.Response("WebSocket Chat API Documentation"),
                   500: openapi.Response("Error trying to connect")}
    )
    def get(self, request):
        return Response({
            "info": "This is a fake endpoint used to document the WebSocket API for Swagger UI."
        })        