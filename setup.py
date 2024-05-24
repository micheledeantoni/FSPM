from setuptools import setup, find_packages

# Function to load requirements from a requirements.txt file.
def load_requirements(filename):
    """Load requirements from a requirements.txt file."""
    with open(filename, 'r') as f:
        lineiter = (line.strip() for line in f)
        return [line for line in lineiter if line and not line.startswith("#")]

# Assuming your requirements.txt is in the same directory as setup.py
requirements = load_requirements("requirements.txt")

setup(
    name='FSPM',
    version='1.0',
    packages=find_packages(),
    install_requires=requirements,  # Use the loaded requirements
    entry_points={
        'gui_scripts': [
            'fspmgui = FSPM.GUI.interface:main'
        ]
    },
    author='Michele Deantoni',
    author_email='michele.deantoni.MD@gmail.com',
    description='Football Statistical Parameter Mapping Application',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/micheledeantoni',
)
