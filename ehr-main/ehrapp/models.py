from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone




departments=[('Endocrinologist','Endocrinologist'),
             ('Cardiologist','Cardiologist'),
            
]
class Doctor(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/DoctorProfilePic/',null=True,blank=True)
    department= models.CharField(max_length=50,choices=departments,default='Endocrinologist')
    status=models.BooleanField(default=False)
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return "{} ({})".format(self.user.first_name,self.department)



class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pic/PatientProfilePic/', null=True, blank=True)
    address = models.TextField(blank=True, default='')
    treatment_type = models.TextField(blank=True, default='')
    assignedDoctorId = models.TextField(blank=True, default='')
    admitDate = models.TextField(blank=True, default='')
    status = models.TextField(blank=True, default='True')
    notes = models.TextField(blank=True, default='')
    cholesterol_level = models.TextField(blank=True, default='0')
    weight_lb = models.TextField(blank=True, default='0')
    bp_1s = models.TextField(blank=True, default='0')
    decryption  = models.TextField(blank=True, default='',null=True)
    # New Updated Fields
    last_updated = models.TextField(blank=True, default='')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_patients')


    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return self.user.first_name+" ("+self.treatment_type+")"


class Appointment(models.Model):
    patientId=models.PositiveIntegerField(null=True)
    doctorId=models.PositiveIntegerField(null=True)
    patientName=models.CharField(max_length=40,null=True)
    doctorName=models.CharField(max_length=40,null=True)
    appointmentDate=models.DateField(auto_now=True)
    description=models.TextField(max_length=500)
    status=models.BooleanField(default=False)


class Notification(models.Model):
    doctorId=models.PositiveIntegerField(null=True,blank=True)
    patientId=models.PositiveIntegerField(null=True,blank=True)
    msg = models.CharField(max_length=40,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
