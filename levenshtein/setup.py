# from distutils.core import setup, Extension
# setup(name='levenshtein', version='1.0',  \
#       ext_modules=[Extension('levenshtein', ['levenshtein.c'])])

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("levenshtein", ["levenshtein.pyx"])]

setup(
  name = 'Levenshtein Distance',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)
