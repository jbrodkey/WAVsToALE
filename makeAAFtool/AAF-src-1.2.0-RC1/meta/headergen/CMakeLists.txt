###############################################################################
#
# $Id$ $Name$
#
# The contents of this file are subject to the AAF SDK Public Source
# License Agreement Version 2.0 (the "License"); You may not use this
# file except in compliance with the License.  The License is available
# in AAFSDKPSL.TXT, or you may obtain a copy of the License from the
# Advanced Media Workflow Association, Inc., or its successor.
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied.  See
# the License for the specific language governing rights and limitations
# under the License.  Refer to Section 3.3 of the License for proper use
# of this Exhibit.
#
# WARNING:  Please contact the Advanced Media Workflow Association,
# Inc., for more information about any additional licenses to
# intellectual property covering the AAF Standard that may be required
# to create and distribute AAF compliant products.
# (http://www.amwa.tv/policies).
#
# Copyright Notices:
# The Original Code of this file is Copyright 1998-2012, licensor of the
# Advanced Media Workflow Association.  All rights reserved.
#
# The Initial Developer of the Original Code of this file and the
# licensor of the Advanced Media Workflow Association is
# Avid Technology.
# All rights reserved.
#
###############################################################################

#
# Generate built-in metadata dictionary from ref-impl/include/AAFMetaDictionary.h.
#
# Usage:
#
#   Linux:
#       mkdir out
#       cd out
#       cmake -G "Unix Makefiles" ..
#       cmake --build .
#   Windows:
#       mkdir out
#       cd out
#       cmake -G "Visual Studio 12 2013 Win64" ..
#       cmake --build .
#   macOS:
#       mkdir out
#       cd out
#       cmake -G "Xcode" ..
#       cmake --build .

cmake_minimum_required(VERSION 3.10 FATAL_ERROR)

project(HeaderGen)

get_filename_component(CURRENT_DIR_ABS "${CMAKE_CURRENT_LIST_DIR}" ABSOLUTE)
list(APPEND CMAKE_MODULE_PATH "${AAFSDK_ROOT}/build")

set(OUT_BINARIES_DIR ${CURRENT_DIR_ABS}/bin)
set(OUT_HEADERS_DIR ${CURRENT_DIR_ABS}/include)
set(INSTALL_HEADERS_DIR ${CURRENT_DIR_ABS}/../../ref-impl/include)
set(INSTALL_BUILTINS_DIR ${CURRENT_DIR_ABS}/../../ref-impl/src/impl)

# path to generated/modified AAFMetaDictionary.h file to use
set(AAFMETADICT_PATH ${INSTALL_HEADERS_DIR}/AAFMetaDictionary_headergen.h)

include_directories(
    ${CURRENT_DIR_ABS}
    ${INSTALL_HEADERS_DIR}
)


# classDefUid
set(TARGETNAME classDefUid)
set(OUTPUTNAME AAFClassDefUIDs.h)
add_executable(${TARGETNAME} headergen_headerGenUtils_classDefUid.cpp headergen_classDefUid.cpp headerGenUtils_classDefUid.h ${AAFMETADICT_PATH})
set_target_properties(${TARGETNAME} PROPERTIES OUTPUT_NAME "${TARGETNAME}")
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG ${OUT_BINARIES_DIR})
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE ${OUT_BINARIES_DIR})
add_custom_command(TARGET ${TARGETNAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUT_HEADERS_DIR}/
    COMMAND $<TARGET_FILE:${TARGETNAME}> AAFClassDefUIDs > ${OUT_HEADERS_DIR}/${OUTPUTNAME}
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/${OUTPUTNAME} ${INSTALL_HEADERS_DIR}/${OUTPUTNAME}
    COMMENT "Generating ${OUTPUTNAME}..."
)

# extEnumUid
set(TARGETNAME extEnumUid)
set(OUTPUTNAME AAFExtEnum.h)
add_executable(${TARGETNAME} headergen_headerGenUtils_extEnumUid.cpp headergen_extEnumUid.cpp headerGenUtils_extEnumUid.h ${AAFMETADICT_PATH})
set_target_properties(${TARGETNAME} PROPERTIES OUTPUT_NAME "${TARGETNAME}")
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG ${OUT_BINARIES_DIR})
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE ${OUT_BINARIES_DIR})
add_custom_command(TARGET ${TARGETNAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUT_HEADERS_DIR}/
    COMMAND $<TARGET_FILE:${TARGETNAME}> AAFExtEnum > ${OUT_HEADERS_DIR}/${OUTPUTNAME}
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/${OUTPUTNAME} ${INSTALL_HEADERS_DIR}/${OUTPUTNAME}
    COMMENT "Generating ${OUTPUTNAME}..."
)

