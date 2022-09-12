#!/usr/bin/env python3
from sys import stderr, stdout, exit, argv
from os import environ
import os.path

from multilanguage import Env, Lang, TALcolors

problem=os.path.split(environ["TAL_META_DIR"])[-1]
args_list = [
    ('service',str),
    ('metafile',str),
]

ENV =Env(args_list)
TAc =TALcolors(ENV)
LANG=Lang(ENV, TAc, lambda fstring: eval(f"f'{fstring}'"))

def die_or_overcome(succeed_or_die):
    if succeed_or_die:
        for out in [stdout, stderr]:
            print(LANG.render_feedback("operation-necessary", ' This operation is necessary. The synopsis service aborts and drops the channel.'), file=out)
        exit(1)
    else:
        for out in [stdout, stderr]:
            print(LANG.render_feedback("operation-not-necessary", ' We overcome this problem by resorting on the information hardcoded within the meta.yaml file set as default by whom has deployed the problem on the server you are receiving this information from. Hope that getting the problem specific information from this file is good enough for you (it is reasonable to expect that the metafile set as default is the most updated one).'), file=out)
        return None

def regex_with_single_match_for_sure(regex:str):
    for c in regex:
        if c in '[]\.*+?{}|()':
            return False
    return True
    
def load_meta_yaml_file(meta_yaml_file, succeed_or_die):
    try:
        import ruamel.yaml
    except Exception as e:
        print(e)
        for out in [stdout, stderr]:
            TAc.print(LANG.render_feedback("ruamel-missing", 'Internal error (if you are invoking a cloud service, please, report it to those responsible for the service hosted; otherwise, install the python package \'ruamel\' on your machine).'), "red", ["bold"], file=out)
            print(LANG.render_feedback("ruamel-required", ' the service \'synopsis\' needs to read the .yaml files of the problem in order to provide you with the information required. If \'ruamel\' is not installed in the environment where the \'rtald\' daemon runs, the service \'synopsis\' can not perform.'), file=out)
            print(LANG.render_feedback("operation-necessary", ' This operation is necessary. The synopsis service aborts and drops the channel.'), file=out)
        exit(1)
    try:
      with open(meta_yaml_file, 'r') as stream:
        try:
            meta_yaml_book = ruamel.yaml.safe_load(stream)
        except:
            for out in [stdout, stderr]:
                TAc.print(LANG.render_feedback("metafile-unparsable", f'Internal error (if you are invoking a cloud service, please, report it to those responsible for the service hosted; otherwise, signal it to the problem maker unless you have altered the file yourself): The file \'{meta_yaml_file}\' could not be loaded as a .yaml file.'), "red", ["bold"], file=out)
            return die_or_overcome(succeed_or_die)
    except IOError as ioe:
        for out in [stdout, stderr]:
            TAc.print(LANG.render_feedback("metafile-missing", f'Internal error (if you are invoking a cloud service, please, report it to those responsible for the service hosted; otherwise, signal it to the problem maker unless you have altered the file yourself): The required yaml file of problem "{ENV.problem}" could not be accessed for the required information. File not found: \'{meta_yaml_file}\''), "red", ["bold"], file=out)
            print(ioe, file=out)
        return die_or_overcome(succeed_or_die)
    return meta_yaml_book


meta_yaml_book = None
if environ["TAL_metafile"] not in ["main","default"]:
    meta_yaml_file = os.path.join(environ["TAL_META_DIR"],f'meta.{environ["TAL_metafile"]}.yaml')
    meta_yaml_book = load_meta_yaml_file(meta_yaml_file, succeed_or_die = False)
if meta_yaml_book == None:
    meta_yaml_file = os.path.join(environ["TAL_META_DIR"],"meta.yaml")
    meta_yaml_book = load_meta_yaml_file(meta_yaml_file, succeed_or_die = True)
    
if ENV['service'] not in meta_yaml_book['services'].keys():
    TAc.print(LANG.render_feedback("wrong-service-name", f'\nSorry, you asked information about service "{ENV["service"]}" which however does not appear among the services currently offered for problem "{problem}".'), "red", ["bold"])
    TAc.print('\n\nList of all Services:', "red", ["bold", "underline"], end="  ")
    print(", ".join(meta_yaml_book['services'].keys()),end="\n\n")
    exit(0)

service_of = LANG.render_feedback("service-of", f'   (service of the "{problem}" problem)')
TAc.print("\n"+ENV['service'], "yellow", ["bold"], end="")
TAc.print(service_of, "yellow", end="")
TAc.print(LANG.render_feedback("info-source", f' [the problem specific information for this SYNOPSIS help sheet is gathered from the .yaml file \'{meta_yaml_file}\']'), "green")

