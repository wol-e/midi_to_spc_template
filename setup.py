from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='midi_to_spc_template',
      version='0.1',
      description='Create AddmusicK input file from midi',
      long_description=readme(),
      url='http://github.com/wol-e/midi',
      author='Wolfgang Spindeler @wol-e',
      author_email='',
      license='',
      packages=['midi_to_spc_template'],
      scripts=['bin/midi-to-spc-template'],
      install_requires=[
          'mido',
          'pandas'
      ],
      zip_safe=False)
