# -*- coding: utf-8 -*-

import yaml
import zeep
import sys
import os
import ldif
import ldap
import unidecode
from ldap import modlist

ldap_server = ldap.initialize('ldap://10.6.143.50')

admin_password = os.getenv("LDAP_ADMIN_PASSWORD")

ldap_server.simple_bind_s('cn=admin,dc=uh,dc=cu', admin_password)

wsdl = 'http://sigenuwebservices.uh.cu/servicedefinition.wsdl'

class MyLDIF(ldif.LDIFParser):
    def __init__(self, input):
        ldif.LDIFParser.__init__(self,input)

    def handle(self,dn,entry):
        try:
            ldif = modlist.addModlist(entry)
            ldap_server.add_s(dn, ldif)
        except Exception:
            basedn = "ou=Estudiantes,dc=uh,dc=cu"
            student = ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(ci=%s)(objectclass=%s))" % (entry["ci"][0].decode('utf8'), "Estudiante"))
            ldif = modlist.modifyModlist(student[0][1], entry)
            ldap_server.modify_s(dn, ldif)
        


class SigenuClient:
    """Encapsulation for methods wich populate and modify the ldap server
    from sigenu webservices."""

    def __init__(self, config_yml_path, firstUidNumber):
        """Receives the path to the config file"""
        self.__uidNumber = firstUidNumber
        with open(config_yml_path, 'r') as stream:
            try:
                config_obj = yaml.safe_load(stream)
                self.__students_schema = config_obj["students_schema"]
            except yaml.YAMLError:
                perror('Error while parsing the config yml file in LDIFFromSQLServer!')

    def generate_ldif(self, number_of_rows=0):
        """Generates the ldif file from the webservices to populate the ldap
        for the first time overriding existing data.
        The second parameter is for testing and should be ignored."""
        client = zeep.Client(wsdl=wsdl)
        
        faculties = client.service.Faculties()
        problems = []

        with open("./output/students.ldif", "w+") as f:
            row_number = 1
            for faculty in faculties:
                cursor = client.service.StudentsByFaculty(faculty_id=faculty["id"])
                print(faculty["name"], len(cursor))

                uidNumber = self.__uidNumber

                rows = self.__remove_duplicates(cursor)

                for row in rows:
                    try:
                        self.__process_row(row, f, row_number, uidNumber, faculty["id"], faculty["name"])
                        row_number += 1
                        uidNumber+=1
                    except Exception as e:
                        print(str(e))
                        problems.append(row["idsigenu"])
                break
            counter = 0
            for problem in problems:
                f.write("# Problem %d (Sigenu ID): %s\n" % (counter, problem))
                counter+=1

        # populate ldap
        parser = MyLDIF(open('/api/app/sigenu_client/output/students.ldif', 'rb'))
        parser.parse()


        return uidNumber

    def __remove_duplicates(self, cursor):
        correct_list = []
        final_list = []
        for row in cursor:
            try:
                try:
                    # The first line throws an exception if not value in the list
                    index = correct_list.index(row["ci"])
                    correct_list.remove(row["ci"])
                    final_list.pop(index)
                except ValueError:
                    correct_list.append(row["ci"])
                    final_list.append(row)
            except Exception:
                # Ignore rows with errors
                continue 
        return final_list

    def __get_uid(self, name, last_name, second_last_name):
        name = unidecode.unidecode(name)
        last_name = unidecode.unidecode(last_name)
        second_last_name = unidecode.unidecode(second_last_name)

        name = name.split()[0].lower()
        last_name = last_name.split(' ')[0].lower()
        second_last_name = second_last_name.split(' ')[0].lower()
        basedn = "ou=Estudiantes,dc=uh,dc=cu"
        possible_uid = name  + '.' + last_name

        if len(ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(uid=%s)(objectclass=%s))" % (possible_uid, "Estudiante"))):
            possible_uid = name + '.' +second_last_name
            if len(ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(uid=%s)(objectclass=%s))" % (possible_uid, "Estudiante"))):
                for i in range(1,1000):
                    possible_uid = name + '.' +second_last_name +str(i)
                    if len(ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(uid=%s)(objectclass=%s))" % (possible_uid, "Estudiante"))):
                        continue
                    uid = possible_uid
                    break
            else:
                uid = possible_uid
        else:
            uid = possible_uid

        return uid
    def __process_row(self, row, open_file, row_number, uidNumber, faculty_id, faculty_name):

        open_file.write("# Entry %d: \n" % row_number)
        open_file.write("%s: %s\n" % ('dn','uid='+str(row["ci"])+',ou=Estudiantes,dc=uh,dc=cu'))
        for entry in self.__students_schema:
            open_file.write("%s: %s\n" % (entry[0], str(row[entry[1]])))
        
        # Entries outside the services
        
        open_file.write("%s: %s\n" % ('idfacultad', faculty_id))
        open_file.write("%s: %s\n" % ('facultad', faculty_name))
        open_file.write("%s: %s\n" % ('cn', str(row["name"])))
        open_file.write("%s: %s\n" % ('cuotainternet', "0"))
        open_file.write("%s: %d\n" % ('edad', age_from_ci(str(row["ci"]))))
        open_file.write("%s: %s\n" % ('pcc', str(row["politic_org"] == "pcc").upper()))
        open_file.write("%s: %s\n" % ('ujc', str(row["politic_org"] == "ujc").upper()))
        open_file.write("%s: %s\n" % ('esbaja', str(row["status"] == "Activo").upper()))
        open_file.write("%s: %s\n" % ('objectclass', 'Estudiante'))
        open_file.write("%s: %s\n" % ('objectclass', 'posixAccount'))
        open_file.write("%s: %s\n" % ('objectclass', 'shadowAccount'))
        open_file.write("%s: %s\n" % ('uidNumber', move_first_ceros(str(row["ci"]))))
        open_file.write("%s: %d\n" % ('gidNumber', 10000))
        open_file.write("%s: %s\n" % ('userPassword', '12345678'))
        open_file.write("%s: %s\n" % ('homeDirectory', '/'))
        open_file.write("%s: %s\n" % ('uid', str(row["ci"])))
        open_file.write("%s: %s\n" % ('sn', str(row["middle_name"])+ " " +str(row["last_name"])))


        open_file.write("\n")
        pass

def age_from_ci(ci):
    return 0

def move_first_ceros(ci):
    while ci[0] == '0':
        ci = ci[1:] + ci[0]
    return ci

def perror(msg, exit_status=1):
    print(msg)
    exit(exit_status)


if __name__ == "__main__":
    handler = SigenuClient("config.yml", 5000)
    handler.generate_ldif(number_of_rows=10)