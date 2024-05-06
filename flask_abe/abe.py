from flask import Flask, request, jsonify
from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.schemes.abenc.abenc_yct14 import EKPabe
from charm.core.engine.util import objectToBytes, bytesToObject
import logging
import base64
import json
import os
import ast

os.environ['PYTHONUTF8'] = '1'

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
app = Flask(__name__)


group = PairingGroup('MNT224')
kpabe = EKPabe(group)

with open('data.json', 'r') as file:
    existing_data = json.load(file)

@app.route("/check")
def hello():
    try:
        print('test api')
        group = PairingGroup('MNT224')
        kpabe = EKPabe(group)
        attributes = [ 'ONE1', 'two', 'THREE']
        (master_public_key, master_key) = kpabe.setup(attributes)
        policy = '(ONE1 or THREE) and (THREE or two)'
        secret_key = kpabe.keygen(master_public_key, master_key, policy)
        print(policy,attributes)
        print('secrat type',type(secret_key))
        msg = "Some Random Message"
        cipher_text = kpabe.encrypt(master_public_key, msg.encode("utf-8"), attributes)
        print('cipher type',type(cipher_text))
        decrypted_msg = kpabe.decrypt(cipher_text, secret_key)
        if(msg==decrypted_msg):
            print('msg is same',decrypted_msg)
        else:
            print('not same msg')

        return jsonify({'decrypty':str(decrypted_msg)})
    except Exception as error:
        print('error is:',error)

@app.route("/encryption", methods=['POST'])
def encryption():
    try:
        global existing_data
        patient_encrypted = {}
        input_json = request.get_json(force=True)
        p_dict = input_json['patient']
        p_dict['user'] = str(p_dict['user'])
        p_dict['status'] = str(p_dict['status'])
        patient_attributes = [input_json['doctor']['username'].upper(),input_json['patient']['treatment_type'].upper(),input_json['doctor']['department'].upper()]
        policy = '('+input_json['doctor']['username'].upper()+' or '+input_json['doctor']['department'].upper()+') and ('+input_json['doctor']['department'].upper()+' or '+input_json['patient']['treatment_type'].upper()+')'
        print('check policy and attributes')
        print('making master keys.....',policy,patient_attributes)
        (master_public_key, master_key) = kpabe.setup(patient_attributes)
        print('master key done and secret key making')
        secret_key = kpabe.keygen(master_public_key, master_key, policy)
        print('sectar key generated',type(secret_key))
        for key,value in p_dict.items():
            print('check value',key,value,type(value))
            if value:
                cipher_text = kpabe.encrypt(master_public_key, value.encode("utf-8"), patient_attributes)
                patient_encrypted[key] = str(objectToBytes(cipher_text,group))
        patient_encrypted['secret_key'] = str(objectToBytes(secret_key,group))
        existing_data[str(p_dict['user'])] = patient_encrypted['secret_key']
        with open('data.json', 'w') as file:
            json.dump(existing_data, file, indent=4)
        return jsonify(patient_encrypted)
    except Exception as error:
        logger.error(error)


@app.route("/decryption", methods=['POST'])
def decryption():
    # try:
    global group,kpabe
    all_obj = []
    input_json = request.get_json(force=True)
    patients = input_json['patient']
    for patient in patients:
        decrypted_obj = {}
        print(patient['user_id'])
        secrat_key = bytesToObject(ast.literal_eval(patient['decryption']),group)
        print('secrat type',type(secrat_key))
        print('check type of address',type(ast.literal_eval(patient['address'])))
        address_encrypted = bytesToObject(ast.literal_eval(patient['address']),group)
        check_address = kpabe.decrypt(address_encrypted, secrat_key)
        print('check address',check_address.decode('utf-8'))

        admitDate_encrypted = bytesToObject(ast.literal_eval(patient['admitDate']),group)
        check_admitDate = kpabe.decrypt(admitDate_encrypted, secrat_key)
        print('check address',check_admitDate.decode('utf-8'))

        status_encrypted = bytesToObject(ast.literal_eval(patient['status']),group)
        check_status = kpabe.decrypt(status_encrypted, secrat_key)
        print('check address',check_status.decode('utf-8'))

        treatment_type_encrypted = bytesToObject(ast.literal_eval(patient['treatment_type']),group)
        treatment_type_status = kpabe.decrypt(treatment_type_encrypted, secrat_key)
        print('check treatment_type',treatment_type_status.decode('utf-8'))

        bp_1s_encrypted = bytesToObject(ast.literal_eval(patient['bp_1s']),group)
        bp_1s_status = kpabe.decrypt(bp_1s_encrypted, secrat_key)
        print('check bp_1s',bp_1s_status.decode('utf-8'))
        
        cholesterol_level_encrypted = bytesToObject(ast.literal_eval(patient['cholesterol_level']),group)
        cholesterol_level_status = kpabe.decrypt(cholesterol_level_encrypted, secrat_key)
        print('check cholesterol_level',cholesterol_level_status.decode('utf-8'))

        notes_encrypted = bytesToObject(ast.literal_eval(patient['notes']),group)
        notes_status = kpabe.decrypt(notes_encrypted, secrat_key)
        print('check notes',notes_status.decode('utf-8'))

        weight_lb_encrypted = bytesToObject(ast.literal_eval(patient['weight_lb']),group)
        weight_lb_status = kpabe.decrypt(weight_lb_encrypted, secrat_key)
        print('check weight_lb',weight_lb_status.decode('utf-8'))

        decrypted_obj={
            'user_id': str(patient['user_id']),
            'weight_lb': str(weight_lb_status.decode('utf-8')),
            'notes': str(notes_status.decode('utf-8')),
            'cholesterol_level' : str(cholesterol_level_status.decode('utf-8')),
            'bp_1s' : str(bp_1s_status.decode('utf-8')),
            'treatment_type' : str(treatment_type_status.decode('utf-8')),
            'status' : str(check_status.decode('utf-8')),
            'address' : str(check_address.decode('utf-8')),
        }
        print(decrypted_obj)
        logger.info('decrypted object :'+str(decrypted_obj))    
        all_obj.append(decrypted_obj)
        print(all_obj)
        # logger.info('all decrypted object :'+type(all_obj))
        logger.info('all decrypted object :'+str(all_obj))  
        logger.info('all decrypted josnoify object :'+ json.dumps(all_obj) )

    return json.dumps(all_obj)
    # except Exception as error:
    #     logger.error('decryption error :'+str(error))


if __name__ == "__main__":
    app.run(host='172.29.0.16', port=5010,debug=True, use_reloader=False)
