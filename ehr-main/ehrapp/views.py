from django.shortcuts import render,redirect,reverse, get_object_or_404
from . import forms,models
from .models import Patient, User, Notification
from .forms import PatientForm
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponse, HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime,timedelta,date
from django.conf import settings
from django.db.models import Q
from django.forms.models import model_to_dict
import datetime
from django.utils import timezone
from django.forms import HiddenInput
from django.http import JsonResponse

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import PatientSerializer, UserSerializer
from django.contrib.auth import login, logout
from .edch import *
import codecs
import base64
import requests
import logging
import json
logger = logging.getLogger(__name__)

shared_key = b'\xe0\x0fVp:2]~\xf6\xdd\xbc\x15%}SP\xa7\xfe\xd3lT\x16\xeb\x83\xe1V\xce\xbe>\r\x97\x16'
# -----------------------------------------------------------------------------------------
# API END POINTS 
# -----------------------------------------------------------------------------------------
#login
@api_view(['POST'])
def patient_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    userpublickeypem = request.data.get('userpublickeypem')
    print('username:...................',username)
    user = User.objects.filter(username=username).first()
    if user:
        if user.check_password(password):
            login(request, user)
            userpublickeypem = userpublickeypem.replace('\\n', '\n')
            byte_key = userpublickeypem.encode("utf-8")
            global shared_key
            shared_key = generate_shared_secret_on_server(generate_server_keys_for_server(),byte_key)
            return Response({'message': 'Login successful','shared_key':base64.b64encode(shared_key).decode('utf-8')}, status=status.HTTP_200_OK)
        else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({'error': 'user not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = User.objects.filter(username=username).first()
    if user and user.check_password(password):
        login(request, user)
        return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

#logout
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    logout(request)
    return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


# #Patients Record
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_patients(request):
    patients = Patient.objects.all()
    serializer = PatientSerializer(patients, many=True)
    return Response(serializer.data)

# #Individual Patients
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_patient_data(request):
    try:
        encrypted_msg = request.data.get('encrypted_msg')
        encrypted_msg, _ = codecs.escape_decode(encrypted_msg, 'hex')
        patient_id = decrypt_message_on_server(shared_key, encrypted_msg)
        patient = Patient.objects.get(id=int(patient_id))
        serializered_data = PatientSerializer(patient).data
        encrypted_msg = encrypt_message_on_server(shared_key, str(serializered_data))
        return Response(base64.b64encode(encrypted_msg).decode('utf-8'), status=status.HTTP_200_OK)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
def flask_api(request):
    try:
        print('check flask api...........')
        responce = requests.get('http://172.29.0.16:5002/check',json={'question':'what is the answer?'})
        print('responce in django')
        return Response(responce.text, status=status.HTTP_200_OK)
    except Exception as err:
        print(err)
        return Response({'error': 'error from flask'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# -----------------------------------------------------------------------------------------


# Create your views here.
def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/index.html')

#----------------------------LOGIN VIEWS------------------------------------------------

#signup/login page for admin
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/adminclick.html')


#signup/login page for doctor
def doctorclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/doctorclick.html')


#signup/login page for patient
def patientclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/patientclick.html')


#----------------------------SIGNUP VIEWS------------------------------------------------

def admin_signup_view(request):
    form=forms.AdminSigupForm()
    if request.method=='POST':
        form=forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.set_password(user.password)
            user.save()
            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)
            return HttpResponseRedirect('adminlogin')
    return render(request,'hospital/adminsignup.html',{'form':form})




def doctor_signup_view(request):
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST)
        doctorForm=forms.DoctorForm(request.POST,request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            doctor=doctorForm.save(commit=False)
            doctor.user=user
            doctor=doctor.save()
            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)
        return HttpResponseRedirect('doctorlogin')
    return render(request,'hospital/doctorsignup.html',context=mydict)


def patient_signup_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST)
        patientForm=forms.PatientForm(request.POST,request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.user=user
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient=patient.save()
            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)
        return HttpResponseRedirect('patientlogin')
    return render(request,'hospital/patientsignup.html',context=mydict)






#checking user is doctor, patient or admin
def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()
def is_doctor(user):
    return user.groups.filter(name='DOCTOR').exists()
def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()


#---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,DOCTOR OR PATIENT
def afterlogin_view(request):
    if is_admin(request.user):
        return redirect('admin-dashboard')
    elif is_doctor(request.user):
        accountapproval=models.Doctor.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('doctor-dashboard')
        else:
            return render(request,'hospital/doctor_wait_for_approval.html')
    elif is_patient(request.user):
        accountapproval=models.Patient.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('patient-dashboard')
        else:
            return render(request,'hospital/patient_wait_for_approval.html')
    return HttpResponse("Invalid user type. Contact your administrator.")

@api_view(['GET'])
def afterlogin_view_encryption(request):
    print('check user', request.user)
    # try:
    accountapproval = models.Doctor.objects.get(user_id=87)
    if accountapproval:
        patient = models.Patient.objects.filter(assignedDoctorId=accountapproval.user_id)
        decrypt_patient = PatientSerializer(patient, many=True).data
        doctor = {
            'user_id': accountapproval.user.id,
            'username': accountapproval.user.username,
            'department': accountapproval.department,
        }
        print('check key in django', type(patient), type(decrypt_patient))
        response = requests.post('http://172.29.0.16:5010/decryption', json={'patient': decrypt_patient, 'doctor': doctor})
        if response.status_code == 200:
            logger.info(response)
            logger.info(dir(response))
            patient_decrypted = response.json()
            logger.info('patient decrypted: ' + str(patient_decrypted))
            return HttpResponse(patient_decrypted, status=status.HTTP_200_OK)
        else:
            return HttpResponse("flask have responce ", status=status.HTTP_404_NOT_FOUND)
    else:
        return HttpResponse("doctor data not found", status=status.HTTP_404_NOT_FOUND)
    # except Exception as error:
    #     return HttpResponse(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def update_patient(request):
    doctorId = request.data.get('doctorId')
    cholesterol_level = request.data.get('cholesterol_level')
    treatment_type = request.data.get('treatment_type')
    weight_lb = request.data.get('weight_lb')
    address = request.data.get('address')
    notes = request.data.get('notes')
    status = request.data.get('status')
    bp_1s = request.data.get('bp_1s')
    patient_id = request.data.get('patient_id')
    current_time = datetime.datetime.now()
    docter = models.Doctor.objects.get(user_id=doctorId)

    patient_to_encrypt = {
                'user' : patient_id,
                'address' : address,
                'treatment_type' : treatment_type,
                'admitDate' : current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'status' : status,
                'notes' : notes,
                'cholesterol_level' : cholesterol_level,
                'weight_lb' : weight_lb,
                'bp_1s' : bp_1s,
                'last_updated':current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
    docter_to_encrypt = {
                'username': docter.user.username,
                'department':docter.department
            }
    responce = requests.post('http://172.29.0.16:5010/encryption',json={'patient':patient_to_encrypt,'doctor':docter_to_encrypt})
    if responce.status_code ==200:
        patient_encrypted = responce.json()
        patient = Patient.objects.get(user_id=patient_id)
        patient.address = patient_encrypted['address']
        patient.treatment_type = patient_encrypted['treatment_type']
        patient.admitDate = patient_encrypted['admitDate']
        patient.status = patient_encrypted['status']
        patient.notes = patient_encrypted['notes']
        patient.cholesterol_level = patient_encrypted['cholesterol_level']
        patient.weight_lb = patient_encrypted['weight_lb']
        patient.bp_1s = patient_encrypted['bp_1s']
        patient.decryption = patient_encrypted['secret_key']
        patient.last_updated = patient_encrypted['last_updated']
        patient.save()
        notification = Notification.objects.create(
            doctorId=doctorId,
            patientId=patient_id,
            msg=f'{docter.user.first_name} {docter.user.last_name} edit your information'
            )
        notification.save()
        patient_data = PatientSerializer(patient).data
        decrypt_reaponce = requests.post('http://172.29.0.16:5010/decryption', json={'patient': [patient_data]})
        if decrypt_reaponce.status_code == 200:
            return HttpResponse(decrypt_reaponce)
        else:
            return HttpResponse('decryption failed')
    return HttpResponse('encryption failed')

@api_view(['GET'])
def get_notification(request):
    patient_id = request.data.get('patient_id')
    latest_notification = Notification.objects.filter(patientId=patient_id).order_by('-created_at').first()
    if latest_notification:
        notification_dict = {
            'id': latest_notification.id,
            'doctorId': latest_notification.doctorId,
            'patientId': latest_notification.patientId,
            'msg': latest_notification.msg,
            'created_at': latest_notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        Notification.objects.filter(patientId=patient_id).order_by('-created_at').first().delete()
        return JsonResponse(notification_dict)
    else:
        return JsonResponse({'notifucation':'empty'})


#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    #for both table in admin dashboard
    doctors=models.Doctor.objects.all().order_by('-id')
    patients=models.Patient.objects.all().order_by('-id')
    #for three cards
    doctorcount=models.Doctor.objects.all().filter(status=True).count()
    pendingdoctorcount=models.Doctor.objects.all().filter(status=False).count()

    patientcount=models.Patient.objects.all().filter(status=True).count()
    pendingpatientcount=models.Patient.objects.all().filter(status=False).count()

    appointmentcount=models.Appointment.objects.all().filter(status=True).count()
    pendingappointmentcount=models.Appointment.objects.all().filter(status=False).count()
    mydict={
    'doctors':doctors,
    'patients':patients,
    'doctorcount':doctorcount,
    'pendingdoctorcount':pendingdoctorcount,
    'patientcount':patientcount,
    'pendingpatientcount':pendingpatientcount,
    'appointmentcount':appointmentcount,
    'pendingappointmentcount':pendingappointmentcount,
    }
    return render(request,'hospital/admin_dashboard.html',context=mydict)


# this view for sidebar nav on admin page
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_doctor_view(request):
    return render(request,'hospital/admin_doctor.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_doctor_from_hospital_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    return redirect('admin-view-doctor')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)

    userForm=forms.DoctorUserForm(instance=user)
    doctorForm=forms.DoctorForm(request.FILES,instance=doctor)
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST,instance=user)
        doctorForm=forms.DoctorForm(request.POST,request.FILES,instance=doctor)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            doctor=doctorForm.save(commit=False)
            doctor.status=True
            doctor.save()
            return redirect('admin-view-doctor')
    return render(request,'hospital/admin_update_doctor.html',context=mydict)




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_doctor_view(request):
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST)
        doctorForm=forms.DoctorForm(request.POST, request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            doctor=doctorForm.save(commit=False)
            doctor.user=user
            doctor.status=True
            doctor.save()

            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)

        return HttpResponseRedirect('admin-view-doctor')
    return render(request,'hospital/admin_add_doctor.html',context=mydict)




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_doctor_view(request):
    #those whose approval are needed
    doctors=models.Doctor.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_doctor.html',{'doctors':doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    doctor.status=True
    doctor.save()
    return redirect(reverse('admin-approve-doctor'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    return redirect('admin-approve-doctor')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_specialisation_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor_specialisation.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_view(request):
    return render(request,'hospital/admin_patient.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_patient_from_hospital_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-view-patient')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)

    userForm=forms.PatientUserForm(instance=user)
    patientForm=forms.PatientForm(request.FILES,instance=patient)
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST,instance=user)
        patientForm=forms.PatientForm(request.POST,request.FILES,instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.status=True
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient.save()
            return redirect('admin-view-patient')
    return render(request,'hospital/admin_update_patient.html',context=mydict)





@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_patient_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST)
        patientForm=forms.PatientForm(request.POST,request.FILES)
        print(userForm.errors)
        print(patientForm.errors)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            patient=patientForm.save(commit=False)
            patient.user=user
            patient.status=True
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            # patient.save()
            docter = models.Doctor.objects.get(user_id=request.POST.get('assignedDoctorId'))
            current_time = datetime.datetime.now()
            patient_to_encrypt = {
                'user' : patient.user.id,
                'address' : patient.address,
                'treatment_type' : patient.treatment_type,
                'admitDate' : current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'status' : patient.status,
                'notes' : patient.notes,
                'cholesterol_level' : patient.cholesterol_level,
                'weight_lb' : patient.weight_lb,
                'bp_1s' : patient.bp_1s,
                'last_updated':current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            docter_to_encrypt = {
                'username': docter.user.username,
                'department':docter.department
            }
            try:
                responce = requests.post('http://172.29.0.16:5005/encryption',json={'patient':patient_to_encrypt,'doctor':docter_to_encrypt})
                if responce.status_code == 200:
                    patient_encrypted = responce.json()
                    logger.info(patient_encrypted)
                    patient.user = patient.user
                    patient.address = patient_encrypted['address']
                    patient.treatment_type = patient_encrypted['treatment_type']
                    patient.assignedDoctorId = patient.assignedDoctorId
                    patient.admitDate = patient_encrypted['admitDate']
                    patient.status = patient_encrypted['status']
                    patient.notes = patient_encrypted['notes']
                    patient.cholesterol_level = patient_encrypted['cholesterol_level']
                    patient.weight_lb = patient_encrypted['weight_lb']
                    patient.bp_1s = patient_encrypted['bp_1s']
                    patient.decryption = patient_encrypted['secret_key']
                    patient.last_updated = patient_encrypted['last_updated']
                    patient.save()
            except json.JSONDecodeError as e:
                print("Error decoding JSON:", e)
                logger.info(e)
            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)
        else:
            user_errors = None
            patient_errors = None
            if not userForm.is_valid():
                user_errors = userForm.errors

            if not patientForm.is_valid():
                patient_errors = patientForm.errors
            for field_name, error_list in user_errors.items():
                logger.error(f"Errors for user form {field_name}: {', '.join(error_list)}")

            # for field_name, error_list in patient_errors.items():
                # logger.error(f"Errors for patient form {field_name}: {', '.join(error_list)}")
        return HttpResponseRedirect('admin-view-patient')
    return render(request,'hospital/admin_add_patient.html',context=mydict)




#-----------------APPOINTMENT START--------------------------------------------------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_appointment_view(request):
    return render(request,'hospital/admin_appointment.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_appointment_view(request):
    appointments=models.Appointment.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_appointment.html',{'appointments':appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_appointment_view(request):
    appointmentForm=forms.AppointmentForm()
    mydict={'appointmentForm':appointmentForm,}
    if request.method=='POST':
        appointmentForm=forms.AppointmentForm(request.POST)
        if appointmentForm.is_valid():
            appointment=appointmentForm.save(commit=False)
            appointment.doctorId=request.POST.get('doctorId')
            appointment.patientId=request.POST.get('patientId')
            appointment.doctorName=models.User.objects.get(id=request.POST.get('doctorId')).first_name
            appointment.patientName=models.User.objects.get(id=request.POST.get('patientId')).first_name
            appointment.status=True
            appointment.save()
        return HttpResponseRedirect('admin-view-appointment')
    return render(request,'hospital/admin_add_appointment.html',context=mydict)



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_appointment_view(request):
    #those whose approval are needed
    appointments=models.Appointment.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_appointment.html',{'appointments':appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.status=True
    appointment.save()
    return redirect(reverse('admin-approve-appointment'))



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    return redirect('admin-approve-appointment')
#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------






#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_dashboard_view(request):
    #for three cards
    patientcount=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id).count()
    appointmentcount=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id).count()

    #for  table in doctor dashboard
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id).order_by('-id')
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid).order_by('-id')
    appointments=zip(appointments,patients)
    mydict={
    'patientcount':patientcount,
    'appointmentcount':appointmentcount,
    'appointments':appointments,
    'doctor':models.Doctor.objects.get(user_id=request.user.id), #for profile picture of doctor in sidebar
    }
    return render(request,'hospital/doctor_dashboard.html',context=mydict)



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_patient_view(request):
    mydict={
    'doctor':models.Doctor.objects.get(user_id=request.user.id), #for profile picture of doctor in sidebar
    }
    return render(request,'hospital/doctor_patient.html',context=mydict)