# propertyDefUid
set(TARGETNAME propertyDefUid)
set(OUTPUTNAME AAFPropertyDefs.h)
add_executable(${TARGETNAME} headergen_headerGenUtils_propertyDefUid.cpp headergen_propertyDefUid.cpp headerGenUtils_propertyDefUid.h ${AAFMETADICT_PATH})
set_target_properties(${TARGETNAME} PROPERTIES OUTPUT_NAME "${TARGETNAME}")
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG ${OUT_BINARIES_DIR})
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE ${OUT_BINARIES_DIR})
add_custom_command(TARGET ${TARGETNAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUT_HEADERS_DIR}/
    COMMAND $<TARGET_FILE:${TARGETNAME}> AAFPropertyDefs > ${OUT_HEADERS_DIR}/${OUTPUTNAME}
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/${OUTPUTNAME} ${INSTALL_HEADERS_DIR}/${OUTPUTNAME}
    COMMENT "Generating ${OUTPUTNAME}..."
)

# propertyId
set(TARGETNAME propertyId)
set(OUTPUTNAME AAFPropertyIDs.h)
add_executable(${TARGETNAME} headergen_headerGenUtils_propertyId.cpp headergen_propertyId.cpp headerGenUtils_propertyId.h ${AAFMETADICT_PATH})
set_target_properties(${TARGETNAME} PROPERTIES OUTPUT_NAME "${TARGETNAME}")
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG ${OUT_BINARIES_DIR})
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE ${OUT_BINARIES_DIR})
add_custom_command(TARGET ${TARGETNAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUT_HEADERS_DIR}/
    COMMAND $<TARGET_FILE:${TARGETNAME}> AAFPropertyIDs > ${OUT_HEADERS_DIR}/${OUTPUTNAME}
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/${OUTPUTNAME} ${INSTALL_HEADERS_DIR}/${OUTPUTNAME}
    COMMENT "Generating ${OUTPUTNAME}..."
)

# storedObjectUid
set(TARGETNAME storedObjectUid)
set(OUTPUTNAME AAFStoredObjectIDs.h)
add_executable(${TARGETNAME} headergen_headerGenUtils_storedObjectUid.cpp headergen_storedObjectUid.cpp headerGenUtils_storedObjectUid.h ${AAFMETADICT_PATH})
set_target_properties(${TARGETNAME} PROPERTIES OUTPUT_NAME "${TARGETNAME}")
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG ${OUT_BINARIES_DIR})
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE ${OUT_BINARIES_DIR})
add_custom_command(TARGET ${TARGETNAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUT_HEADERS_DIR}/
    COMMAND $<TARGET_FILE:${TARGETNAME}> AAFStoredObjectIDs > ${OUT_HEADERS_DIR}/${OUTPUTNAME}
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/${OUTPUTNAME} ${INSTALL_HEADERS_DIR}/${OUTPUTNAME}
    COMMENT "Generating ${OUTPUTNAME}..."
)

# typeDefUid
set(TARGETNAME typeDefUid)
set(OUTPUTNAME AAFTypeDefUIDs.h)
add_executable(${TARGETNAME} headergen_headerGenUtils_typeDefUid.cpp headergen_typeDefUid.cpp headerGenUtils_typeDefUid.h ${AAFMETADICT_PATH})
set_target_properties(${TARGETNAME} PROPERTIES OUTPUT_NAME "${TARGETNAME}")
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG ${OUT_BINARIES_DIR})
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE ${OUT_BINARIES_DIR})
add_custom_command(TARGET ${TARGETNAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUT_HEADERS_DIR}/
    COMMAND $<TARGET_FILE:${TARGETNAME}> AAFTypeDefUIDs > ${OUT_HEADERS_DIR}/${OUTPUTNAME}
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/${OUTPUTNAME} ${INSTALL_HEADERS_DIR}/${OUTPUTNAME}
    COMMENT "Generating ${OUTPUTNAME}..."
)

