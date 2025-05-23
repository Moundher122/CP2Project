from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, company,  Student,MCF,Notfications
from . import tasks
#from post.serializer import opportunity_serializer

class Fcmserlaizer(serializers.ModelSerializer):
  class Meta:
    model=MCF
    fields=['token']
class notficationserlaizer(serializers.ModelSerializer):
  class Meta:
     model=Notfications
     fields='__all__'
class CompanySerializer(serializers.ModelSerializer):
  class Meta:
    model = company
    fields = ['category']
class EducationSerializer(serializers.Serializer):
    degree = serializers.CharField()
    institution = serializers.CharField()
    start = serializers.CharField()
    end = serializers.CharField()

class atachementser(serializers.Serializer):
   size=serializers.CharField()
   name=serializers.CharField()
   link=serializers.URLField()
   created_at=serializers.DateTimeField()
class experienceSerializer(serializers.Serializer):
    title = serializers.CharField()
    company = serializers.CharField()
    start = serializers.CharField()
    end = serializers.CharField()
class StudentSerializer(serializers.ModelSerializer):
  skills =serializers.ListField(
     child=serializers.JSONField(),
     required=False,
  )
  cv=serializers.JSONField(required=False)
  education = EducationSerializer(many=True, required=False)
  experience=serializers.ListField(
      child=experienceSerializer(),
      required=False
  )
  class Meta:
    model = Student
    fields = ['education','gendre','description','skills','rating','category','cv','experience']
  def to_representation(self, instance):
    if  isinstance(instance.skills[0],list) :
     instance.skills = instance.skills[0]
    representation = super().to_representation(instance)
    return representation
  def create(self, validated_data):
        student = Student.objects.create(**validated_data)
        return student
  def update(self, instance, validated_data):
        education=validated_data.pop('education',None)
        cv =validated_data.pop('cv',None)
        if education :
            instance.education=education
        if cv:
            instance.cv=cv
            
        instance.save()
        return super().update(instance, validated_data)



class UserCompanySerializer(serializers.ModelSerializer):
  company = CompanySerializer(required=False)
  password=serializers.CharField(write_only=1)
  type=serializers.CharField(read_only=True)
  location=serializers.CharField(required=False)
  pic=serializers.ImageField(required=False)
  class Meta:
    model = User
    fields = ['id','name', 'email', 'number', 'company','type','pic','profilepic','links','date_joined','password','location']
  def create(self, validated_data):
        company_data = validated_data.pop('company', None)  
        validated_data['password'] = make_password(validated_data['password'])
        if 'pic' in validated_data:
            validated_data['profilepic']= tasks.upload_to_supabase(validated_data.pop('pic'),validated_data['name'])
        user = User.objects.create(**validated_data)
        if company_data:
            ompany = company.objects.create(**company_data)
            user.company = ompany  
            user.save()
        ser=CompanySerializer(data={'skill_input':[]})
        if ser.is_valid():
            ser.save()
        user.company=ser.instance
        user.save()
        return user
  def update(self, instance, validated_data):
        company_data = validated_data.pop('company', {})
        if 'pic' in validated_data:
            validated_data['profilepic']= tasks.upload_to_supabase(validated_data.pop('pic'),instance.name)
        instance = super().update(instance, validated_data)
        if company_data is not None:
            company_instance = instance.company
            if company_instance:
                company_serializer = CompanySerializer(
                    instance=company_instance,
                    data=company_data,
                    partial=self.partial 
                )
                company_serializer.is_valid(raise_exception=True)
                companyvar = company_serializer.save()
            else :
               companyvar= company.objects.create()
               instance.type='Company'
            instance.company = companyvar
            instance.save()
        return instance
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    
    # Check if 'company' exists in the representation
    if 'company' in representation:
        company_representation = representation.pop('company')

        
        # If company_representation is a dictionary, merge it
        if isinstance(company_representation, dict):
            representation.update(company_representation)
        else:
            # If it's not a dictionary, just append it or handle it differently
            representation['company'] = company_representation
    
    return representation
  
  
studentlist=['gendre','description','category','skills','experience']
class UserStudentSerializer(serializers.ModelSerializer):
  gendre=serializers.CharField(required=False,write_only=True)
  education = serializers.ListField(   
      child=serializers.ListField(
         child=serializers.JSONField(),
      ),
      required=False,
  )
  description=serializers.CharField(required=False,write_only=True)
  category=serializers.CharField(required=False,write_only=True)
  experience=serializers.ListField(
      child=serializers.CharField(),
      required=False,
      write_only=1
  )
  skills =serializers.ListField(
     child=serializers.JSONField(),
     required=False,
     write_only=True
  )
  student = StudentSerializer(required=False)
  password=serializers.CharField(write_only=1)
  type=serializers.CharField()
  pic=serializers.ImageField(required=False)
  cv_input=serializers.FileField(required=False)
  location=serializers.CharField(required=False)
  #savedposts = opportunity_serializer(required = False)
  def create(self,validated_data):
        Student_data = {}
        if 'student' in validated_data:
         Student_data = validated_data.pop('student', None)  
        validated_data['password'] = make_password(validated_data['password'])
        if 'pic' in validated_data:
         validated_data['profilepic']= tasks.upload_to_supabase(validated_data.pop('pic'),validated_data['name'])
        user = User.objects.create(**validated_data)
        if not Student_data :
            student = Student.objects.create(**Student_data)
            user.student = student  
            user.save()
        return user
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    student = representation.pop('student', None)  # default to None
    if student:
        representation.update(student)  # Merge only if it exists
    return representation
  def update(self, instance, validated_data):
        Student_data = validated_data.pop('student', {})
        print('validated_data',validated_data)
        if 'pic' in validated_data:
            validated_data['profilepic']= tasks.upload_to_supabase(validated_data.pop('pic'),instance.name)
        if 'cv_input' in validated_data:
            Student_data['cv']= tasks.upload_to_supabase_pdf(validated_data.pop('cv_input'),instance.name)
        if 'education' in validated_data:
            Student_data['education']=validated_data.pop('education',[])[0]
        for item in studentlist:
         if item in validated_data:
           Student_data[item]=validated_data.pop(item,None)
        instance = super().update(instance, validated_data)
        if Student_data is not None:
            Student_instance = instance.student
            if Student_instance:
                Student_serializer = StudentSerializer(
                    instance=Student_instance,
                    data=Student_data,
                    partial=self.partial)
                Student_serializer.is_valid(raise_exception=True)
                student = Student_serializer.save()
            else :
               student=Student.objects.create()
               instance.type='Student'
            instance.student = student
            instance.save()
        return instance
  class Meta:
    model = User
    fields = ['id','name', 'email', 'number', 'student','type','profilepic','pic','cv_input','links','date_joined','password','location','education']+studentlist
