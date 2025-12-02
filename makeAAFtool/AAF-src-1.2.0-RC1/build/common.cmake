set(AAFSDK_VERSION_STRING "1.2.0")
set(AAFSDK_TARGET_DIR "${CMAKE_BINARY_DIR}")
set(AAFSDK_SHARED_DIR "${AAFSDK_ROOT}/out")

set(CMAKE_C_COMPILE_OBJECT "<CMAKE_C_COMPILER> <DEFINES> <INCLUDES> <FLAGS> -o <OBJECT> -c <SOURCE>")
set(CMAKE_CXX_COMPILE_OBJECT "<CMAKE_CXX_COMPILER> <DEFINES> <INCLUDES> <FLAGS> -o <OBJECT> -c <SOURCE>")

macro(target_copy_files target src dst)
  set(files ${ARGN})
  foreach(file ${files})
    add_custom_command(TARGET ${target} POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy ${src}/${file} ${dst}/${file}
      COMMENT "Copying ${file} to ${dst}"
    )
  endforeach()
endmacro()