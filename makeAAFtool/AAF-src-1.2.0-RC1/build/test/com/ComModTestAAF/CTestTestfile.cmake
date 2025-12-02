# CMake generated Testfile for 
# Source directory: /Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/test/com/ComModTestAAF
# Build directory: /Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/test/com/ComModTestAAF
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(ComModTestAAF "/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/Test/ComModTestAAF")
set_tests_properties(ComModTestAAF PROPERTIES  ENVIRONMENT "LD_LIBRARY_PATH=/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/RefImpl:" WORKING_DIRECTORY "/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/Test" _BACKTRACE_TRIPLES "/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/test/com/ComModTestAAF/CMakeLists.txt;116;add_test;/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/test/com/ComModTestAAF/CMakeLists.txt;0;")
add_test(ComModTestAAF-XML "/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/Test/ComModTestAAF" "-e" "XML" "-s" "AAFRandomRawStorage")
set_tests_properties(ComModTestAAF-XML PROPERTIES  ENVIRONMENT "LD_LIBRARY_PATH=/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/RefImpl:" WORKING_DIRECTORY "/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/Test" _BACKTRACE_TRIPLES "/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/test/com/ComModTestAAF/CMakeLists.txt;119;add_test;/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/test/com/ComModTestAAF/CMakeLists.txt;0;")
