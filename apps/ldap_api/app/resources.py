from flask_restful import Resource, reqparse
from flask_jsonpify import jsonify
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required,
                                get_jwt_identity, set_access_cookies, unset_jwt_cookies,
                                set_refresh_cookies, get_raw_jwt)
from pymemcache.client import base
from .models import UserRole
from app import config, utils
from flask import request, Response
from ldap import modlist
import crypt
import random
import string
import os
import ldap
import json
from .ldif_from_database import LDIFFromSQLServer
from .sigenu_client import SigenuClient

parser = reqparse.RequestParser()
parser.add_argument(
    'username', help='This field cannot be blank', required=True)
parser.add_argument(
    'password', help='This field cannot be blank', required=True)

# Configuraciones según el entorno
configuration = config.set_environment(os.getenv("LDAP_API_ENVIRONMENT"))

ldap_server = ldap.initialize(configuration.LDAP_SERVER_URI,
                trace_level=utils.DEBUG_LEVEL[configuration.PYTHON_LDAP_DEBUG_LVL])

admin_password = os.getenv("LDAP_ADMIN_PASSWORD")

ldap_server.simple_bind_s('cn=admin,dc=uh,dc=cu', admin_password)


def verify_user_password(user_dn, password):
    try:
        ldap_server.simple_bind_s(user_dn, password)
        ldap_server.simple_bind_s('cn=admin,dc=uh,dc=cu', admin_password)
        return True
    except ldap.LDAPError:
        return False

class UserLogin(Resource):
    def post(self):
        data = parser.parse_args()

        filters = "(|(objectclass=Trabajador)(objectclass=Externo)(objectclass=Estudiante))(correo=%s)" % data[
                    'username']

        user_account = ldap_server.search_s(
            "dc=uh,dc=cu", ldap.SCOPE_SUBTREE, "(&%s)" % filters)

        if len(user_account) == 0:
            return {'message': 'Credenciales incorrectas'}, 403

        user_account = user_account[0]
        user_account_json = json.dumps(user_account, cls=utils.MyEncoder)
        user_account = json.loads(user_account_json)

        if verify_user_password(user_account[0], data['password']):
            access_token = create_access_token(identity=data['username'])
            refresh_token = create_refresh_token(identity=data['username'])

            resp = jsonify({'login': True, 'role': 'admin'})
            set_access_cookies(resp, access_token)
            set_refresh_cookies(resp, refresh_token)
            resp.status_code = 200
            return resp
        else:
            return {'message': 'Credenciales incorrectas'}, 403


class UserLogout(Resource):
    def post(self):
        resp = jsonify({'logout': True})
        unset_jwt_cookies(resp)
        resp.status_code = 200
        return resp


class Users(Resource):
    @jwt_required
    def get(self):
        filters = "(|(objectclass=Trabajador)(objectclass=Externo)(objectclass=Estudiante))"
        args = request.args
        filters += __set_filters__(args)

        users_account = ldap_server.search_s(
            "dc=uh,dc=cu", ldap.SCOPE_SUBTREE, "(&%s)" % filters)
        users_account = [
            {
                "name": x[1]['cn'],
                "last_name":x[1]['sn'],
                "ci":x[1].get('CI', '-'),
                "id":x[0],
                "correo": x[1].get('Correo', 'N/D')

            } for x in users_account]
        users_account_json = json.dumps(users_account, cls=utils.MyEncoder)
        users_account = json.loads(users_account_json)

        return {'usuarios': users_account}


class Workers(Resource):
    @jwt_required
    def get(self):
        filters = "(objectclass=Trabajador)"
        args = request.args
        filters += __set_filters__(args)

        workers_account = ldap_server.search_s(
            "ou=Trabajadores,dc=uh,dc=cu", ldap.SCOPE_SUBTREE, "(&%s)" % filters)
        workers_account = [
            {
                "name": x[1]['cn'],
                "last_name":x[1]['sn'],
                "ci":x[1].get('CI', '-'),
                "area":x[1]['Area'],
                "ocupation":x[1]['Cargo'],
                "id":x[0],
                "correo": x[1].get('Correo', 'N/D')
            } for x in workers_account]
        workers_account_json = json.dumps(workers_account, cls=utils.MyEncoder)
        workers_account = json.loads(workers_account_json)

        return {'workers': workers_account}

    def post(self):
        data = request.get_json()
        ci = data.get('ci')
        workers_account = ldap_server.search_s(
            "ou=Trabajadores,dc=uh,dc=cu", ldap.SCOPE_SUBTREE, "(ci=%s)" % ci)
        workers_account_json = json.dumps(workers_account, cls=utils.MyEncoder)
        workers_account = json.loads(workers_account_json)
        if len(workers_account):
            workers_account = workers_account[0]
            email = workers_account[1].get('Correo', None)
            if email and email[0] != "N/D":
                return {'error': 'Este usuario ya existe en directorio', 'email': email[0]}, 403
            else:
                uid = workers_account[1]['uid'][0]
                new_email = __generate_new_email__(uid, "Trabajador", workers_account[1]['Area'][0])

                try:
                    dn = workers_account[0]
                    modList = modlist.modifyModlist({'Correo': [email[0].encode(
                        'utf-8') if email else email]}, {'Correo': [new_email.encode('utf-8')]})

                    ldap_server.modify_s(dn, modList)
                except Exception as e:
                    return {'e': str(e)}

                return {'email': new_email}

        return {'error': 'Este trabajador no existe en el directorio.'}, 404

    @jwt_required
    def patch(self):
        # GET UIDNUMBERCOUNTER
        try:
            client = base.Client((configuration.MEMCACHED_HOST, 11211))
            uidNumberCounter = int(__translate_byte_types__(
                client.get('uidNumberCounter')))
        except Exception as e:
            print(e)
            return {"error": "No se pudo obtener el uidNumber de memcached"}

        try:
            handler = LDIFFromSQLServer("./app/ldif_from_database/config.yml", uidNumberCounter)
            newUidNumber = handler.generate_ldif(number_of_rows=10, restore=True)
            client.set('uidNumberCounter',newUidNumber)
        except Exception as e:
            return {'e': str(e)}

        return {'status': 'terminado satisfactoriamente'}


class Students(Resource):
    @jwt_required
    def get(self):
        filters = "(objectclass=Estudiante)"
        args = request.args
        filters += __set_filters__(args)

        students_account = ldap_server.search_s(
            "ou=Estudiantes,dc=uh,dc=cu", ldap.SCOPE_SUBTREE, "(&%s)" % filters)
        students_account = [
            {
                "name": x[1]['cn'],
                "last_name":x[1]['sn'],
                "ci":x[1].get('CI', '-'),
                "id":x[0],
                "faculty": x[1].get('Facultad', '-'),
                "carrer": x[1].get('Carrera', '-'),
                "grade": x[1].get('Grade ', '-')
            } for x in students_account]
        students_account_json = json.dumps(
            students_account, cls=utils.MyEncoder)
        students_account = json.loads(students_account_json)

        return {'students': students_account}

    def post(self):
        data = request.get_json()
        ci = data.get('ci')
        student_accounts = ldap_server.search_s(
            "ou=Estudiantes,dc=uh,dc=cu", ldap.SCOPE_SUBTREE, "(ci=%s)" % ci)
        student_accounts_json = json.dumps(student_accounts, cls=utils.MyEncoder)
        student_accounts = json.loads(student_accounts_json)
        if len(student_accounts):
            student_accounts = student_accounts[0]
            email = student_accounts[1].get('Correo', None)
            if email and email[0] != "N/D":
                return {'error': 'Este usuario ya existe en directorio', 'email': email[0]}, 403
            else:
                uid = student_accounts[1]['uid'][0]
                new_email = __generate_new_email__(uid, "Estudiantes", student_accounts[1]['IdFacultad'])

                try:
                    dn = student_accounts[0]
                    modList = modlist.modifyModlist({'Correo': [email[0].encode(
                        'utf-8') if email else email]}, {'Correo': [new_email.encode('utf-8')]})

                    ldap_server.modify_s(dn, modList)
                except Exception as e:
                    return {'e': str(e)}

                return {'email': new_email}

        return {'error': 'Este estudiante no existe en el directorio.'}, 404

    @jwt_required
    def patch(self):
        # GET UIDNUMBERCOUNTER
        try:
            client = base.Client((configuration.MEMCACHED_HOST, 11211))
            uidNumberCounter = int(__translate_byte_types__(
                client.get('uidNumberCounter')))
        except Exception as e:
            print(e)
            return {"error": "No se pudo obtener el uidNumber de memcached"}

        try:
            handler = SigenuClient("./app/sigenu_client/config.yml", uidNumberCounter)
            newUidNumber = handler.generate_ldif(number_of_rows=10)
            client.set('uidNumberCounter', newUidNumber)
        except Exception as e:
            return {'e': str(e)}


