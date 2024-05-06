from django.dispatch import receiver
from ehrapp.signals import doctor_details_edited
from ehrapp.models import Notification, Doctor
import models
@receiver(doctor_details_edited)
def notify_patient_on_doctor_edit(sender, instance, **kwargs):
    # Extract necessary information from the instance and perform notification logic
    docter = models.Doctor.objects.get(user_id=sender)
    notification = Notification.objects.create(
        doctorId=sender,
        patientId=instance,
        msg=f'{docter.user.first_name} {docter.user.last_name} edit your information'
        )
    notification.save()
    # Implement your notification logic here, such as sending an email or a notification to the patient
