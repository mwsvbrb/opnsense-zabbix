import json
import subprocess
import sys
import xml.etree.ElementTree as ET

# Parse the XML configuration file
root = ET.parse('/conf/config.xml').getroot()

# Run the 'ifconfig' command and capture its output
with subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE) as process:
    if len(sys.argv) == 3:
        want_name = sys.argv[1]
        want_value = sys.argv[2]
    else:
        want_name = False
        want_value = False

    interfaces = []
    interface = None

    # Process each line of the 'ifconfig' output
    for line in process.stdout:
        line = line.decode('utf-8')
        if not line.startswith('\t'):
            # New interface block
            name = line.split(':')[0]

            # Skip if the interface name does not match the desired name
            if want_name and want_name != name:
                continue

            # Append the previous interface to the list
            if interface is not None:
                interfaces.append(interface)

            # Start a new interface dictionary
            interface = {'name': name}

            # Find the interface description in the XML configuration
            interfaces_element = root.find('interfaces')
            if interfaces_element is not None:
                for conf_interface in interfaces_element:
                    if_element = conf_interface.find('if')
                    descr_element = conf_interface.find('descr')
                    if if_element is not None and if_element.text == name:
                        if descr_element is not None:
                            interface['description'] = descr_element.text
        else:
            # Continue processing the current interface
            if interface is None:
                continue

            line = line.strip()
            data = line.split(':')
            if len(data) < 2:
                continue

            field_name = data[0]
            if want_value and field_name != want_value:
                continue

            # Process specific fields
            fields = data[1].split(' ')
            if field_name == 'carp':
                interface['carp'] = 0 if fields[1] == 'MASTER' else 1
            elif field_name == 'status' and 'status' not in interface:
                interface['status'] = data[1].strip()  # Remove leading/trailing whitespace

    # Append the last interface to the list
    if interface is not None:
        interfaces.append(interface)

# Print the results in JSON format
if not want_name:
    print(json.dumps(interfaces, indent=2))
else:
    if want_name == 'lo0' and want_value == 'status':
        print('active')
    else:    
        print(interfaces[0].get(want_value, 'Value not found'))
