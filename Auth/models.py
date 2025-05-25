from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin
types=[
    ('Student','Student'),
    ('Company','Company'),
    ('Admin','Admin')
]
CATEGORY_CHOICES = [
        ('EC', 'Economics'),
        ('CS', 'Computer Science & IT'),
        ('EN', 'Engineering'),
        ('HL', 'Healthcare'),
        ('BM', 'Business & Management'),
        ('LW', 'Law'),
        ('ED', 'Education'),
        ('AH', 'Arts & Humanities'),
    ]
Gendre=[
    ('M','Men'),
    ('F','Female'),
    ('P','Prefer not to say')
]
class company(models.Model):
    category=models.CharField( max_length=50,choices=CATEGORY_CHOICES,null=True)
    REQUIRED_FIELDS = ['category']

class MCF(models.Model):
    user=models.ForeignKey("Auth.User", verbose_name=(""), on_delete=models.CASCADE,null=1)
    token=models.CharField(max_length=500)
    def __str__(self):
        return self.token
    

class Student(models.Model):
    cv=models.JSONField(null=1,blank=1)
    description = models.TextField(max_length=1000,null=True)
    education=models.JSONField(default=list)
    gendre=models.CharField(choices=Gendre, max_length=50,default='P')
    category=models.CharField( max_length=50,choices=CATEGORY_CHOICES,null=True,blank=True)
    skills=models.JSONField(default=list,null=True)
    experience=models.JSONField(default=list)
    rating=models.IntegerField(default=5)
    experience=models.JSONField(default=list)
    savedposts=models.ManyToManyField('post.Opportunity', verbose_name=("opportunity"),related_name='saved_by')
    REQUIRED_FIELDS = ['education']


class MyAccountManager(BaseUserManager):
    def create_user(self,email,name,type,password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not name:
            raise ValueError("Users must have a username")
        if not type:
            raise ValueError("User must defined the type")
        user = self.model(
            email = self.normalize_email(email),
            name = name,
            type=type
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self,email,name,password):
        user = self.create_user(
            email = self.normalize_email(email),
            password = password,
            name = name,
            type='Admin'
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser,PermissionsMixin):
    location=models.CharField(max_length=50,null=True)
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    number=models.CharField(null=True)
    links = models.JSONField(null=True, blank=True)
    company=models.OneToOneField("company", verbose_name=("company"),null=True,on_delete=models.SET_NULL,related_name="user")
    student=models.OneToOneField("Student", verbose_name=("Students"), null=True,on_delete=models.SET_NULL,related_name="user")
    profilepic=models.JSONField(null=1,blank=1)
    type=models.CharField( choices=types,max_length=50,null=True)
    date_joined = models.DateField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    class Meta:
        permissions=[
            ('company','company'),
            ('student','student'),
        ]
    objects = MyAccountManager()
    USERNAME_FIELD = 'name'
    REQUIRED_FIELDS = ['email']
    def __str__(self):      
        return self.name
    def has_perm(self, perm, obj=None):
     if perm == "Auth.company" and self.type == "Company":
        return True
     if perm == "Auth.student" and self.type == "Student":
        return True
     return self.is_superuser or super().has_perm(perm, obj)

notfication_type=[
    ('message','message'),
    ('invitation','invitation'),
    ('other','other')
]
class Notfications(models.Model):
    user=models.ForeignKey("Auth.User", verbose_name=("user"), on_delete=models.CASCADE)
    description=models.TextField()
    time=models.TimeField(auto_now_add=True)
    isseen=models.BooleanField(default=False)
    type=models.CharField(choices=notfication_type,null=True)

