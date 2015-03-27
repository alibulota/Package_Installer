#!usr/bin/env python
from subprocess import call
import urllib2
import os
import sys
import re
import json

CACHED_PATHS = {}


def scan(target_name):
    """
    Return the full file path to a file, including file_name.

    If the file is not found, print 'File or directory not found'
    to the console and return None.
    """
    if CACHED_PATHS[target_name]:
        return CACHED_PATHS[target_name]
    else:
        extension = os.path.splitext(target_name)[1]
        if 'Windows' in os.environ.get('OS'):
            # Assumes the drive letter is C
            walker = os.walk('C:/')
        else:
            walker = os.walk('/')
        if extension:
                # Search for a file
            for directory, sub_dir, files in walker:
                for each_file in files:
                    if re.match(target_name, each_file):
                        return directory + target_name
        else:
            # Search for a directory
            for directory, sub_dir, files in walker:
                if re.search("/{}".format(target_name), directory):
                    return directory
        # If the whole directory has been scanned with
        # no result...
        print 'File or directory not found'
        return None

def execute(command_line):
    command_line = command_line
    if 'win' not in sys.platform:
        command_line.insert(0, 'sudo')
    call(command_line)

{% for choice in choices %}
{% spaceless %}
# For choice {{choice.name}}
{% for step in choice.ordered_steps %}
{% spaceless %}

{% if step.step_type == 'dl' %}

# Download and run {{step}}
url = '{{step.url}}'
scan_result = None
not_linux = True

{% if choice.category == 'git' %}
# Detect OS and change url accordingly...
if 'win' in sys.platform:
    # The url for git will be the url used for the windows exe
    print 'Windows detected'
elif 'darwin' in sys.platform:
    print 'Mac detected'
    url = None
elif 'linux' in sys.platform:
    print 'Linux detected'
    not_linux = False
else:
    print 'WARNING: Failed to determine OS'
{% endif %}

if not_linux and url:
    print "Downloading from {}".format(url)
    response = urllib2.urlopen(url)
    {% if step.args %}
    scan_result = scan('{{step.args}}')

    if scan_result:
        file_name = scan_result + os.path.basename('{{step.url}}')
    else:
        file_name = ""
    {% else %}
    file_name = os.path.basename(url)
    {% endif %}

    if not "{{step.args}}" or scan_result:
        with open(file_name, 'wb') as f:
            f.write(response.read())

        if os.path.splitext(file_name)[1] == '.py':
            execute([sys.executable, file_name])
            {% if choice.category == 'git' %}
            raw_input('Enter anything to continue when finished installing git.')
            {% endif %}
        else:
            print "Running file_name"
            execute(['./'+file_name])

{% if choice.category == 'git' %}
elif url is None:
    call(['sudo', 'xcode-select', '--install'])
    raw_input('Enter anything to continue when finished installing xcode and git.')
else:
    # This will prompt user for sudo password
    call(['sudo', 'apt-get', 'install', 'git'])
{% endif %}
{% endif %}

{% if step.step_type == 'edprof' %}
# Edit a profile
profile_name = os.path.expanduser('~/')+'.bashrc'
print 'Adding {{step.args|safe}} to ~/.bashrc'
with open(profile_name, 'a') as f:
    f.write('\n'+'export {{step.args|safe}}')
# call(['source', '~/.bashrc'])
{% endif %}

{% if step.step_type == 'edfile' %}
scan_result = None
scan_result = scan('{{step.args}}') 
if scan_result:
    file_name = scan_result + os.path.basename('{{step.url}}')
else:
    file_name = ""

if file_name:
{% if choice.category == 'subl' %}
    with open(file_name, 'w+') as f:
        settings_as_json = json.loads(f.read())
        key, val = "{{step.args}}".split(',')
        settings_as_json[key] = val
        f.write(json.dumps(settings_as_json))
{% else %}
    with open(file_name, 'a') as f:
        f.write('{{step.args}}')
{% endif %}
else:
    print "file not found"

{% endif %}

{% if step.step_type == 'env' %}
# Add a key, value pair for a subsequent call([])
key, val = "{{step.args}}".split(',')
os.putenv(key, val)
{% endif %}

{% if step.step_type == 'pip' %}
# Pip install, assuming the exact name of the package as used for 'pip install [package]'
# is given in the args field for a step
execute(['pip', 'install', "{{step.args}}"])
{% endif %}

{% if step.step_type == 'exec' %}
command_line = "{{step.args}}".split(',')
print "Executing " + ' '.join(command_line)
execute(command_line)
{% endif %}

{% endspaceless %}
{% endfor %}

{% endspaceless %}
{% endfor %}