class Externs(Resource):
    @jwt_required
    def get(self):
        filters = "(objectclass=Externo)"
        args = request.args
        filters += __set_filters__(args)

        externs_account = ldap_server.search_s(
            "ou=Externos,dc=uh,dc=cu", ldap.SCOPE_SUBTREE, "(&%s)" % filters)
        externs_account = [
            {
                "name": x[1]['cn'][0],
                "last_name":x[1]['sn'][0],
                "ci":x[1].get('CI', '-'),
                "id":x[0],
                "email": x[1].get('Correo', 'N/D')

            } for x in externs_account]
        externs_account_json = json.dumps(externs_account, cls=utils.MyEncoder)
        externs_account = json.loads(externs_account_json)

        return {'externs': externs_account}

    @jwt_required
    def post(self):
        data = request.get_json()
        old_login = data.get('old_login')
        can_use_old_login = False

        if old_login:
            extern_account = ldap_server.search_s(
                "ou=Externos,dc=uh,dc=cu", ldap.SCOPE_ONELEVEL, "(&(correo=%s)(objectclass=Externo))" % data.get('old_login_email'))
            if not len(extern_account):
                can_use_old_login = True

        # CREATE ACCOUNT
        # GENERATE NEW EMAIL
        name = data.get('name').split()[0]
        last_name = data.get('last_name')
        first_last_name, second_last_name = last_name.lower().split()
        possible_email = name.lower() + '.' + first_last_name + \
                                    __map_area_to_email_domain__(
                                        data.get('area'), "Externo")

        if can_use_old_login:
            email = data.get('old_login_email')
        else:
            if len(ldap_server.search_s("ou=Externos,dc=uh,dc=cu", ldap.SCOPE_ONELEVEL, "(&(correo=%s)(objectclass=Externo))" % possible_email)):
                possible_email = name.lower() + '.' + second_last_name + \
                                            __map_area_to_email_domain__(
                                                data.get('area'), "Externo")
                if len(ldap_server.search_s("ou=Externos,dc=uh,dc=cu", ldap.SCOPE_ONELEVEL, "(&(correo=%s)(objectclass=Externo))" % possible_email)):
                    for i in range(1, 1000):
                        possible_email = name.lower() + '.' + second_last_name + str(i) + \
                                                    __map_area_to_email_domain__(
                                                        data.get('area'), "Externo")
                        if len(ldap_server.search_s("ou=Externos,dc=uh,dc=cu", ldap.SCOPE_ONELEVEL, "(&(correo=%s)(objectclass=Externo))" % possible_email)):
                            continue
                        email = possible_email
                        break
                else:
                    email = possible_email
            else:
                email = possible_email

        # GET UIDNUMBERCOUNTER
        try:
            client = base.Client((configuration.MEMCACHED_HOST, 11211))
            uidNumberCounter = int(__translate_byte_types__(
                client.get('uidNumberCounter')))
        except Exception as e:
            print(e)
            return {"error": "Can't get uidNumberCounter from memcached"}

        uid = email.split('@')[0].strip()
        dn = 'uid=%s,ou=Externos,dc=uh,dc=cu' % uid
        password = '{CRYPT}' + __sha512_crypt__(data.get('password'), 500000)

        created_at = data.get('created_at').split('-')
        created_at = created_at[0] + created_at[1] + created_at[2]
        expires = data.get('expires').encode('utf-8')
        expires = expires[0] + expires[1] + expires[2]
        modList = modlist.addModlist({
            'CI':                   [data.get('ci').encode('utf-8')],
            'cn':                   [name.encode('utf-8')],
            'sn':                   [last_name.encode('utf-8')],
            'correo':               [email.encode('utf-8')],
            'fechadecreacion':      [str(created_at).encode('utf-8')],
            'fechadebaja':          [str(expires).encode('utf-8')],
            'tienecorreo':          [b'TRUE' if data.get('email') else b'FALSE'],
            'tieneinternet':        [b'TRUE' if data.get('internet') else b'FALSE'],
            'tienechat':            [b'TRUE' if data.get('chat') else b'FALSE'],
            'description':          [data.get('comments').encode('utf-8') if data.get('comments') != "" else b"N/D"],
            'userpassword':         [password.encode('utf-8')],
            'homeDirectory':        [('/home/'+uid+'/').encode('utf-8')],
            'uid':                  uid.encode('utf-8'),
            'uidNumber':            move_first_ceros(str(data.get('ci')).strip()).encode('utf8'),
            'gidNumber':            "10000".encode('utf8'),
            'objectClass':          [b'Externo', b'posixAccount', b'shadowAccount']
        })
        #    'uidNumber':            uidNumberCounter
        ldap_server.add_s(dn, modList)

        result = {'extern_data': 'success'}
        return jsonify(result)

def move_first_ceros(ci):
    while ci[0] == '0':
        ci = ci[1:] + ci[0]
    return ci

class SecurityQuestions(Resource):
    def get(self):
        data = request.args

        users_account = ldap_server.search_s("dc=uh,dc=cu", ldap.SCOPE_SUBTREE,
           "(&(|(objectclass=Trabajador)(objectclass=Externo)(objectclass=Estudiante))(correo=%s))" % data.get("email"))
        if len(users_account):
            users_account = users_account[0]
            users_account_json = json.dumps(users_account, cls=utils.MyEncoder)
            users_account = json.loads(users_account_json)

            questions = users_account[1].get('QuestionSec', None)

            if questions:
                return {'preguntas': questions}
            else:
                return {'error': 'No tiene preguntas de seguridad'}
        else:
            return {'error':'Credenciales incorrectas'}, 403

    def patch(self):
        data = request.get_json()

        users_account = ldap_server.search_s("dc=uh,dc=cu", ldap.SCOPE_SUBTREE,
           "(&(|(objectclass=Trabajador)(objectclass=Externo)(objectclass=Estudiante))(correo=%s))" % data.get("email"))
        if len(users_account):
            users_account = users_account[0]
            users_account_json = json.dumps(users_account, cls=utils.MyEncoder)
            users_account = json.loads(users_account_json)

            if not verify_user_password(users_account[0], data.get("password")):
                return {'error':'Credenciales incorrectas'}, 403

            questions = users_account[1].get('QuestionSec', None)
            answers = users_account[1].get('AnswerSec', None)

            if questions:
                return {'preguntas': questions, 'respuestas': answers}
            else:
                return {'error': 'No tiene preguntas de seguridad'}
        else:
            return {'error':'Credenciales incorrectas'}, 403

    def post(self):
        data = request.get_json()
        users_account = ldap_server.search_s("dc=uh,dc=cu", ldap.SCOPE_SUBTREE,
            "(&(|(objectclass=Trabajador)(objectclass=Externo)(objectclass=Estudiante))(correo=%s))" % data.get("email"))
        if len(users_account):
            users_account = users_account[0]
            users_account_json = json.dumps(users_account, cls=utils.MyEncoder)
            users_account = json.loads(users_account_json)

            answers = users_account[1].get('AnswerSec', None)
            if answers:
                possible_answers = data.get('answers')
                for i in range(len(answers)):
                    if answers[i] != possible_answers[i]:
                        return {'check': 'false'}, 403
                
                new_password = '{CRYPT}' + __sha512_crypt__(data.get('password'), 500000)
                try:
                    old_password = map(lambda s: s.encode('utf-8'), users_account[1].get('userPassword'))
                except Exception:
                    return {'error':str(users_account[1].get('userPassword'))}, 500
                try:
                    dn = users_account[0]
                    modList = modlist.modifyModlist( {'userPassword': old_password}, 
                                                    {'userPassword': [new_password.encode('utf-8')] } )

                    ldap_server.modify_s(dn,modList)
                except Exception as e:
                    return {'error':str(e)}

            else:
                return {'warning': 'No tiene respuestas de seguridad'}
        else:
            return {'error': 'Id de usuario incorrecto'}

    def put(self):
        data = request.get_json()
        users_account = ldap_server.search_s("dc=uh,dc=cu", ldap.SCOPE_SUBTREE,
            "(&(|(objectclass=Trabajador)(objectclass=Externo)(objectclass=Estudiante))(correo=%s))" % data.get("email"))
        if len(users_account):
            users_account = users_account[0]
            users_account_json = json.dumps(users_account, cls=utils.MyEncoder)
            users_account = json.loads(users_account_json)

            if not verify_user_password(users_account[0], data.get("password")):
                return {'error':'Credenciales incorrectas'}, 403

            questions = map(lambda s: s.encode('utf-8'), data.get('questions'))
            answers = map(lambda s: s.encode('utf-8'), data.get('answers'))

            current_questions = users_account[1].get('QuestionSec', [])
            current_answers = users_account[1].get('AnswerSec', [])

            dn = users_account[0]
            modList = modlist.modifyModlist({'QuestionSec': current_questions, 'AnswerSec': current_answers},
                                                {'QuestionSec': questions, 'AnswerSec': answers})

            ldap_server.modify_s(dn, modList)

            return {'success': 'Preguntas y respuestas añadidas'}
        else:
            return {'error':'Credenciales incorrectas'}, 403