#Updated Code


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_update_patient_view(request, pk):
    patient = models.Patient.objects.get(id=pk)
    user = models.User.objects.get(id=patient.user_id)

    if request.method == 'POST':
        userForm = forms.PatientUserForm(request.POST, instance=user)
        patientForm = forms.PatientForm(request.POST, request.FILES, instance=patient)

        # Exclude the password field from form validation and update
        userForm.fields['password'].required = False

        if patientForm.is_valid():
            patient = patientForm.save(commit=False)
            patient.status = True
            patient.assignedDoctorId = request.user.id  # Assign the currently logged-in doctor's ID
            patient.last_updated = timezone.now()  # Set the timestamp of the last update
            patient.updated_by = request.user  # Set the currently logged-in doctor as the updater
            patient.save()
            print('updated')

            return redirect('doctor-view-patient')
        else:
            print('not updated. Form validation failed.')
            print('Patient Form Errors:', patientForm.errors)
    else:
        userForm = forms.PatientUserForm(instance=user)
        patientForm = forms.PatientForm(instance=patient)

        # Hide the password field in the template
        userForm.fields['password'].widget = HiddenInput()
        # Add the assignedDoctorId field as a hidden input with the doctor's ID
        patientForm.fields['assignedDoctorId'].widget = HiddenInput()
        patientForm.fields['assignedDoctorId'].initial = request.user.id

    mydict = {'userForm': userForm, 
              'patientForm': patientForm} 

    return render(request, 'hospital/doctor_update_patient.html', context=mydict)