if "description" in meta_yaml_book['services'][ENV['service']].keys():
    #CLEANED-OUT f-string
    TAc.print("\n"+LANG.render_feedback('description', 'Description') % {'problem':problem} +":", "green", ["bold"])
    for line in meta_yaml_book['services'][ENV['service']]['description'].split('\n'):
        #CLEANED-OUT f-string
        print("   "+line % {'problem':problem} )
if "example" in meta_yaml_book['services'][ENV['service']].keys():
    if type(meta_yaml_book["services"][ENV["service"]]["example"]) == str:
        TAc.print(f"   {LANG.render_feedback('example', 'Example')}: ", ["bold"], end="")
        print(meta_yaml_book['services'][ENV['service']]['example'])
    elif type(meta_yaml_book["services"][ENV["service"]]["example"]) == list:
        TAc.print("   " + LANG.render_feedback('example-tagged', f'Example [{meta_yaml_book["services"][ENV["service"]]["example"][0]}]') +": ", ["bold"], end="")
        print(meta_yaml_book['services'][ENV['service']]['example'][1])
else:
    i = 1
    while ("example"+str(i)) in meta_yaml_book['services'][ENV['service']].keys():
      if type(meta_yaml_book["services"][ENV["service"]]["example"+str(i)]) == str:
        TAc.print(f"   {LANG.render_feedback('example', 'Example')} {i}: ", ["bold"], end="")
        print(meta_yaml_book['services'][ENV['service']]['example'+str(i)])
      elif type(meta_yaml_book["services"][ENV["service"]]["example"+str(i)]) == list:
        TAc.print("   " + LANG.render_feedback('example-tagged', f'Example {i} [{meta_yaml_book["services"][ENV["service"]]["example"+str(i)][0]}]') +": ", ["bold"], end="")
        print(meta_yaml_book['services'][ENV['service']]['example'+str(i)][1])
      i += 1
args_eliminanda = []
for arg in meta_yaml_book['services'][ENV['service']]['args']:
    if regex_with_single_match_for_sure(meta_yaml_book['services'][ENV['service']]['args'][arg]['regex']):
        args_eliminanda.append(arg)
for arg in args_eliminanda:
    del meta_yaml_book['services'][ENV['service']]['args'][arg]