class ChangePassword(Resource):
    def post(self):
        users_account = ldap_server.search_s("dc=uh,dc=cu", ldap.SCOPE_SUBTREE,
            "(&(|(objectclass=Trabajador)(objectclass=Externo)(objectclass=Estudiante))(correo=%s))" % request.get_json().get('email'))
        if len(users_account):
            users_account = users_account[0]
            users_account_json = json.dumps(users_account, cls=utils.MyEncoder)
            users_account = json.loads(users_account_json)

            data = request.get_json()
            if not verify_user_password(users_account[0], data.get('oldpassword')):
                return {'error':'Credenciales incorrectas'}, 403

            new_password = '{CRYPT}' + __sha512_crypt__(data.get('password'), 500000)
            old_password = map(lambda s: s.encode('utf-8'), users_account[1].get('userPassword'))

            try:
                dn = users_account[0]
                modList = modlist.modifyModlist( {'userPassword': old_password}, 
                                                {'userPassword': [new_password.encode('utf-8')] } )

                ldap_server.modify_s(dn,modList)
            except Exception as e:
                return {'error':str(e)}

            return {'success': 'Contraseña cambiada exitosamente'}
        else:
            return {'error': 'Credenciales incorrectas'}, 403

class ServiceStudentInternetQuote(Resource):
    def get(self):
        users_account = ldap_server.search_s("dc=uh,dc=cu", ldap.SCOPE_SUBTREE,
            "(&(objectclass=Estudiante)(correo=%s))" % request.get_json().get('email'))
        if len(users_account):
            mbytes = 0
            users_account = users_account[0]
            users_account_json = json.dumps(users_account, cls=utils.MyEncoder)
            users_account = json.loads(users_account_json)

            # agregar algortimo para calculo de cuotas

            return {'cuota': mbytes}
        else:
            return {'error': 'No existe un estudiante registrado con ese correo.'} 

