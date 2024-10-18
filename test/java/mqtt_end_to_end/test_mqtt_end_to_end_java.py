import random
import string
import sys
import os
import subprocess
import shutil
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'.replace('/', os.path.sep)))
sys.path.append(os.path.join(project_root))

import xregistry

# this test invokes the xregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both
def run_test():
    # clean the output directory
    if os.path.exists(os.path.join(project_root, 'tmp/test/java/'.replace('/', os.path.sep))):
        shutil.rmtree(os.path.join(project_root, 'tmp/test/java/'.replace('/', os.path.sep)))

    local_repo_arg = '-Dmaven.repo.local='+os.path.join(project_root, 'tmp/test/java/repo'.replace('/', os.path.sep))
    local_ce_libs = os.path.join(project_root, 'tmp/test/java/ce_libs'.replace('/', os.path.sep))
    if not os.path.exists(local_ce_libs):
        subprocess.check_call(['git', 'clone', 'https://github.com/clemensv/io.cloudevents.experimental.endpoints.git', local_ce_libs], stdout=sys.stdout, stderr=sys.stderr, shell=True)
        # build the ce libs
        subprocess.check_call(['mvn', '--quiet', 'clean', 'install', local_repo_arg], cwd=local_ce_libs, stdout=sys.stdout, stderr=sys.stderr, shell=True)

    # generate the producer
    sys.argv = ['xregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'java',
                '--definitions', os.path.join(os.path.dirname(__file__), 'mqtt_end_to_end.xreg.json'),
                '--output', os.path.join(project_root, 'tmp/test/java/mqtt_end_to_end/producer/'.replace('/', os.path.sep)),
                '--projectname', 'Contoso.ERP.Producer']
    assert xregistry.cli() == 0
    subprocess.check_call(['mvn', '--quiet', 'install', local_repo_arg], cwd=os.path.join(project_root, 'tmp/test/java/mqtt_end_to_end/producer/'.replace('/', os.path.sep)), stdout=sys.stdout, stderr=sys.stderr, shell=True)
    # generate the consumer
    sys.argv = [ 'xregistry', 'generate', 
                '--style', 'consumer', 
                '--language', 'java',
                '--definitions', os.path.join(os.path.dirname(__file__), 'mqtt_end_to_end.xreg.json'),
                '--output', os.path.join(project_root, 'tmp/test/java/mqtt_end_to_end/consumer/'),
                '--projectname', 'Contoso.ERP.Consumer']
    assert xregistry.cli() == 0
    subprocess.check_call(['mvn', '--quiet', 'clean', 'install',local_repo_arg], cwd=os.path.join(project_root, 'tmp/test/java/mqtt_end_to_end/consumer/'.replace('/', os.path.sep)), stdout=sys.stdout, stderr=sys.stderr, shell=True)
    # run mvn verify on the s here that references the generated files already
    
    subprocess.check_call(['mvn', '--quiet', 'clean', 'install', local_repo_arg], cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)
    subprocess.check_call(['java', '-jar', 'target/mqtt_end_to_end-1.0-SNAPSHOT.jar'], cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)
    
def xtest_mqtt_end_to_end():
    container_name = ''.join(random.choices(string.ascii_lowercase, k=10))
    start_command = "docker run --name {} -p 127.11.0.1:1883:1883 -v {}:/mosquitto/config/ -v {}:/mosquitto/log -d eclipse-mosquitto".\
                          format(container_name, os.path.join(os.path.dirname(__file__), 'mosquitto', 'config'), os.path.join(os.path.dirname(__file__), 'mosquitto', 'logs'))
    subprocess.run(start_command, shell=True, check=True)
    # give the broker a chance to start. wait 20 seconds
    time.sleep(30)
    
    try:
        run_test()
    finally:
        stop_command = "docker stop {}".format(container_name)
        subprocess.run(stop_command, shell=True, check=True)
        delete_command = "docker rm {}".format(container_name)
        subprocess.run(delete_command, shell=True, check=True)