if len(meta_yaml_book['services'][ENV['service']]['args']) > 0:
    TAc.print(LANG.render_feedback("the-num-arguments", f'\nThe service {ENV["service"]} has {len(meta_yaml_book["services"][ENV["service"]]["args"])} arguments:'), "green", ["bold"])
    for a,i in zip(meta_yaml_book['services'][ENV['service']]['args'],range(1,1+len(meta_yaml_book['services'][ENV['service']]['args']))):
        TAc.print(str(i)+". ", "white", ["bold"], end="")
        TAc.print(a, "yellow", ["bold"])
        TAc.print('   regex: ', ["bold"], end="")
        print(meta_yaml_book['services'][ENV['service']]['args'][a]['regex'])
        if "regex-explained" in meta_yaml_book['services'][ENV['service']]['args'][a].keys():
            TAc.print('   regex-explained: ', ["bold"], end="")
            print(meta_yaml_book['services'][ENV['service']]['args'][a]['regex-explained'])
        if "regex-URL" in meta_yaml_book['services'][ENV['service']]['args'][a].keys():
            TAc.print('   regex-URL: ', ["bold"], end="Ctrl-click on the link ")
            print(meta_yaml_book['services'][ENV['service']]['args'][a]['regex-URL'])
        if "default" in meta_yaml_book['services'][ENV['service']]['args'][a].keys():
            TAc.print('   Default Value: ', ["bold"], end="")
            print(meta_yaml_book['services'][ENV['service']]['args'][a]['default'])
        else:
            TAc.print(f'   The argument {a} is mandatory.', ["bold"])
        if "explain" in meta_yaml_book['services'][ENV['service']]['args'][a].keys():
            if type(meta_yaml_book["services"][ENV["service"]]['args'][a]["explain"]) == str:
                TAc.print(f"   {LANG.render_feedback('explain', 'Explanation')}: ", ["bold"], end="")
                #CLEANED-OUT f-string
                print(meta_yaml_book['services'][ENV['service']]['args'][a]['explain'] % {'problem':problem} )
            elif type(meta_yaml_book["services"][ENV["service"]]['args'][a]["explain"]) == list:
                #CLEANED-OUT f-string
                TAc.print("   " + LANG.render_feedback('explain-tagged', f'Explanation [{meta_yaml_book["services"][ENV["service"]]["args"][a]["explain"][0]}]') +": ", ["bold"], end="")
                print(meta_yaml_book['services'][ENV['service']]['args'][a]['explain'][1] % {'problem':problem} )
        i = 1
        while ("explain"+str(i)) in meta_yaml_book['services'][ENV['service']]['args'][a].keys():
          if type(meta_yaml_book["services"][ENV["service"]]['args'][a]["explain"+str(i)]) == str:
            print(" "*6, end="")
                #CLEANED-OUT f-string
            print(meta_yaml_book['services'][ENV['service']]['args'][a]['explain'+str(i)] % {'problem':problem} )
            #TAc.print(f"   {LANG.render_feedback('explain', 'Explanation')} {i}: ", ["bold"], end="")
            #print(eval(f"f'{meta_yaml_book['services'][ENV['service']]['args'][a]['explain'+str(i)]}'"))
          elif type(meta_yaml_book["services"][ENV["service"]]['args'][a]["explain"+str(i)]) == list:
            TAc.print("   " + LANG.render_feedback('explain-tagged', f'Explanation {i} [{meta_yaml_book["services"][ENV["service"]]["args"][a]["explain"+str(i)][0]}]') +": ", ["bold"], end="")
            #CLEANED-OUT f-string
            print(meta_yaml_book['services'][ENV['service']]['args'][a]['explain'+str(i)][1] % {'problem':problem} )
          i += 1
        if "example" in meta_yaml_book['services'][ENV['service']]['args'][a].keys():
            if type(meta_yaml_book["services"][ENV["service"]]['args'][a]["example"]) == str:
                TAc.print(f"   {LANG.render_feedback('example', 'Example')}: ", ["bold"], end="")
                print(meta_yaml_book['services'][ENV['service']]['args'][a]['example'])
            elif type(meta_yaml_book["services"][ENV["service"]]['args'][a]["example"]) == list:
                TAc.print("   " + LANG.render_feedback('example-tagged', f'Example [{meta_yaml_book["services"][ENV["service"]]["args"][a]["example"][0]}]') +": ", ["bold"], end="")
                print(meta_yaml_book['services'][ENV['service']]['args'][a]['example'][1])
        else:
            i = 1
            while ("example"+str(i)) in meta_yaml_book['services'][ENV['service']]['args'][a].keys():
              if type(meta_yaml_book["services"][ENV["service"]]['args'][a]["example"+str(i)]) == str:
                TAc.print(f"   {LANG.render_feedback('example', 'Example')} {i}: ", ["bold"], end="")
                print(meta_yaml_book['services'][ENV['service']]['args'][a]['example'+str(i)])
              elif type(meta_yaml_book["services"][ENV["service"]]['args'][a]["example"+str(i)]) == list:
                TAc.print("   " + LANG.render_feedback('example-tagged', f'Example {i} [{meta_yaml_book["services"][ENV["service"]]["args"][a]["example"+str(i)][0]}]') +": ", ["bold"], end="")
                print(meta_yaml_book['services'][ENV['service']]['args'][a]['example'+str(i)][1])
              i += 1
        if "note" in meta_yaml_book['services'][ENV['service']]['args'][a].keys():
            #CLEANED-OUT f-string
            TAc.print(f"   {LANG.render_feedback('note', 'Note')}: ", ["bold"], end="")
            print(meta_yaml_book['services'][ENV['service']]['args'][a]['note'] % {'problem':problem} )
        else:    
            i = 1
            while ("note"+str(i)) in meta_yaml_book['services'][ENV['service']]['args'][a].keys():
                TAc.print(f"   {LANG.render_feedback('note', 'Note')} {i}: ", ["bold"], end="")
                #CLEANED-OUT f-string
                print(meta_yaml_book['services'][ENV['service']]['args'][a]['note'+str(i)] % {'problem':problem} )
                i += 1        

print(LANG.render_feedback("regex-cloud-resource", '\nThe arguments of all TALight services take in as possible values only simple strings that can be streamed from the \'rtal\' client to the \'rtald\' daemon (and finally acquired as environment variables). For each argument, the family of allowed string values is described by means of a regex. If the correct interpretation of the regex confuses you, then take profit of the online support at \'https://extendsclass.com/regex-tester.html\'.\n'))

# Now printing the footing lines:
if "help" in meta_yaml_book['services'].keys():
    TAc.print(LANG.render_feedback("index-help-pages", 'Index of the Help Pages:'), "red", ["bold", "underline"], end="  ")
    print(meta_yaml_book['services']['help']['args']['page']['regex'][2:-2])
TAc.print(LANG.render_feedback("list-services", f'List of all services for problem "{problem}":'), "red", ["bold", "underline"], end="  ")
print(",  ".join(TAc.colored(_, "yellow", ["bold"]) for _ in meta_yaml_book['services'].keys()))
    
exit(0)