# genDefInstances
set(TARGETNAME genDefInstances)
add_executable(${TARGETNAME} headergen_headerGenUtils_genDefInstances.cpp headergen_genDefInstances.cpp headerGenUtils_genDefInstances.h ${AAFMETADICT_PATH})
set_target_properties(${TARGETNAME} PROPERTIES OUTPUT_NAME "${TARGETNAME}")
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG ${OUT_BINARIES_DIR})
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE ${OUT_BINARIES_DIR})
add_custom_command(TARGET ${TARGETNAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUT_HEADERS_DIR}/
    COMMAND $<TARGET_FILE:${TARGETNAME}> OperationDefinition kAAF > ${OUT_HEADERS_DIR}/AAFOperationDefs_genDefInstances.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> ParameterDefinition kAAF > ${OUT_HEADERS_DIR}/AAFParameterDefs_genDefInstances_target1.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> DataDefinition kAAF > ${OUT_HEADERS_DIR}/AAFDataDefs_genDefInstances.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> ContainerDefinition kAAF > ${OUT_HEADERS_DIR}/AAFContainerDefs_genDefInstances.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> InterpolationDefinition kAAF > ${OUT_HEADERS_DIR}/AAFInterpolatorDefs_genDefInstances.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> OPDefinition kAAF > ${OUT_HEADERS_DIR}/AAFOPDefs.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> KLVDataDefinition kAAF > ${OUT_HEADERS_DIR}/AAFKLVDataDefs.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> TaggedValueDefinition kAAF > ${OUT_HEADERS_DIR}/AAFTaggedValueDefs.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> TaggedValueDefinition kAAF > ${OUT_HEADERS_DIR}/AAFTaggedValueDefs_target1.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> PluginDefinition kAAF > ${OUT_HEADERS_DIR}/AAFPluginDefs_genDefInstances_target1.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> CodecDefinition kAAF > ${OUT_HEADERS_DIR}/AAFCodecDefs_genDefInstances.h
    COMMAND $<TARGET_FILE:${TARGETNAME}> CompressionDefinition kAAF > ${OUT_HEADERS_DIR}/AAFCompressionDefs.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFOperationDefs_genDefInstances.h ${INSTALL_HEADERS_DIR}/AAFOperationDefs_genDefInstances.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFParameterDefs_genDefInstances_target1.h ${INSTALL_HEADERS_DIR}/AAFParameterDefs_genDefInstances_target1.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFDataDefs_genDefInstances.h ${INSTALL_HEADERS_DIR}/AAFDataDefs_genDefInstances.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFContainerDefs_genDefInstances.h ${INSTALL_HEADERS_DIR}/AAFContainerDefs_genDefInstances.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFInterpolatorDefs_genDefInstances.h ${INSTALL_HEADERS_DIR}/AAFInterpolatorDefs_genDefInstances.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFOPDefs.h ${INSTALL_HEADERS_DIR}/AAFOPDefs.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFKLVDataDefs.h ${INSTALL_HEADERS_DIR}/AAFKLVDataDefs.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFTaggedValueDefs.h ${INSTALL_HEADERS_DIR}/AAFTaggedValueDefs.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFTaggedValueDefs_target1.h ${INSTALL_HEADERS_DIR}/AAFTaggedValueDefs_target1.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFPluginDefs_genDefInstances_target1.h ${INSTALL_HEADERS_DIR}/AAFPluginDefs_genDefInstances_target1.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFCodecDefs_genDefInstances.h ${INSTALL_HEADERS_DIR}/AAFCodecDefs_genDefInstances.h
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/AAFCompressionDefs.h ${INSTALL_HEADERS_DIR}/AAFCompressionDefs.h
    COMMENT "Generating definition headers..."
)

# genDefInstBuiltins
set(TARGETNAME genDefInstBuiltins)
add_executable(${TARGETNAME} headergen_headerGenUtils_genDefInstBuiltins.cpp headergen_genDefInstBuiltins.cpp headerGenUtils_genDefInstBuiltins.h ${AAFMETADICT_PATH})
set_target_properties(${TARGETNAME} PROPERTIES OUTPUT_NAME "${TARGETNAME}")
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG ${OUT_BINARIES_DIR})
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE ${OUT_BINARIES_DIR})
add_custom_command(TARGET ${TARGETNAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUT_HEADERS_DIR}/
    COMMAND $<TARGET_FILE:${TARGETNAME}> DataDefinition kAAF > ${OUT_HEADERS_DIR}/ImplAAFDictionary.cpp_target1
    COMMAND $<TARGET_FILE:${TARGETNAME}> ContainerDefinition kAAF > ${OUT_HEADERS_DIR}/ImplAAFDictionary.cpp_target2
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/ImplAAFDictionary.cpp_target1 ${INSTALL_BUILTINS_DIR}/ImplAAFDictionary.cpp_target1
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/ImplAAFDictionary.cpp_target2 ${INSTALL_BUILTINS_DIR}/ImplAAFDictionary.cpp_target2
)

# result
set(TARGETNAME result)
set(OUTPUTNAME AAFResult.h)
add_executable(${TARGETNAME} headergen_headerGenUtils_result.cpp headergen_result.cpp headerGenUtils_result.h ../../ref-impl/include/AAFMetaResult.h)
set_target_properties(${TARGETNAME} PROPERTIES OUTPUT_NAME "${TARGETNAME}")
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG ${OUT_BINARIES_DIR})
set_target_properties(${TARGETNAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE ${OUT_BINARIES_DIR})
add_custom_command(TARGET ${TARGETNAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUT_HEADERS_DIR}/
    COMMAND $<TARGET_FILE:${TARGETNAME}> AAFResult > ${OUT_HEADERS_DIR}/${OUTPUTNAME}
    COMMAND ${CMAKE_COMMAND} -E copy ${OUT_HEADERS_DIR}/${OUTPUTNAME} ${INSTALL_HEADERS_DIR}/${OUTPUTNAME}
    COMMENT "Generating ${OUTPUTNAME}..."
)

add_custom_target(HeaderGen ALL
    DEPENDS classDefUid extEnumUid propertyDefUid propertyId storedObjectUid typeDefUid genDefInstances genDefInstBuiltins result
    COMMENT "Generating all headers..."
)
