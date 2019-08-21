import yaml

if __name__ == "__main__":
    from dependences.sqlserver_manager import ConnectionManager
else:
    from app.ldif_from_database.dependences.sqlserver_manager import ConnectionManager

import os
import ldif
import unidecode
import ldap
from ldap import modlist

ldap_server = ldap.initialize('ldap://10.6.143.50')

admin_password = os.getenv("LDAP_ADMIN_PASSWORD")

ldap_server.simple_bind_s('cn=admin,dc=uh,dc=cu', admin_password)


class MyLDIF(ldif.LDIFParser):
    def __init__(self, input):
        ldif.LDIFParser.__init__(self,input)

    def handle(self,dn,entry):
        try:
            ldif = modlist.addModlist(entry)
            ldap_server.add_s(dn, ldif)
        except Exception:
            basedn = "ou=Trabajadores,dc=uh,dc=cu"
            worker = ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(ci=%s)(objectclass=%s))" % (entry["ci"][0].decode('utf8'), "Trabajador"))
            ldif = modlist.modifyModlist(worker[0][1], entry)
            ldap_server.modify_s(dn, ldif)
        

class LDIFFromSQLServer:
    """Encapsulation for methods wich populate and modify the ldap server
    from a sql server database."""

    def __init__(self, config_yml_path, firstUidNumber):
        """Receives the path to the config file"""
        self.__uidNumber = firstUidNumber
        self.connection_handler = ConnectionManager(config_yml_path)
        with open(config_yml_path, 'r') as stream:
            try:
                config_obj = yaml.safe_load(stream)
                self.__workers_schema = config_obj["workers_schema"]
            except yaml.YAMLError:
                perror('Error while parsing the config yml file in LDIFFromSQLServer!')

    def generate_ldif(self, restore=False, number_of_rows=0):
        """Generates the ldif file from the database to populate the ldap
        for the first time overriding existing data.
        The optional second parameter defines wheter the database is restored or not.
        The third parameter is for testing and should be ignored."""
        if restore:
            self.connection_handler.restore()
        cursor = self.connection_handler.execute_sql_query(
            'SELECT No_CI, Nombre, Sexo, Apellido_1, Apellido_2, Desc_Cargo, Desc_Direccion '
            'FROM ((Nomina_UH.dbo.Empleados_Gral e '
            'INNER JOIN Nomina_UH.dbo.RH_Cargos g ON g.Id_Cargo = e.Id_Cargo) '
            'INNER JOIN Nomina_UH.dbo.RH_Plantilla_Plazas p '
            'ON g.Id_Cargo = p.Id_Cargo and e.Id_Direccion = p.Id_Direccion) '
            'INNER JOIN Nomina_UH.dbo.RH_Plantilla r '
            'ON r.Id_Direccion = p.Id_Direccion '
            'GROUP BY No_CI, Nombre, Sexo, Apellido_1, Apellido_2, Desc_Cargo, Desc_Direccion')

        with open("./output/workers.ldif", "w+") as f:
            row_number = 1
            uidNumber = self.__uidNumber
            # Limited count ?
            if number_of_rows > 0:
                rows_left = number_of_rows
                for row in cursor:
                    self.__process_row(row, f, row_number, uidNumber)
                    row_number += 1
                    rows_left -= 1
                    if rows_left == 0:
                        break
                    uidNumber+=1
            else:
                for row in cursor:
                    self.__process_row(row, f, row_number, uidNumber)
                    row_number += 1
                    uidNumber+=1

        # populate ldap
        parser = MyLDIF(open('/api/app/ldif_from_database/output/workers.ldif', 'rb'))
        parser.parse()

        return uidNumber

    def generate_modify_population(self):
        """Generates the ldif file from the database to modify
        the ldap keeping unmodified data untouched."""
        raise NotImplementedError

    def __get_uid(self, name, last_name, second_last_name):
        name = unidecode.unidecode(name)
        last_name = unidecode.unidecode(last_name)
        second_last_name = unidecode.unidecode(second_last_name)

        name = name.split()[0].lower()
        last_name = last_name.split(' ')[0].lower()
        second_last_name = second_last_name.split(' ')[0].lower()
        basedn = "ou=Trabajadores,dc=uh,dc=cu"
        possible_uid = name  + '.' + last_name

        if len(ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(uid=%s)(objectclass=%s))" % (possible_uid, "Trabajador"))):
            possible_uid = name + '.' +second_last_name
            if len(ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(uid=%s)(objectclass=%s))" % (possible_uid, "Trabajador"))):
                for i in range(1,1000):
                    possible_uid = name + '.' +second_last_name +str(i)
                    if len(ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(uid=%s)(objectclass=%s))" % (possible_uid, "Trabajador"))):
                        continue
                    uid = possible_uid
                    break
            else:
                uid = possible_uid
        else:
            uid = possible_uid

        return uid

    def __process_row(self, row, open_file, row_number, uidNumber):
        uid_to_use = ''
        basedn = "ou=Trabajadores,dc=uh,dc=cu"
        query_results = ldap_server.search_s(basedn, ldap.SCOPE_ONELEVEL, "(&(ci=%s)(objectclass=%s))" % (str(row[0]).strip(), "Trabajador"))
        # IF is there...
        email_to_use = ''
        if len(query_results):
            uid_to_use = query_results[0][1]["uid"][0].decode('utf8')
            print(query_results[0][1])
            try:
                email_to_use = str(query_results[0][1]["Correo"][0])
            except Exception:
                pass
            print(email_to_use)

        else:
            uid_to_use = str(self.__get_uid(str(row[1]), str(row[3]), str(row[4])))

        open_file.write("# Entry %d: \n" % row_number)
        open_file.write("%s: %s\n" % ('dn','uid='+uid_to_use+',ou=Trabajadores,dc=uh,dc=cu'))
        for entry in self.__workers_schema:
            if type(entry[1]) == list:
                open_file.write("%s: %s\n" % (entry[0], ' '.join([str(row[x]) for x in entry[1]])))
            else:
                open_file.write("%s: %s\n" % (entry[0], str(row[entry[1]])))
        
        # Entries outside the database
        open_file.write("%s: %s\n" % ('objectclass', 'Trabajador'))
        open_file.write("%s: %s\n" % ('objectclass', 'posixAccount'))
        open_file.write("%s: %s\n" % ('objectclass', 'shadowAccount'))
        open_file.write("%s: %s\n" % ('uidNumber', move_first_ceros(str(row[0]).strip())))
        open_file.write("%s: %d\n" % ('gidNumber', 10000))
        open_file.write("%s: %s\n" % ('userPassword', '12345678'))
        open_file.write("%s: %s\n" % ('homeDirectory', '/home/'+uid_to_use+'/'))
        open_file.write("%s: %s\n" % ('uid', uid_to_use))
        if len(email_to_use):
            open_file.write("%s: %s\n" % ('correo', email_to_use))

        open_file.write("\n")
        pass


def perror(msg, exit_status=1):
    print(msg)
    exit(exit_status)

def move_first_ceros(ci):
    while ci[0] == '0':
        ci = ci[1:] + ci[0]
    return ci

if __name__ == "__main__":
    handler = LDIFFromSQLServer("config.yml", 5000)
    handler.generate_ldif(number_of_rows=11, restore=False)
