# -*- coding: utf-8 -*-

import yaml
import zeep
import sys

wsdl = 'http://sigenuwebservices.uh.cu/servicedefinition.wsdl'
client = zeep.Client(wsdl=wsdl)

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

    def generate_first_time_population(self, number_of_rows=0):
        """Generates the ldif file from the webservices to populate the ldap
        for the first time overriding existing data.
        The second parameter is for testing and should be ignored."""
        
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
                        self.__process_row(row, f, row_number, uidNumber, faculty["id"])
                        row_number += 1
                        uidNumber+=1
                    except Exception:
                        problems.append(row["idsigenu"])

            counter = 0
            for problem in problems:
                f.write("# Problem %d (Sigenu ID): %s\n" % (counter, problem))
                counter+=1

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


    def __process_row(self, row, open_file, row_number, uidNumber, faculty_id):

        open_file.write("# Entry %d: \n" % row_number)
        for entry in self.__students_schema:
            open_file.write("%s: %s\n" % (entry[0], str(row[entry[1]])))
        
        # Entries outside the services
        open_file.write("%s: %s\n" % ('dn', 'Estudiante'))
        open_file.write("%s: %s\n" % ('idfacultad', faculty_id))
        open_file.write("%s: %s\n" % ('cuotadeinternet', "0"))
        open_file.write("%s: %s\n" % ('pcc', str(row["politic_org"] == "pcc")))
        open_file.write("%s: %s\n" % ('ujc', str(row["politic_org"] == "ujc")))
        open_file.write("%s: %s\n" % ('esbaja', str(row["status"] == "Activo")))
        open_file.write("%s: %s\n" % ('objectclass', 'Estudiante'))
        open_file.write("%s: %s\n" % ('objectclass', 'posixAccount'))
        open_file.write("%s: %s\n" % ('objectclass', 'shadowAccount'))
        open_file.write("%s: %d\n" % ('uidNumber', uidNumber))
        open_file.write("%s: %d\n" % ('gidNumber', 10000))
        open_file.write("%s: %s\n" % ('homeDirectory', '---------'))
        open_file.write("%s: %d\n" % ('uid', uidNumber))

        open_file.write("\n")
        pass


def perror(msg, exit_status=1):
    print(msg)
    exit(exit_status)


if __name__ == "__main__":
    handler = SigenuClient("config.yml")
    handler.generate_first_time_population(number_of_rows=10)