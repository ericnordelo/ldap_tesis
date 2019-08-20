import yaml

if __name__ == "__main__":
    from dependences.sqlserver_manager import ConnectionManager
else:
    from app.ldif_from_database.dependences.sqlserver_manager import ConnectionManager

import os
import ldif
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

    def __process_row(self, row, open_file, row_number, uidNumber):
        open_file.write("# Entry %d: \n" % row_number)
        open_file.write("%s: %s\n" % ('dn','uid='+str(row[0]).strip()+',ou=Trabajadores,dc=uh,dc=cu'))
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
        open_file.write("%s: %s\n" % ('homeDirectory', '/'))
        open_file.write("%s: %s\n" % ('uid', str(row[0]).strip()))
        # open_file.write("%s: %s\n" % ('correo', '---------'))

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
    handler.generate_ldif(number_of_rows=10, restore=False)
