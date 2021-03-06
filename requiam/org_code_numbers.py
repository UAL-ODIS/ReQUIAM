from os import path
from os import mkdir

# For database/CSV
import pandas as pd
import numpy as np
from urllib.error import URLError

# For LDAP query
from .ldap_query import ual_grouper_base, ual_ldap_query, ldap_search

from datetime import date

today = date.today()


def get_numbers(lc, org_url, log_func):
    """
    Purpose:
      Determine number of individuals in each organization code with
      Library privileges

    :param lc: LDAPConnection() object
    :param org_url: URL that provides CSV
    :param log_func: LogClass object for logging

    :return ldc:
    """

    try:
        df = pd.read_csv(org_url)

        n_org_codes = df.shape[0]
        log_func.info(f"Number of organizational codes : {n_org_codes}")

        org_codes = df['Organization Code'].values

        # Arrays for members with library privileges based on classification
        total       = np.zeros(n_org_codes, dtype=int)
        lib_total   = np.zeros(n_org_codes, dtype=int)
        lib_faculty = np.zeros(n_org_codes, dtype=int)
        lib_staff   = np.zeros(n_org_codes, dtype=int)
        lib_student = np.zeros(n_org_codes, dtype=int)
        lib_dcc     = np.zeros(n_org_codes, dtype=int)

        # Query based on Library patron group for set logic
        faculty_query = ['({})'.format(ual_grouper_base('ual-faculty'))]
        staff_query   = ['({})'.format(ual_grouper_base('ual-staff'))]
        student_query = ['({})'.format(ual_grouper_base('ual-students'))]
        dcc_query     = ['({})'.format(ual_grouper_base('ual-dcc'))]

        log_func.info("Getting faculty, staff, student, and dcc members ... ")
        faculty_members = ldap_search(lc, faculty_query)
        staff_members   = ldap_search(lc, staff_query)
        student_members = ldap_search(lc, student_query)
        dcc_members     = ldap_search(lc, dcc_query)
        log_func.info("Completed faculty, staff, student, and dcc queries")

        for org_code, ii in zip(org_codes, range(n_org_codes)):

            if ii % round(n_org_codes/10) == 0 or ii == n_org_codes-1:
                log_func.info("{0: >3}% completed ...".format(round((ii+1)/n_org_codes * 100)))

            total_members   = ldap_search(lc, ual_ldap_query(org_code,
                                                             classification='none'))
            library_members = ldap_search(lc, ual_ldap_query(org_code))

            total[ii]       = len(total_members)
            lib_total[ii]   = len(library_members)

            lib_faculty[ii] = len(library_members & faculty_members)
            lib_staff[ii]   = len(library_members & staff_members)
            lib_student[ii] = len(library_members & student_members)
            lib_dcc[ii]     = len(library_members & dcc_members)

        df['total']         = total
        df['pgrps-tot']     = lib_total
        df['pgrps-faculty'] = lib_faculty
        df['pgrps-staff']   = lib_staff
        df['pgrps-student'] = lib_student
        df['pgrps-dcc']     = lib_dcc

        df_sort = df.sort_values(by='Organization Code')
        df_sort.to_csv('org_code_numbers.csv', index=False)

    except URLError:
        log_func.info("Unable to retrieve data from URL !")
        log_func.info("Please check your internet connection !")
        log_func.info("create_csv terminating !")
        raise URLError("Unable to retrieve Google Sheet")
