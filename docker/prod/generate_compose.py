import sys
import os
import jinja2

# Jinja template directory
TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = "docker-compose.yml.j2"

# The list of commands (passed as input)
feeds = sys.argv[1:]

# Load the Jinja template
templateLoader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
templateEnv = jinja2.Environment(loader=templateLoader)
template = templateEnv.get_template(TEMPLATE_FILE)

# Render the template with the services list
output = template.render(feeds=feeds)

# Write the rendered template to a docker-compose.yml file
with open(f"docker-compose.yaml", "w") as f:
    f.write(output)

print("docker-compose.yml generated successfully!")