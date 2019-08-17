from flask_restful import Resource, reqparse
from flask_jsonpify import jsonify
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required,
                                get_jwt_identity, set_access_cookies, unset_jwt_cookies,
                                set_refresh_cookies, get_raw_jwt)
from pymemcache.client import base
from .models import UserModel
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

            resp = jsonify({'login': True})
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

        # args = request.args
        # page = int(args.get('page',1))
        # workers_account = workers_account[(page-1)*configuration.PAGE_COUNT:page*configuration.PAGE_COUNT]

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
                name = workers_account[1]['cn'][0].split()[0].lower()
                last_name, second_last_name = workers_account[1]['sn'][0].split(
                )
                new_email = __generate_new_email__("ou=Trabajadores,dc=uh,dc=cu", name, last_name.lower(),
                    second_last_name.lower(), "Trabajador", workers_account[1]['Area'])

                try:
                    dn = workers_account[0]
                    modList = modlist.modifyModlist({'Correo': [email[0].encode(
                        'utf-8') if email else email]}, {'Correo': [new_email.encode('utf-8')]})

                    ldap_server.modify_s(dn, modList)
                except Exception as e:
                    return {'e': str(e)}

                return {'email': new_email}

        return {'error': 'Este trabajador no existe en el directorio.'}, 404

    # @jwt_required
    def patch(self):
        # GET UIDNUMBERCOUNTER
        try:
            client = base.Client((configuration.MEMCACHED_HOST, 11211))
            uidNumberCounter = int(__translate_byte_types__(
                client.get('uidNumberCounter')))
        except Exception as e:
            print(e)
            return {"error": "Can't get uidNumberCounter from memcached"}

        try:
            handler = LDIFFromSQLServer("./app/ldif_from_database/config.yml", uidNumberCounter)
            newUidNumber = handler.generate_ldif(number_of_rows=10, restore=True)
            client.set('uidNumberCounter',newUidNumber)
        except Exception as e:
            return {'e': str(e)}

        return {'status': 'done'}


class Students(Resource):
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
                name = student_accounts[1]['cn'][0].split()[0].lower()
                last_name, second_last_name = student_accounts[1]['sn'][0].split(
                )
                new_email = __generate_new_email__("ou=Estudiantes,dc=uh,dc=cu", name, last_name.lower(),
                    second_last_name.lower(), "Estudiantes", student_accounts[1]['Area'])

                try:
                    dn = student_accounts[0]
                    modList = modlist.modifyModlist({'Correo': [email[0].encode(
                        'utf-8') if email else email]}, {'Correo': [new_email.encode('utf-8')]})

                    ldap_server.modify_s(dn, modList)
                except Exception as e:
                    return {'e': str(e)}

                return {'email': new_email}

        return {'error': 'Este estudiante no existe en el directorio.'}, 404

    # @jwt_required
    def patch(self):
        # GET UIDNUMBERCOUNTER
        try:
            client = base.Client((configuration.MEMCACHED_HOST, 11211))
            uidNumberCounter = int(__translate_byte_types__(
                client.get('uidNumberCounter')))
        except Exception as e:
            print(e)
            return {"error": "Can't get uidNumberCounter from memcached"}

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
                "correo": x[1].get('Correo', 'N/D')

            } for x in externs_account]
        externs_account_json = json.dumps(externs_account, cls=utils.MyEncoder)
        externs_account = json.loads(externs_account_json)

        return {'externs': externs_account}

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

        dn = 'uid=%s,ou=Externos,dc=uh,dc=cu' % email
        password = '{CRYPT}' + __sha512_crypt__(data.get('password'), 500000)

        try:
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
                'uid':                  email.encode('utf-8'),
                'objectClass':          [b'Externo'],
                'uidNumber':            uidNumberCounter
            })
            ldap_server.add_s(dn, modList)
        except Exception as e:
            return {'error': str(e), 'aqui': 'error'}

        result = {'extern_data': 'success'}
        return jsonify(result)


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
    def post(self):
        users_account = ldap_server.search_s("dc=uh,dc=cu", ldap.SCOPE_SUBTREE,
            "(&(objectclass=Estudiante)(correo=%s))" % request.get_json().get('email'))
        if len(users_account):
            mbytes = 0
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

            return {'cuota': mbytes}
        else:
            return {'error': 'No existe un estudiante registrado con ese correo.'} 

def __map_area_to_email_domain__(area, category):
    # THIS SHOULD BE DOMAIN FOR DDI
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

def __generate_new_email__(basedn,name,last_name,second_last_name,category,area):
    possible_email = name  + '.' + last_name.lower() + __map_area_to_email_domain__(area, category)

    if len(ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(correo=%s)(objectclass=%s))" % (possible_email, category))):
        possible_email = name.lower() + '.' +second_last_name + __map_area_to_email_domain__(area, category)
        if len(ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(correo=%s)(objectclass=%s))" % (possible_email, category))):
            for i in range(1,1000):
                possible_email = name.lower() + '.' +second_last_name +str(i) + __map_area_to_email_domain__(area, category)
                if len(ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(correo=%s)(objectclass=%s))" % (possible_email, category))):
                    continue
                email = possible_email
                break
        else:
            email = possible_email
    else:
        email = possible_email

    return email