def __map_area_to_email_domain__(area, category):
    if category == "Externo":
        return '@'+area
    
    if category == "Estudiante":
        domain = 'default'
        if area == "223.0.06816_12":
            domain = "ifal.uh.cu"
        if area == "223.0.06816_14":
            domain = "flex.uh.cu",
        if area == "223.0.06816_09":
            domain = "fayl.uh.cu",
        if area == "223.0.06816_03":
            domain = "geo.uh.cu",
        if area == "223.0.06816_02":
            domain = "fisica.uh.cu",
        if area == "223.0.06816_11":
            domain = "fcf.uh.cu",
        if area == "-1d4dd374:1552abd9bee:8f9":
            domain = "fdes.uh.cu"
        if area == "223.0.06816_04":
            domain = "matcom.uh.cu",
        if area == "223.0.06816_16":
            domain = "sangeronimo.ohc.cu"
        if area == "223.0.06816_15":
            domain = "ftur.uh.cu"
        if area == "223.0.06816_10":
            domain = "fec.uh.cu",
        if area == "223.0.06816_13":
            domain = "fbio.uh.cu",
        if area == "223.0.06816_06":
            domain = "ffh.uh.cu",
        if area == "223.0.06816_07":
            domain = "fcom.uh.cu",
        if area == "fenhi.f.001":
            domain = "fenhi.uh.cu",
        if area == "223.0.06816_08":
            domain = "lex.uh.cu",
        if area == "223.0.06816_05":
            domain = "psico.uh.cu",
        if area == "223.0.06816_01":
            domain = "fq.uh.cu",
        return '@estudiantes.'+domain
    
    elif category == "Trabajador":
        area = area.strip().upper()
        domain = 'iris.uh.cu'
        domains = {
            "RECTORADO":    	"rect.uh.cu",
          	"ADMINISTRACION DE RECTORADO":	"rect.uh.cu",
            "GRUPO DE SERVICIOS":	"rect.uh.cu",
          	"RECTORADO   GRUPO (ETSC)":	"rect.uh.cu",
          	"GRUPO DE AUDITORIA":	"rect.uh.cu",
          	"GRUPO DE ASESORIA TECNICA":	"rect.uh.cu",
          	"DEPARTAMENTO DE PLANIFICACIÓN Y ORGANIZACIÓN":	"rect.uh.cu",
          	"DEPARTAMENTO DE INFORMACIÓN Y ESTADÍSTICAS":	"rect.uh.cu",
          	"RECTORADO SECRETARIA GENERAL":   	"rect.uh.cu",
          	"DEPARTAMENTO  JURIDICO":	"rect.uh.cu",
          	"GRUPO DE CONTROL ACADEMICO DE PREGRADO":	"rect.uh.cu",
          	"RECTORADO SECRETARIA GENERAL ARCHIVO CENTRAL":  	"rect.uh.cu",
          	"RECTORADO  COMISION PROV INGRESO":	"rect.uh.cu",
          	"RECTORADO RECURSOS HUMANOS":   	"rect.uh.cu",
          	"RECTORADO RECURSOS HUMANOS  CUADROS": 	"rect.uh.cu",
          	"RECTORADO RECURSOS HUMANOS GRUPO (ATENCION A PROFESORES)":	"rect.uh.cu",
          	"RECTORADO RECURSOS HUMANOS GRUPO (CONTRATACION)":	"rect.uh.cu",
          	"RECTORADO RECURSOS HUMANOS RECURSOS HUMANOS RECURSOS LABORALES": 	"rect.uh.cu",
          	"RECTORADO RECURSOS HUMANOS RECURSOS HUMANOS OTS Y PHT": 	"rect.uh.cu",
          	"RECTORADO ECONOMIA":   	"rect.uh.cu",
          	"AREA  DOCENTE":	"rect.uh.cu",
          	"GRUPO DE GESTION CONTABLE- FINANCIERA":	"rect.uh.cu",
          	"GRUOI DE REDES Y SERVICIOS TELEMATICOS":	"iris.uh.cu",
          	"GRUPO DE SEGURIDAD INFORMATICA":	"iris.uh.cu",
          	"GRUPO DE SERVICIOS TECNICOS":	"iris.uh.cu",
          	"RECTORADO ECONOMIA PLANIFICACION Y EST.":  	"rect.uh.cu",
          	"RECTORADO ECONOMIA PLANIFICACION Y EST. PLANIFICACION": 	"rect.uh.cu",
          	"RECTORADO ECONOMIA CONTABILIDAD":  	"rect.uh.cu",
          	"RECTORADO ECONOMIA CONTABILIDAD CONTABILIDAD": 	"rect.uh.cu",
          	"RECTORADO ECONOMIA CONTABILIDAD CONTROL DE INVENTAR.": 	"rect.uh.cu",
          	"RECTORADO C.E.M.I.":   	"rect.uh.cu",
          	"RECTORADO C.E.SALUD Y BIENESTAR HUMANO":	"rect.uh.cu",
          	"RECTORADO C.E.(FLACSO).": "rect.uh.cu"   	,
          	"ADMINISTRACION": 	"rect.uh.cu"   	,
          	# CENTRO DE ESTUDIOS TURISTICOS	
          	# SECRETARIA DE FACULTAD	
          	# ADMINISTRACION	
          	# DEPARTAMENTO DOCENTE CETUR.	
          	# CENTRO DE ESTUDIOS TURISTICO	
          	# ADMINISTRACIION	
          	# DEPARTAMENTO ENTIDADES DE HOSPITALIDAD	
          	# DEPARTAMENTO FORMACION BASICA	
          	# UNIDAD DOCENTE (SALVADOR ALLENDE)	
          	# UNIDAD DOCENTE (GIRON)	
          	# UNIDAD DOCENTE (TARARA)	
          	# UNIDAD DOCENTE (TULIPAN)	
          	# UNIDAD DOCENTE (EAEHT0)	
          	# UNIDAD DOCENTE (UCI)	
          	# DIRECCION DE PUBLICACIONES ACADEMICAS	
          	# GRUPO DOCENTE 	
          	# GRUPO DE EDICION	
          	# GRUPO ADMINISTRATIVO	
          	# VICERECTORIA (UNIVERSIALIZACION)	
          	#   GRUPO DE INFORMATIZACION	
          	#   GRUPO DE ESTUDIOS SOCIALES	
          	#  GRUPO DE ATENCION A (Diferido )	
          	# DIRECCION DOCENTE METODOLOGICA	
          	#  DIRECCION DE UNIVERSALIZACION	
          	# DEPARTAMENTO DE PREPARACION PARA LA DEFENSA	
          	# DIRECCION DE CALIDAD	
          	# AREA DOCENTE (SEDE MARIANAO)	
          	# SECRETARIA DOCENTE   	
          	# AREA  DOCENTE	
          	# ADMINISTRACION	
          	# AREA DOCENTE (SEDE BOYEROS)	
          	# SECRETARIA  DOCENTE	
          	# AREA  DOCENTE	
          	# ADMINISTRACION	
          	# AREA DOCENTE (SEDE LA LISA)	
          	# SECRETARIA  DOCENTE	
          	# AREA DOCENTE	
          	# ADMINISTRACION	
          	# AREA DOCENTE (SEDE COTORRO)	
          	# SECRETARIA DOCENTE	
          	# AREA DOCENTE	
          	# ADMINISTRACION	
          	# SEDE UNIVERSITARIA MUNICIPAL (PLAZA DE LA REVOLUCION)	
          	# SECRETARIA DOCENTE	
          	# ADMINISRACION	
          	# AREA DOCENTE	
          	# FILIAL UNIVERSITARIA TERRITORIAL(Habana del Este-Guanabacoa-Regla=	
          	# SECRETARIA DOCENTE	
          	# AREA  DOCENTE	
          	# ADMINISTRACION	
          	# FILIAL UNIVERSITARIA TERRITORIAL (San Miguel del Padron-Cotorro)	
          	# SECRETARIA DOCENTE	
          	# AREA  DOCENTE	
          	# ADMINISTRACION	
          	# SEDE UNIVERSITARIA MUNICIPAL (CENTRO HABANA)	
          	# SECRETARIA DOCENTE	
          	# ADMINISTRACION	
          	# AREA DOCENTE	
          	# SEDE UNIVERSITARIA MUNICIPAL (HABANA VIEJA)	
          	# SECRETARIA DOCENTE	
          	# ADMINISTRACION	
          	# AREA DOCENTE	
          	# SEDE UNIVERSITARIA MUNICIPAL (CERRO)	
          	# SECRETARIA DOCENTE	
          	# ADMINISTRACION	
          	# AREA  DOCENTE	
          	# SEDE UNIVERSITARIA MUNICIPAL (10 DE OCTUBRE)	
          	# SECRETARIA DOCENTE	
          	# ADMINISTRACION	
          	# AREA DOCENTE	
          	# SEDE UNIVERSITARIA MUNICIPAL (PLAYA)	
          	# SECRETARIA DOCENTE	
          	# ADMINISTRACION	
          	# AREA  DOCENTE	
          	# SEDE UNIVERSITARIA MUNICIPAL (HABANA DEL ESTE)	
          	# SECRETARIA DOCENTE	
          	# ADMINISTRACION	
          	# AREA  DOCENTE	
          	# SEDE UNIVERSITARIA MUNICIPAL (GUANABACOA)	
          	# SECRETARIA DOCENTE	
          	# ADMINISRACION	
          	# AREA  DOCENTE	
          	# SEDE UNIVERSITARIA MUNICIPAL (ARROYO NARANJO)	
          	# SECRETARIA DOCENTE	
          	# ADMINISTRACION	
          	# AREA  DOCENTE	
          	# SEDE UNIVERSITARIA MUNICIPAL (SAN MIGUEL DEL PADRON)	
          	# SECRETARIA DOCENTE	
          	# ADMINISTRACION	
          	# AREA  DOCENTE	
          	# ESCUELA DE TRABAJADORES SOCIALES ( COJIMAR )	
          	# SECRETARIA DOCENTE	
          	# ADMINISTTRACION	
          	# DIRECCION DOCENTE	
          	# DEPARTAMENTO I.C.T.B.	
          	# DIRECCION DE ACTIVIDADES	
          	# DIRECCION DE UNIDADES	
          	# ESCUELA DE TRABAJADORES SOCIALES  (PROYECTO ESPERANZA SOCIAL)	
          	# SECRETARIA  DOCENTE	
          	# ADMINISTRACCION	
          	# DIRECCION DOCENTE	
          	# DIRECCION DE UNIDADES	
          	# VICERECTORIA  DE ECONOMIA	
          	# DIRECCION DE CONTABILIDAD Y FINANZA	
          	# GRUPO DE CONTABILIDAD	
          	# GRUPO DE FINANZA 	
          	# DIRECCION DE ECONOMIA(UP-UH)	
          	# CENTO DE GASTOS DE  DOCENCIA	
          	# CENTRO DE GASTOS DE  CIENCIA YTECNICA	
          	# CENTRO DE GASTOS DE ASEGURAMIENTO	
          	# DIORECCION DE PLANIFICACION Y ESTADISTICA	
          	# GRUPO DE PLANIFICACION	
          	# GRUPO DE ESTADISTICA	
          	# VICERECTORIA [ATENCION ACTIVIDADES DOCENTES Y ADMINISTRATIVAS]	
          	# VICERECTORIA  (ATENCION A ESTUDIANTES)	
          	#  GRUPO DE ESTUDIOS SOCIALES	
          	# VICERECTORIA (DOCENTE EDUCATIVA)	
          	# DOCENTE EDUCATIVA  DEPARTAMENTO DEFENSA  	
          	# DOCENTE EDUCATIVA DOCENTE METODOLOGICA   	
          	# DOCENTE EDUCATIVA CULT. FIS. SUP. ATL.   	
          	# DOCENTE EDUCATIVA CULT. FIS. SUP. ATL. EDUC. FIS. Y DEPORT.  	
          	# DOCENTE EDUCATIVA CULT. FIS. SUP. ATL. ADMINISTRATIVO  	
          	# SECCIÓN DE SERVICIOS INTERNOS	
          	# POSTGRADO Y R.I. EXTENSION UNIVERSITARIA.	
          	# GRUPO DOCENTE DE EXTENSION UNIVERSITARIA	
          	# MUSEO  FRAGUA MARTIANA	
          	# POSTGRADO Y R.I. EXTENSION UNIVERSIT.  GRUPO DE TV UNIV H. 	
          	# POSTGRADO Y R.I. EXTENSION UNIVERSIT.  ADMIN. EXT. UNIVERS. 	
          	# POSTGRADO Y R.I. EXTENSION UNIVERSIT.  CASA ESTUDIANTIL 	
          	# VICERECTORIA (INVESTIGACION)	
          	# IVICERECTORIA INVESTIGACION (O.T.R.I.)	
          	# GRUPO DE SERVICIOS TELEMATICOS  (RED)	
          	# DIRECCION DE CIENCIA Y TECNICA  	
          	"INVESTIGACION CIENT. C.E.P.E.S.":   	"cepes.uh.cu",
          	"GRUPO DE TECNOLOGIA EDUCATIVA":	"cepes.uh.cu",
          	"INVESTIGACION CIENT. C.E.P.E.S.  COMPUTACION": 	"cepes.uh.cu",
          	"INVESTIGACION CIENT. C.E.P.E.S.  PEDAGOGIA Y PSICOL.": 	"cepes.uh.cu",
          	"INVESTIGACION CIENT. C.E.P.E.S.  DESARROLLO Y ECONOM.": 	"cepes.uh.cu",
          	"INVESTIGACION CIENT. C.E.P.E.S.  AREA DE INV. DESARROLLO.":	"cepes.uh.cu",
          	 "GRUPO DE INFORMATICA  EDUCATIVA":	"cepes.uh.cu",
          	"INVESTIGACION CIENT. C.E.P.E.S.  ADMINISTRATIVA": 	"cepes.uh.cu",
          	"INVESTIGACION CIENT. I.M.R.E.":   	"imre.uh.cu",
          	# "CENTRO COSTO Y DE PAGOS"
          	"INVESTIGACION CIENT. I.M.R.E.AREA INVESTIGATIVA":	"imre.uh.cu",
          	"GRUPO DE ENERMAT":	"imre.uh.cu",
          	"GRUPO DE LUCES":	"imre.uh.cu",
          	"GRUPO DE NANOMAT":	"imre.uh.cu",
          	"GRUPO DE QUIMAT":	"imre.uh.cu",
          	"GRUPO DE LASER":	"imre.uh.cu",
          	"INVESTIGACION CIENT. I.M.R.E.TALLER.":	"imre.uh.cu",
          	"INVESTIGACION CIENT. I.M.R.E. ADMINISTRATIVO":  	"imre.uh.cu",
          	"INVESTIGACION CIENT. CENTRO DE BIOMATERIALES":	"biomat.uh.cu",
          	"INVESTIGACION CIENT. CENTRO DE BIOMATERIA  PROMOCION Y COMERCIA": 	"biomat.uh.cu",
          	"INVESTIGACION CIENT. CENTRO DE BIOMATERIA  GRUPO PRODUCCION.": 	"biomat.uh.cu",
          	"DEPARTAMENTO DE DESARROLLO TECNOLOGICO":	"biomat.uh.cu",
          	"INVESTIGACION CIENT. CENTRO DE BIOMATERIA QUIMICA MACROMOLEC.":  	"biomat.uh.cu",
          	"INVESTIGACION CIENT. CENTRO DE BIOMATERIA CERAMICA Y COMPOSIT.":  	"biomat.uh.cu",
          	"INVESTIGACION CIENT. CENTRO DE BIOMATERIA ASEGUR DE LA CALIDAD":  	"biomat.uh.cu",
          	"INVESTIGACION CIENT. CENTRO DE BIOMAT. ADMINISTRATIVO":  	"biomat.uh.cu",
          	"INVESTIGACION CIENT. C.E.S.E.U.":   	"cehseu.uh.cu",
          	"INVESTIGACION CIENT. C.E.S.E.U.  SECC ADMINISTRATIVA": 	"cehseu.uh.cu",
          	"INVESTIGACION CIENT. C.E.S.E.U. AREA DE INVEST. DES.":  	"cehseu.uh.cu",
          	"INVESTIGACION CIENT. C.I.E.I.":   	"ciei.uh.cu",
          	"INVESTIGACION CIENT. C.I.E.I. ECONOMIA INTERNAC.":  	"ciei.uh.cu",
          	"INVESTIGACION CIENT. C.I.E.I. ADMINISTRATIVO":  	"ciei.uh.cu",
          	"INVESTIGACION CIENT. C.E.D.E.M.":   	"cedem.uh.cu",
          	"INVESTIGACION CIENT. C.E.D.E.M. ADMINISTRATIVO":  	"cedem.uh.cu",
          	"INVESTIGACION CIENT. C.E.D.E.M. ADMINISTRATIVO  IMPRENTA":	"cedem.uh.cu",
          	"INVESTIGACION CIENT. C.E.E.C.":   	"ceec.uh.cu",
          	"INVESTIGACION CIENT. C.E.E.C.  SECCION ADMINISTRATI": 	"ceec.uh.cu",
          	"INVESTIGACION CIENT. C.E.MEDIO ANBIENTE":   	"ceec.uh.cu",
          	#  GRUPO DOCENTE	
          	#  GRUPO DE EDICONES	
          	#  GRUPO ADMINISTRATIVO	
          	"INVESTIGACION CIENTIFICA DIRECCION DE INFORMACION CIENTIFICO TECNICA":	"dict.uh.cu",
          	"GRUPO DOCENTE (DIR. INFORMACION)":	"dict.uh.cu",
          	"INVESTIGACION CIENTIFICA DIRECCION DE INFORMACION CIENTIFICO TECNICA  DPTO PROC TECN INFORM":	"dict.uh.cu",
          	"INVESTIGACION CIENTIFICA DIRECCION DE INFORMACION CIENT TECNICA  DPTO PROC TECN INFOR  GRPO DESARR":	"dict.uh.cu",
          	"INVESTIGACION CIENTIFICA DIRECCION DE INFORMACION CIENT TECNICA  DPTO PROC TECN INFOR  GRPO ANALIT": 	"dict.uh.cu",
          	"INVESTIGACION CIENTIFICA DIRECCION DE INFORMACION CIENT TECNICA  DPTO PROC TECN INFOR  GRPO TEC INF": 	"dict.uh.cu",
          	"INVESTIGACION CIENTIFICA DIRECCION DE INFORMACION CIENT TECNICA  DPTO SERVICIOS INFORMATICOS":	"dict.uh.cu",
          	"INVESTIGACION CIENTIFICA DIRECCION DE INFORMACION CIENT TECNICA  DPTO SERV INFOR  GPO CONSUL Y REFER":	"dict.uh.cu",
          	"INVESTIGACION CIENTIFICA DIRECCION DE INFORMACION CIENT TECNICA  DPTO SERV INFOR  GPO FONDOS INFORM":	"dict.uh.cu",
          	"INVESTIGACION CIENTIFICA DIRECCION DE INFORMACION CIENT TECNICA  DPTO SERV INFOR  GPO TRADUCCIONES":	"dict.uh.cu",
          	"INVESTIGACION CIENTIFICA DIRECCION DE INFORMACION CIENT TECNICA  SECCION ADMINISTRATIVA":	"dict.uh.cu",
          	# VICERECTORIA POSGRADO Y REL INTERN.	
          	# Direccion Administrativa COPE	
          	# GRUPO DE SERVICIOS ACADEMICOS INTERNACIONALES(OSAI-UH)	
          	# DEPARTAMENTO DE COMUNICACION	
          	# POSTGRADO Y R.I. RELACIONES INTERNACIONALES.	
          	#  GRUPO DE SERVICIOS ACADEMICOS INTERNACIONALES (OSAI-UH)	
          	# POSTGRADO Y R.I. RELACIONES INTERNAC.  COLABORACION 	
          	# GRUPO DE GESTION DE PROYECTOS INTERNACIONALES Y DONATIVOS	
          	# POSTGRADO Y R.I. RELACIONES INTERNAC.  SECCION DE TRAMITES.	
          	# POSTGRADO Y R.I. RELACIONES INTERNAC.  SECC ADMINISTRATIVA 	
          	# DIRECCIÓN DE COMUNICACIÓN	
          	# POSTGRADO Y R.I. DIRECCION DE POSGRAD   	
          	# DIRECCION DE EVENTOS Y SERVICIOS ACADEMICOS INTERNACIONALES	
          	# DEPARTAMENTO DE SERVICIOS ACADEMICOS INTERNACIONALES	
          	# GRUPO ADMINISTRATIVO	
          	"CENTRO DE ESTUDIOS DE ADMINISTRACION PUBLICA":	"ceap.uh.cu",
          	# INSTITUTO  CONFUCIO	
          	# SECRETARIA  DOCENTE	
          	# SECCION  ADMINISTRATIVA	
          	# DEPARTAMENTO DOCENTE DE LENGUA CHINA	
          	# VICERECTORIA  DE SERVICIOS	
          	# UNIDAD PRESUPUESTADA DDE ASEGURAMIENTO [UPA]	
          	# DEPARTAMENTO DE RECURSOS HUMANOS	
          	# DIRECCION DE ECONOMIA	
          	# CENTRO DE GASTOS DE SERVICIOS	
          	# CENTRO DE GASTOS DE ASEGURAMIENTO	
          	# GRUPO DE CONTROL Y ANALISIS	
          	# VICERECRORIA DE SERVICIOS . SEGURIDAD Y PROTECCION.	
          	# VICERECTORIA DE SERVICIOS DIR.  ASEGURAMIENTO	
          	# ECONOMIA Y SERVICIOS ASEGURAMIENTO GESTION Y COMPRAS  	
          	# ECONOMIA Y SERVICIOS ASEGURAMIENTO ALMACENAJE Y DISTR.  	
          	# ECONOMIA Y SERVICIOS ASEGURAMIENTO ALMACENAJE Y DISTR. TRANSPORTE 	
          	# ECONOMIA Y SERVICIOS ASEGURAMIENTO ALMACENAJE Y DISTR. MEDIOS DE VIDA 	
          	# ECONOMIA Y SERVICIOS ASEGURAMIENTO ALMACENAJE Y DISTR. MEDIOS DE ESTUDIO 	
          	# SECCION  DE  FERRETERIA	
          	# SERVICIOS ASEGURAMIENTO LIBRERIA´ALMA MATER  	
          	# DIRECCION DE ASEGURAMIENTO (LIBRERIA ALMA MATER)	
          	# SECCION ADMINISTRATIVA (CASA DE PROTOCOLO)	
          	# VIRECTORIA DE SERVICIOS. DIRECCION DE SERVICIOS	
          	# CENTRO CONTABLE Y DE PAGOS	
          	# ECONOMIA Y SERVICIOS SERVICIOS  ALIMENTACION 	
          	# ECONOMIA Y SERVICIOS SERVICIOS  COMEDOR JOSE MACHADO 	
          	# ECONOMIA Y SERVICIOS SERVICIOS  COMEDOR JOSE MACHADO # 1	
          	# ECONOMIA Y SERVICIOS SERVICIOS  COMEDOR JOSE MACHADO # 2	
          	# ECONOMIA Y SERVICIOS SERVICIOS  CENTRO DE ELABORACIO 	
          	# ECONOMIA Y SERVICIOS SERVICIOS  CENTRO DE ELABORACIO DULCERIA Y PANADERIA	
          	# ECONOMIA Y SERVICIOS SERVICIOS  CENTRO DE ELABORACIO ELABORACION	
          	# ECONOMIA Y SERVICIOS SERVICIOS ACTIVIDADES Y COMUN.  	
          	# ECONOMIA Y SERVICIOS SERVICIOS ACTIVIDADES Y COMUN.  CORRESPONDENCIA	
          	# ECONOMIA Y SERVICIOS SERVICIOS ACTIVIDADES Y COMUN. SECC. SERVICIOS INTE 	
          	# ADMINISTRACION (EDIFICIO VARONA)	
          	# ECONOMIA Y SERVICIOS SERVICIOS TRANSPORTE  	
          	# ECONOMIA Y SERVICIOS SERVICIOS TRANSPORTE  TRANSPORTE	
          	# ECONOMIA Y SERVICIOS SERVICIOS EQUIPOS AUTOMOTOR  	
          	# ECONOMIA Y SERVICIOS SERVICIOS EQUIPOS AUTOMOTOR  # 1	
          	# ECONOMIA Y SERVICIOS SERVICIOS EQUIPOS AUTOMOTOR  # 2	
          	# ECONOMIA Y SERVICIOS SERVICIOS EQUIPOS AUTOMOTOR CONT. Y OP. OMNIBUS 	
          	# ECONOMIA Y SERVICIOS SERVICIOS ADM. EDIF. MELLA  	
          	# ECONOMIA Y SERVICIOS SERVICIOS ADM. EDIF. MELLA MANTENIM. Y SERVIC. 	
          	# ECONOMIA Y SERVICIOS SERVICIOS ADM. EDIF. MELLA MANTENIM. Y SERVIC. MANTENIMIENTO	
          	# ECONOMIA Y SERVICIOS SERVICIOS ADM. EDIF. MELLA MANTENIM. Y SERVIC. SERVICIOS	
          	# ECONOMIA Y SERVICIOS SERVICIOS ADM. EDIF. MELLA (CENTRO DE ELABORACION)	
          	# ECONOMIA Y SERVICIOS SERVICIOS ADM. EDIF. MELLA COCINA COMEDOR COCINA	
          	# ECONOMIA Y SERVICIOS SERVICIOS  IMPRENTA 	
          	# VICERECTORIA DE SERVICIOS. DIRECCION DE SERVICIOS A EVENTOS	
          	# SECCION DE SERVICIO	
          	# SECCION DE ALOJAMIENTO	
          	# SECCION DE MANTENIMIENTO	
          	# SERVICIOS SERVICIOS A EVENTOS  VILLA  41 Y 18 	
          	# ECONOMIA Y SERVICIOS SERVICIOS A EVENTOS  COCINA COMEDOR # 1	
          	# ECONOMIA Y SERVICIOS SERVICIOS A EVENTOS  COCINA COMEDOR # 2	
          	# ECONOMIA Y SERVICIOS SERVICIOS A EVENTOS  MANTENIM. Y ALOJAM. 	
          	# ECONOMIA Y SERVICIOS SERVICIOS A EVENTOS  MANTENIM. Y ALOJAM. MANTENIMIENTO	
          	# ECONOMIA Y SERVICIOS SERVICIOS A EVENTOS  MANTENIM. Y ALOJAM. MANTENIMIENTO PLAYA	
          	# SERVICIOS SERVICIOS A EVENTOS VILLA MIRAMAR 5TA.62  	
          	# ECONOMIA Y SERVICIOS SERVICIOS A EVENTOS (CASA DE PROTOCOLO)	
          	# VICERECTORIA DE SERVICIOS . DIR INGENIERO PRINCIPAL	
          	# GRUPO DE ASEAORIA LEGAL	
          	# GRUPO DE ADMINISTRACION	
          	# GRUPO DECONTROL LOGISTICO Y ECONOMICO	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL  ASEG.TECNICO A  EDIF 	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL MANTENIMIENTO ESP.  	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL MANTENIMIENTO ESP. MANTENIMIENTO PLOMERIA	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL MANTENIMIENTO ESP. MANTENIMIENTO OPERACIONES VARIAS	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL MANTENIMIENTO ESP. MANTENIMIENTO BRIGADA CARPINTERIA	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL REFRIGERACION  	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL REFRIGERACION  ENRROLLADO Y MAQUIN.	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL REFRIGERACION  REFRIGER. DOMESTICA	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL MECANICA INDUSTRIAL  CALDERAS	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL MECANICA INDUSTRIAL  CAMPANA	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL MECANICA INDUSTRIAL  HIDRAULICA	
          	# ECONOMIA Y SERVICIOS INGENIERO PRINCIPAL MIRAMAR Y COMPUTAC.  	
          	# VICERECTORIA DE SERVICIOS . BRIG ASP. CONTINGENTE	
          	# ECONOMIA Y SERVICIOS CONTINGENTE ADMINISTRACION  	
          	# ECONOMIA Y SERVICIOS CONTINGENTE ASEGURAMIENTO  	
          	# ECONOMIA Y SERVICIOS CONTINGENTE EQUIPOS  	
          	# ECONOMIA Y SERVICIOS CONTINGENTE TECNICO PRODUCTIVO  	
          	# ECONOMIA Y SERVICIOS CONTINGENTE TECNICO PRODUCTIVO  EJECUTOR # 1	
          	# ECONOMIA Y SERVICIOS CONTINGENTE TECNICO PRODUCTIVO  EJECUTOR # 2	
          	# ECONOMIA Y SERVICIOS CONTINGENTE TECNICO PRODUCTIVO  EJECUTOR # 3	
          	# VICERECTORIA DE SERVICIOS. DIR DE RESIDENCIA ESTUDIANTIL	
          	# DIRECCION DE RESIDENCIAS ESTUDIANTILES	
          	# ECONOMIA Y SERVICIOS RESID. ESTUDIANTIL RES. EST. 12 Y MAL.  	
          	# SECCION DE MANTENIMIENTO	
          	# SECCION CENTRO DE ELABORACION	
          	# ECONOMIA Y SERVICIOS RESID. ESTUDIANTIL RES. EST. F Y 3RA.  	
          	# SALA  DE COMPUTACION	
          	# SECCION DE MANTENIMIENTO	
          	# SECCION DE CENTRO DE ELABORACION	
          	# ECONOMIA Y SERVICIOS RESID. ESTUDIANTIL RES. EST. F Y 3RA. ASEGURAMIENTO 	
          	# ECONOMIA Y SERVICIOS RESID. ESTUDIANTIL RES. EST. ALAMAR 6  	
          	# GRUPO DE MANTENIMIENTO	
          	# COCINA COMEDOR	
          	# ECONOMIA Y SERVICIOS RESID. ESTUDIANTIL RES. EST. MICRO X  	
          	# GRUPO DE MANTENIMIENTO	
          	# COCINA COMEDOR	
          	# ECONOMIA Y SERVICIOS RESID. ESTUDIANTIL RES. EST. GUITERAS  	
          	# GRUPO DE MANTENIMIENTO	
          	# COCINA COMEDOR	
          	# CENTRO DE ELABORACION DEL ESTE	
          	# DIRECCION DE ALIMENTACION	
          	# DEPARTAMENTO ECONOMICO	
          	# DEPERTAMENTO GASTRONOMICO	
          	"FACULTAD DE ECONOMIA":	"fec.uh.cu",
          	"ECONOMIA   SECRETARIA FACULTAD": 	"fec.uh.cu",
          	"ECONOMIA   ADMINISTRACION": 	"fec.uh.cu",
          	"GRIPO DE ICTB  . BIBLIOTECA.":	"fec.uh.cu",
          	"ECONOMIA  DESARROLLO ECONOM.":  	"fec.uh.cu",
          	"ECONOMIA  MACRO Y MICROECONOM.":  	"fec.uh.cu",
          	"ECONOMIA  CIENCIAS EMPRESARIA.":  	"fec.uh.cu",
          	"ECONOMIA  DE PLANIFICACION DE LA ECONOMIA NACIONAL":	"fec.uh.cu",
          	"ECONOMIA  ESTADIS. E INFORMAT.":  	"fec.uh.cu",
          	"ECONOMIA  ESTADIS. E INFORMAT. LABORATORIO COMPUT.": 	"fec.uh.cu",
          	"FACULTAD DE CONTABILIDAD Y FINANZAS":	"fcf.uh.cu",
          	"CONTAB. Y FINANZAS   SECRETARIA FACULTAD": 	"fcf.uh.cu",
          	"CONTAB. Y FINANZAS   ADMINISTRACION": 	"fcf.uh.cu",
          	"CONTAB. Y FINANZAS   IDIOMAS": 	"fcf.uh.cu",
          	"CONTAB. Y FINANZAS  CONTABIL. Y AUDITOR.":  	"fcf.uh.cu",
          	"CONTAB. Y FINANZAS  COSTOS Y SISTEMAS":  	"fcf.uh.cu",
          	"CONTAB. Y FINANZAS  FINANZAS":  	"fcf.uh.cu",
          	"CONTAB. Y FINANZAS CETED":   	"fcf.uh.cu",
          	"FACULTAD DE EDUCACION A DISTANCIA":	"fed.uh.cu",
          	"EDUCACION A DISTANCI   SECRETARIA FACULTAD": 	"fed.uh.cu",
          	"EDUCACION A DISTANCI   ADMINISTRACION": 	"fed.uh.cu",
          	"MATEMATICA Y COMPUT.":    	"matcom.uh.cu",
          	"GRUPO DE CRIPTOGRAFIA":	"matcom.uh.cu",
          	"MATEMATICA Y COMPUT.   SECRETARIA FACULTAD": 	"matcom.uh.cu",
          	"MATEMATICA Y COMPUT.   ADMINISTRACION": 	"matcom.uh.cu",
          	"MATEMATICA Y COMPUT. DPTO MATEMATICA":	"matcom.uh.cu",
          	"MATEMATICA Y COMPUT.  DPTO MATEMATICA  APLICADA":	"matcom.uh.cu",
          	"MATEMATICA Y COMPUT.  DPTO COMPUTACION 1.":	"matcom.uh.cu",
          	"MATEMATICA Y COMPUT.DPTO DE  COMPUTACION 2.":	"matcom.uh.cu",
          	"MATEMATICA Y COMPUT.  COMPUTACION LABORATORIO COMPUT.": 	"matcom.uh.cu",
          	"GRUPO DE TRABAJO (CASA DEL SOFTWARE)":	"matcom.uh.cu",
          	"CENTRO DE ESTUDIOS DE CRIPTOGRAFIA":	"matcom.uh.cu",
          	"QUIMICA":    	"fq.uh.cu",
          	"QUIMICA   SECRETARIA FACULTAD": 	"fq.uh.cu",
          	"QUIMICA   ADMINISTRACION": 	"fq.uh.cu",
          	# BIBLIOTECA	
          	"QUIMICA  QUIMICA INORGANICA":  	"fq.uh.cu",
          	"QUIMICA  QUIMICA ORGANICA":  	"fq.uh.cu",
          	"QUIMICA  QUIMICA ANALITICA":  	"fq.uh.cu",
          	"QUIMICA  QUIMICA FISICA":  	"fq.uh.cu",
          	"QUIMICA  QUIMICA GENERAL":  	"fq.uh.cu",
          	"QUIMICA  AREA INVEST. DESARR. LABORAT BIO-INORGANI": 	"fq.uh.cu",
          	"QUIMICA  AREA INVEST. DESARR. LAB SINTESIS ORGANIC": 	"fq.uh.cu",
          	"QUIMICA C.E.ANTIGENO SINTET.":   	"fq.uh.cu",
          	"QUIMICA C.E.ANTIGENO SINTET.  ADMINISTRACION": 	"fq.uh.cu",
          	"DEPARTAMENTO DE GLICOCONJUGACION":	"fq.uh.cu",
          	"DEPARTAMENTO DE QUIMICA":	"fq.uh.cu",
          	"DEPARTAMENTO DE CALIDAD":	"fq.uh.cu",
          	"QUIMICA C.E.PROD NATURALES.":   	"fq.uh.cu",
          	"QUIMICA C.E.PROD NATURALES.  ADMINISTRACION (C.E)": 	"fq.uh.cu",
          	"FISICA":    	"fisica.uh.cu",
          	"FISICA   SECRETARIA FACULTAD": 	"fisica.uh.cu",
          	"FISICA   ADMINISTRACION": 	"fisica.uh.cu",
          	"FISICA  FISICA GENERAL":  	"fisica.uh.cu",
          	"FISICA  FISICA APLICADA":  	"fisica.uh.cu",
          	"FISICA  FISCA TEORICA":  	"fisica.uh.cu",
          	"BIOLOGIA":    	"fbio.uh.cu",
          	"GRUPO DE INFORMATIZACION":	"fbio.uh.cu",
          	"GRUPO DE ICTB (BIBLIOTECA)":	"fbio.uh.cu",
          	"BIOLOGIA   SECRETARIA FACULTAD": 	"fbio.uh.cu",
          	"BIOLOGIA  ADMINISTRATIVO":  	"fbio.uh.cu",
          	"BIOLOGIA  BIOQUIMICA":  	"fbio.uh.cu",
          	"BIOLOGIA  MICROBIOLOGIA":  	"fbio.uh.cu",
          	"BIOLOGIA  BIOLOGIA VEGETAL":  	"fbio.uh.cu",
          	"BIOLOGIA  BIOL. ANIMAL Y HUM.":  	"fbio.uh.cu",
          	 "( MUSEOS  )":	"fbio.uh.cu",
          	"BIOLOGIA  AREA INVEST. DESARR.":  	"fbio.uh.cu",
          	"BIOLOGIA  LABORAT. DOC. BIOL.":  	"fbio.uh.cu",
          	"BIOLOGIA C.E.DE PROTEINAS":   	"fbio.uh.cu",
          	"BIOLOGIA C.I.M.":   	"fbio.uh.cu",
          	"GRUPO DE MANEJO Y CONSERVACION DE RECURSOS MARINOS":	"fbio.uh.cu",
          	"GRUPO DE ECOLOGIA MARINA":	"fbio.uh.cu",
          	"GRUPO DE CAMBIO CLIMATICO":	"fbio.uh.cu",
          	"GRUPO DE ACUICULTURA":	"fbio.uh.cu",
          	"GRUPO DE GENETICA DE LA CONSERVACION":	"fbio.uh.cu",
          	"BIOLOGIA C.I.M. BIOLOGIA MARINA":  	"fbio.uh.cu",
          	"BIOLOGIA C.I.M. ADMINISTRATIVO":  	"fbio.uh.cu",
          	"GEOGRAFIA":    	"geo.uh.cu",
          	"GEOGRAFIA   SECRETARIA FACULTAD": 	"geo.uh.cu",
          	"GEOGRAFIA   ADMINISTRACION": 	"geo.uh.cu",
          	"GEOGRAFIA   GEOGRAFIA FISICA": 	"geo.uh.cu",
          	"GEOGRAFIA   GEOGRAFIA ECONOMICA": 	"geo.uh.cu",
          	"FILOSOFIA E HISTORIA":    	"ffh.uh.cu",
          	"FILOSOFIA E HISTORIA   SECRETARIA FACULTAD": 	"ffh.uh.cu",
          	"FILOSOFIA E HISTORIA   ADMINISTRACION": 	"ffh.uh.cu",
          	"FILOSOFIA E HISTORIA  FILOSOFIA ESPECIAL.":  	"ffh.uh.cu",
          	"FILOSOFIA E HISTORIA  SOCIOLOGIA":  	"ffh.uh.cu",
          	"FILOSOFIA E HISTORIA  SOCIOLOGIA ESC.T.SOC(COJIMAR)": 	"ffh.uh.cu",
          	"FILOSOFIA E HISTORIA  FTP P/L C. SOC. EC.":  	"ffh.uh.cu",
          	"FILOSOFIA E HISTORIA  FTP P/L C. NAT. Y M.":  	"ffh.uh.cu",
          	"FILOSOFIA E HISTORIA  HISTORIA DE CUBA":  	"ffh.uh.cu",
          	"FILOSOFIA E HISTORIA  HISTORIA":  	"ffh.uh.cu",
          	"FILOSOFIA E HISTORIA C.E.CASA FDO ORTIZ":   	"ffh.uh.cu",
          	"DERECHO":    	"lex.uh.cu",
          	#  GRUPO DE I.C.T.B (BIBLIOTECA)	
          	"DERECHO   SECRETARIA FACULTAD": 	"lex.uh.cu",
          	"DERECHO   ADMINISTRACION": 	"lex.uh.cu",
          	"DERECHO  JURIDICOS BASICOS":  	"lex.uh.cu",
          	"DERECHO  JURIDICOS BASICOS ESC.T.SOC.(COJIMAR)": 	"lex.uh.cu",
          	"DERECHO  PENAL":  	"lex.uh.cu",
          	"DERECHO  PENAL ESC.T.SOC.(COJIMAR)": 	"lex.uh.cu",
          	"DERECHO  ECONOMICO INTERNAC.":  	"lex.uh.cu",
          	"DERECHO  ECONOMICO INTERNAC. ESC.T.SOC.(COJIMAR)": 	"lex.uh.cu",
          	"DERECHO  CIVIL":  	"lex.uh.cu",
          	"DERECHO  CIVIL ESC.T.SOC.(COJIMAR)": 	"lex.uh.cu",
          	"PSICOLOGIA":    	"psico.uh.cu",
          	"PSICOLOGIA   SECRETARIA FACULTAD": 	"psico.uh.cu",
          	"PSICOLOGIA   ADMINISTRACION": 	"psico.uh.cu",
          	"PSICOLOGIA  FORMACION BASICA":  	"psico.uh.cu",
          	"PSICOLOGIA  FORMACION BASICA ESC.T.SOC(COJIMAR)": 	"psico.uh.cu",
          	"PSICOLOGIA  EJERCICIO D/LA PROF.":  	"psico.uh.cu",
          	"PSICOLOGIA  EJERCICIO D/LA PROF. ESC.T.SOC(COJIMAR) .": 	"psico.uh.cu",
          	"ARTES Y LETRAS":    	"fayl.uh.cu",
          	"ARTES Y LETRAS   SECRETARIA FACULTAD": 	"fayl.uh.cu",
          	"ARTES Y LETRAS   ADMINISTRACION": 	"fayl.uh.cu",
          	"GRUPO EDITORIAL (U-H)":	"fayl.uh.cu",
          	"ARTES Y LETRAS  ESTUDIOS LITERARIOS":  	"fayl.uh.cu",
          	"ARTES Y LETRAS  LINGUISTICA":  	"fayl.uh.cu",
          	"ARTES Y LETRAS  LINGUISTICA ESC.T.SOC.(COJIMAR)": 	"fayl.uh.cu",
          	"ARTES Y LETRAS  HISTORIA DEL ARTE":  	"fayl.uh.cu",
          	"DEPARTAMENTO DE PATRIMONIO":	"fayl.uh.cu",
          	"DEPARTAMENTO DE ESTUDIOS SOCIOCULTURALES":	"fayl.uh.cu",
          	"LENGUAS EXTRANJERAS":    "flex.uh.cu",
          	"LENGUAS EXTRANJERAS   SECRETARIA FACULTAD": 	"flex.uh.cu",
          	"LENGUAS EXTRANJERAS   ADMINISTRACION": 	"flex.uh.cu",
          	"LENGUAS EXTRANJERAS  INGLES":  	"flex.uh.cu",
          	"LENGUAS EXTRANJERAS  PREST. INGLES":  	"flex.uh.cu",
          	"LENGUAS EXTRANJERAS  PREST. INGLES ESC.T.SOC.(COJIMAR)": 	"flex.uh.cu",
          	"LENGUAS EXTRANJERAS  FRANCES Y PORTUGUES":  	"flex.uh.cu",
          	"LENGUAS EXTRANJERAS  ALEMAN":  	"flex.uh.cu",
          	"LENGUAS EXTRANJERAS  RUSO E/ ITALIAN0":  	"flex.uh.cu",
          	"LENGUAS EXTRANJERAS  ESPAÑOL":  	"flex.uh.cu",
          	"CENTRO DE IDIOMAS":	"flex.uh.cu",
          	"COMUNICACION":    	"fcom.uh.cu",
          	"COMUNICACION   SECRETARIA FACULTAD": 	"fcom.uh.cu",
          	"COMUNICACION   ADMINISTRACION": 	"fcom.uh.cu",
          	"COMUNICACION   COMUNICACION E.T.SOC": 	"fcom.uh.cu",
          	"COMUNICACION  BIBLIOT Y CIENC INF":  	"fcom.uh.cu",
          	"COMUNICACION  PERIODISMO":  	"fcom.uh.cu",
          	"COMUNICACION  COMUNICACION SOCIAL":  	"fcom.uh.cu",
          	"FACULTAD DE LENGUA ESPAÑOLA PARA NO HISPANOHABLANTES":	"fenhi.uh.cu"
          	# SECRETARIA DE FACULTAD	
          	# BIBLIOTECA	
          	# GRUPO DE ACTIVIDADES ADMINISTRATIVAS	
          	# DEPARTAMENTO DE DIAGNOSTICO	
          	# DEPARTAMENTO DE EXTENSION UNIVERSITARIA	
          	# UNIDAD I DE PREPARATORIA	
          	# UNIDAD II DE PREPARATORIA	
          	# PROGRAMA DE PERFECCIONAMIENTO - COJIMAR	
          	# DEPARTAMENTO DE PRACTICA INTEGRAL DE LENGUA ESPAÑOLA	
          	# DEPARTAMENTO DE LENGUA Y COMUNICACION	
          	# DEPARTAMENTO DE ESTUDIOS LINGUISTICOS	
          	# AREA DE RESERVA	
        }
        
        try:
            domain = domains[area]
        except Exception:
            pass

        return '@'+domain
    
    
    # default
    return "@iris.uh.cu"

