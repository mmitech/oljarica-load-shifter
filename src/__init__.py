import os
import importlib

# Get the path to the current directory
package_dir = os.path.dirname(__file__)

# Iterate over the files in the package directory
for file_name in os.listdir(package_dir):
    if file_name.endswith('.py') and file_name != '__init__.py':
        # Construct the module name by removing the file extension
        module_name = file_name[:-3]

        # Import the module dynamically
        module = importlib.import_module(f'{__name__}.{module_name}')

        # Optionally, you can do something with the imported module
        # For example, you can access its functions or variables
        print(f"Module {module_name} imported successfully.")