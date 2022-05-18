#!/usr/bin/env pyhton3

from os import environ
import os
from lib_grades import lib_grades
from Token import Token

DEBUG = False

if not DEBUG:
    from multilanguage import Env, Lang, TALcolors
    from TALfiles import TALfilesHelper

    # METADATA OF THIS SERVICE
    args_list = [
        ('problem', str),
        ('service', str),
        ('student', str),
        ('download', int)
    ]

    ENV = Env(args_list)
    TAc = TALcolors(ENV)
    LANG = Lang(ENV, TAc, lambda fstring: eval(f"f'{fstring}'"), print_opening_msg = 'now')
    TALf = TALfilesHelper(TAc, ENV)

# START CODING YOUR SERVICE:

def main(problem : str, service : str, token : str, path : str, student : str):
    if not Token.isTeacher(token):
        print('Unauthorized')
        return

    lg = lib_grades()
    lg.loadFile(problem, service, student, path)

    lg.getProblemList().printToConsole()

    if not DEBUG:
            if ENV['download'] == 1:
                TALf.str2output_file(lg.getProblemList().instanceToString(), "result.csv")
        
if __name__ == "__main__":
    if DEBUG:
        main("all_problems", "all_services", "_0123456789_RomeoRizzi", os.path.join(os.getcwd(), "log_algorithms"), "PincoPallo")
    else:
        main(ENV['problem'], ENV['service'], environ['TAL_META_EXP_TOKEN'], environ['TAL_META_EXP_LOG_DIR'], ENV['student'])