def __translate_byte_types__(instance):
    instance_json = json.dumps(instance, cls=utils.MyEncoder)
    return json.loads(instance_json)

def __sha512_crypt__(password, rounds=5000):
    rand = random.SystemRandom()
    salt = ''.join([rand.choice(string.ascii_letters + string.digits)
                    for _ in range(16)])

    prefix = '$6$'
    rounds = max(1000, min(999999999, rounds))
    prefix += 'rounds={0}$'.format(rounds)
    return crypt.crypt(password, prefix + 'abcdefghijklmnop')

def __set_filters__(args):
    filters = ""
    if args.get('nombre',False):
        filters += ("(cn=*%s*)" % args.get('nombre'))
    if args.get('correo',False):
        filters += ("(correo=*%s*)" % args.get('correo'))
    if args.get('apellidos',False):
        filters += ("(sn=*%s*)" % args.get('apellidos'))
    if args.get('fechaInicio',False):
        filters += ("(fechadecreacion>=%s)" % args.get('fechaInicio'))
    if args.get('fechaFin',False):
        filters += ("(fechadecreacion<=%s)" % args.get('fechaFin'))

    return filters

def __generate_new_email__(uid,category,area):
    email = uid + __map_area_to_email_domain__(area, category)

    return email


class Admins(Resource):
    @jwt_required
    def get(self):
        users = UserRole.query.filter_by(role='admin').all()
        return jsonify({'administradores': users})

    @jwt_required
    def put(self):
        data = request.get_json()

        users_account = ldap_server.search_s("dc=uh,dc=cu", ldap.SCOPE_SUBTREE,
            "(&(objectclass=Trabajador)(correo=%s))" % data.get('email'))
        if len(users_account):
            user = UserRole.query.filter_by(email=data.get('email')).first()
            if user is None:
                user = UserRole(data.get('email'), 'admin')
                user.save_to_db()
            else:
                if user.role == 'admin':
                    return {'error': 'Este usuario ya es administrador.'} 
                else:
                    user.role = 'admin'
                    user.save_to_db()

            return {'success': 'Administrador agregado satisfactoriamente.'} 

        else:
            return {'error': 'No existe un trabajador registrado con ese correo.'} 

    @jwt_required
    def delete(self):
        data = request.get_json().get('email')

        users_account = ldap_server.search_s("dc=uh,dc=cu", ldap.SCOPE_SUBTREE,
            "(&(objectclass=Trabajador)(correo=%s))" % data.get('email'))
        if len(users_account):
            user = UserRole.query.filter_by(email=data.get('email')).first()
            if user is None:
                return {'error': 'Este usuario no es administrador.'} 
            else:
                if user.role == 'admin':
                    user.remove_from_db()
                else:
                    return {'error': 'Este usuario no es administrador.'} 

            return {'success': 'Administrador removido satisfactoriamente.'} 

        else:
            return {'error': 'No existe un trabajador registrado con ese correo.'} 