#Updated Code:
@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_patient_view(request):
    patients = models.Patient.objects.all().filter(status=True, assignedDoctorId=request.user.id)
    doctor = models.Doctor.objects.get(user_id=request.user.id)  # for profile picture of the doctor in sidebar
    return render(request, 'hospital/doctor_view_patient.html', {'patients': patients, 'doctor': doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def search_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    # whatever user write in search box we get in query
    query = request.GET['query']
    patients=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id).filter(Q(treatment_type__icontains=query)|Q(user__first_name__icontains=query))
    return render(request,'hospital/doctor_view_patient.html',{'patients':patients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_appointment.html',{'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_view_appointment.html',{'appointments':appointments,'doctor':doctor})



#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------






#---------------------------------------------------------------------------------
#------------------------ PATIENT RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view(request):
    try:
        patient=models.Patient.objects.get(user_id=request.user.id)
        doctor=models.Doctor.objects.get(user_id=patient.assignedDoctorId)
        mydict={
        'patient':patient,
        'doctorName':doctor.get_name,
        'treatment_type':patient.treatment_type,
        'doctorDepartment':doctor.department,
        'admitDate':patient.admitDate,
        }
        return render(request,'hospital/patient_dashboard.html',context=mydict)
    except Exception as error:
        return Response({'error': error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view_for_flutter(request):
    try:
        encrypted_msg = request.data.get('encrypted_msg')
        encrypted_msg, _ = codecs.escape_decode(encrypted_msg, 'hex')
        patient_id = decrypt_message_on_server(shared_key, encrypted_msg)
        patient=models.Patient.objects.get(user_id=int(patient_id))
        doctor=models.Doctor.objects.get(user_id=patient.assignedDoctorId)
        mydict={
        'patient':patient,
        'doctorName':doctor.get_name,
        'treatment_type':patient.treatment_type,
        'doctorDepartment':doctor.department,
        'admitDate':patient.admitDate,
        }
        encrypted_msg = encrypt_message_on_server(shared_key, str(mydict))
        return Response(base64.b64encode(encrypted_msg).decode('utf-8'), status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'error': error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_appointment.html',{'patient':patient})



def patient_view_doctor_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_view_doctor.html',{'patient':patient,'doctors':doctors})



def search_doctor_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    
    # whatever user write in search box we get in query
    query = request.GET['query']
    doctors=models.Doctor.objects.all().filter(status=True).filter(Q(department__icontains=query)| Q(user__first_name__icontains=query))
    return render(request,'hospital/patient_view_doctor.html',{'patient':patient,'doctors':doctors})




@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    appointments=models.Appointment.objects.all().filter(patientId=request.user.id)
    return render(request,'hospital/patient_view_appointment.html',{'appointments':appointments,'patient':patient})
   

#------------------------ PATIENT RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------